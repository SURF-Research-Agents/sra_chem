import os

def _resolve_path(path: str) -> str:
    """If CHEMGRAPH_LOG_DIR is set and path is relative, prepend it."""
    log_dir = os.environ.get("CHEMGRAPH_LOG_DIR")
    if log_dir and not os.path.isabs(path):
        # Create directory if it doesn't exist (race condition safe-ish)
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, path)
    return path


from pydantic import BaseModel, Field
from typing import List, Optional, Union


class AtomsData(BaseModel):
    """AtomsData object inherited from Pydantic BaseModel. Used to store atomic data (from ASE Atoms object or QCElemental Molecule object) that cannot be parsed via LLM Schema."""

    numbers: List[int] = Field(..., description="Atomic numbers")
    positions: List[List[float]] = Field(..., description="Atomic positions")
    cell: Optional[Union[List[List[float]], None]] = Field(
        default=None, description="Cell vectors or None"
    )
    pbc: Optional[Union[List[bool], None]] = Field(
        default=None, description="Periodic boundary conditions or None"
    )
