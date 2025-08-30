from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator
from datetime import datetime

''' Validation model for LLM-extracted data.'''

class FormGEntry(BaseModel):
    # accession_number: str # added manually
    report_date: str
    issuer: str
    name_person_filing: str
    class_: str  # 'class' is a reserved keyword
    cusip: str
    shares_owned: int
    percent_of_class: str
    voting_sole: str
    voting_shared: str
    shares_dispo_sole: str
    shares_dispo_shared: str

    @field_validator('report_date')
    @classmethod # methods that are bound to the class and not the instance of the class. They can access class variables and other class methods.
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%m/%d/%Y")
        except ValueError:
            raise ValueError("report_date must be in 'mm/dd/yyyy' format")
        return v