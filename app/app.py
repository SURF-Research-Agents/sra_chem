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

app = Flask('ChemAgent')
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
            for chunk in willma_agent.stream(question, 
                                             config={"callbacks": [langfuse_handler]}):
                yield chunk
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

    # def generate():
    #     try:
    #         for chunk in willma_agent.stream(
    #             question, config={"callbacks": [langfuse_handler]}
    #         ):
    #             if isinstance(chunk, dict):
    #                 event = chunk.get("event", "")
    #                 if event in ("on_chat_model_stream", "on_llm_stream"):
    #                     content = chunk.get("data", {}).get("chunk", {}).get("content", "")
    #                 elif event == "on_agent_action":
    #                     content = chunk.get("data", {}).get("text", "")
    #                 else:
    #                     content = str(chunk.get("data", ""))
    #             else:
    #                 content = str(chunk)

    #             if content:
    #                 payload = json.dumps({
    #                     "choices": [{"delta": {"role": "assistant", "content": content}}]
    #                 })
    #                 yield f'data: {payload}\n\n'
    #         yield 'data: [DONE]\n\n'
    #     except Exception as e:
    #         logger.exception("Streaming error")
    #         error_payload = json.dumps({"error": str(e)})
    #         yield f'data: {error_payload}\n\n'

    # return Response(
    #     generate(),
    #     mimetype="text/event-stream",
    #     headers={
    #         "Cache-Control": "no-cache",
    #         "Connection": "keep-alive",
    #         "X-Accel-Buffering": "no",
    #     },
    #     direct_passthrough=True,
    # )

if __name__ == "__main__":
    app.run(debug=True, port=8000)
