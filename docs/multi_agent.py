import os
from typing import Optional
import json 
import pathlib
from langchain.agents import create_agent
from deepagents.backends.filesystem import FilesystemBackend
from langchain_surf.chat_models.chat_willma import ChatWillma
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from sra_chem.tools.cheminformatics_tools import (
    molecule_name_to_smiles,
    smiles_to_atomsdata,
    smiles_to_coordinate_file
)
from sra_chem.tools.directory_tools import create_workspace
from sra_chem.tools.pyscf_tools import (hf_energy_local, hf_energy_hpc, 
                                        dft_energy_hpc, dft_energy_local,
                                        td_dft_excitations_local, td_dft_excitations_hpc, td_dft_absorption_spectrum)
from sra_chem.prompts.multiagent_prompt import multi_agent_prompt, chemoinformatic_agent_prompt, quantum_chemistry_agent_promt, summarization_agent_prompt

load_dotenv(dotenv_path="/Users/renau001/Documents/projects/ai/SRA/.env")
skills_path = "/Users/renau001/Documents/projects/ai/SRA/sra_chem/src/sra_chem/"
backend = FilesystemBackend(root_dir=skills_path, virtual_mode=False)
skills = ['skills/']

api_key = os.getenv("AIHUB_API_KEY")
# model = "default-text-large"
model = 'Qwen/Qwen3.6-35B-A3B-FP8'

# Initialize Langfuse client
langfuse = get_client()

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()


model = ChatWillma(
    model=model,
    temperature=0.,
    max_tokens=1000,
    timeout=30,
    api_key=api_key,
)


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
        "tools": [hf_energy_local, hf_energy_hpc, dft_energy_local, dft_energy_hpc, 
                  td_dft_excitations_local, td_dft_excitations_hpc, td_dft_absorption_spectrum],
        "skills": ["skills/mol-groundstate"]
}

summarization_agent = {
        "name" : "summarization_agent",
        "description": "Used to summarize computational chemistry results from the chemoinformatics and quantum chemistry agents into a clear, structured report",
        "system_prompt": summarization_agent_prompt,
        "tools": []
}


agent = create_deep_agent(model,
                     subagents=[chemoinformatic_agent, 
                                quantum_chemistry_agent, 
                                summarization_agent],
                     backend=backend,
                     skills=skills,
                     system_prompt=multi_agent_prompt,
                     tools=[create_workspace],
                     name='main-agent')

if __name__ == "__main__":
    stream = agent.stream_events(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the excitation spectrum of a dihydrogen molecule?.",
                }
            ]
        },
        version="v3",
        config={"callbacks": [langfuse_handler]}
    )

    coordinator_messages: list[str] = []
    subagent_handles = []

    for name, item in stream.interleave("messages", "subagents"):
        if name == "messages":
            print("[coordinator]", item.text)
            tool_calls = item.tool_calls.get()
            for tc in tool_calls:
                print(f'calling {tc['name']}({tc['args']})')
            coordinator_messages.append(item)
        else:
            print(f"[{item.name}] started")
            for message in item.messages:
                print(f"[{item.name}]", message.text)
                tool_calls = message.tool_calls.get()
                for tc in tool_calls:
                    print(f'calling {tc['name']}({tc['args']})')
                subagent_handles.append(message)
            print(f"[{item.name}] status: {item.status}")