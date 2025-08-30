from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict

class LLMClient:
    def __init__(self, model_name):
        self.model_name = model_name
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )

    def build_prompt(file_text):
        # prepare the model input
        prompt_file = f"prompt.txt"
        folder = '.'
        with open(os.path.join(folder, prompt_file), "r") as f:
            system_prompt = f.read().strip()


        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": file_text}
        ]
        return messages