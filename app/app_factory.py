import json
import logging
from uuid import uuid4

from flask import Flask, Response, request
from werkzeug.exceptions import BadRequest

from langchain_ui.message import OpenAIRequest
from langchain_ui.agents.agent_utils import format_data

logger = logging.getLogger(__name__)


def create_app(agent, model_name, langfuse_handler):
    """Create and configure the Flask application."""

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
                        content = []
                        content.append(str(item.text))

                        data = format_data(
                            chunk_id=str(uuid4()),
                            model=model_name,
                            system_fingerprint=str(uuid4()),
                            content='\n'.join(content)
                        )
                        yield bytes(f"data: {data}\n\n", "utf-8")
                    else:
                        data = format_data(
                            chunk_id=str(uuid4()),
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
                                content.append(f'⚗️```{tc["name"]}```')
                            data = format_data(
                                chunk_id=str(uuid4()),
                                model=model_name,
                                system_fingerprint=str(uuid4()),
                                content='\n'.join(content)
                            )
                            yield bytes(f"data: {data}\n\n", "utf-8")

                        data = format_data(
                            chunk_id=str(uuid4()),
                            model=model_name,
                            system_fingerprint=str(uuid4()),
                            content=f"\n\n↪*{item.name} terminated with status: {item.status}*\n"
                        )
                        yield bytes(f"data: {data}\n\n", "utf-8")

                # Send final chunk with finish_reason=stop
                data = format_data(
                    chunk_id=str(uuid4()),
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

    return app
