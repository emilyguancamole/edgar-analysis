from time import time
from openai import AzureOpenAI
import logging
import traceback
# from pydantic import BaseModel
from llm.base_llm_client import BaseLLMClient
from llm.hf_llm_client import HfLLMClient
from models import FormGEntry
# from jsonschema import ValidationError
from pydantic import ValidationError

class OpenAILLMClient(BaseLLMClient):
    def __init__(self, api_key, model_name, debug=False, debug_log_path="llm_debug.log"):
        self.model_name = model_name
        self.client = AzureOpenAI(
            azure_endpoint="https://gpt4-endoscribe.openai.azure.com/",
            api_version="2025-03-01-preview",
            api_key=api_key # api key from config file
        )
        self.debug = debug
        self.debug_log_path = debug_log_path
        if self.debug:
            logging.basicConfig(filename=self.debug_log_path, level=logging.DEBUG)

    #! for now, using same as hf_llm_client
    def build_messages(self, filing_text, system_prompt_file="llm/prompt.txt"):
        return HfLLMClient.build_messages(self, filing_text, system_prompt_file)
    
    
    def extract_and_validate(self, file_text, entry_model, max_tries=1) -> dict:
        """Extracts data from the given file text using the LLM. Uses Strcutred Output to validate it against the provided Pydantic model."""
        messages = self.build_messages(file_text)
        attempt = 0
        last_exception = None # store the last exception if all retries fail
        while attempt <= max_tries:
            attempt += 1
        # using structured outputs to ensure json #todo this is from openai api, make sure correct
            try:
                response = self.client.responses.parse(
                    model = self.model_name,
                    input = messages,
                    text_format = FormGEntry
                )
                llm_response = response.output_parsed.dict()
                print("Openai LLM Response:", llm_response)
                return llm_response

            except (ValidationError, ValueError) as e:
                logging.error(f"Error during LLM extraction: {e}")
                traceback.print_exc() # print traceback
                if attempt <= max_tries:
                    print("Retrying extraction due to validation error...")
                    time.sleep(1)  # brief pause before retrying
                    return self.extract_and_validate(file_text, entry_model, max_tries=1)
                else:
                    last_exception = e
                    raise e