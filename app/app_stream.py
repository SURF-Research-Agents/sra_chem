import logging
import os
import json
from dotenv import load_dotenv
from flask import Flask, Response, request
from werkzeug.exceptions import BadRequest

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from langchain_ui.message import OpenAIRequest
from sra_chem.agents.single_agent import create_chem_agent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv('/Users/renau001/Documents/projects/ai/SRA/.env')
api_key = os.getenv("AIHUB_API_KEY")

langfuse = get_client()
langfuse_handler = CallbackHandler()

app = Flask('ChemAgentStream')
willma_agent = create_chem_agent(api_key=api_key)


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
        try:
            for event in willma_agent.stream(question,
                                             stream_mode='updates',
                                             config={"callbacks": [langfuse_handler]}):
                print(event)
                for key, value in event.items():
                    if isinstance(value, list):
                        for item in value:
                            if hasattr(item, 'content') and item.content:
                                payload = json.dumps({
                                    "choices": [{"delta": {"role": "assistant", "content": item.content}}]
                                })
                                yield f'data: {payload}\n\n'
                            if hasattr(item, 'tool_calls') and item.tool_calls:
                                for tc in item.tool_calls:
                                    payload = json.dumps({
                                        "choices": [{
                                            "delta": {
                                                "role": "assistant",
                                                "tool_calls": [{
                                                    "index": 0,
                                                    "id": tc.get('id', ''),
                                                    "type": "function",
                                                    "function": {
                                                        "name": tc.get('name', ''),
                                                        "arguments": json.dumps(tc.get('args', {}))
                                                    }
                                                }]
                                            }
                                        }]
                                    })
                                    yield f'data: {payload}\n\n'
                    elif hasattr(value, 'content') and value.content:
                        payload = json.dumps({
                            "choices": [{"delta": {"role": "assistant", "content": value.content}}]
                        })
                        yield f'data: {payload}\n\n'
                    elif key in ('agent', 'subagent'):
                        agent_name = key
                        payload = json.dumps({
                            "choices": [{
                                "delta": {
                                    "role": "assistant",
                                    "content": f"[Agent: {agent_name}]"
                                }
                            }]
                        })
                        yield f'data: {payload}\n\n'
                if key == 'values':
                    yield 'data: [DONE]\n\n'
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
