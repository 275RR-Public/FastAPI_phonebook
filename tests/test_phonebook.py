import pytest
from fastapi.testclient import TestClient
from app import app, Session, PhoneBook
import csv

# Fixture to provide a clean test client and reset the database before each test
@pytest.fixture(scope='function')
def client():
    client = TestClient(app)
    session = Session()
    session.query(PhoneBook).delete()  # Clear the database
    session.commit()
    session.close()
    yield client

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

# Test the List endpoint
def test_list_phonebook_empty(client):
    response = client.get("/PhoneBook/list")
    assert response.status_code == 200
    assert response.json() == []  # Empty list when database is empty

def test_list_phonebook_after_add(client):
    client.post("/PhoneBook/add", json={"full_name": "Bruce Schneier", "phone_number": "+1(703) 111-2121"})
    response = client.get("/PhoneBook/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['full_name'] == "Bruce Schneier"
    assert data[0]['phone_number'] == "+1(703) 111-2121"

# Test the Add endpoint with CSV parameters
@pytest.mark.parametrize("full_name, phone_number, expected_status", load_add_test_cases())
def test_add_person(client, full_name, phone_number, expected_status):
    response = client.post("/PhoneBook/add", json={"full_name": full_name, "phone_number": phone_number})
    assert response.status_code == expected_status

# Test the Delete by Name endpoint with CSV parameters
@pytest.mark.parametrize("full_name, add_before, expected_status", load_delete_by_name_test_cases())
def test_delete_by_name(client, full_name, add_before, expected_status):
    if add_before:
        client.post("/PhoneBook/add", json={"full_name": full_name, "phone_number": "12345"})
    response = client.put("/PhoneBook/deleteByName", params={"full_name": full_name})
    assert response.status_code == expected_status

# Test the Delete by Number endpoint with CSV parameters
@pytest.mark.parametrize("phone_number, add_before, expected_status", load_delete_by_number_test_cases())
def test_delete_by_number(client, phone_number, add_before, expected_status):
    if add_before:
        client.post("/PhoneBook/add", json={"full_name": "Test Person", "phone_number": phone_number})
    response = client.put("/PhoneBook/deleteByNumber", params={"phone_number": phone_number})
    assert response.status_code == expected_status