"""Multi-Agent Orchestrator for chemoinformatics and quantum chemistry workflows.

This module provides a coordinated two-agent system where:
- The Chemoinformatics Agent handles molecular representation, SMILES manipulation,
  and 3D structure generation.
- The Quantum Chemistry Agent handles electronic structure calculations,
  geometry optimization, and energy computations.

The orchestrator manages the handoff between agents, enabling complex
workflows such as:
1. Convert molecule name → SMILES → 3D coordinates → HF energy
2. Analyze molecular properties and predict quantum chemical properties
3. Batch processing of multiple molecules through QC calculations
"""

from typing import Any, Dict, List, Optional
import pathlib
from deepagents.backends.filesystem import FilesystemBackend
from langchain_ui.agents.multi_agent import create_willma_multi_agent

from sra_chem.tools.cheminformatics_tools import (
    molecule_name_to_smiles,
    smiles_to_atomsdata,
    smiles_to_coordinate_file,
)
from sra_chem.tools.pyscf_tools import (
    hf_energy_local,
    hf_energy_hpc,
)
from sra_chem.tools.directory_tools import create_workspace
from sra_chem.prompts.multiagent_prompt import (
    multi_agent_prompt, chemoinformatic_agent_prompt, 
    quantum_chemistry_agent_promt, summarization_agent_prompt)

def create_multi_agent(
    api_key: str,
    model: str = "default-text-large",
    temperature: float = 0.1,
    max_tokens: int = 1000,
    timeout: int = 30,
) -> Any:
    """Create a multi-agent system coordinating chemoinformatics and quantum chemistry.

    This creates a single orchestrator agent with access to all tools from
    both the chemoinformatics and quantum chemistry agents, enabling
    end-to-end workflows from molecule name to quantum chemical properties.

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
        Configured orchestrator agent instance.

    Examples
    --------
    >>> agent = create_multi_agent(api_key="your-api-key")
    >>> result = agent.stream("Calculate the HF energy of water with 6-31g* basis")
    """
    skills_path = "/Users/renau001/Documents/projects/ai/SRA/sra_chem/src/sra_chem/"
    backend = FilesystemBackend(root_dir=skills_path)
    skills = ['skills/']

    chemoinformatic_agent = {
        "name" : "chemoinformatic_agent",
        "description": "Used to perform chemoinformatic tasks such as converting a molecule name into a smiles or a smiles into coordinates",
        "system_prompt": chemoinformatic_agent_prompt,
        "tools": [molecule_name_to_smiles, smiles_to_atomsdata, smiles_to_coordinate_file],
        "skills": ["skills/mol-xyz"]
    }

    quantum_chemistry_agent = {
            "name" : "quantum_agent",
            "description": "Used to perform quantum chemistry tasks such as computing the ground state energy of a molecule",
            "system_prompt": quantum_chemistry_agent_promt,
            "tools": [hf_energy_local, hf_energy_hpc],
            "skills": ["skills/mol-groundstate"]
    }

    summarization_agent = {
            "name" : "summarization_agent",
            "description": "Used to summarize computational chemistry results from the chemoinformatics and quantum chemistry agents into a clear, structured report",
            "system_prompt": summarization_agent_prompt,
            "tools": []
    }


    return create_willma_multi_agent(
        api_key=api_key,
        model=model,
        subagents=[chemoinformatic_agent,
                   quantum_chemistry_agent,
                   summarization_agent],
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        tools=[create_workspace],
        instructions=multi_agent_prompt,
        backend=backend,
        skills=skills,
        name='main-agent'
    )

