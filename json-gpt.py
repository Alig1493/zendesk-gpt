import json
import os
import pprint

from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain.chains import RetrievalQA
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.llms import Ollama
from langchain.retrievers.self_query.base import SelfQueryRetriever

from langchain.docstore.document import Document
from langchain.retrievers.self_query.chroma import ChromaTranslator
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings, GPT4AllEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
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
    "is_public"
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
    "via": "extra dict information for zendesk ticket"
}
document_content_description = "List of zendesk tickets for subdomain: supportive5741"

metadata_field_info = []

# Process the CSV into the embedable content vs the metadata and put it into Document format so that we can chunk it into pieces.
docs = []
with open("zendesk.json") as jsonfile:
    json_dict_list = json.load(jsonfile)

json_keys = list(json_dict_list[0].keys())

for json_dict_key, json_dict_value in json_dict_list[0].items():
    metadata_field_info.append(
        AttributeInfo(**{
            "name": json_dict_key,
            "description": metadata_description_dict[json_dict_key],
            "type": "integer" if isinstance(json_dict_value, int) else "string"
        })
    )


for json_dict in json_dict_list:
    to_metadata = {}
    values_to_embed = {}
    for key, value in json_dict.items():
        if key not in exclude_metadata and value:
            to_metadata[key] = value
        if key in columns_to_embed:
            values_to_embed[key] = value
    to_embed = "\n".join(f"{k.strip()}: {v.strip() if isinstance(v, str) else v}" for k, v in values_to_embed.items())
    newDoc = Document(page_content=to_embed, metadata=to_metadata)
    docs.append(newDoc)

splitter = CharacterTextSplitter(
    separator="\n", chunk_size=500, chunk_overlap=0, length_function=len
)
documents = splitter.split_documents(docs)
# db = Chroma.from_documents(documents, GPT4AllEmbeddings())
db = Chroma.from_documents(documents, HuggingFaceEmbeddings(model_name=embeddings_model_name))
query = "show me tickets with 2fa issues. also include ticket urls in the response for each ticket."
docs = db.similarity_search(query)
# print(docs[0].page_content)
# print(docs[0].metadata)

pprint.pprint(docs[0])
print("="*50)

llm = Ollama(
    model=model,
    verbose=True,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
)
print(f"Ollama test using model {model}:")
print(llm("Why is the sky blue? Answer in one short sentence."))

# print("="*50)
# print("testing SelfQueryRetriever")
# retriever = SelfQueryRetriever.from_llm(
#     llm,
#     db,
#     document_content_description,
#     metadata_field_info,
#     verbose=True
# )
# retriever.get_relevant_documents(query)
print("="*50)
print("testing RetrievalQA")

qachain = RetrievalQA.from_chain_type(llm, retriever=db.as_retriever())
print(qachain({"query": query}))
