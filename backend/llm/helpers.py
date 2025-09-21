from llm.hf_llm_client import HfLLMClient
from llm.openai_llm_client import OpenAILLMClient


def get_llm_client(config, debug):
        if config['provider'] == 'huggingface':
            return HfLLMClient(config['model_name'], debug=debug)
        elif config['provider'] == 'openai':
            return OpenAILLMClient(config['api_key'], config['model_name'], debug=debug)
        else:
            raise ValueError("Unknown LLM provider")