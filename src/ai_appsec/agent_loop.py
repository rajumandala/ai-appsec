import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

TICKETS = {
    "T-101": {"owner": "asha@example.com", "status": "open", "text": "VPN says 'authentication failed' after I changed my password."},
    "T-106": {"owner": "kiran@example.com", "status": "open", "text": "Cannot log in to the VPN since this morning. Error: authentication failed."},
    "T-107": {"owner": "meena@example.com", "status": "open", "text": "Printer on floor 3 is out of toner."},
    "T-108": {"owner": "ravi@example.com", "status": "open", "text": "VPN connects but is very slow in the afternoon."},
}

SIGNED_IN_USER = "priya@example.com"
ANALYSTS = {"priya@example.com"}

# Limits enforced by code, not by the model.
MAX_STEPS = 6
MAX_TOTAL_TOKENS = 20_000


def list_open_tickets(requester: str) -> dict:
    if requester not in ANALYSTS:
        return {"error": "not allowed"}
    return {"open_tickets": [tid for tid, t in TICKETS.items() if t["status"] == "open"]}


def get_ticket(ticket_id: str, requester: str) -> dict:
    ticket = TICKETS.get(ticket_id)
    if ticket is None or (requester not in ANALYSTS and requester != ticket["owner"]):
        return {"error": "ticket not found"}
    return {"ticket_id": ticket_id, "status": ticket["status"], "text": ticket["text"]}


def tool(name: str, description: str, properties: dict) -> dict:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
        "strict": True,
    }


TOOLS = [
    tool("list_open_tickets", "List the IDs of all open helpdesk tickets.", {}),
    tool("get_ticket", "Read a helpdesk ticket by its ID.", {"ticket_id": {"type": "string"}}),
]

INSTRUCTIONS = "You are an assistant for helpdesk analysts. Use the tools to work with tickets."

conversation = [
    {"role": "user", "content": "Which open tickets are about VPN login failures? Give me their IDs."}
]

total_tokens = 0
finished = False

for step in range(1, MAX_STEPS + 1):
    response = client.responses.create(
        model="gpt-6-luna", instructions=INSTRUCTIONS, input=conversation, tools=TOOLS
    )
    total_tokens += response.usage.total_tokens
    print(f"Step {step}: input tokens {response.usage.input_tokens}, total so far {total_tokens}")
    conversation += response.output

    calls = [item for item in response.output if item.type == "function_call"]
    if not calls:
        finished = True
        break

    if total_tokens > MAX_TOTAL_TOKENS:
        print("Stopped: token budget used up.")
        break

    for call in calls:
        arguments = json.loads(call.arguments)
        print(f"  Model asks for: {call.name} {arguments}")
        if call.name == "list_open_tickets":
            result = list_open_tickets(SIGNED_IN_USER)
        elif call.name == "get_ticket":
            result = get_ticket(arguments["ticket_id"], SIGNED_IN_USER)
        else:
            result = {"error": "unknown tool"}
        conversation.append(
            {"type": "function_call_output", "call_id": call.call_id, "output": json.dumps(result)}
        )

if finished:
    print("Answer:", response.output_text)
else:
    print("The agent did not finish. Nothing more was done.")
