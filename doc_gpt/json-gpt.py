import time

from document_parser.json_coversational_retriver import get_conversational_retriever_chain


def run_query_prompt(query: str = "show me tickets with 2fa issues.") -> None:
    start_time = time.time()
    print(start_time)
    qa_chain = get_conversational_retriever_chain()
    chain_output = qa_chain({"question": query})
    print(chain_output["answer"])
    print("follow up chain output:\n")
    chain_output = qa_chain({"question": "How many tickets did you retrieve in the previous answer?"})
    print(chain_output["answer"])
    print("Total time taken: ", time.time() - start_time)


run_query_prompt()
