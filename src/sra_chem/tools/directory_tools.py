import os
import uuid
from datetime import datetime

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
    {'path': '/current/working/dir/abc12345-def6-7890-abcd-ef1234567890'}
    """
    dir_name = str(datetime.now()).replace('.',':').replace(' ','_')
    new_dir = os.path.join(os.getcwd(), f"sra_chem_{dir_name}")
    os.makedirs(new_dir, exist_ok=True)
    return {"path": os.path.abspath(new_dir)}
