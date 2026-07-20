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
from sra_chem.tools.pyscf_tools import ground_state_energy_local, ground_state_energy_hpc
from sra_chem.prompts.single_agent_prompt import single_agent_prompt

skills_path = "/Users/renau001/Documents/projects/ai/SRA/sra_chem/src/sra_chem/"
backend = FilesystemBackend(root_dir=skills_path)
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
                            create_workspace],
                     backend=backend,
                     skills=skills,
                     system_prompt=single_agent_prompt)


# result = agent.invoke(
#     {"messages": [{"role": "user", "content": "What are the atomic coordinate of cafeine?"}]},
#     config={"callbacks": [langfuse_handler]}
# )
# print(result)


result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the ground state energy of water using sto-6g basis?"}]},
    config={"callbacks": [langfuse_handler]}
)
print(result['messages'][-1].content)