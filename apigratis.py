import json
from llamaapi import LlamaAPI

# Initialize the LlamaAPI with your API token
api_token = "LL-Z8mrEuQPmlMauJWuXwIDlnoi9bFiSlFqiYQSx8E3lEfEleU7Zt5YB3qGUgeKOf2e"  # Replace <your_api_token> with your actual API token
llama = LlamaAPI(api_token)

texto = "Please summarize the following text: \n\nWashington, officially the State of Washington,[3] is a state in the Pacific Northwest region of the United States. It is often referred to as Washington state [a] to distinguish it from the national capital,[4] both named for George Washington (the first U.S. president). Washington borders the Pacific Ocean to the west, Oregon to the south, Idaho to the east, and the Canadian province of British Columbia to the north. The state was formed from the western part of the Washington Territory, which was ceded by the British Empire in the Oregon Treaty of 1846. It was admitted to the Union as the 42nd state in 1889. Olympia is the state capital, and the most populous city is Seattle."

api_request_json = {
  "model": "llama3-70b",
  "messages": [
    {"role": "system", "content": "You are a llama assistant that summarizes texts."},
    {"role": "user", "content": texto},
  ]
}

# Make your request and handle the response
response = llama.run(api_request_json)
print(json.dumps(response.json()['choices'][0]['message']['content']))