import asyncio
import json
import sys

from dotenv import load_dotenv
from mcp import Client, StdioServerParameters
from openai import OpenAI

load_dotenv()

openai_client = OpenAI()

SIGNED_IN_USER = "asha@example.com"
MAX_STEPS = 6

# The MCP servers this assistant uses. Each one is a program that the client starts.
SERVERS = {
    "tickets": StdioServerParameters(
        command=sys.executable,
        args=["src/ai_appsec/mcp_ticket_server.py"],
        env={"SIGNED_IN_USER": SIGNED_IN_USER},
    ),
    "weather": StdioServerParameters(
        command=sys.executable,
        args=["src/ai_appsec/mcp_weather_server.py"],
    ),
}

QUESTION = "What is the weather in Chennai?"


def to_openai_tool(mcp_tool) -> dict:
    """Turn a tool description from an MCP server into the format OpenAI expects."""
    return {
        "type": "function",
        "name": mcp_tool.name,
        "description": mcp_tool.description,
        "parameters": mcp_tool.input_schema,
    }


async def main():
    async with Client(SERVERS["tickets"]) as tickets, Client(SERVERS["weather"]) as weather:
        # 1. Ask each server which tools it has.
        tools, owner = [], {}
        for mcp_client in (tickets, weather):
            for mcp_tool in (await mcp_client.list_tools()).tools:
                print(f"Tool {mcp_tool.name}: {mcp_tool.description!r}")
                tools.append(to_openai_tool(mcp_tool))
                owner[mcp_tool.name] = mcp_client

        # 2. The agent loop from Concept 4. Tool calls now go to the MCP servers.
        conversation = [{"role": "user", "content": QUESTION}]
        for step in range(1, MAX_STEPS + 1):
            response = openai_client.responses.create(
                model="gpt-6-luna", input=conversation, tools=tools
            )
            conversation += response.output
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                print("Answer:", response.output_text)
                return
            for call in calls:
                arguments = json.loads(call.arguments)
                print(f"Step {step}: model asks for {call.name} {arguments}")
                result = await owner[call.name].call_tool(call.name, arguments)
                conversation.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps([c.model_dump() for c in result.content]),
                    }
                )
        print("The agent did not finish. Nothing more was done.")


asyncio.run(main())
