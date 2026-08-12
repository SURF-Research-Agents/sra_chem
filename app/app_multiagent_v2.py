import logging
import os
from dotenv import load_dotenv
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.memory import InMemorySaver


from langchain_surf.chat_models.chat_willma import ChatWillma
from langchain_ui.app.multiagent_app_factory import create_app
from sra_chem.tools.directory_tools import create_workspace

from sra_chem.subagents.pyscf.pyscf_agent import create_pyscf_agent
from sra_chem.subagents.pyscf.pyscf_resource_estimation_agent import create_pyscf_resource_estimation_agent
from sra_chem.subagents.chemoinformatics.chemoinformatics_agent import create_chemoinformatics_agent
from sra_chem.subagents.summarization.summarization_agent import create_summarization_agent

from sra_chem.prompts.multiagent_prompt import multi_agent_prompt

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

chemoinformatic_agent = create_chemoinformatics_agent(
    api_key=api_key,
    model=model_name,
)


quantum_chemistry_agent = create_pyscf_agent(
    api_key=api_key,
    model=model_name,
)

summarization_agent = create_summarization_agent(
    api_key=api_key,
    model=model_name,
)

resource_estimation_agent = create_pyscf_resource_estimation_agent(
    api_key=api_key,
    model=model_name,
)

agent = create_deep_agent(model,
                     subagents=[chemoinformatic_agent,
                                quantum_chemistry_agent,
                                summarization_agent,
                                resource_estimation_agent],
                     backend=backend,
                     skills=skills,
                     system_prompt=multi_agent_prompt,
                     tools=[create_workspace],
                     checkpointer=InMemorySaver(),
                     name='main-agent')

app = create_app(agent, model_name)



if __name__ == "__main__":
    app.run(debug=True, port=8000)
