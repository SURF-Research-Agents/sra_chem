import logging
import os
from dotenv import load_dotenv
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend


from langchain_surf.chat_models.chat_willma import ChatWillma
from langchain_ui.app.multiagent_app_factory import create_app
from sra_chem.tools.cheminformatics_tools import (
    molecule_name_to_smiles,
    smiles_to_atomsdata,
    smiles_to_coordinate_file
)
from sra_chem.tools.directory_tools import create_workspace
from sra_chem.tools.hf_tools import hf_energy_local, hf_energy_hpc
from sra_chem.tools.dft_tools import dft_energy_local, dft_energy_hpc
from sra_chem.tools.tddft_tools import td_dft_absorption_spectrum, td_dft_excitations_hpc,td_dft_excitations_local

from sra_chem.prompts.multiagent_prompt import multi_agent_prompt, chemoinformatic_agent_prompt, quantum_chemistry_agent_promt, summarization_agent_prompt
# from app_factory import create_app

logging.basicConfig(level=logging.INFO)

load_dotenv('/Users/renau001/Documents/projects/ai/SRA/.env')
api_key = os.getenv("AIHUB_API_KEY")
model_name = 'Qwen/Qwen3.6-35B-A3B-FP8'
# model_name = 'Qwen/Qwen3.6-27B-FP8'
# model_name = 'mistralai/Mistral-Small-3.2-24B-Instruct-2506'
# model_name = 'openai/gpt-oss-120b'


skills_path = "/Users/renau001/Documents/projects/ai/SRA/sra_chem/src/sra_chem/"
backend = FilesystemBackend(root_dir=skills_path, virtual_mode=False)
skills = ['skills/']


model = ChatWillma(
    model=model_name,
    temperature=0.1,
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
        "tools": [hf_energy_local, hf_energy_hpc, dft_energy_hpc, dft_energy_local, td_dft_absorption_spectrum, td_dft_excitations_hpc,td_dft_excitations_local],
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

app = create_app(agent, model_name)


if __name__ == "__main__":
    app.run(debug=True, port=8000)
