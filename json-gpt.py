import json
import os

from langchain import PromptTemplate
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.llms import Ollama

from langchain.docstore.document import Document
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma


# Define the columns we want to embed vs which ones we want in metadata
embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
model = os.environ.get("MODEL", "mistral")
columns_to_embed = [
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
exclude_metadata = ["via", "tags"]

metadata_description_dict = {
    "assignee_id": "assignee id in integer of the zendesk ticket",
    "brand_id": "brand id in integer of the zendesk ticket",
    "collaborator_ids": "List of collaborator id's of the zendesk ticket",
    "created_at": "creation date time of the zendesk ticket",
    "custom_fields": "list of custom fields of the zendesk ticket",
    "description": "description of the zendesk ticket",
    "due_at": "due at datetime for the zendesk ticket",
    "external_id": "external id of the zendesk ticket",
    "fields": "list of fields of the zendesk ticket",
    "forum_topic_id": "forum topic id of the zendesk ticket",
    "group_id": "group id  in integer of the zendesk ticket",
    "has_incidents": "boolean field to indicate if zendesk ticket has incidents",
    "id": "zendesk ticket id in integer",
    "organization_id": "organization id in integer of the zendesk ticket",
    "priority": "priority rating of the zendesk ticket",
    "problem_id": "problem id in integer of the zendesk ticket",
    "raw_subject": "raw subject of the zendesk ticket",
    "recipient": "email address of the recipient of the zendesk ticket",
    "requester_id": "requester id in integer of the zendesk ticket",
    "satisfaction_rating": "satisfaction rating of the zendesk ticket",
    "sharing_agreement_ids": "sharing agreement ids of the zendesk ticket",
    "status": "status of the zendesk ticket",
    "subject": "subject of zendesk ticket",
    "submitter_id": "submitter id in integer of the zendesk ticket",
    "tags": "list of tags of the zendesk ticket",
    "type": "type of zendesk ticket",
    "updated_at": "updated at datetime of zendesk ticket",
    "url": "url of the zendesk ticket",
    "follower_ids": "follower_ids of the zendesk ticket",
    "email_cc_ids": "email_cc_ids of the zendesk ticket",
    "is_public": "boolean field denoting in zendesk ticket is public or not",
    "custom_status_id": "custom status id of the zendesk ticket",
    "followup_ids": "list of followup_ids of the zendesk ticket",
    "allow_channelback": "boolean field denoting if channelback is allowed for zendesk ticket",
    "allow_attachments": "boolean field denoting if attachments is allowed for zendesk ticket",
    "from_messaging_channel": "boolean field denoting if zendesk ticket was from messaging channel",
    "via": "extra dict information for zendesk ticket",
}
document_content_description = "List of zendesk tickets for subdomain: supportive5741"

metadata_field_info = []

docs = []
with open("zendesk.json") as jsonfile:
    json_dict_list = json.load(jsonfile)

json_keys = list(json_dict_list[0].keys())

for json_dict_key, json_dict_value in json_dict_list[0].items():
    metadata_field_info.append(
        AttributeInfo(
            **{
                "name": json_dict_key,
                "description": metadata_description_dict[json_dict_key],
                "type": "integer" if isinstance(json_dict_value, int) else "string",
            }
        )
    )


for json_dict in json_dict_list:
    to_metadata = {}
    values_to_embed = {}
    for key, value in json_dict.items():
        if key not in exclude_metadata and value:
            to_metadata[key] = value
        if key in columns_to_embed:
            values_to_embed[key] = value
    to_embed = "\n".join(
        f"{k.strip()}: {v.strip() if isinstance(v, str) else v}"
        for k, v in values_to_embed.items()
    )
    newDoc = Document(page_content=to_embed, metadata=to_metadata)
    docs.append(newDoc)

splitter = CharacterTextSplitter(
    separator="\n", chunk_size=500, chunk_overlap=0, length_function=len
)
documents = splitter.split_documents(docs)
# db = Chroma.from_documents(documents, GPT4AllEmbeddings())
db = Chroma.from_documents(
    documents, HuggingFaceEmbeddings(model_name=embeddings_model_name)
)

template = """
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

query = "show me tickets with 2fa issues."


memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
llm = Ollama(
    model=model,
    # verbose=True,
    # callback_manager=CallbackManager([]),
)

print("="*50)
print("testing RetrievalQA")
prompt = PromptTemplate(input_variables=["context", "chat_history", "question"], template=template)

# qachain = RetrievalQA.from_chain_type(
#     llm,
#     retriever=db.as_retriever(),
#     # return_source_documents=True,
#     chain_type_kwargs={"prompt": PromptTemplate.from_template(template)}
# )
# chain_output = qachain({"query": query})
# print(chain_output["result"])

qachain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=db.as_retriever(),
    memory=memory,
    combine_docs_chain_kwargs={"prompt": prompt}
)
chain_output = qachain({"question": query})
print(chain_output["answer"])
print("follow up chain output:\n")
chain_output = qachain({"question": "How many tickets did you retrieve in the previous answer?"})
print(chain_output["answer"])
