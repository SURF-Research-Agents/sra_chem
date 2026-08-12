import os
from pathlib import Path

from langchain_core.tools import tool



@tool
def write_md_summary(path: str, content: str) -> str:
    """Write content to a Markdown file.

    Parameters
    ----------
    path : str
        File path to write to.
    content : str
        Content to write to the file.

    Returns
    -------
    str
        Absolute path to the written file.

    Examples
    --------
    >>> write_md_summary("report.md", "# Summary\\n\\nResults here.")
    '/current/working/dir/report.md'
    """
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = Path(os.getcwd()) / file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return str(file_path.resolve())