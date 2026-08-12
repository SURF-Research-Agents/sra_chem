"""LangGraph compiled subagent for quantum chemistry / PySCF calculations.

This module provides a compiled LangGraph agent that replicates the
quantum chemistry agent defined in app/app_multiagent_v2.py, using the
same tools and skills.
"""

from typing import Any

from langchain.agents import create_agent
# from langgraph.checkpoint.memory import MemorySaver
from deepagents import CompiledSubAgent

from langchain_surf.chat_models.chat_willma import ChatWillma


from sra_chem.subagents.pyscf.tools.hf_tools import hf_energy_local, hf_energy_hpc
from sra_chem.subagents.pyscf.tools.dft_tools import dft_energy_local, dft_energy_hpc
from sra_chem.subagents.pyscf.tools.tddft_tools import (
    td_dft_absorption_spectrum,
    td_dft_excitations_hpc,
    td_dft_excitations_local,
)

from sra_chem.subagents.pyscf.prompt.pyscf_agent_prompt import pyscf_agent_prompt

# Tools and skills matching the quantum_chemistry_agent in app_multiagent_v2.py
TOOLS = [
    hf_energy_local,
    hf_energy_hpc,
    dft_energy_local,
    dft_energy_hpc,
    td_dft_absorption_spectrum,
    td_dft_excitations_hpc,
    td_dft_excitations_local,
]


def create_pyscf_agent(
    api_key: str,
    model: str = "Qwen/Qwen3.6-35B-A3B-FP8",
    temperature: float = 0.1,
    max_tokens: int = 1000,
    timeout: int = 30,
) -> Any:
    """Create a compiled LangGraph subagent for quantum chemistry calculations.

    This agent uses the same tools and skills as the ``quantum_agent`` defined
    in ``app/app_multiagent_v2.py``.

    Parameters
    ----------
    api_key : str
        API key for the LLM service.
    model : str, optional
        Model to use, by default ``"Qwen/Qwen3.6-35B-A3B-FP8"``.
    temperature : float, optional
        Sampling temperature, by default 0.1.
    max_tokens : int, optional
        Maximum tokens per response, by default 1000.
    timeout : int, optional
        Request timeout in seconds, by default 30.

    Returns
    -------
    Any
        Compiled LangGraph agent (Runnable) instance.
    """
    llm = ChatWillma(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        api_key=api_key,
    )

    # checkpointer = MemorySaver()

    graph = create_agent(
        llm,
        tools=TOOLS,
        system_prompt=pyscf_agent_prompt,
    )

    agent = CompiledSubAgent(
        name="PySCF Agent",
        description="Agent for quantum chemistry calculations using PySCF",
        runnable=graph
    )

    return agent