# doc

## Changes

- updated dockerfile
  - "FROM python:3.10-slim" to "FROM python:3.13-slim"
  - added "RUN python -m pip install --upgrade pip"
- updated requirements.txt
  - removed versioning to allow latest

---

## References

1) https://fastapi.tiangolo.com/
2) https://github.com/sumanentc/python-sample-FastAPI-application
3) https://dassum.medium.com/building-rest-apis-using-fastapi-sqlalchemy-uvicorn-8a163ccf3aa1
4) https://regex101.com/
5) https://medium.com/@ramanbazhanau/mastering-sqlalchemy-a-comprehensive-guide-for-python-developers-ddb3d9f2e829
6) https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
7) https://www.propelauth.com/post/a-practical-guide-to-dependency-injection-with-fastapis-depends

## Usage
Testing:
  - pytest tests/test_phonebook.py
Verbose Testing:
  - pytest tests/test_phonebook.py -v


Docker
1. Navigate to the root directory of the project:
```bash
cd /FastAPI_phonebook-main
```
2. (OPTIONAL) Create your own SECRET_KEY or use the provided key:
```bash
openssl rand -hex 32
```
3. Create the .env file:
```bash
SECRET_KEY=f85b6d28654557d2879c593439ae824224158219d9984785d6072ae594487677
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///phonebook.db
```
4. Build the Docker image:
```bash
docker build -t phonebook .
```
5. Run the container:
```bash
docker run -p 8000:8000 --env-file .env phonebook
```
6. Navigate your browser to http://127.0.0.1:8000/docs
7. Simulated Users have been created with Roles:
```bash
# Hardcoded users
users = {
    "readuser": {
        "username": "readuser",
        "hashed_password": pwd_context.hash("readpassword"),
        "role": "Read"
    },
    "rwuser": {
        "username": "rwuser",
        "hashed_password": pwd_context.hash("rwpassword"),
        "role": "ReadWrite"
    }
}
```
8. Test the /token endpoint with the plaintext usernames and passwords.
9. For the other endpoints, click Authorize and enter a username and password.

HTML STATUS CODES USED:
200 - OK
400 - BAD REQUEST       # validate fail or person exists (for add)
401 - UNAUTHORIZED      # bad jwt, username, or password
403 - FORBIDDEN         # role fail (read tries r/w)
404 - NOT FOUND         # person doesnt exist (for del)

DB is not persisted in Docker.
DB is deleted during testing for a clean slate.

---
