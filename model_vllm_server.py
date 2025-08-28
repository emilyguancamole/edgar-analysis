import requests
import json


def query_vllm(prompt: str):
    url = "http://localhost:8000/v1/completions"
    headers = {
        "Content-Type": "application/json" # need for JSON requests
        # "Authorization":
    }  
    data = { # request body -- data object formatted for completions
        "model": "Qwen/Qwen3-14B",
        "prompt": prompt,
        "temperature": 0.7,
        "max_tokens": 32768,
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"

'''
Available routes are:
INFO 08-27 19:10:17 [launcher.py:36] Route: /openapi.json, Methods: HEAD, GET
INFO 08-27 19:10:17 [launcher.py:36] Route: /docs, Methods: HEAD, GET
INFO 08-27 19:10:17 [launcher.py:36] Route: /docs/oauth2-redirect, Methods: HEAD, GET
INFO 08-27 19:10:17 [launcher.py:36] Route: /redoc, Methods: HEAD, GET
INFO 08-27 19:10:17 [launcher.py:36] Route: /health, Methods: GET
INFO 08-27 19:10:17 [launcher.py:36] Route: /load, Methods: GET
INFO 08-27 19:10:17 [launcher.py:36] Route: /ping, Methods: GET, POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /tokenize, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /detokenize, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /v1/models, Methods: GET
INFO 08-27 19:10:17 [launcher.py:36] Route: /version, Methods: GET
INFO 08-27 19:10:17 [launcher.py:36] Route: /v1/chat/completions, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /v1/completions, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /v1/embeddings, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /pooling, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /score, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /v1/score, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /v1/audio/transcriptions, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /rerank, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /v1/rerank, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /v2/rerank, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /invocations, Methods: POST
INFO 08-27 19:10:17 [launcher.py:36] Route: /metrics, Methods: GET
'''

if __name__ == "__main__":
    prompt = "Give me a short introduction to large language model."
    response = query_vllm(prompt)
    print("Response from vLLM server:", response)