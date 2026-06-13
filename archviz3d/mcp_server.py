"""archviz-3d MCP server."""

from mcp.server.fastmcp import FastMCP
from .engine import render, list_types

mcp = FastMCP("archviz-3d")


@mcp.tool()
def archviz3d_generate(type: str, data: dict, options: dict | None = None) -> str:
    """Generate a self-contained 3D HTML visualization.

    Args:
        type: 3D type (building, floorplan)
        data: Parameters (floors, rooms, explode, wireframe, etc.)
        options: Optional (theme, title)
    """
    try:
        return render(type, data, options or {})
    except (ValueError, FileNotFoundError) as e:
        return f"Error: {e}"


@mcp.tool()
def archviz3d_list_types() -> str:
    """List available 3D visualization types with schemas."""
    import json
    types = list_types()
    result = []
    for t in types:
        result.append(f"### {t['type']}\n{t['description']}\n\n**Schema:**\n```json\n{json.dumps(t['schema'], indent=2)}\n```\n\n**Example:**\n```json\n{json.dumps(t.get('example', {}), indent=2)}\n```\n")
    return "\n".join(result)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
