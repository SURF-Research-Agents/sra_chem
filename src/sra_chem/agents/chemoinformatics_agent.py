"""Chemoinformatics Agent for molecular analysis and property prediction."""

from typing import Any, List
import pathlib
from deepagents.backends.filesystem import FilesystemBackend
from langchain_ui.agents.agent import create_willma_agent

from sra_chem.tools.cheminformatics_tools import (
    molecule_name_to_smiles,
    smiles_to_atomsdata,
    smiles_to_coordinate_file,
)
from sra_chem.tools.directory_tools import create_workspace
from sra_chem.prompts.single_agent_prompt import single_agent_prompt


def create_chemoinformatics_agent(
    api_key: str,
    model: str = "default-text-large",
    temperature: float = 0.1,
    max_tokens: int = 1000,
    timeout: int = 30,
) -> Any:
    """Create a chemoinformatics agent specialized in molecular analysis.

    This agent handles:
    - Converting molecule names to SMILES strings
    - Generating 3D molecular structures from SMILES
    - Creating coordinate files (XYZ format)
    - Molecular property analysis

    Parameters
    ----------
    api_key : str
        API key for the LLM service.
    model : str, optional
        Model to use, by default "default-text-large".
    temperature : float, optional
        Sampling temperature, by default 0.1.
    max_tokens : int, optional
        Maximum tokens per response, by default 1000.
    timeout : int, optional
        Request timeout in seconds, by default 30.

    Returns
    -------
    Any
        Configured willma agent instance.
    """
    skills_path = "/Users/renau001/Documents/projects/ai/SRA/sra_chem/src/sra_chem/"
    backend = FilesystemBackend(root_dir=skills_path)
    skills = ['skills/']

    return create_willma_agent(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        tools=[
            molecule_name_to_smiles,
            smiles_to_atomsdata,
            smiles_to_coordinate_file,
            create_workspace,
        ],
        instructions=single_agent_prompt,
        backend=backend,
        skills=skills,
    )
