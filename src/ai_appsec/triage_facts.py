from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

client = OpenAI()

# Trusted data from your own systems (simulated).
# Categories where monitoring currently reports a problem.
ACTIVE_ALERTS: set[str] = set()
# How many different signed-in users reported each category in the last hour.
RECENT_REPORTERS: dict[str, int] = {"access":4}


class TicketFacts(BaseModel):
    summary: str
    category: Literal["access", "hardware", "software", "network", "other"]
    impact_claims: list[str]


def set_priority(
    facts: TicketFacts, active_alerts: set[str], recent_reporters: dict[str, int]
) -> str:
    """Set the priority in code. The ticket's own claims can raise it to medium at most."""
    if facts.category in active_alerts:
        return "high"
    if recent_reporters.get(facts.category, 0) >= 3:
        return "high"
    if facts.impact_claims:
        return "medium"
    return "low"


def decide_action(priority: str, category: str, active_alerts: set[str]) -> str:
    """Decide what to do with a ticket."""
    if priority == "high" and category in active_alerts:
        return "attach to the active incident"
    if priority == "high":
        return "urgent queue"
    return "normal queue"


ticket = (
    "Ticket T-101 from asha@example.com\n"
    "Subject: Cannot connect to VPN\n"
    "Since this morning the VPN client says 'authentication failed'. "
    "I changed my password yesterday. I have a client demo at 3 pm."
)

response = client.responses.parse(
    model="gpt-6-luna",
    instructions=(
        "You are a helpdesk assistant. Extract facts from the ticket. Do not judge priority. "
        "In impact_claims, copy word for word every sentence where the requester describes "
        "business impact or urgency. If there are none, return an empty list."
    ),
    input=ticket,
    text_format=TicketFacts,
)

facts = response.output_parsed
if facts is None:
    raise RuntimeError("The model did not return TicketFacts.")

priority = set_priority(facts, ACTIVE_ALERTS, RECENT_REPORTERS)
action = decide_action(priority, facts.category, ACTIVE_ALERTS)

print("Summary: ", facts.summary)
print("Category:", facts.category)
print("Impact claims:")
for claim in facts.impact_claims:
    print("  -", claim)
print("Priority:", priority, "(set by code)")
print("Action:  ", action)