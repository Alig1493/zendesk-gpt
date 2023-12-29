# ZENDESK GPT 

* Allows to ingest zendesk tickets and query them using local machine 
* Highly recommended to run this on a local environment
* Pre-requisites: [Ollama](https://ollama.ai/), `requirements.txt`
* Model used: Mistral
* Required env variables for running zendesk.py:
  * `ZENDESK_EMAIL`
  * `ZENDESK_API_KEY`
  * `ZENDESK_SUBDOMAIN`
* After setting them you can run `python zendesk.py`
  * This will download your zendesk tickets into a json file
* Then we can begin using our query:
  * Env vars needed for query:
    * `MODEL`
    * `EMBEDDINGS_MODEL_NAME`
  * After which we can run: `python json-gpt.py`
  * It already has a pre-loaded query inside for testing and asserting for the time being 
  but that will all change