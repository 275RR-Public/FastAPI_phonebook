from dotenv import load_dotenv
import os

load_dotenv()

# created key with "openssl rand -hex 32"
SECRET_KEY = os.getenv("SECRET_KEY")
if SECRET_KEY is None:
    raise ValueError("environment variable is not set")

ALGORITHM = os.getenv("ALGORITHM")
if ALGORITHM is None:
    raise ValueError("environment variable is not set")

ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
if ACCESS_TOKEN_EXPIRE_MINUTES is None:
    raise ValueError("environment variable is not set")
ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES)

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("environment variable is not set")