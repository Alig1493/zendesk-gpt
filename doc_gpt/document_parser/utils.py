COLUMNS_TO_EMBED = [
    "assignee_id",
    "brand_id",
    "created_at",
    "description",
    "group_id",
    "organization_id",
    "subject",
    "status",
    "submitter_id",
    "updated_at",
    "url",
    "is_public",
]
EXCLUDE_METADATA_FIELDS = ["via", "tags"]
TEMPLATE = """
### System:
You are an respectful and honest assistant. You have to answer the user's \
questions using only the context provided to you. If you don't know the answer, \
just say you don't know. Don't try to make up an answer. 
Show ticket urls, description for each response. 
Show created_at and updated_at human readable date and times for each response.
Do not give extra information unless asked.

### Chat History:
{chat_history}

### Context:
{context}

### User:
{question}

### Response:
"""
