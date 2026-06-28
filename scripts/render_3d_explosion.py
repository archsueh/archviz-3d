#!/usr/bin/env python3
"""
3D Exploded View Animation Renderer.
Simulates 3D explosion effect using Pillow.
Cross-optimization: archviz-3d + archviz-animate
"""
import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Theme
THEME = {
    "bg": "#000000",
    "white": "#f4f0ee",
    "muted": "#cfc7c5",
    "frame": "#5c6265",
    "green": "#22c86f",
    "cyan": "#7ee3d6",
    "purple": "#bd54d3",
    "amber": "#f4b64e",
}

# 3D-like colors for parts
PART_COLORS = [
    "#7ee3d6",  # Cyan
    "#22c86f",  # Green
    "#bd54d3",  # Purple
    "#f4b64e",  # Amber
    "#ff7ab6",  # Pink
    "#6b8aff",  # Blue
]

SCALE = 2
DEFAULT_W = 800
DEFAULT_H = 600
DEFAULT_FRAMES = 30
DEFAULT_FPS = 15


def hex_rgba(value, alpha=255):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def c(v):
    return int(round(v * SCALE))


def load_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, c(size))
        except OSError:
            continue
    return ImageFont.load_default()


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - (-2 * t + 2) ** 3 / 2


def draw_3d_rect(draw, x, y, w, h, d, color, alpha=255):
    """Draw a 3D-looking rectangle with depth effect."""
    # Front face
    draw.rectangle(
        [c(x), c(y), c(x + w), c(y + h)],
        fill=hex_rgba(color, alpha),
        outline=hex_rgba(THEME["white"], 100),
    )
    
    # Top face (simulate depth)
    top_color = hex_rgba(color, int(alpha * 0.8))
    points = [
        (c(x), c(y)),
        (c(x + d), c(y - d)),
        (c(x + w + d), c(y - d)),
        (c(x + w), c(y)),
    ]
    draw.polygon(points, fill=top_color, outline=hex_rgba(THEME["white"], 80))
    
    # Right face
    right_color = hex_rgba(color, int(alpha * 0.6))
    points = [
        (c(x + w), c(y)),
        (c(x + w + d), c(y - d)),
        (c(x + w + d), c(y + h - d)),
        (c(x + w), c(y + h)),
    ]
    draw.polygon(points, fill=right_color, outline=hex_rgba(THEME["white"], 80))


def render_frame(data, progress, width, height):
    """Render a single frame of 3D explosion animation."""
    img = Image.new("RGBA", (width * SCALE, height * SCALE), hex_rgba(THEME["bg"]))
    draw = ImageDraw.Draw(img)
    
    # Title
    title = data.get("title", "3D Exploded View")
    font_title = load_font(24, bold=True)
    draw.text(
        (c(40), c(30)),
        title,
        font=font_title,
        fill=hex_rgba(THEME["white"]),
    )
    
    # Subtitle
    subtitle = data.get("subtitle", "")
    if subtitle:
        font_sub = load_font(14)
        draw.text(
            (c(40), c(60)),
            subtitle,
            font=font_sub,
            fill=hex_rgba(THEME["muted"]),
        )
    
    # Parts
    parts = data.get("parts", [])
    if not parts:
        return img
    
    # Center position
    cx = width / 2
    cy = height / 2
    
    # Animation progress with easing
    t = ease_in_out_cubic(progress)
    
    # Draw parts with explosion effect
    font_label = load_font(12)
    
    for i, part in enumerate(parts):
        # Part properties
        name = part.get("name", f"Part {i+1}")
        base_x = part.get("x", 0)
        base_y = part.get("y", 0)
        base_z = part.get("z", 0)
        w = part.get("width", 80)
        h = part.get("height", 60)
        d = part.get("depth", 20)
        explode_x = part.get("explode_x", 0)
        explode_y = part.get("explode_y", 0)
        explode_z = part.get("explode_z", 0)
        
        # Calculate exploded position
        x = cx + base_x + explode_x * t
        y = cy + base_y + explode_y * t
        z = base_z + explode_z * t
        
        # Scale based on z-depth (perspective simulation)
        scale = 1.0 + z * 0.005
        w_scaled = w * scale
        h_scaled = h * scale
        
        # Color
        color = PART_COLORS[i % len(PART_COLORS)]
        
        # Draw 3D part
        draw_3d_rect(draw, x - w_scaled/2, y - h_scaled/2, w_scaled, h_scaled, d, color)
        
        # Draw label
        label = name
        bbox = draw.textbbox((0, 0), label, font=font_label)
        label_width = bbox[2] - bbox[0]
        draw.text(
            (c(x - label_width / 2 / SCALE), c(y + h_scaled/2 + 10)),
            label,
            font=font_label,
            fill=hex_rgba(THEME["white"]),
        )
        
        # Draw connection line to center (when exploded)
        if t > 0.1:
            line_alpha = int(100 * t)
            draw.line(
                [(c(cx), c(cy)), (c(x), c(y))],
                fill=hex_rgba(THEME["frame"], line_alpha),
                width=c(1),
            )
    
    # Draw center point
    draw.ellipse(
        [c(cx - 5), c(cy - 5), c(cx + 5), c(cy + 5)],
        fill=hex_rgba(THEME["green"]),
        outline=hex_rgba(THEME["white"]),
    )
    
    # Draw explosion indicator
    if t > 0.5:
        font_anno = load_font(10)
        draw.text(
            (c(cx + 20), c(cy - 20)),
            "EXPLODED",
            font=font_anno,
            fill=hex_rgba(THEME["green"]),
        )
    
    return img


def render_3d_explosion(data, outdir, basename, frames=DEFAULT_FRAMES, fps=DEFAULT_FPS):
    """Render 3D explosion animation as GIF."""
    width = data.get("width", DEFAULT_W)
    height = data.get("height", DEFAULT_H)
    
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    # Generate frames
    images = []
    for i in range(frames):
        progress = i / (frames - 1)
        frame = render_frame(data, progress, width, height)
        images.append(frame)
    
    # Save GIF
    gif_path = outdir / f"{basename}.gif"
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=int(1000 / fps),
        loop=0,
    )
    print(f"GIF saved: {gif_path}")
    
    # Save static PNG (exploded view)
    png_path = outdir / f"{basename}.png"
    images[-1].save(png_path)
    print(f"PNG saved: {png_path}")
    
    return gif_path, png_path


def main():
    parser = argparse.ArgumentParser(description="3D explosion animation renderer")
    parser.add_argument("--spec", required=True, help="JSON spec file")
    parser.add_argument("--outdir", default="./output", help="Output directory")
    parser.add_argument("--basename", default="explosion", help="Output filename base")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES, help="Number of frames")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help="Frames per second")
    args = parser.parse_args()
    
    # Load spec
    with open(args.spec, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Render
    gif_path, png_path = render_3d_explosion(
        data, args.outdir, args.basename, args.frames, args.fps
    )
    
    print(f"\nDone! Generated:")
    print(f"  - {gif_path}")
    print(f"  - {png_path}")


if __name__ == "__main__":
    main()
