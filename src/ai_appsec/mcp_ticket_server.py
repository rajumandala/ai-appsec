import os

from mcp.server.mcpserver import MCPServer

TICKETS = {
    "T-101": {"owner": "asha@example.com", "status": "open", "text": "VPN says 'authentication failed' after I changed my password."},
    "T-102": {"owner": "ravi@example.com", "status": "open", "text": "Laptop battery drains in one hour."},
}

# Who is using this server. The client sets it when it starts the server.
# It is never a tool argument, so the model cannot change it.
SIGNED_IN_USER = os.environ["SIGNED_IN_USER"]

server = MCPServer("tickets")


@server.tool()
def get_ticket(ticket_id: str) -> dict:
    """Read a helpdesk ticket by its ID."""
    ticket = TICKETS.get(ticket_id)
    if ticket is None or ticket["owner"] != SIGNED_IN_USER:
        return {"error": "ticket not found"}
    return {"ticket_id": ticket_id, "status": ticket["status"], "text": ticket["text"]}


if __name__ == "__main__":
    server.run()  # talks to the client over stdin and stdout
