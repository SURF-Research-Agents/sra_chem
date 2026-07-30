import logging
import os
import json
import time
from dotenv import load_dotenv
from flask import Flask, Response, request
from werkzeug.exceptions import BadRequest
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from langchain_ui.message import OpenAIRequest
from langchain_ui.agents.agent_utils import format_data
from langchain_surf.chat_models.chat_willma import ChatWillma

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
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv('/Users/renau001/Documents/projects/ai/SRA/.env')
api_key = os.getenv("AIHUB_API_KEY")
model_name = 'Qwen/Qwen3.6-35B-A3B-FP8'

langfuse = get_client()
langfuse_handler = CallbackHandler()


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




app = Flask('MultiAgentChem')



@app.route("/chat/completions", methods=["POST"])
def chat():


    try:
        payload = request.get_json(force=True, silent=True)
        if not payload:
            raise BadRequest("Missing JSON body")

        chat_request = OpenAIRequest(**payload)
        question = chat_request.messages[-1].content

        if not question:
            raise BadRequest("Empty question")
    except (BadRequest, TypeError, KeyError) as e:
        return Response(
            f'data: {{"error": "{str(e)}"}}\n\n',
            mimetype="text/event-stream",
            status=400
        )
    


    def generate():
        formated_question = {
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": question,
                                    }
                                ]
                            }
        try:

            stream = agent.stream_events(
                    formated_question,
                    version='v3',
                    config={"callbacks": [langfuse_handler]}
                )

            for name, item in stream.interleave("messages", "subagents"):

                print("\n=============\n")
                print(name, item)
                print("\n=============\n")

                if name == "messages":
                    # print("[coordinator]", item.text)
                    content = []
                    content.append(str(item.text))
                    # tool_calls = item.tool_calls.get()
                    # for tc in tool_calls:
                    #     content.append(f'⚗️```{tc['name']}```')
                        
                    data = format_data(chunk_id=str(uuid4()),
                                        model=model_name,
                                        system_fingerprint=str(uuid4()),
                                        content='\n'.join(content)
                                        )
                    yield bytes(f"data: {data}\n\n", "utf-8")
                else:
                    # print(f"[{item.name}] started")
                    data = format_data(chunk_id=str(uuid4()),
                                        model=model_name,
                                        system_fingerprint=str(uuid4()),
                                        content=f"\n🤖 *Delegating task to {item.name}*\n"
                                        )
                    yield bytes(f"data: {data}\n\n", "utf-8")
                    for message in item.messages:

                        content = []
                        content.append(str(message.text))
                        tool_calls = message.tool_calls.get()
                        for tc in tool_calls:
                            content.append(f'⚗️```{tc['name']}```')
                        data = format_data(chunk_id=str(uuid4()),
                                            model=model_name,
                                            system_fingerprint=str(uuid4()),
                                            content='\n'.join(content)
                                            )
                        yield bytes(f"data: {data}\n\n", "utf-8")
                    # print(f"[{item.name}] status: {item.status} \n")
                    data = format_data(chunk_id=str(uuid4()),
                                        model=model_name,
                                        system_fingerprint=str(uuid4()),
                                        content=f"\n\n↪*{item.name} terminated with status: {item.status}*\n"
                                        )
                    yield bytes(f"data: {data}\n\n", "utf-8")

            # Send final chunk with finish_reason=stop
            data = format_data(chunk_id=str(uuid4()),
                                model=model_name,
                                system_fingerprint=str(uuid4()),
                                content=""
                                )
            parsed = json.loads(data)
            parsed["choices"][0]["finish_reason"] = "stop"
            yield bytes(f"data: {json.dumps(parsed)}\n\n", "utf-8")

        except Exception as e:
            logger.exception("Streaming error")
            yield f'data: {{"error": "{str(e)}"}}\n\n'

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
        direct_passthrough=True,
    )


if __name__ == "__main__":
    app.run(debug=True, port=8000)
