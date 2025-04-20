from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from libs.database import engine, Base, get_db
from libs.models import PhoneBook, Person, User
from libs.auth import pwd_context, users, create_access_token, require_roles, get_username_from_token
from libs.config import ACCESS_TOKEN_EXPIRE_MINUTES
from libs.logger import AuditLogger, get_audit_logger
from sqlalchemy.orm import Session
from datetime import timedelta

app = FastAPI()

# Create database schema
Base.metadata.create_all(bind=engine)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors for incoming requests.

    Parameters:
        - request: Request - The incoming HTTP request.
        - exc: RequestValidationError - The validation error raised.

    Returns:
        - JSONResponse with status code 400 and error details.
    """
    username = get_username_from_token(request)
    audit_logger = get_audit_logger()

    # Determine the action based on request method and path
    action = "unknown"
    log_message = "Failed: Validation error"
    if request.method == "POST" and request.url.path == "/PhoneBook/add":
        action = "add"
        log_message = "Failed to add: Validation error"
    elif request.method == "PUT" and request.url.path == "/PhoneBook/deleteByName":
        action = "deleteByName"
        log_message = "Failed to delete by name: Validation error"
    elif request.method == "PUT" and request.url.path == "/PhoneBook/deleteByNumber":
        action = "deleteByNumber"
        log_message = "Failed to delete by number: Validation error"

    # Extract validation error details
    errors = exc.errors()
    error_messages = [f"{error['loc'][0]}: {error['msg']}" for error in errors]
    detail = ", ".join(error_messages)

    # Log the failed attempt and return JSON
    audit_logger.log(username, action, log_message)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": error_messages})

# API Endpoints (token, list, add, deleteByName, deleteByNumber)
# Uses parameterized queries, auth, and logging
@app.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Authenticate a user and issue an access token.

    Parameters:
        - form_data: OAuth2PasswordRequestForm - Form containing username and password.
        - audit_logger: AuditLogger - Logger for auditing login attempts.

    Returns:
        - Dictionary containing access_token and token_type on success.
        - Raises HTTPException with status 400 on invalid credentials.
    """
    try:
        user = users.get(form_data.username)
        if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"]},
            expires_delta=access_token_expires
        )
        audit_logger.log(form_data.username, "token", f"Status: {status.HTTP_200_OK}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        audit_logger.log(form_data.username, "token", f"Status: {e.status_code}")
        raise

@app.get("/PhoneBook/list")
def list_phonebook(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Read", "ReadWrite"])),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    List all entries in the phonebook.

    Parameters:
        - db: Session - Database session for querying.
        - current_user: User - Authenticated user with required roles.
        - audit_logger: AuditLogger - Logger for auditing the operation.

    Returns:
        - List of person objects with full_name and phone_number.
        - Raises HTTPException with status 500 on server error.
    """
    try:
        phonebook = db.query(PhoneBook).all()
        audit_logger.log(current_user.username, "list", f"Status: {status.HTTP_200_OK}")
        return phonebook
    except HTTPException as e:
        audit_logger.log(current_user.username, "list", f"Status: {e.status_code}")
        raise

@app.post("/PhoneBook/add")
def add_person(
    person: Person,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ReadWrite"])),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Add a new entry to the phonebook.

    Parameters:
        - person: Person - Object containing full_name and phone_number.
        - db: Session - Database session for adding the entry.
        - current_user: User - Authenticated user with ReadWrite role.
        - audit_logger: AuditLogger - Logger for auditing the operation.

    Returns:
        - Dictionary with success message on successful addition.
        - Raises HTTPException with status 500 on server error.
    """
    try:
        existing_by_name = db.query(PhoneBook).filter_by(full_name=person.full_name).first()
        existing_by_number = db.query(PhoneBook).filter_by(phone_number=person.phone_number).first()
        if existing_by_name or existing_by_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Person already exists in the database")
        new_person = PhoneBook(full_name=person.full_name, phone_number=person.phone_number)
        db.add(new_person)
        db.commit()
        audit_logger.log(current_user.username, "add", f"Added: {person.full_name}")
        return {"message": "Person added successfully"}
    except HTTPException as e:
        audit_logger.log(current_user.username, "add", f"Failed to add: {e.detail}")
        raise

@app.put("/PhoneBook/deleteByName")
def delete_by_name(
    full_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ReadWrite"])),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Delete a phonebook entry by full name.

    Parameters:
        - full_name: str - Full name of the person to delete.
        - db: Session - Database session for deletion.
        - current_user: User - Authenticated user with ReadWrite role.
        - audit_logger: AuditLogger - Logger for auditing the operation.

    Returns:
        - Dictionary with success message on successful deletion.
        - Raises HTTPException with status 404 if not found, 500 on server error.
    """
    try:
        Person.validate_full_name(full_name)
        person = db.query(PhoneBook).filter_by(full_name=full_name).first()
        if not person:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found in the database")
        db.delete(person)
        db.commit()
        audit_logger.log(current_user.username, "deleteByName", f"Deleted by name: {full_name}")
        return {"message": "Person deleted successfully"}
    except (ValueError, HTTPException) as e:
        status_code = e.status_code if isinstance(e, HTTPException) else status.HTTP_400_BAD_REQUEST
        detail = e.detail if isinstance(e, HTTPException) else str(e)
        audit_logger.log(current_user.username, "deleteByName", f"Failed to delete by name: {detail}")
        raise HTTPException(status_code=status_code, detail=detail)

@app.put("/PhoneBook/deleteByNumber")
def delete_by_number(
    phone_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ReadWrite"])),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Delete a phonebook entry by phone number.

    Parameters:
        - phone_number: str - Phone number of the person to delete.
        - db: Session - Database session for deletion.
        - current_user: User - Authenticated user with ReadWrite role.
        - audit_logger: AuditLogger - Logger for auditing the operation.

    Returns:
        - Dictionary with success message on successful deletion.
        - Raises HTTPException with status 404 if not found, 500 on server error.
    """
    try:
        Person.validate_phone_number(phone_number)
        person = db.query(PhoneBook).filter_by(phone_number=phone_number).first()
        if not person:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found in the database")
        db.delete(person)
        db.commit()
        audit_logger.log(current_user.username, "deleteByNumber", f"Deleted by number: {person.full_name}")
        return {"message": "Person deleted successfully"}
    except (ValueError, HTTPException) as e:
        status_code = e.status_code if isinstance(e, HTTPException) else status.HTTP_400_BAD_REQUEST
        detail = e.detail if isinstance(e, HTTPException) else str(e)
        audit_logger.log(current_user.username, "deleteByNumber", f"Failed to delete by number: {detail}")
        raise HTTPException(status_code=status_code, detail=detail)