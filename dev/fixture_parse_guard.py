"""Parse-tree checks for dev scripts that emit metrics fixture goldens."""


def tree_contains_unparsable(segment: object) -> bool:
    """Return True if any descendant segment is SQLFluff ``unparsable``."""
    if getattr(segment, "is_type", lambda *_: False)("unparsable"):
        return True
    return any(tree_contains_unparsable(child) for child in getattr(segment, "segments", ()) or ())
