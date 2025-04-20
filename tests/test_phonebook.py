import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from libs.database import Base, get_db
from libs.models import PhoneBook
from app import app
import csv, os, logging


TEST_DATABASE_URL = "sqlite:///test_phonebook.db"

# Create the engine for the disk-based test database
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
# Create a session factory for interacting with the database
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Create the database schema once at the start of the test run
Base.metadata.create_all(bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply the dependency override to the FastAPI app
app.dependency_overrides[get_db] = override_get_db

# Fixture to clear the database before each test
@pytest.fixture(scope="function", autouse=True)
def clear_database():
    session = TestingSessionLocal()
    session.query(PhoneBook).delete()  # Clear all records
    session.commit()
    session.close()

# Fixture to clear the logs before each test
@pytest.fixture
def clear_log_file():
    audit_logger = logging.getLogger("audit")
    # Close and remove all handlers to release the file lock
    # Use a copy to avoid modifying list during iteration
    for handler in audit_logger.handlers[:]:
        handler.close()
        audit_logger.removeHandler(handler)
    # Now safe to delete the file
    if os.path.exists('audit.log'):
        os.remove('audit.log')


# Test client fixture
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# Token fixtures
@pytest.fixture(scope="module")
def read_user_token(client):
    response = client.post("/token", data={"username": "readuser", "password": "readpassword"})
    return response.json()["access_token"]

@pytest.fixture(scope="module")
def readwrite_user_token(client):
    response = client.post("/token", data={"username": "rwuser", "password": "rwpassword"})
    return response.json()["access_token"]


# Check logs for expected message
def check_audit_log(expected_message):
    with open('audit.log', 'r') as f:
        logs = f.read()
        return expected_message in logs

# Load test cases from CSV files
def load_add_test_cases():
    with open('tests/add_tests.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [(row['full_name'], row['phone_number'], int(row['expected_status'])) for row in reader]

def load_delete_by_name_test_cases():
    with open('tests/delete_by_name_tests.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [(row['full_name'], row['add_before'] == 'true', int(row['expected_status'])) for row in reader]

def load_delete_by_number_test_cases():
    with open('tests/delete_by_number_tests.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [(row['phone_number'], row['add_before'] == 'true', int(row['expected_status'])) for row in reader]


# Authentication and Authorization Tests
def test_access_without_token(client):
    endpoints = [
        (client.get, "/PhoneBook/list", {}),
        (client.post, "/PhoneBook/add", {"json": {"full_name": "Test", "phone_number": "12345"}}),
        (client.put, "/PhoneBook/deleteByName", {"params": {"full_name": "Test"}}),
        (client.put, "/PhoneBook/deleteByNumber", {"params": {"phone_number": "12345"}}),
    ]
    for method, url, kwargs in endpoints:
        response = method(url, **kwargs)
        assert response.status_code == 401, f"Expected 401 for {url}, got {response.status_code}"

def test_access_with_invalid_token(client):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/PhoneBook/list", headers=headers)
    assert response.status_code == 401

def test_list_with_read_user(client, read_user_token):
    headers = {"Authorization": f"Bearer {read_user_token}"}
    response = client.get("/PhoneBook/list", headers=headers)
    assert response.status_code == 200

def test_add_with_read_user(client, read_user_token):
    headers = {"Authorization": f"Bearer {read_user_token}"}
    response = client.post("/PhoneBook/add", json={"full_name": "Test", "phone_number": "12345"}, headers=headers)
    assert response.status_code == 403

def test_all_endpoints_with_readwrite_user(client, readwrite_user_token):
    headers = {"Authorization": f"Bearer {readwrite_user_token}"}
    # Test list endpoint
    response = client.get("/PhoneBook/list", headers=headers)
    assert response.status_code == 200
    # Test add endpoint
    response = client.post("/PhoneBook/add", json={"full_name": "Bruce Schneier", "phone_number": "+1(703) 111-2121"}, headers=headers)
    assert response.status_code == 200
    # Test delete by name endpoint
    response = client.put("/PhoneBook/deleteByName", params={"full_name": "Bruce Schneier"}, headers=headers)
    assert response.status_code == 200

def test_list_with_read_user(client, read_user_token, clear_log_file):
    headers = {"Authorization": f"Bearer {read_user_token}"}
    response = client.get("/PhoneBook/list", headers=headers)
    assert response.status_code == 200
    expected_log = "User: readuser - Action: list - Status: 200"
    assert check_audit_log(expected_log), "Audit log missing for list operation"


# Parameterized Tests Using CSV Data
@pytest.mark.parametrize("full_name, phone_number, expected_status", load_add_test_cases())
def test_add_person(client, readwrite_user_token, full_name, phone_number, expected_status, clear_log_file):
    headers = {"Authorization": f"Bearer {readwrite_user_token}"}
    response = client.post("/PhoneBook/add", json={"full_name": full_name, "phone_number": phone_number}, headers=headers)
    assert response.status_code == expected_status
    if expected_status == 200:
        expected_log = f"User: rwuser - Action: add - Added: {full_name}"
        assert check_audit_log(expected_log), f"Audit log missing for add: {full_name}"
    else:
        expected_log = "User: rwuser - Action: add - Failed to add:"
        assert check_audit_log(expected_log), f"Audit log missing for failed add: {full_name}"

@pytest.mark.parametrize("full_name, add_before, expected_status", load_delete_by_name_test_cases())
def test_delete_by_name(client, readwrite_user_token, full_name, add_before, expected_status, clear_log_file):
    headers = {"Authorization": f"Bearer {readwrite_user_token}"}
    if add_before:
        client.post("/PhoneBook/add", json={"full_name": full_name, "phone_number": "12345"}, headers=headers)
    response = client.put("/PhoneBook/deleteByName", params={"full_name": full_name}, headers=headers)
    assert response.status_code == expected_status
    if expected_status == 200:
        expected_log = f"User: rwuser - Action: deleteByName - Deleted by name: {full_name}"
        assert check_audit_log(expected_log), f"Audit log missing for deleteByName: {full_name}"
    else:
        expected_log = "User: rwuser - Action: deleteByName - Failed to delete by name:"
        assert check_audit_log(expected_log), f"Audit log missing for failed deleteByName: {full_name}"

@pytest.mark.parametrize("phone_number, add_before, expected_status", load_delete_by_number_test_cases())
def test_delete_by_number(client, readwrite_user_token, phone_number, add_before, expected_status, clear_log_file):
    headers = {"Authorization": f"Bearer {readwrite_user_token}"}
    if add_before:
        client.post("/PhoneBook/add", json={"full_name": "Test Person", "phone_number": phone_number}, headers=headers)
    response = client.put("/PhoneBook/deleteByNumber", params={"phone_number": phone_number}, headers=headers)
    assert response.status_code == expected_status
    if expected_status == 200:
        expected_log = "User: rwuser - Action: deleteByNumber - Deleted by number: Test Person"
        assert check_audit_log(expected_log), f"Audit log missing for deleteByNumber: {phone_number}"
    else:
        expected_log = "User: rwuser - Action: deleteByNumber - Failed to delete by number:"
        assert check_audit_log(expected_log), f"Audit log missing for failed deleteByNumber: {phone_number}"