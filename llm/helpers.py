from llm.hf_llm_client import HfLLMClient
from llm.openai_llm_client import OpenAILLMClient


def get_llm_client(config):
        if config['provider'] == 'huggingface':
            return HfLLMClient(config['model_name'], debug=config.get('debug', False))
        elif config['provider'] == 'openai':
            return OpenAILLMClient(config['api_key'], config['model_name'], debug=config.get('debug', False))
        else:
            raise ValueError("Unknown LLM provider")