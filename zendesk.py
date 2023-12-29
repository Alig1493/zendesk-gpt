import os
import json
from zenpy import Zenpy

CREDS = {
    "email": os.getenv("ZENDESK_EMAIL"),
    "token": os.getenv("ZENDESK_API_KEY"),
    "subdomain": os.getenv("ZENDESK_SUBDOMAIN")
}


print(1)
zenpy_client = Zenpy(**CREDS)
print(2)
tickets = zenpy_client.search(type="ticket")
print(3)
ticket_list = []

for ticket in tickets:
    print(4)
    ticket_list.append(ticket.to_dict())


with open("zendesk.json", "w+") as zendesk_json_file:
    zendesk_json_file.write(json.dumps(ticket_list, indent=2))
