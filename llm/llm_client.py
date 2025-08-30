from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict, Optional, Type
import os
import json
import time
from pydantic import ValidationError
from models import FormGEntry

class LLMClient:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )

    def build_messages(self, filing_text):
        # prepare the model input
        system_prompt_file = f"llm/prompt.txt"
        folder = '.'
        with open(os.path.join(folder, system_prompt_file), "r") as f:
            system_prompt = f.read().strip()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": filing_text}
        ]
        return messages
    
    def extract_data_llm(self, file_text) -> str:
        messages = self.build_messages(file_text)
        print("MESSAGES", messages)
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        print("\nGenerating...\n")
        # conduct text completion
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=32768 # recommended output len for most queries
        )
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

        # parsing thinking content
        try:
            # rindex finding 151668 (</think>)
            index = len(output_ids) - output_ids[::-1].index(151668)
        except ValueError:
            index = 0

        thinking_content = self.tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
        llm_response = self.tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

        # print("thinking content:", thinking_content) #! debug
        print("content:", llm_response)
        return llm_response

    def extract_and_validate(self, file_text, entry_model: FormGEntry, max_retries = 1) -> dict:
        """Call the LLM to extract JSON from the given file_text, parse it, and validate with the given pydantic model.

        max_retries: # retries on decode or validation errors.

        Returns
        """
        attempt = 0
        last_exception = None # store the last exception if all retries fail
        while attempt <= max_retries:
            attempt += 1
            try:
                data = self.extract_data_llm(file_text) # get extraction for one file
                print("LLM raw output:", data)
                print()
                data_json = json.loads(data)
                # If model returned a JSON string (double-encoded), try decode again
                if isinstance(data_json, str):
                    try:
                        data_json = json.loads(data_json)
                    except json.JSONDecodeError:
                        pass # leave as string, handled below
                print("Parsed JSON:", data_json)
                
                try:
                    data_json = self._coerce_types(data_json) # coerce types for some number-looking fields
                except ValueError as e: # treat as validation errors for max_retries
                    raise ValueError(f"type coercion error: {e}")
                
                validated = entry_model(**data_json) # validate filing data with pydantic mode. returns a model instance
                print()
                print("Validated entries:", validated)
                return validated.dict()

            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                print(f"LLM extraction/validation error (attempt {attempt}/{max_retries+1}): {e}")
                last_exception = e
                if attempt <= max_retries:
                    # todo could pass a clarification prompt to the LLM. or have it fix itself
                    time.sleep(0.5)
                    continue
                else:
                    break

        # If reach here, raise last exception for the caller to handle
        raise last_exception


    ### Helper functions for parsing/cleaning values ###
    def _parse_int(self, value):
        if value is None:
            return None
        if isinstance(value, int):
            return value
        s = str(value).strip()
        if s == "":
            return None
        s = s.replace(",", "")
        try:
            # force floats to int
            return int(float(s))
        except Exception as e:
            raise ValueError(f"cannot parse int from {value}: {e}")
        
    def _parse_percent(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        if s == "":
            return None
        s = s.replace(",", "")
        # if contains percent sign, remove it
        if s.endswith("%"):
            s = s[:-1].strip()
        try:
            return float(s)
        except Exception as e:
            raise ValueError(f"cannot parse percent from {value}: {e}")

    def _coerce_types(self, data: dict) -> dict:
        out = dict(data) # shallow copy to avoid mutating input
        for k in ("shares_owned", "shares_dispo_sole", "shares_dispo_shared"): # fields to coerce to int
            if k in out:
                out[k] = self._parse_int(out[k])
        if "percent_of_class" in out:
            out["percent_of_class"] = self._parse_percent(out["percent_of_class"])
        return out
