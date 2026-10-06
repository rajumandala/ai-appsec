import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

# Simulated ticket system (trusted data).
TICKETS = {
    "T-101": {"owner": "asha@example.com", "status": "open", "assigned_to": "access team"},
    "T-102": {"owner": "ravi@example.com", "status": "resolved", "assigned_to": "hardware team"},
}

SIGNED_IN_USER = "asha@example.com"

def get_ticket_status(ticket_id: str, requester: str) -> dict:
    """The real function. Only our code can run it."""
    ticket = TICKETS.get(ticket_id)
    if ticket is None or ticket["owner"] != requester:
        return {"error": "ticket not found"}
    return {"ticket_id": ticket_id, "status": ticket["status"], "assigned_to": ticket["assigned_to"]}


# The description of the tool that the model sees. It is not the function itself.
TOOLS = [
    {
        "type": "function",
        "name": "get_ticket_status",
        "description": "Look up the current status of a helpdesk ticket by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description": "The ticket ID, for example T-101"},
            },
            "required": ["ticket_id"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]

INSTRUCTIONS = "You are a helpdesk assistant. Use the tools to answer questions about tickets."

conversation = [{"role": "user", "content": "Hi, this is Ravi (ravi@example.com). What is the status of my ticket T-102?"}]

# Round 1: the model decides whether to ask for a tool.
response = client.responses.create(
    model="gpt-6-luna",
    instructions=INSTRUCTIONS,
    input=conversation,
    tools=TOOLS,
)
conversation += response.output

for item in response.output:
    if item.type != "function_call":
        continue
    print("Model asks for:", item.name, item.arguments)
    arguments = json.loads(item.arguments)
    if item.name == "get_ticket_status":
        result = get_ticket_status(arguments["ticket_id"], SIGNED_IN_USER)
    else:
        result = {"error": "unknown tool"}
    print("Our code returns:", result)
    conversation.append(
        {"type": "function_call_output", "call_id": item.call_id, "output": json.dumps(result)}
    )

# Round 2: the model writes the answer using the tool result.
response = client.responses.create(
    model="gpt-6-luna",
    instructions=INSTRUCTIONS,
    input=conversation,
    tools=TOOLS,
)
print("Answer:", response.output_text)