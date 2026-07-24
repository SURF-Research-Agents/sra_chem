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
from langchain_ui.agents.agent import create_willma_agent

from sra_chem.agents.chemoinformatics_agent import create_chemoinformatics_agent
from sra_chem.agents.quantum_chemistry_agent import create_quantum_chemistry_agent
from sra_chem.tools.cheminformatics_tools import (
    molecule_name_to_smiles,
    smiles_to_atomsdata,
    smiles_to_coordinate_file,
)
from sra_chem.tools.pyscf_tools import (
    ground_state_energy_local,
    ground_state_energy_hpc,
)
from sra_chem.tools.directory_tools import create_workspace


# Orchestrator prompt that defines the multi-agent coordination
multi_agent_prompt = """You are a computational chemistry orchestrator that coordinates between two specialized agents:

## Chemoinformatics Agent
Handles molecular representation and structure generation:
- Converting molecule names to SMILES strings
- Generating 3D molecular structures from SMILES
- Creating coordinate files (XYZ format) for quantum chemistry calculations

## Quantum Chemistry Agent
Handles electronic structure calculations:
- Hartree-Fock ground state energy computations
- Basis set selection and calculation setup
- HPC job submission for expensive calculations

## Workflow Coordination
When a user asks about a molecule's properties or energies:
1. First, use the chemoinformatics tools to get the molecular structure
2. Then, pass the coordinate file to the quantum chemistry agent for calculations
3. Combine results from both agents to provide a comprehensive answer

## Instructions
1. Extract all relevant inputs from the user's query (molecule names, SMILES, methods, basis sets).
2. If structure generation is needed, use cheminformatics tools first.
3. If quantum calculations are needed, use the coordinate file from step 2.
4. Base all responses strictly on actual tool outputs—never fabricate results.
5. Review previous tool outputs. If they indicate failure, retry with adjusted inputs.
6. Write all files in a dedicated temporary directory.
7. Report energies in both Hartree and eV units.
8. Provide clear, comprehensive summaries combining results from both agents.
"""


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

    return create_willma_agent(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        tools=[
            # Cheminformatics tools
            molecule_name_to_smiles,
            smiles_to_atomsdata,
            smiles_to_coordinate_file,
            # Quantum chemistry tools
            ground_state_energy_local,
            ground_state_energy_hpc,
            # Utility tools
            create_workspace,
        ],
        instructions=multi_agent_prompt,
        backend=backend,
        skills=skills,
    )


def create_separate_agents(
    api_key: str,
    model: str = "default-text-large",
    temperature: float = 0.1,
    max_tokens: int = 1000,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Create separate chemoinformatics and quantum chemistry agents.

    This returns a dictionary with both agents instantiated separately,
    useful when you want to call them independently.

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
    Dict[str, Any]
        Dictionary with keys 'chemoinformatics' and 'quantum_chemistry'.

    Examples
    --------
    >>> agents = create_separate_agents(api_key="your-api-key")
    >>> chem_agent = agents['chemoinformatics']
    >>> qc_agent = agents['quantum_chemistry']
    """
    chem_agent = create_chemoinformatics_agent(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    qc_agent = create_quantum_chemistry_agent(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    return {
        'chemoinformatics': chem_agent,
        'quantum_chemistry': qc_agent,
    }
