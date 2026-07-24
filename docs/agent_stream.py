import os
import json
from typing import Optional
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
from sra_chem.tools.pyscf_tools import ground_state_energy_local, ground_state_energy_hpc
from sra_chem.prompts.single_agent_prompt import single_agent_prompt

skills_path = "/Users/renau001/Documents/projects/ai/SRA/sra_chem/src/sra_chem/"
backend = FilesystemBackend(root_dir=skills_path, virtual_mode=False)
skills = ['skills/']

load_dotenv(dotenv_path="/Users/renau001/Documents/projects/ai/SRA/.env")

api_key = os.getenv("AIHUB_API_KEY")
model = "default-text-large"

# Initialize Langfuse client
langfuse = get_client()

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()


model = ChatWillma(
    model=model,
    temperature=0.1,
    max_tokens=1000,
    timeout=30,
    api_key=api_key,
)

agent = create_deep_agent(model,
                     tools=[molecule_name_to_smiles,
                            smiles_to_atomsdata,
                            smiles_to_coordinate_file,
                            ground_state_energy_local,
                            ground_state_energy_hpc,
                            ],
                     backend=backend,
                     skills=skills,
                     system_prompt=single_agent_prompt)


# Stream events and print intermediate steps
for event in agent.stream(
    {"messages": [{"role": "user", "content": "What is the ground state energy of caffiene?"}]},
    stream_mode='updates',
    config={"callbacks": [langfuse_handler]}
):
    for key, value in event.items():
        print(f"--- {key} ---")
        if isinstance(value, list):
            for item in value:
                if hasattr(item, 'content'):
                    print(f"  content: {item.content}")
                if hasattr(item, 'tool_calls') and item.tool_calls:
                    for tc in item.tool_calls:
                        print(f"  tool_call: {tc.get('name', 'unknown')} -> {tc.get('args', {})}")
        elif hasattr(value, 'content'):
            print(f"  content: {value.content}")
        else:
            print(f"  {value}")
    print()
