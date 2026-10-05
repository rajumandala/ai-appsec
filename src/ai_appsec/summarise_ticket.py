from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

ticket = (
    "Ticket T-101 from asha@example.com\n"
    "Subject: Cannot connect to VPN\n"
    "Since this morning the VPN client says 'authentication failed'. "
    "I changed my password yesterday. I have a client demo at 3 pm."
)

response = client.responses.create(
    model="gpt-6-luna",
    instructions="You are a helpdesk assistant. Summarise the ticket in one sentence.",
    input=ticket,
)

print("Summary:", response.output_text)
print("Response ID:", response.id)
print("Tokens in:", response.usage.input_tokens)
print("Tokens out:", response.usage.output_tokens)