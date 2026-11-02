"""Lab 3: copy this file to app/agent/main.py in a scaffolded AgentCore project."""
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from weather_agent import build_agent

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict):
    question = payload.get("prompt") if isinstance(payload, dict) else None
    if not isinstance(question, str) or not question.strip() or len(question) > 500:
        return {"error": "Provide a non-empty 'prompt' string of at most 500 characters."}
    agent = build_agent()
    return {"result": str(agent(question.strip()))}


if __name__ == "__main__":
    app.run()
