import os
from datetime import datetime
from pathlib import Path

from langchain_core.tools import tool


@tool
def create_workspace() -> dict:
    """Create a new directory with a unique UUID name and return its path.

    Returns
    -------
    dict
        A dict with the absolute path to the newly created directory.

    Examples
    --------
    >>> create_workspace()
    {'path': PosixPath('/current/working/dir/abc12345-def6-7890-abcd-ef1234567890')}
    """
    dir_name = str(datetime.now()).replace('.','-').replace(' ','_').replace(':','-')
    new_dir = Path(os.getcwd()) / f"sra_chem_{dir_name}"
    new_dir.mkdir(exist_ok=True)
    return {"path": new_dir.resolve()}


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file.

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
    >>> write_file("report.md", "# Summary\\n\\nResults here.")
    '/current/working/dir/report.md'
    """
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = Path(os.getcwd()) / file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return str(file_path.resolve())
