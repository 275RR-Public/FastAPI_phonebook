# Secure Phone Book REST API

This project implements a secure Phone Book REST API as specified in the "Input_Validation_Assignment.pdf." It uses FastAPI, SQLAlchemy, and JWT authentication, with input validation via regular expressions, audit logging, and role-based authorization.

## Modifications to provided Dockerfile

**Dockerfile**:

- `FROM python:3.10-slim` updated to `FROM python:3.13-slim`
- added `RUN python -m pip install --upgrade pip`

**requirements.txt**:

- removed versioning to allow latest
- added multiple libraries as needed

## Setup Instructions

### Prerequisites

- Docker (required for building and running the application)
- Git (optional, for cloning the repository)

### Steps to Build and Run

1. **Clone the Repository** (if not already downloaded):

   ```bash
   git clone <repository-url>
   cd FastAPI_phonebook-main
   ```

2. **Generate a Secret Key** (optional, or use the provided example):

   ```bash
   openssl rand -hex 32
   ```

3. **Create the** `.env` **File**: Create a file named `.env` in the root directory with the following content:

   ```bash
   SECRET_KEY=f85b6d28654557d2879c593439ae824224158219d9984785d6072ae594487677
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   DATABASE_URL=sqlite:///phonebook.db
   ```

4. **Build the Docker Image**:

   ```bash
   docker build -t phonebook .
   ```

   This uses the provided `Dockerfile` to install dependencies and set up the environment.

5. **Run the Docker Container**:

   ```bash
   docker run -p 8000:8000 --env-file .env phonebook
   ```

   The API will be accessible at `http://127.0.0.1:8000`.

6. **Access the API**:

   - Open a browser and navigate to http://127.0.0.1:8000/docs for the Swagger UI.
   - Click `Authorize` in Swagger UI to test endpoints with the following hardcoded users:
     - **Read-only User**: `username: readuser`, `password: readpassword`
     - **Read/Write User**: `username: rwuser`, `password: rwpassword`

### Running Unit Tests

Open a terminal in your running Docker container (`Exec` in Docker Desktop):

- **Run Tests**:

  ```bash
  pytest tests/test_phonebook.py
  ```

- **Verbose Mode**:

  ```bash
  pytest tests/test_phonebook.py -v
  ```

NOTE: This will delete any current logs to test on a clean slate.

## Dependencies

All dependencies are included in the Docker image via `requirements.txt`. Key libraries:

- FastAPI: REST API framework
- SQLAlchemy: Database ORM
- PyJWT: JWT authentication
- Pydantic: Data validation
- pytest: Unit testing

## Notes

- The database (`phonebook.db`) is not persisted across Docker runs unless mounted as a volume.
- Audit logs are written to `audit.log` within the container.