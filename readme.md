# ZENDESK GPT 

Resources: [Neum AI blogpost](https://www.neum.ai/post/llm-spreadsheets), 
[langchain](https://python.langchain.com/docs/get_started), [ollama](https://ollama.ai)

* Allows to ingest zendesk tickets and query them using local machine 
* Highly recommended to run this on a local environment
* Pre-requisites: [Ollama](https://ollama.ai/), `requirements.txt`
* Model used: Mistral
* Required env variables for running zendesk.py:
  * `ZENDESK_EMAIL`
  * `ZENDESK_API_KEY`
  * `ZENDESK_SUBDOMAIN`
  * `MONGO_URI`
* After setting them you can run `python zendesk.py`
  * This will download your zendesk tickets into a json file
* Then we can begin using our query:
  * Env vars needed for query:
    * `MODEL`
    * `EMBEDDINGS_MODEL_NAME`
  * After which we can run: `python demo.py`
  * It already has a pre-loaded query inside for testing and asserting for the time being 
  but that will all change


## [Update]
* Add [fastapi](https://fastapi.tiangolo.com/) to create apis to send queries to our gpt model
* Add google auth to authenticate and authorize users in session.
* Added mongodb persistent storage to store relevant information
* Running model queries in the background as threaded tasks to avoid holding up the main thread
for uvicorn