#!/usr/bin/env python3
"""archviz consistency kit — one portable file, per-repo config, stdlib only.

Why one file and not six
------------------------
The archviz family is five repositories that share one design system. The
existing convention is "archviz-diagram is the source, the others carry synced
copies" — which is exactly the disease this kit treats: a fact written in more
than one place drifts. Six checkers copied into five repos is thirty places.

So: **one** checker file, plus one `archviz-checks.json` per repo. The config
differs per repo because the repos genuinely differ; the code does not.

    scripts/check_archviz.py                  # run every configured check
    scripts/check_archviz.py --only routing   # run one check
    scripts/check_archviz.py --list           # list configured checks
    scripts/check_archviz.py --self-test      # adversarial fixtures
    scripts/check_archviz.py --self-hash      # KIT_VERSION + sha256 (drift audit)

Checks
------
  version   SKILL.md `metadata.version` is the release truth; CHANGELOG top
            entry and pyproject.toml are checked against it, and declared code
            files may not carry a hardcoded semver literal.
  budget    SKILL.md LF-normalized bytes <= the configured cap. The cap counts
            LF-normalized bytes, so a checkout with core.autocrlf=true measures
            the committed size and normalisation never loosens the gate.
  routing   Every name in every declared registry appears in the frontmatter
            `description` — the only text an agent reads *before* deciding to
            load the skill. Names may be satisfied by a declared alias.
  counts    Declared count claims match a computed truth. Claims are located by
            a semantic regex, never by grepping for the bare number: a table
            row `| 14 | Pyramid / funnel |` uses 14 as an ordinal, and a naive
            digit search reports it as a stale count.
  cjk       Declared files decode as UTF-8, HTML files declare a charset, and
            no file carries a mojibake signature. This family is CJK-first, so
            an encoding fault is a content fault, not a cosmetic one.
  palette   Optional: the palette registry is written down in several places
            and they must agree. Off unless the config declares it.

Exit codes
----------
  0  every configured check passed
  1  at least one check failed
  2  usage / IO error, or the config could not be read

The kit deliberately never imports the project package. Two of the five repos
have no virtualenv, and a checker that cannot run in the repo it guards is not
a gate.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path

KIT_VERSION = 1

ROOT = Path(__file__).resolve().parent.parent
CONFIG_NAME = "archviz-checks.json"

SEMVER = r"\d+\.\d+\.\d+"
BARE_SEMVER_RE = re.compile(rf"\A{SEMVER}\Z")

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
META_BLOCK_RE = re.compile(r"^metadata:\s*$(.*?)(?=^\S|\Z)", re.S | re.M)
META_VERSION_RE = re.compile(rf"^\s+version:\s*\"?({SEMVER})\"?\s*$", re.M)
DESCRIPTION_RE = re.compile(r"^description:\s*(.*?)(?=^\S|\Z)", re.S | re.M)
TRIGGERS_RE = re.compile(r"^\s+triggers:\s*(.*?)(?=^\S|\Z)", re.S | re.M)
CHANGELOG_RE = re.compile(rf"^##\s+v?({SEMVER})\b", re.M)
PYPROJECT_RE = re.compile(rf"^version\s*=\s*\"({SEMVER})\"\s*$", re.M)

# A UTF-8 payload read as latin-1/cp1252 leaves these. They are high-signal:
# none of them occurs in legitimate English or Chinese prose.
MOJIBAKE_MARKERS = ("â€", "Ã¢", "ï¼", "ã€", "Ã¤", "Ã©", "Ã¨", "Ã¶", "Ã¼", "ÃŸ", "Â·", "Ã±")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")


# ─────────────────────────── 通用 ───────────────────────────


class Result:
    """One check's verdict. `notes` are printed only on success."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.failures: list[str] = []
        self.notes: list[str] = []
        self.skipped: str = ""

    def fail(self, msg: str) -> None:
        self.failures.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    def skip(self, why: str) -> None:
        self.skipped = why

    @property
    def ok(self) -> bool:
        return not self.failures


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def lf_bytes(path: Path) -> int:
    """Byte length with CRLF normalised to LF.

    Counts the committed size rather than the checkout's, so the gate does not
    depend on the developer's `core.autocrlf`.
    """
    return len(path.read_bytes().replace(b"\r\n", b"\n"))


def compile_re(pattern: str, flags: str = "") -> re.Pattern[str]:
    f = 0
    if "M" in flags:
        f |= re.M
    if "S" in flags:
        f |= re.S
    if "I" in flags:
        f |= re.I
    return re.compile(pattern, f)


def code_semver_literals(src: str) -> list[tuple[int, str]]:
    """`(lineno, value)` for semver string literals in *code*.

    AST-based rather than a regex over the raw text: a regex also matches semver
    mentioned in comments and docstrings, which is exactly where a "we used to
    hardcode 0.2.5 here" note belongs. Only real string constants that are not
    docstrings count.
    """
    import ast

    tree = ast.parse(src)
    docstrings: set[int] = set()
    doc_owners = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(node, doc_owners) or not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            docstrings.add(id(first.value))

    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if id(node) in docstrings:
            continue
        if BARE_SEMVER_RE.match(node.value.strip()):
            hits.append((node.lineno, node.value.strip()))
    return hits


# ─────────────────────────── 注册表 ───────────────────────────


def registry_names(root: Path, spec: dict) -> list[str]:
    """Extract a registry's names from its declared source.

    Kinds:
      source_regex    regex over a source file (`block` then `entry`)
      markdown_table  regex over a markdown table (`entry`, capture group 1)
      literal         names listed in the config itself (last resort)
    """
    kind = spec.get("kind")
    if kind == "literal":
        return list(spec.get("values", []))

    path = root / spec["file"]
    if not path.exists():
        raise FileNotFoundError(f"registry source not found: {path}")
    text = read_text(path)

    if kind == "source_regex":
        block = spec.get("block")
        scope = text
        if block:
            m = compile_re(block, spec.get("block_flags", "MS")).search(text)
            if not m:
                raise ValueError(f"registry block not found in {spec['file']}: {block}")
            scope = m.group(1)
        return compile_re(spec["entry"], spec.get("flags", "M")).findall(scope)

    if kind == "markdown_table":
        return [n.strip() for n in compile_re(spec["entry"], spec.get("flags", "M")).findall(text)]

    raise ValueError(f"unknown registry kind: {kind!r}")


def normalise(name: str) -> str:
    """Fold a type name for matching.

    Hyphens, underscores and runs of whitespace all become one space, so
    `stacked-bar` and `stacked bar` are the same name. Case is folded.
    """
    return re.sub(r"[\s_-]+", " ", name.strip().lower())


ASCII_ONLY_RE = re.compile(r"\A[\x00-\x7F]*\Z")


def mentions(haystack: str, needle: str) -> bool:
    """True if *needle* is routed by *haystack*.

    ASCII needles are matched on word boundaries; non-ASCII ones are not.

    Word boundaries are load-bearing for ASCII: `treemap` contains `tree`, so a
    substring test would report the Tree type as routed by a description that
    never names it. They are meaningless for CJK, where every character is a
    word character: `\\b手绘\\b` does not match inside `手绘风格`, so a Chinese
    alias would silently never be satisfiable. The rule is therefore
    "boundaries for ASCII, substring for CJK", not one or the other.
    """
    n = normalise(needle)
    pattern = r"\b" + re.escape(n) + r"\b" if ASCII_ONLY_RE.match(n) else re.escape(n)
    return re.search(pattern, haystack) is not None


# ─────────────────────────── 各检查 ───────────────────────────


def check_version(root: Path, cfg: dict) -> Result:
    r = Result("version")
    spec = cfg.get("version")
    if not spec:
        r.skip("config 未声明 version 段")
        return r

    skill = root / cfg.get("skill_md", "SKILL.md")
    if not skill.exists():
        r.fail(f"SKILL.md 不存在: {skill}")
        return r
    text = read_text(skill)

    fm = FRONTMATTER_RE.search(text)
    if not fm:
        r.fail("SKILL.md 不以 YAML frontmatter 开头（--- ... ---）")
        return r
    block = META_BLOCK_RE.search(fm.group(1))
    if not block:
        r.fail("SKILL.md frontmatter 缺少 `metadata:` 块")
        return r
    m = META_VERSION_RE.search(block.group(1))
    if not m:
        r.fail("SKILL.md 的 `metadata:` 里没有规范的 `version: X.Y.Z`")
        return r
    version = m.group(1)
    r.note(f"真源 SKILL.md metadata.version  {version}")

    changelog = spec.get("changelog")
    if changelog:
        p = root / changelog
        if not p.exists():
            r.fail(f"{changelog} 不存在")
        else:
            cm = CHANGELOG_RE.search(read_text(p))
            if not cm:
                r.fail(f"{changelog} 没有 `## X.Y.Z` 标题")
            elif cm.group(1) != version:
                r.fail(
                    f"{changelog} 首条是 {cm.group(1)}，SKILL.md metadata.version 是 {version}"
                    f" —— 补一节 `## {version}`（或改版本号）"
                )
            else:
                r.note(f"{changelog} 首条  {cm.group(1)}")

    pyproject = spec.get("pyproject")
    if pyproject:
        p = root / pyproject
        if not p.exists():
            r.fail(f"{pyproject} 不存在")
        else:
            pm = PYPROJECT_RE.search(read_text(p))
            if not pm:
                r.fail(f'{pyproject} 没有 `version = "X.Y.Z"` 行')
            elif pm.group(1) != version:
                r.fail(
                    f"{pyproject} version 是 {pm.group(1)}，SKILL.md metadata.version 是 {version}"
                    f" —— 安装元数据会误报 release"
                )
            else:
                r.note(f"{pyproject} version  {pm.group(1)}")

    for rel in spec.get("no_literal_in", []):
        p = root / rel
        if not p.exists():
            r.note(f"{rel} 不存在 —— 跳过字面量检查")
            continue
        try:
            hits = code_semver_literals(read_text(p))
        except SyntaxError as e:
            r.fail(f"{rel} 无法解析: {e}")
            continue
        if hits:
            where = ", ".join(f"line {ln}: {val!r}" for ln, val in hits)
            r.fail(
                f"{rel} 硬编码了版本字面量（{where}）—— 必须运行时从 SKILL.md 读取，"
                "否则打 tag / 发 release 会用过期版本号"
            )
        else:
            r.note(f"{rel} 无硬编码版本字面量")

    return r


def check_budget(root: Path, cfg: dict) -> Result:
    r = Result("budget")
    cap = cfg.get("skill_md_max_bytes")
    if not cap:
        r.skip("config 未声明 skill_md_max_bytes")
        return r

    skill = root / cfg.get("skill_md", "SKILL.md")
    if not skill.exists():
        r.fail(f"SKILL.md 不存在: {skill}")
        return r
    size = lf_bytes(skill)

    if size > cap:
        r.fail(
            f"SKILL.md {size} 字节，超过上限 {cap}（LF 归一化计数）—— "
            "把细节移进 references/，不要删 description（见 docs/decisions）"
        )
    else:
        pct = size / cap * 100
        r.note(f"SKILL.md {size} / {cap} 字节（{pct:.1f}%，余 {cap - size}）")

    ga = root / ".gitattributes"
    if cfg.get("require_lf_pin"):
        if not ga.exists():
            r.fail(".gitattributes 不存在 —— SKILL.md 未钉 LF，字节上限会随检出平台漂移")
        else:
            text = read_text(ga)
            pinned = any(
                line.split()[0] in (cfg.get("skill_md", "SKILL.md"), "SKILL.md")
                and "eol=lf" in line
                for line in text.splitlines()
                if line.strip() and not line.strip().startswith("#")
            )
            if not pinned:
                r.fail(".gitattributes 未把 SKILL.md 钉到 eol=lf —— 上限计数会漂移")
            else:
                r.note(".gitattributes 已钉 SKILL.md → eol=lf")

    return r


def check_routing(root: Path, cfg: dict) -> Result:
    r = Result("routing")
    spec = cfg.get("routing")
    if not spec:
        r.skip("config 未声明 routing 段")
        return r

    skill = root / cfg.get("skill_md", "SKILL.md")
    text = read_text(skill)
    fm = FRONTMATTER_RE.search(text)
    if not fm:
        r.fail("SKILL.md 不以 YAML frontmatter 开头")
        return r

    dm = DESCRIPTION_RE.search(fm.group(1))
    if not dm:
        r.fail("SKILL.md frontmatter 缺少 `description`")
        return r
    raw = dm.group(1)
    # A YAML block scalar's indentation is not part of the text.
    description = normalise(" ".join(line.strip() for line in raw.splitlines()))

    tm = TRIGGERS_RE.search(fm.group(1))
    triggers = normalise(tm.group(1)) if tm else ""

    total = 0
    missing_all: list[str] = []
    for reg_id in spec.get("registries", []):
        reg = cfg["registries"].get(reg_id)
        if reg is None:
            r.fail(f"routing 引用了未定义的注册表: {reg_id}")
            continue
        try:
            names = registry_names(root, reg)
        except (OSError, ValueError) as e:
            r.fail(f"注册表 {reg_id} 读取失败: {e}")
            continue
        aliases = reg.get("aliases", {})
        skip = set(reg.get("skip", []))
        missing: list[str] = []
        for name in names:
            if name in skip:
                continue
            total += 1
            candidates = [name] + list(aliases.get(name, []))
            if not any(mentions(description, c) for c in candidates):
                missing.append(name)
        if missing:
            missing_all += missing
            r.fail(
                f"注册表 {reg_id}: {len(missing)}/{len(names)} 个名字未出现在 description 里 "
                f"—— {', '.join(missing[:12])}"
                + (" …" if len(missing) > 12 else "")
            )
        else:
            r.note(f"注册表 {reg_id}: {len(names)} 个名字全部命中 description")

    if total and not missing_all:
        r.note(f"description 路由面覆盖 {total}/{total}")

    if spec.get("also_check_triggers") and triggers:
        known: set[str] = set()
        for reg in cfg["registries"].values():
            for name in reg.get("literal_names", []) or []:
                known.add(normalise(name))
        if not known:
            r.note("triggers 交叉检查已跳过（config 未声明 literal_names）")

    return r


def check_counts(root: Path, cfg: dict) -> Result:
    r = Result("counts")
    claims = cfg.get("counts") or []
    if not claims:
        r.skip("config 未声明 counts")
        return r

    for claim in claims:
        cid = claim.get("id", "?")
        truth = claim.get("truth", {})
        try:
            want = compute_truth(root, cfg, truth)
        except (OSError, ValueError) as e:
            r.fail(f"[{cid}] 真值计算失败: {e}")
            continue

        for a in claim.get("assertions", []):
            path = root / a["file"]
            if not path.exists():
                r.fail(f"[{cid}] 断言文件不存在: {a['file']}")
                continue
            text = read_text(path)
            pat = compile_re(a["regex"], a.get("flags", "M"))
            found = pat.findall(text)
            if not found:
                r.fail(
                    f"[{cid}] {a['file']} 里找不到断言点（正则 {a['regex']!r}）—— "
                    "断言点被改名或删除，计数已失去约束"
                )
                continue
            for got in found:
                got_i = int(got)
                if got_i != want:
                    ln = text[: pat.search(text).start()].count("\n") + 1 if a.get("report_line") else 0
                    where = f"{a['file']}:{ln}" if ln else a["file"]
                    r.fail(f"[{cid}] {where} 声明 {got_i}，实为 {want}")
        r.note(f"[{cid}] 真值 {want}，{len(claim.get('assertions', []))} 处断言一致")

    return r


def compute_truth(root: Path, cfg: dict, truth: dict) -> int:
    kind = truth.get("kind")
    if kind == "registry_len":
        reg = cfg["registries"][truth["registry"]]
        return len(registry_names(root, reg))
    if kind == "markdown_table_rows":
        text = read_text(root / truth["file"])
        scope = text
        if truth.get("section"):
            m = re.search(rf"^#+\s*{re.escape(truth['section'])}.*?$", text, re.M)
            if not m:
                raise ValueError(f"找不到小节: {truth['section']}")
            rest = text[m.end():]
            nxt = re.search(r"^#+\s", rest, re.M)
            scope = rest[: nxt.start()] if nxt else rest
        return len(compile_re(truth["entry"], "M").findall(scope))
    if kind == "glob_count":
        n = 0
        for pattern in truth["globs"]:
            n += len(list(root.glob(pattern)))
        return n
    if kind == "literal":
        return int(truth["value"])
    raise ValueError(f"unknown truth kind: {kind!r}")


def check_cjk(root: Path, cfg: dict) -> Result:
    r = Result("cjk")
    spec = cfg.get("cjk")
    if not spec:
        r.skip("config 未声明 cjk 段")
        return r

    files: list[Path] = []
    for pattern in spec.get("scan", []):
        files += [p for p in root.glob(pattern) if p.is_file()]
    files = sorted(set(files))
    if not files:
        r.fail("cjk 扫描面为空 —— glob 没匹配到任何文件（配置写错了？）")
        return r

    charset_globs = spec.get("require_charset", [])
    exempt = spec.get("charset_exempt", {})
    for rel, why in exempt.items():
        if not str(why).strip():
            r.fail(f"charset_exempt 里 {rel} 没有写明理由 —— 豁免必须留下原因，否则它就是隐藏")
    bad_decode: list[str] = []
    bad_charset: list[str] = []
    mojibake: list[str] = []

    for p in files:
        rel = p.relative_to(root).as_posix()
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            bad_decode.append(f"{rel} ({e})")
            continue

        if text.count("\ufffd"):
            mojibake.append(f"{rel} 含 {text.count(chr(0xFFFD))} 个替换字符 U+FFFD")

        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                mojibake.append(f"{rel} 含乱码特征 {marker!r}")
                break

        if CJK_RE.search(text) is None:
            try:
                repaired = text.encode("latin-1").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
            else:
                if len(CJK_RE.findall(repaired)) >= 4:
                    mojibake.append(
                        f"{rel} 本应是 CJK 却是 0 个汉字，按 latin-1 回转可还原 "
                        f"{len(CJK_RE.findall(repaired))} 个 —— 整文件编码错误"
                    )

        if any(fnmatch.fnmatch(rel, g) for g in charset_globs) and rel not in exempt:
            if not re.search(r"<meta\s+charset\s*=\s*[\"']?utf-8", text, re.I) and not re.search(
                r"charset\s*=\s*utf-8", text, re.I
            ):
                bad_charset.append(rel)

    if bad_decode:
        r.fail(f"{len(bad_decode)} 个文件不是合法 UTF-8: " + "; ".join(bad_decode[:5]))
    if bad_charset:
        r.fail(f"{len(bad_charset)} 个 HTML 未声明 charset=utf-8: " + ", ".join(bad_charset[:8]))
    if mojibake:
        r.fail(f"{len(mojibake)} 个文件带乱码: " + "; ".join(mojibake[:5]))

    if not (bad_decode or bad_charset or mojibake):
        r.note(f"{len(files)} 个文件 UTF-8 合法、无乱码特征（其中 {len(charset_globs)} 类须声明 charset）")
    return r


def check_palette(root: Path, cfg: dict) -> Result:
    r = Result("palette")
    spec = cfg.get("palette")
    if not spec:
        r.skip("config 未声明 palette 段")
        return r

    def names(path: Path, block: str, entry: str, flags: str = "MS") -> list[str]:
        text = read_text(path)
        m = compile_re(block, flags).search(text)
        if not m:
            raise ValueError(f"{path.name} 里找不到注册表块: {block}")
        return compile_re(entry, "M").findall(m.group(1))

    try:
        ids = names(root / spec["truth_file"], spec["truth_block"], spec["truth_entry"])
    except (OSError, ValueError) as e:
        r.fail(f"真源读取失败: {e}")
        return r
    if not ids:
        r.fail("真源注册表为空 —— 解析失败")
        return r

    for other in spec.get("mirrors", []):
        try:
            got = names(root / other["file"], other["block"], other["entry"])
        except (OSError, ValueError) as e:
            r.fail(f"{other['file']} 读取失败: {e}")
            continue
        missing = [x for x in ids if x not in got]
        extra = [x for x in got if x not in ids]
        if missing:
            r.fail(f"{other['file']} 缺: {', '.join(missing)}")
        if extra:
            r.fail(f"{other['file']} 多: {', '.join(extra)}")

    r.note(f"注册表 {len(ids)} 个 id，{len(spec.get('mirrors', []))} 处镜像一致")
    return r


CHECKS = {
    "version": check_version,
    "budget": check_budget,
    "routing": check_routing,
    "counts": check_counts,
    "cjk": check_cjk,
    "palette": check_palette,
}


# ─────────────────────────── 自测 ───────────────────────────

FIXTURE_CONFIG = {
    "skill_md": "SKILL.md",
    "skill_md_max_bytes": 2000,
    "require_lf_pin": True,
    "version": {"changelog": "CHANGELOG.md", "pyproject": "pyproject.toml", "no_literal_in": ["pub.py"]},
    "registries": {
        "styles": {
            "kind": "source_regex",
            "file": "engine.py",
            "block": r"^STYLES = \{(.*?)^\}",
            "entry": r'^\s{4}"([\w-]+)":',
            "aliases": {"watercolor": ["水彩"], "line": ["线条"]},
        }
    },
    "routing": {"registries": ["styles"], "also_check_triggers": False},
    "counts": [
        {
            "id": "styles",
            "truth": {"kind": "registry_len", "registry": "styles"},
            "assertions": [{"file": "SKILL.md", "regex": r"\*\*(\d+) styles\*\*"}],
        }
    ],
    "cjk": {"scan": ["*.html"], "require_charset": ["*.html"]},
}

GOOD_SKILL = """---
name: demo
description: Draws line and watercolor 水彩 figures. Covers line.
metadata:
  version: "1.2.3"
---

# Demo
- **2 styles**: line, watercolor
"""
GOOD_ENGINE = 'STYLES = {\n    "line": {\n        "a": 1,\n    },\n    "watercolor": {\n        "a": 2,\n    },\n}\n'
GOOD_CHANGELOG = "# Changelog\n\n## 1.2.3 (2026-01-01)\n"
GOOD_PYPROJECT = '[project]\nname = "demo"\nversion = "1.2.3"\n'
GOOD_PUB = 'import re\nversion = None  # read at runtime\n'
GOOD_HTML = '<!DOCTYPE html>\n<html><head><meta charset="utf-8"></head><body>水彩</body></html>\n'


def write_fixture(tmp: Path, **overrides: str) -> None:
    base = {
        "SKILL.md": GOOD_SKILL,
        "engine.py": GOOD_ENGINE,
        "CHANGELOG.md": GOOD_CHANGELOG,
        "pyproject.toml": GOOD_PYPROJECT,
        "pub.py": GOOD_PUB,
        "a.html": GOOD_HTML,
        ".gitattributes": "SKILL.md text eol=lf\n",
    }
    base.update(overrides)
    for name, content in base.items():
        (tmp / name).write_text(content, encoding="utf-8")


def run_check(tmp: Path, name: str, cfg: dict) -> bool:
    return CHECKS[name](tmp, cfg).ok


def self_test() -> int:
    import copy
    import tempfile

    cases: list[tuple[str, str, dict, dict, bool]] = [
        # name, check, file overrides, config patch, expected ok
        ("version_ok", "version", {}, {}, True),
        ("version_changelog_stale", "version", {"CHANGELOG.md": "# Changelog\n\n## 1.2.2\n"}, {}, False),
        ("version_pyproject_stale", "version", {"pyproject.toml": '[project]\nversion = "0.0.1"\n'}, {}, False),
        ("version_hardcoded_literal", "version", {"pub.py": 'version = "9.9.9"\n'}, {}, False),
        ("version_literal_in_docstring_is_ok", "version",
         {"pub.py": '"""We used to hardcode 0.2.5 here."""\nversion = None\n'}, {}, True),
        ("budget_ok", "budget", {}, {}, True),
        ("budget_over_cap", "budget", {"SKILL.md": GOOD_SKILL + ("x" * 3000)}, {}, False),
        ("budget_lf_pin_missing", "budget", {".gitattributes": "# nothing\n"}, {}, False),
        ("routing_ok", "routing", {}, {}, True),
        ("routing_missing_name", "routing",
         {"SKILL.md": GOOD_SKILL.replace("line and watercolor 水彩 figures", "figures")}, {}, False),
        ("routing_alias_satisfies", "routing",
         {"SKILL.md": GOOD_SKILL.replace("watercolor 水彩", "水彩").replace(
             "**2 styles**: line, watercolor", "**2 styles**: line, 水彩")}, {}, True),
        ("routing_substring_does_not_satisfy", "routing",
         {"SKILL.md": GOOD_SKILL.replace("line", "linetype")}, {}, False),
        ("routing_cjk_alias_is_substring_matched", "routing",
         {"SKILL.md": GOOD_SKILL.replace("line", "线条艺术")}, {}, True),
        ("counts_ok", "counts", {}, {}, True),
        ("counts_stale", "counts", {"SKILL.md": GOOD_SKILL.replace("**2 styles**", "**6 styles**")}, {}, False),
        ("counts_assertion_gone", "counts",
         {"SKILL.md": GOOD_SKILL.replace("**2 styles**", "several styles")}, {}, False),
        ("cjk_ok", "cjk", {}, {}, True),
        ("cjk_no_charset", "cjk", {"a.html": "<html><body>水彩</body></html>\n"}, {}, False),
        ("cjk_charset_exempt_with_reason", "cjk",
         {"a.html": "<html><body>水彩</body></html>\n"},
         {"charset_exempt": {"a.html": "paste-in fragment"}}, True),
        ("cjk_charset_exempt_without_reason", "cjk",
         {"a.html": "<html><body>水彩</body></html>\n"},
         {"charset_exempt": {"a.html": "   "}}, False),
        ("cjk_replacement_char", "cjk", {"a.html": '<meta charset="utf-8">\ufffd水彩\n'}, {}, False),
        ("cjk_mojibake_marker", "cjk",
         {"a.html": '<meta charset="utf-8">\nâ€œ水彩â€\n'}, {}, False),
        ("cjk_whole_file_wrong_encoding", "cjk",
         {"a.html": '<meta charset="utf-8">\n' + "水彩测试中文".encode("utf-8").decode("latin-1") + "\n"},
         {}, False),
    ]

    failures = 0
    for name, check, overrides, patch, want in cases:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            write_fixture(tmp, **overrides)
            cfg = copy.deepcopy(FIXTURE_CONFIG)
            for key, value in patch.items():
                cfg.setdefault("cjk", {})[key] = value
            try:
                got = run_check(tmp, check, cfg)
            except Exception as e:  # a crash is a failed case, not a crashed suite
                got = f"CRASH {type(e).__name__}: {e}"
        ok = got is want
        if not ok:
            failures += 1
        print(f"  {'PASS' if ok else 'MISMATCH':<9} {name:<38} 期望 {want} 实际 {got}")

    print()
    if failures:
        print(f"自测失败: {failures}/{len(cases)} 个用例行为不符")
        return 1
    print(f"自测通过: {len(cases)}/{len(cases)} 个用例行为符合预期")
    return 0


# ─────────────────────────── 入口 ───────────────────────────


def load_config(root: Path) -> dict:
    path = root / CONFIG_NAME
    if not path.exists():
        raise FileNotFoundError(f"找不到配置 {path}")
    return json.loads(read_text(path))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="check_archviz.py", description=__doc__.split("\n")[0])
    ap.add_argument("--only", action="append", default=[], help="只跑指定检查（可重复）")
    ap.add_argument("--list", action="store_true", help="列出本仓已配置的检查")
    ap.add_argument("--self-test", action="store_true", help="跑对抗性 fixture 自测")
    ap.add_argument("--self-hash", action="store_true", help="打印 KIT_VERSION 与自身 sha256")
    ap.add_argument("--root", default=None, help="仓库根目录（默认脚本的上级）")
    args = ap.parse_args(argv[1:])

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve() if args.root else ROOT

    if args.self_hash:
        digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        print(f"KIT_VERSION {KIT_VERSION}")
        print(f"sha256      {digest}")
        return 0

    try:
        cfg = load_config(root)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: 配置读取失败: {e}", file=sys.stderr)
        return 2

    configured = [c for c in CHECKS if cfg.get(_config_key(c))]
    if not configured:
        print("ERROR: 配置里没有任何可跑的检查段", file=sys.stderr)
        return 2

    if args.list:
        print(f"KIT_VERSION {KIT_VERSION} · {root}")
        for c in configured:
            print(f"  {c}")
        return 0

    todo = args.only or configured
    unknown = [c for c in todo if c not in CHECKS]
    if unknown:
        print(f"ERROR: 未知检查 {', '.join(unknown)}", file=sys.stderr)
        return 2

    results = [CHECKS[c](root, cfg) for c in todo]

    failed = 0
    for res in results:
        if res.skipped:
            print(f"SKIP  {res.name:<8} {res.skipped}")
            continue
        if res.ok:
            print(f"PASS  {res.name:<8} {res.notes[0] if res.notes else ''}")
            for n in res.notes[1:]:
                print(f"          {n}")
        else:
            failed += 1
            print(f"FAIL  {res.name:<8}")
            for f in res.failures:
                print(f"        - {f}")

    print()
    if failed:
        print(f"FAIL — {failed}/{len(results)} 项检查未通过（kit v{KIT_VERSION}）")
        return 1
    print(f"PASS — {len(results)} 项检查全部通过（kit v{KIT_VERSION}）")
    return 0


def _config_key(check: str) -> str:
    return {"version": "version", "budget": "skill_md_max_bytes", "routing": "routing",
            "counts": "counts", "cjk": "cjk", "palette": "palette"}[check]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
