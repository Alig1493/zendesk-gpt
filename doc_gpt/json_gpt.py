import time

from .document_parser.json_coversational_retriver import get_conversational_retriever_chain


async def run_query_prompt(query: str = "show me tickets with 2fa issues.") -> str:
    start_time = time.time()
    print(start_time)
    qa_chain = get_conversational_retriever_chain()
    chain_output = qa_chain({"question": query})
    result = chain_output["answer"]
    print(result)
    print("Total time taken: ", time.time() - start_time)
    return result
