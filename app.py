
import re
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# Note: Bad Request = 400 and Not Found = 404
# Create the FastAPI app
app = FastAPI()

# SQLite database setup
engine = create_engine("sqlite:///phonebook.db", echo=False)
Base = declarative_base()

# Database model
class PhoneBook(Base):
    __tablename__ = "phonebook"
    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    phone_number = Column(String)

# Create database schema
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

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

# Custom exception handler for validation errors (returns 400)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    error_messages = [f"{error['loc'][0]}: {error['msg']}" for error in errors]
    return JSONResponse(status_code=400, content={"detail": error_messages})

# API Endpoints (list, add, delete by name, delete by number)
# Uses parameterized queries
@app.get("/PhoneBook/list")
def list_phonebook():
    """List all phonebook entries."""
    session = Session()
    phonebook = session.query(PhoneBook).all()
    session.close()
    return phonebook

@app.post("/PhoneBook/add")
def add_person(person: Person):
    """
    Add a person with validated name and number.
        - Validate input as a name and a number by Person class
        - Check that person does not already exist in db by name or number
        - Add person
    """
    session = Session()
    existing_by_name = session.query(PhoneBook).filter_by(full_name=person.full_name).first()
    existing_by_number = session.query(PhoneBook).filter_by(phone_number=person.phone_number).first()
    if existing_by_name or existing_by_number:
        session.close()
        raise HTTPException(status_code=400, detail="Person already exists in the database")
    new_person = PhoneBook(full_name=person.full_name, phone_number=person.phone_number)
    session.add(new_person)
    session.commit()
    session.close()
    return {"message": "Person added successfully"}

@app.put("/PhoneBook/deleteByName")
def delete_by_name(full_name: str):
    """
    Delete a person by name with validation.
        - Validate input as a name
        - Check that person exists in db by name
        - Delete person
    """
    try:
        Person.validate_full_name(full_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    session = Session()
    person = session.query(PhoneBook).filter_by(full_name=full_name).first()
    if not person:
        session.close()
        raise HTTPException(status_code=404, detail="Person not found in the database")
    session.delete(person)
    session.commit()
    session.close()
    return {"message": "Person deleted successfully"}

@app.put("/PhoneBook/deleteByNumber")
def delete_by_number(phone_number: str):
    """
    Delete a person by phone number with validation.
        - Validate input as a phone number
        - Check that person exists in db by number
        - Delete person
    """
    try:
        Person.validate_phone_number(phone_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    session = Session()
    person = session.query(PhoneBook).filter_by(phone_number=phone_number).first()
    if not person:
        session.close()
        raise HTTPException(status_code=404, detail="Person not found in the database")
    session.delete(person)
    session.commit()
    session.close()
    return {"message": "Person deleted successfully"}