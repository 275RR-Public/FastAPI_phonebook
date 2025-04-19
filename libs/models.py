from libs.database import Base
from sqlalchemy import Column, Integer, String
import re
from pydantic import BaseModel, field_validator

# Database model
class PhoneBook(Base):
    __tablename__ = "phonebook"
    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    phone_number = Column(String)

# Pydantic model for User
class User(BaseModel):
    username: str
    role: str

# Pydantic model with centralized validation
class Person(BaseModel):
    full_name: str
    phone_number: str

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z.,\'\u2019 -]+$', v):
            raise ValueError('Invalid characters in name')
        if re.search(r"['’]{2}", v):
            raise ValueError('Consecutive apostrophes are not allowed')
        parts = v.split()
        if len(parts) > 3:
            raise ValueError('Name has too many parts')
        for part in parts:
            if part.count('-') > 1:
                raise ValueError('Name has too many hyphens')
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        if not re.match(r'^[+\d()-. ]+$', v):
            raise ValueError('Invalid characters in phone number')
        digits = re.sub(r'\D', '', v)
        if len(digits) < 5 or len(digits) > 15:
            raise ValueError('Phone number must have between 5 and 15 digits')
        extension_pattern = r'^\d{5}$'
        na_pattern = r'^(\+1|1)?\s*(\([2-9]\d{2}\)|[2-9]\d{2})[-.\s]\d{3}[-.\s]\d{4}$|^(\+1|1)?\s*\d{3}[-.\s]\d{4}$'
        intl_pattern = r'^\+[1-9]\d{0,2}(?![0-9])[ -.()]*\d+([ -.()]*\d+)*[ -.()]*$'
        idd_pattern = r'^011\d+$'
        danish_pattern = r'^(\d{2}[ -.]){3}\d{2}$|^\d{4}[ -.]\d{4}$'
        general_pattern = r'^\d+([ -.]\d+)+$'
        if (re.match(extension_pattern, v) or
            re.match(na_pattern, v) or
            re.match(intl_pattern, v) or
            re.match(idd_pattern, v) or
            re.match(danish_pattern, v) or
            re.match(general_pattern, v)):
            return v
        else:
            raise ValueError('Phone number does not match any acceptable format')