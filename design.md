# Project Scope and Design Choices

This project simulates a **Frontend service** and **Cloud services** to avoid incurring billing costs and to stay within the assignment’s scope. In a real-world system, these components would require full CRUD (Create, Read, Update, Delete) operations and security validation. To achieve a functional simulation, specific design choices were made to replicate key functionalities while keeping the implementation within scope. I documented these scope and design choices, fed them to Grok AI to organize and format this report, and further edited this report for clarity.

## Key Design Choices

### User Management
- **Current Approach**: The project hardcodes a set of existing users with assigned roles (e.g., "Read" and "ReadWrite"). No User database or dynamic user management system is implemented.
- **Real-World Equivalent**: A production system would use a secure database to store user details, including hashed passwords, and provide features like user registration, password resets, and dynamic role assignments.

### Authentication and Authorization
- **Current Approach**: The system assumes a username and password are securely received (e.g., via a login form). It verifies these against hardcoded users, issues a JWT (JSON Web Token with token expiration) upon successful login, and uses the token to enforce role-based access to API endpoints.
- **Real-World Equivalent**: A real system would integrate with identity providers (e.g., OAuth2), hash and salt passwords, manage token expiration and refresh, and possibly include multi-factor authentication.
- **Why This Choice?**: This approach demonstrates core concepts like JWT issuance, validation, and role-based permissions without requiring complex infrastructure.

### Database and Persistence
- **Current Approach**: A lightweight database (e.g., SQLite) stores phone book entries, with basic CRUD operations accessible via the API.
- **Real-World Equivalent**: A production environment would use a scalable database (e.g., PostgreSQL or MySQL) with replication, backups, and optimized performance for large datasets.
- **Why This Choice?**: SQLite is portable and easy to set up, making it ideal for a small-scale simulation while still allowing secure database interactions (e.g., parameterized queries).

### Security Validation
- **Current Approach**: Input validation uses Pydantic models with regex patterns for fields like names and phone numbers. JWT tokens are validated for each protected request. Logs are created to allow for an audit
- **Real-World Equivalent**: Additional security layers like rate limiting and monitoring would be implemented.
- **Why This Choice?**: The focus on basic validation and authentication provides a foundation that can be expanded, keeping the project scope manageable.

### Scalability and Extensibility
- The project is designed modularly, allowing future integration of a full user management system (e.g., replacing hardcoded users with a database) or enhanced security features and logging. This structure supports easy expansion to mirror a real-world system.

## Current Flow of the REST API

The REST API flow begins with the assumption that a plaintext username and password have been securely received (e.g., via a login form or Swagger UI). The system then follows these steps:

1. **Credential Verification**: The username and password are checked against hardcoded user data (`username, hashed_password, role`). If valid, the system proceeds.
2. **JWT Token Issuance**: A `JWT token` is generated, embedding the username and role, signed with a secret key, and returned to the client.
3. **Endpoint Access**: The client includes the JWT in the `Authorization` header to access protected endpoints (e.g., `/PhoneBook/list`). The server validates the token and checks the user’s role.
4. **Database Interaction**: For authorized requests, the server validates input (e.g., via Pydantic and Regex) and performs CRUD operations on the database using parameterized queries to prevent SQL injection.
5. **Audit Logging**: The server logs valid requests before sending a response. Invalid requests are caught by a custom exception handling middleware to allow for logging and custom responses.
6. **Response**: The server returns the requested data or an error message based on the request’s outcome.

## Conclusion

This project effectively simulates a secure REST API by implementing authentication, authorization, input validation, and database interactions. Design choices like hardcoding users and using a lightweight database simplify the system while aligning with the assignment’s constraints. The modular design ensures that components like user management or security can be expanded to match a real-world system, making this a solid foundation for further development.
