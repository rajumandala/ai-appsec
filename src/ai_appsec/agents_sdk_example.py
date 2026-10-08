from dataclasses import dataclass

from agents import Agent, RunContextWrapper, Runner, function_tool
from dotenv import load_dotenv

load_dotenv()

TICKETS = {
    "T-101": {"owner": "asha@example.com", "status": "open", "text": "VPN says 'authentication failed' after I changed my password."},
    "T-102": {"owner": "ravi@example.com", "status": "open", "text": "Laptop battery drains in one hour."},
}


@dataclass
class Session:
    signed_in_user: str  # set by our code; never shown to the model


@function_tool
def get_ticket(ctx: RunContextWrapper[Session], ticket_id: str) -> dict:
    """Read a helpdesk ticket by its ID."""
    ticket = TICKETS.get(ticket_id)
    if ticket is None or ticket["owner"] != ctx.context.signed_in_user:
        return {"error": "ticket not found"}
    return {"ticket_id": ticket_id, "status": ticket["status"], "text": ticket["text"]}


agent = Agent(
    name="Helpdesk assistant",
    instructions="You help users with their helpdesk tickets. Use the tools.",
    model="gpt-6-luna",
    tools=[get_ticket],
)

result = Runner.run_sync(
    agent,
    "What is the status of T-101 and T-102?",
    context=Session(signed_in_user="asha@example.com"),
    max_turns=6,
)
print(result.final_output)
