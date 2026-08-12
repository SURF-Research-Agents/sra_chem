"""LangGraph compiled subagent for chemoinformatics tasks.

This module provides a compiled LangGraph agent that replicates the
chemoinformatic_agent defined in app/app_multiagent_v2.py, using the
same tools and skills.
"""

from typing import Any

from langchain_core.messages import SystemMessage
# from langgraph.checkpoint.memory import MemorySaver
from deepagents import CompiledSubAgent
from langchain.agents import create_agent
from langchain_surf.chat_models.chat_willma import ChatWillma

from sra_chem.subagents.chemoinformatics.tools.cheminformatics_tools import (
    molecule_name_to_smiles,
    smiles_to_coordinate_file,
)
from sra_chem.subagents.chemoinformatics.prompt.chemoinformatics_agent_prompt import chemoinformatic_agent_prompt

# Tools and skills matching the chemoinformatic_agent in app_multiagent_v2.py
TOOLS = [
    molecule_name_to_smiles,
    smiles_to_coordinate_file,
]

def create_chemoinformatics_agent(
    api_key: str,
    model: str = "Qwen/Qwen3.6-35B-A3B-FP8",
    temperature: float = 0.1,
    max_tokens: int = 1000,
    timeout: int = 30,
) -> Any:
    """Create a compiled LangGraph subagent for chemoinformatics tasks.

    This agent uses the same tools and skills as the
    ``chemoinformatic_agent`` defined in ``app/app_multiagent_v2.py``.

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

    system_message = SystemMessage(content=chemoinformatic_agent_prompt)

    # checkpointer = MemorySaver()

    graph = create_agent(
        llm,
        tools=TOOLS,
        system_prompt=system_message
    )

    agent = CompiledSubAgent(
        name="Chemoinformatics Agent",
        description="Agent for chemoinformatics tasks such as converting molecule names to SMILES and generating coordinates from SMILES",
        runnable=graph
    )    

    return agent
