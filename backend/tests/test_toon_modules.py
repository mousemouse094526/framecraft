"""The modules of `backend.toon` import each other one way only: no module imports one that
imports it back, at the top or inside a function. A cycle hidden inside a function works until
someone moves the import, so it is caught here instead."""

import ast
from pathlib import Path

TOON = Path(__file__).parent.parent / "toon"


def toon_imports(path: Path) -> set[str]:
    """The `backend.toon` modules a file imports, anywhere in it."""
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module == "backend":
            found |= {"__init__" for alias in node.names if alias.name == "toon"}  # the package itself
        elif isinstance(node, ast.ImportFrom) and node.module == "backend.toon":
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("backend.toon."):
            found.add(node.module.split(".")[2])
        elif isinstance(node, ast.Import):
            found |= {alias.name.split(".")[2] for alias in node.names if alias.name.startswith("backend.toon.")}
    return found


def cycle_from(graph: dict[str, set[str]], start: str) -> list[str] | None:
    """A path of imports from `start` back to it, if there is one."""
    paths = [[start]]
    seen = set()
    while paths:
        path = paths.pop()
        for name in sorted(graph.get(path[-1], ())):
            if name == start:
                return [*path, start]
            if name not in seen:
                seen.add(name)
                paths.append([*path, name])
    return None


def test_no_toon_module_imports_one_that_imports_it_back():
    graph = {path.stem: toon_imports(path) for path in TOON.glob("*.py")}

    cycles = [cycle for name in sorted(graph) if (cycle := cycle_from(graph, name))]

    assert cycles == []
