import os

def _resolve_path(path: str) -> str:
    """If CHEMGRAPH_LOG_DIR is set and path is relative, prepend it."""
    log_dir = os.environ.get("CHEMGRAPH_LOG_DIR")
    if log_dir and not os.path.isabs(path):
        # Create directory if it doesn't exist (race condition safe-ish)
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, path)
    return path