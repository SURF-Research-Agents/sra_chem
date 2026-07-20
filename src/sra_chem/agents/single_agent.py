from typing import Any, List
import pathlib
from deepagents.backends.filesystem import FilesystemBackend
from langchain_ui.agents.agent import create_willma_agent
from sra_chem.tools.cheminformatics_tools import (
    molecule_name_to_smiles,
    smiles_to_atomsdata,
    smiles_to_coordinate_file
)
from sra_chem.prompts.single_agent_prompt import single_agent_prompt

# file_path = pathlib.Path(__file__).parent.resolve()
# skills_path = f"{file_path}../skills/"
# backend = FilesystemBackend(root_dir=skills_path)
# skills = [skills_path]

skills_path = "/Users/renau001/Documents/projects/ai/SRA/sra_chem/src/sra_chem/"
backend = FilesystemBackend(root_dir=skills_path)
skills = ['skills/']

def create_chem_agent(
    api_key: str,
    model: str = "default-text-large",
    temperature: float = 0.1,
    max_tokens: int = 1000,
    timeout: int = 30,
    ):

    return create_willma_agent(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        tools=[molecule_name_to_smiles,
               smiles_to_atomsdata,
               smiles_to_coordinate_file],
        instructions=single_agent_prompt,
        backend=backend,
        skills=skills
    )
