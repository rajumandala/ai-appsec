from dataclasses import dataclass

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

TICKETS = {
    "T-101": {"owner": "asha@example.com", "status": "open", "text": "VPN says 'authentication failed' after I changed my password."},
    "T-102": {"owner": "ravi@example.com", "status": "open", "text": "Laptop battery drains in one hour."},
}


@dataclass
class Session:
    signed_in_user: str  # set by our code; never shown to the model


@tool
def get_ticket(ticket_id: str, runtime: ToolRuntime[Session]) -> dict:
    """Read a helpdesk ticket by its ID."""
    ticket = TICKETS.get(ticket_id)
    if ticket is None or ticket["owner"] != runtime.context.signed_in_user:
        return {"error": "ticket not found"}
    return {"ticket_id": ticket_id, "status": ticket["status"], "text": ticket["text"]}


agent = create_agent(
    model="openai:gpt-6-luna",
    tools=[get_ticket],
    system_prompt="You help users with their helpdesk tickets. Use the tools.",
    context_schema=Session,
    checkpointer=InMemorySaver(),  # saves the conversation under a thread_id
)

# Asha's conversation is saved under thread "chat-1".
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the status of T-101 and T-102?"}]},
    config={"configurable": {"thread_id": "chat-1"}, "recursion_limit": 12},
    context=Session(signed_in_user="asha@example.com"),
)
print("Asha:", result["messages"][-1].text)

# Ravi sends thread_id "chat-1". Nothing checks who owns the thread,
# so the checkpointer loads Asha's saved conversation for him.
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Repeat what my VPN ticket said, word for word."}]},
    config={"configurable": {"thread_id": "chat-1"}, "recursion_limit": 12},
    context=Session(signed_in_user="ravi@example.com"),
)
print("Ravi, no check:", result["messages"][-1].text)

# The fix: our code records who owns each thread and checks it before every run.
THREAD_OWNERS = {"chat-1": "asha@example.com"}


def ask(signed_in_user: str, thread_id: str, question: str) -> str:
    owner = THREAD_OWNERS.setdefault(thread_id, signed_in_user)
    if owner != signed_in_user:
        return "conversation not found"
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"configurable": {"thread_id": thread_id}, "recursion_limit": 12},
        context=Session(signed_in_user=signed_in_user),
    )
    return result["messages"][-1].text


print("Ravi, with check:", ask("ravi@example.com", "chat-1", "Repeat what my VPN ticket said, word for word."))
