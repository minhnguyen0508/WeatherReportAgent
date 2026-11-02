# WeatherReport — AI Weather Forecast Agent

WeatherReport is a Python weather assistant built for a cloud computing and security lab. It answers natural-language questions about U.S. city forecasts using **Amazon Bedrock**, the **Strands Agents SDK**, a local **Model Context Protocol (MCP)** weather tool, and the **Open-Meteo** forecast API. The same agent can run interactively on a computer or through **Amazon Bedrock AgentCore Runtime**.

Example questions:
- “What is the weather today in Los Angeles, CA?”
- “Will it rain in Seattle, WA tomorrow?”
- “What time will it be sunny in Fullerton, CA?”
- “Compare today's forecasts in Fullerton, CA and Irvine, CA.”

## How it works

```text
User (terminal or AgentCore invocation)
  -> Strands agent -> Amazon Bedrock model (selects MCP tool)
  -> MCP weather server -> Open-Meteo geocoding + forecast APIs
  -> MCP result -> Strands / Bedrock -> natural-language answer
```

- **Bedrock** provides the language model.
- **Strands** manages the agent and tool-calling loop.
- **MCP** exposes `get_weather_forecast(city, day)` as a read-only tool.
- **Open-Meteo** supplies geocoding, current conditions, daily and hourly forecasts.
- **AgentCore** hosts the application after deployment (optional for local use).

Forecasts are estimates, not guarantees. The current implementation targets **U.S. cities**, and Fullerton, CA is the default only when no city is supplied. Unknown or ambiguous locations should be checked rather than silently replaced with a different city.

## Repository layout

This README assumes the AgentCore-generated `WeatherReport` project layout:

```text
WeatherReport/
├── README.md
├── .github/workflows/ci.yml
├── tests/test_weather_service.py
├── agentcore/                  # generated AgentCore configuration (if present)
└── app/agent/
    ├── main.py                 # AgentCore entrypoint
    ├── weather_agent.py        # Strands + Bedrock + MCP client
    ├── weather_mcp_server.py   # MCP tool
    ├── weather_service.py      # Open-Meteo integration
    └── pyproject.toml          # Python dependencies
```

If you're using the original starter folder instead, the Python files and `requirements.txt` are at the repository root; adjust commands accordingly.

## Prerequisites

- Python 3.12 (recommended), Git, and an AWS account
- AWS CLI v2 configured with credentials or SSO (`aws sts get-caller-identity`)
- Access to a supported Amazon Bedrock model (including any model-provider first-use requirements)
- Internet access to the Open-Meteo service
- For AgentCore deployment: Node.js, the AgentCore CLI, and `uv`

**Costs:** Bedrock and AgentCore can incur AWS charges. Open-Meteo's no-key endpoint is subject to its non-commercial use and rate limits.

## Run the local agent (Windows CMD)

From the repository root:

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate
cd app\agent
python -m pip install --upgrade pip
python -m pip install -e .
cd ..\..
set AWS_DEFAULT_REGION=us-west-2
set BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0
python app\agent\local_agent.py
```

**Note:** If your AgentCore project doesn't have `app/agent/local_agent.py`, copy `local_agent.py` from the original starter into that directory before running this command. If you use `requirements.txt` in the starter directory instead of `pyproject.toml`, install with `python -m pip install -r requirements.txt` and run `python local_agent.py` there. To stay compatible with the provided `FastMCP` import, use **`mcp>=1,<2`** in your dependency specification. Confirm that the version is compatible with your installed Strands release (`python -m pip check`).

Bedrock defaults can be changed using `BEDROCK_MODEL_ID` and `AWS_DEFAULT_REGION`. Do not commit AWS credentials or `.env` secrets.

## Run tests

The included CI tests mock the weather provider, so **GitHub Actions requires no AWS credentials and makes no live weather API requests**.

From the repository root:

```cmd
python -m pip install pytest requests tzdata
set PYTHONPATH=app\agent
python -m pytest tests -v
```

To manually test a real MCP call, use the original `test_mcp_call.py` from the starter folder, alongside the weather source files. This **live integration test** requires network access and is intentionally excluded from CI.

## AgentCore (optional managed deployment)

From the AgentCore project root, after configuring AWS credentials and the correct model and runtime permissions:

```cmd
agentcore dev
```

In a second Windows CMD terminal:

```cmd
agentcore invoke --runtime agent --local --payload "{\"prompt\":\"Will it rain in Fullerton today?\"}"
```

For cloud deployment and remote invocation:

```cmd
agentcore build
agentcore deploy
agentcore status
agentcore invoke --runtime agent --payload "{\"prompt\":\"What is the weather in Seattle, WA?\"}"
```

Check AgentCore/CloudWatch logs if remote invocations fail. A deployed Runtime needs its **own IAM permissions** to call Bedrock. Verify remote invocations before recording the deployment as successful.

Remove unused AWS resources when finished, following the deployment CLI's cleanup commands, and review the deletion plan carefully.

## CI/CD with GitHub Actions

The workflow in `.github/workflows/ci.yml` runs on pushes to `main` and on pull requests targeting `main`. It checks Python syntax and runs network-free weather-service unit tests. **It does not deploy to AWS**—deployment should remain a separately approved step with properly scoped AWS credentials/roles.

## Security notes

- MCP weather functions are read-only; inputs are constrained to supported locations and forecast days.
- Weather requests use fixed HTTPS API hosts and timeouts.
- Tool output is untrusted; do not allow provider text to override application instructions.
- Use least-privilege IAM permissions for Bedrock and AgentCore.
- Do not commit `.env`, AWS credentials, session tokens, or private keys.
- Avoid logging secrets or sensitive request details.

## Further reading

- [Amazon Bedrock documentation](https://docs.aws.amazon.com/bedrock/)
- [Strands Agents documentation](https://strandsagents.com/)
- [MCP documentation](https://modelcontextprotocol.io/)
- [Amazon Bedrock AgentCore documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Open-Meteo API documentation](https://open-meteo.com/en/docs)
