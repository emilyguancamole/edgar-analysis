
class BaseLLMClient:
    def extract_data_llm(self, file_text) -> str:
        raise NotImplementedError

    def extract_and_validate(self, file_text, entry_model, max_retries=1) -> dict:
        pass

        
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