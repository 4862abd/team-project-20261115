from app.api.schemas.result import KeyPoint


LEVEL_DEPTH = {"대단락": 0, "중단락": 1, "소단락": 2}


def build_key_point_tree(key_points: list[KeyPoint]) -> list[dict]:
    """Arrange the model's ordered flat key points into their paragraph hierarchy."""
    roots: list[dict] = []
    stack: list[dict] = []

    for point in key_points:
        depth = LEVEL_DEPTH.get(point.level, 1)
        node = {"point": point, "depth": depth, "children": []}
        while stack and stack[-1]["depth"] >= depth:
            stack.pop()
        if stack:
            stack[-1]["children"].append(node)
        else:
            roots.append(node)
        stack.append(node)

    return roots
