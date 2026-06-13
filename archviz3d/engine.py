"""
archviz-3d rendering core — Three.js self-contained 3D visualization engine.

Usage:
    from archviz3d.engine import render, list_types

    html = render("building", {"floors": 5, "rooms_per_floor": 4})
"""

import json
import re
from pathlib import Path
from typing import Any

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "html"

TYPE_REGISTRY = {
    "building": {
        "template": "threejs-archviz.html",
        "description": "3D building structure — multi-floor visualization with explode view",
        "schema": {
            "floors": "int — number of floors (1-10, default 3)",
            "rooms_per_floor": "int — rooms per floor (1-8, default 4)",
            "floor_height": "float — floor height in units (default 3.0)",
            "explode": "bool — start in exploded view (default false)",
            "wireframe": "bool — start in wireframe mode (default false)",
        },
        "example": {
            "floors": 3,
            "rooms_per_floor": 4,
            "floor_height": 3.0,
            "explode": False,
            "wireframe": False,
        },
    },
    "floorplan": {
        "template": "threejs-floorplan.html",
        "description": "3D floor plan — room layout with navigation",
        "schema": {
            "rooms": "list[dict] — each has 'name', 'width', 'depth', optional 'color'",
            "floor_height": "float — wall height (default 2.8)",
            "show_labels": "bool — show room name labels (default true)",
        },
        "example": {
            "rooms": [
                {"name": "Living Room", "width": 6, "depth": 5},
                {"name": "Kitchen", "width": 4, "depth": 3},
                {"name": "Bedroom", "width": 4, "depth": 4},
                {"name": "Bathroom", "width": 3, "depth": 2.5},
            ],
            "floor_height": 2.8,
            "show_labels": True,
        },
    },
}


def list_types() -> list[dict]:
    return [
        {"type": t, "description": info["description"], "schema": info["schema"], "example": info.get("example")}
        for t, info in TYPE_REGISTRY.items()
    ]


def render(viz_type: str, data: dict, options: dict | None = None) -> str:
    if viz_type not in TYPE_REGISTRY:
        available = ", ".join(TYPE_REGISTRY.keys())
        raise ValueError(f"Unknown type '{viz_type}'. Available: {available}")

    options = options or {}
    template_info = TYPE_REGISTRY[viz_type]
    template_path = TEMPLATES_DIR / template_info["template"]

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    html = template_path.read_text(encoding="utf-8")

    # Inject parameters
    html = _inject_params(html, viz_type, data)

    # Apply theme
    if "theme" in options:
        html = re.sub(r"<html([^>]*)>", f'<html data-palette="{options["theme"]}"\\1>', html, count=1)

    # Apply title
    if "title" in options:
        html = re.sub(r"<title>.*?</title>", f"<title>{options['title']}</title>", html, count=1)

    return html


def _inject_params(html: str, viz_type: str, data: dict) -> str:
    """Inject parameters into 3D template."""
    if viz_type == "building":
        # Inject floor count and room count
        if "floors" in data:
            html = re.sub(
                r"const FLOORS\s*=\s*\d+",
                f"const FLOORS = {int(data['floors'])}",
                html,
                count=1,
            )
        if "rooms_per_floor" in data:
            html = re.sub(
                r"const ROOMS_PER_FLOOR\s*=\s*\d+",
                f"const ROOMS_PER_FLOOR = {int(data['rooms_per_floor'])}",
                html,
                count=1,
            )
        if "floor_height" in data:
            html = re.sub(
                r"const FLOOR_HEIGHT\s*=\s*[\d.]+",
                f"const FLOOR_HEIGHT = {float(data['floor_height'])}",
                html,
                count=1,
            )
        if data.get("explode"):
            html = html.replace("let isExploded = false", "let isExploded = true")
        if data.get("wireframe"):
            html = html.replace("let isWireframe = false", "let isWireframe = true")

    elif viz_type == "floorplan":
        if "rooms" in data:
            rooms_json = json.dumps(data["rooms"], ensure_ascii=False)
            html = re.sub(
                r"const rooms\s*=\s*\[.*?\];",
                f"const rooms = {rooms_json};",
                html,
                flags=re.DOTALL,
                count=1,
            )

    return html
