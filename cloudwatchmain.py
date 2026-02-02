#create .env file then add this in that file 


#AWS Access Key ID: <your key>
#AWS Secret Access Key: <your secret>
#Default region name: ap-south-1   
#Default output format: json


import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import boto3, uuid, requests
from jose import jwt

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func, select
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

def verify_access_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    header = jwt.get_unverified_header(token)
    key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])
    return jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        issuer=ISSUER,
        options={"verify_aud": False},
    )

# ---------------- DATABASE ----------------

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
Base = declarative_base()

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

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with SessionLocal() as db:
        yield db

# ---------------- Validating SCHEMAS ----------------

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

# ---------------- ROUTES ----------------

#user signup with regioster email and password
@app.post("/signup")
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    if request.password != request.confirm_password:
        raise HTTPException(400, "Passwords do not match")

    res = cognito.sign_up(
        ClientId=CLIENT_ID,
        Username=request.email,
        Password=request.password,
        UserAttributes=[{"Name": "email", "Value": request.email}],
    )

    db.add(User(
        cognito_user_id=uuid.UUID(res["UserSub"]),
        first_name=request.first_name,
        last_name=request.last_name,
        age=request.age,
        email=request.email
    ))
    await db.commit()

    return {"message": "Signup successful. OTP sent"}

#verify the otp for user signup
@app.post("/verify-otp")
async def verify_otp(request: OtpVerifyRequest):
    cognito.confirm_sign_up(
        ClientId=CLIENT_ID,
        Username=request.email,
        ConfirmationCode=request.otp
    )
    return {"message": "OTP verified"}

#Creating user login
@app.post("/login")
async def login(request: LoginRequest):
    response = cognito.initiate_auth(
        ClientId=CLIENT_ID,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": request.email,
            "PASSWORD": request.password,
        },
    )
    return response["AuthenticationResult"]

#Get the user details
@app.get("/users")
async def get_user(
    token_payload=Depends(verify_access_token),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(
            User.cognito_user_id == uuid.UUID(token_payload["sub"]),
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "User not found")

    return user

#update the user details
@app.put("/users/me")
async def update_user(
    request: UpdateUserRequest,
    token_payload=Depends(verify_access_token),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(
            User.cognito_user_id == uuid.UUID(token_payload["sub"]),
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "User not found")

    if request.first_name:
        user.first_name = request.first_name
    if request.last_name:
        user.last_name = request.last_name
    if request.age:
        user.age = request.age

    user.updated_at = func.now()
    await db.commit()

    return {"message": "Profile updated successfully"}

#delete the user details
@app.delete("/users/search")
async def delete_user(
    identifier: str,
    token=Depends(verify_access_token),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == identifier)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "User not found")

    user.deleted_at = func.now()
    await db.commit()

    return {"message": "User deleted"}
