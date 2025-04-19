from fastapi import FastAPI, HTTPException, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from libs.database import engine, Base, get_db
from libs.models import PhoneBook, Person, User
from libs.auth import pwd_context, users, create_access_token, require_roles
from libs.config import ACCESS_TOKEN_EXPIRE_MINUTES
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta


app = FastAPI()

# Create database schema
Base.metadata.create_all(bind=engine)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    error_messages = [f"{error['loc'][0]}: {error['msg']}" for error in errors]
    return JSONResponse(status_code=400, content={"detail": error_messages})


# API Endpoints (token, list, add, deleteByName, deleteByNumber)
# Uses parameterized queries
# Uses authentication and authorization
@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint to obtain token"""
    user = users.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/PhoneBook/list")
def list_phonebook(db: Session = Depends(get_db), current_user: User = Depends(require_roles(["Read", "ReadWrite"]))):
    """List all phonebook entries."""
    phonebook = db.query(PhoneBook).all()
    return phonebook

@app.post("/PhoneBook/add")
def add_person(person: Person, db: Session = Depends(get_db), current_user: User = Depends(require_roles(["ReadWrite"]))):
    """
    Add a person with validated name and number.
        - Validate input as a name and a number by Person class
        - Check that person does not already exist in db by name or number
        - Add person
    """
    existing_by_name = db.query(PhoneBook).filter_by(full_name=person.full_name).first()
    existing_by_number = db.query(PhoneBook).filter_by(phone_number=person.phone_number).first()
    if existing_by_name or existing_by_number:
        raise HTTPException(status_code=400, detail="Person already exists in the database")
    new_person = PhoneBook(full_name=person.full_name, phone_number=person.phone_number)
    db.add(new_person)
    db.commit()
    return {"message": "Person added successfully"}

@app.put("/PhoneBook/deleteByName")
def delete_by_name(full_name: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles(["ReadWrite"]))):
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
    person = db.query(PhoneBook).filter_by(full_name=full_name).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found in the database")
    db.delete(person)
    db.commit()
    return {"message": "Person deleted successfully"}

@app.put("/PhoneBook/deleteByNumber")
def delete_by_number(phone_number: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles(["ReadWrite"]))):
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
    person = db.query(PhoneBook).filter_by(phone_number=phone_number).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found in the database")
    db.delete(person)
    db.commit()
    return {"message": "Person deleted successfully"}