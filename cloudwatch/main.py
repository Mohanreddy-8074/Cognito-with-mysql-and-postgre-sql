import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import boto3, uuid, requests
from jose import jwt
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from botocore.exceptions import ClientError

from cloudwatch.logging_config import logger
from cloudwatch.middleware.logging_middleware import LoggingMiddleware
from cloudwatch.exception_handler import global_exception_handler

# Load .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

APP_NAME = os.getenv("APP_NAME", "FastAPI App")

app = FastAPI(title=APP_NAME)
app.add_middleware(LoggingMiddleware)
app.add_exception_handler(Exception, global_exception_handler)

# AWS Cognito
AWS_REGION = os.getenv("AWS_REGION")
CLIENT_ID = os.getenv("CLIENT_ID")
USER_POOL_ID = os.getenv("USER_POOL_ID")
cognito = boto3.client("cognito-idp", region_name=AWS_REGION)

# JWT validation
security = HTTPBearer()
ISSUER = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{USER_POOL_ID}"
jwks = requests.get(f"{ISSUER}/.well-known/jwks.json").json()

def verify_access_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        token = credentials.credentials
        header = jwt.get_unverified_header(token)
        key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])
        payload = jwt.decode(
            token, key, algorithms=["RS256"], issuer=ISSUER, options={"verify_aud": False}
        )
        return payload
    except Exception as e:
        logger.error(f"Token verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    cognito_user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    age = Column(Integer)
    email = Column(String(255), unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login_at = Column(DateTime)
    deleted_at = Column(DateTime)

Base.metadata.create_all(bind=engine)

# Schemas
class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    age: int
    email: EmailStr
    password: str
    confirm_password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateUserRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    age: int | None = None

class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

# Routes
@app.post("/signup")
def signup(request: SignupRequest):
    if request.password != request.confirm_password:
        raise HTTPException(400, "Passwords do not match")
    try:
        res = cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=request.email,
            Password=request.password,
            UserAttributes=[{"Name": "email", "Value": request.email}],
        )
        db = SessionLocal()
        db.add(User(cognito_user_id=uuid.UUID(res["UserSub"]), first_name=request.first_name,
                    last_name=request.last_name, age=request.age, email=request.email))
        db.commit()
        db.close()
        return {"message": "Signup successful. OTP sent"}
    except ClientError as e:
        raise HTTPException(400, e.response["Error"]["Message"])
    except IntegrityError:
        raise HTTPException(400, "User already exists")

@app.post("/verify-otp")
def verify_otp(request: OtpVerifyRequest):
    try:
        cognito.confirm_sign_up(ClientId=CLIENT_ID, Username=request.email, ConfirmationCode=request.otp)
        return {"message": "OTP verified"}
    except Exception:
        raise HTTPException(400, "OTP verification failed")

@app.post("/login")
def login(request: LoginRequest):
    try:
        response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": request.email, "PASSWORD": request.password},
        )
        return response["AuthenticationResult"]
    except ClientError as e:
        raise HTTPException(status_code=401, detail=f"{e.response['Error']['Code']}: {e.response['Error']['Message']}")

@app.get("/users")
def get_user(token_payload=Depends(verify_access_token)):
    cognito_uuid = token_payload["sub"]
    db = SessionLocal()
    user = db.query(User).filter(User.cognito_user_id==uuid.UUID(cognito_uuid), User.deleted_at.is_(None)).first()
    db.close()
    if not user:
        raise HTTPException(404, "User not found")
    return user

@app.put("/users/me")
def update_user(request: UpdateUserRequest, token_payload=Depends(verify_access_token)):
    cognito_uuid = token_payload["sub"]
    db = SessionLocal()
    user = db.query(User).filter(User.cognito_user_id==uuid.UUID(cognito_uuid), User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(404, "User not found")
    if request.first_name:
        user.first_name = request.first_name
    if request.last_name:
        user.last_name = request.last_name
    if request.age:
        user.age = request.age
    user.updated_at = func.now()
    db.commit()
    db.close()
    return {"message": "Profile updated successfully"}

@app.delete("/users/search")
def delete_user(identifier: str, token=Depends(verify_access_token)):
    db = SessionLocal()
    user = db.query(User).filter(User.email == identifier).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.deleted_at = func.now()
    db.commit()
    db.close()
    return {"message": "User deleted"}
