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

