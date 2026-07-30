"""Quantum Chemistry Agent for electronic structure calculations."""

from typing import Any, List
import pathlib
from deepagents.backends.filesystem import FilesystemBackend
from langchain_ui.agents.agent import create_willma_agent

from sra_chem.tools.hf_tools import (
    hf_energy_local,
    hf_energy_hpc,
)

from sra_chem.tools.dft_tools import (
    dft_energy_local,
    dft_energy_hpc,
)

from sra_chem.tools.tddft_tools import (
    td_dft_excitations_local,
    td_dft_excitations_hpc,
    td_dft_absorption_spectrum,
)
from sra_chem.tools.directory_tools import create_workspace
from sra_chem.prompts.single_agent_prompt import single_agent_prompt


# Quantum chemistry specific instructions
quantum_chemistry_prompt = """You are an expert in quantum chemistry and electronic structure theory, using advanced computational tools to solve complex problems.

Instructions:
1. Extract all relevant inputs from the user's query, such as molecule coordinate files, methods (HF, DFT), basis sets, and target properties.
2. If a tool is needed, call it using the correct schema.
3. Base all responses strictly on actual tool outputs—never fabricate results, energies, or molecular properties.
4. Review previous tool outputs. If they indicate failure (e.g., non-convergence), retry with adjusted parameters (tighter convergence criteria, different initial guess, or larger basis set).
5. Use available simulation data directly. If data is missing, clearly state that a tool call is required.
6. If no tool call is needed, respond using factual domain knowledge.
7. Write all files in a dedicated temporary directory.
8. For Hartree-Fock calculations, specify appropriate basis sets (sto-3g for quick estimates, 6-31g* or cc-pvdz for production quality).
9. Clearly report energies in both Hartree and eV units.
10. When submitting HPC jobs, be aware of cluster queue times and resource limits.
11. For TD-DFT calculations, use appropriate functionals (b3lyp or pbe) and basis sets; report excitation energies in eV and wavelengths in nm.
12. For absorption spectra, use n_states=50 and sigma=0.3 eV for smooth spectra unless otherwise specified.
"""


def create_quantum_chemistry_agent(
    api_key: str,
    model: str = "default-text-large",
    temperature: float = 0.1,
    max_tokens: int = 1000,
    timeout: int = 30,
) -> Any:
    """Create a quantum chemistry agent specialized in electronic structure calculations.

    This agent handles:
    - Hartree-Fock ground state energy calculations (local and HPC)
    - Basis set selection guidance
    - Convergence troubleshooting
    - Electronic structure analysis

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
            hf_energy_local,
            hf_energy_hpc,
            td_dft_excitations_local,
            td_dft_excitations_hpc,
            td_dft_absorption_spectrum,
            create_workspace,
        ],
        instructions=quantum_chemistry_prompt,
        backend=backend,
        skills=skills,
    )
