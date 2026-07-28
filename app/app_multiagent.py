import logging
import os
import json
import time
from dotenv import load_dotenv
from flask import Flask, Response, request
from werkzeug.exceptions import BadRequest

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from langchain_ui.message import OpenAIRequest
from sra_chem.agents.multi_agent import create_multi_agent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv('/Users/renau001/Documents/projects/ai/SRA/.env')
api_key = os.getenv("AIHUB_API_KEY")

langfuse = get_client()
langfuse_handler = CallbackHandler()

app = Flask('MultiAgentChem')

willma_agent = create_multi_agent(api_key=os.getenv("AIHUB_API_KEY"))



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
                                             stream_mode='updates',
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


if __name__ == "__main__":
    app.run(debug=True, port=8000)
