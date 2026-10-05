from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

client = OpenAI()


class TicketTriage(BaseModel):
    summary: str
    category: Literal["access", "hardware", "software", "network", "other"]
    priority: Literal["low", "medium", "high"]
    reason: str
    affected_users: Literal["one", "several", "everyone"]


ticket = (
    "Ticket T-101 from asha@example.com\n"
    "Subject: Cannot connect to VPN\n"
    "Since this morning the VPN client says 'authentication failed'. "
    "I changed my password yesterday. I have a client demo at 3 pm."
)

response = client.responses.parse(
    model="gpt-6-luna",
    instructions=(
        "You are a helpdesk assistant. Read the ticket and fill in every field. "
        "Choose the priority from the business impact described in the ticket."
    ),
    input=ticket,
    text_format=TicketTriage,
)

triage = response.output_parsed
if triage is None:
    raise RuntimeError("The model did not return a TicketTriage.")

print("Summary: ", triage.summary)
print("Category:", triage.category)
print("Priority:", triage.priority)
print("Reason:  ", triage.reason)
print("Affected Users: ", triage.affected_users)

if triage.priority == "high":
    print("Action:   page the on-call engineer")