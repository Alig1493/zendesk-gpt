import json
import os
from typing import Dict, List, Any

from langchain import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma

from .config import get_env
from .utils import EXCLUDE_METADATA_FIELDS, COLUMNS_TO_EMBED, TEMPLATE


def get_json_dict_list(filename: str) -> List[Dict[str, Any]]:
    with open(filename) as jsonfile:
        return json.load(jsonfile)


def get_db(documents: List[Document]):
    # return Chroma.from_documents(documents, GPT4AllEmbeddings())
    file_path = "./chroma_db"
    embedding_function = HuggingFaceEmbeddings(
        model_name=get_env("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
    )
    print(os.path.exists(file_path))
    if os.path.exists(file_path):
        return Chroma(persist_directory=file_path, embedding_function=embedding_function)
    return Chroma.from_documents(
        documents,
        embedding_function,
        persist_directory=file_path
    )


def get_documents_from_json(filename: str = None) -> List[Document]:
    docs = []
    for json_dict in get_json_dict_list(filename):
        to_metadata = {}
        values_to_embed = {}
        for key, value in json_dict.items():
            if key not in EXCLUDE_METADATA_FIELDS and value:
                to_metadata[key] = value
            if key in COLUMNS_TO_EMBED:
                values_to_embed[key] = value
        to_embed = "\n".join(
            f"{k.strip()}: {v.strip() if isinstance(v, str) else v}"
            for k, v in values_to_embed.items()
        )
        docs.append(Document(page_content=to_embed, metadata=to_metadata))
    return docs


def load_json_dict_list_to_db(filename: str = None) -> Chroma:
    splitter = CharacterTextSplitter(
        separator="\n", chunk_size=200, chunk_overlap=0, length_function=len
    )
    documents = splitter.split_documents(
        get_documents_from_json(filename)
    )
    return get_db(documents)


def get_conversational_retriever_chain():
    source_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'source_files/zendesk.json'))
    print(source_file_path)
    db = load_json_dict_list_to_db(source_file_path)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    llm = Ollama(
        model=get_env("MODEL", "mistral"),
        # verbose=True,
        # callback_manager=CallbackManager([]),
    )
    print("=" * 50)
    print("testing RetrievalQA")
    prompt = PromptTemplate(
        input_variables=["context", "chat_history", "question"],
        template=TEMPLATE
    )
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=db.as_retriever(),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt}
    )
