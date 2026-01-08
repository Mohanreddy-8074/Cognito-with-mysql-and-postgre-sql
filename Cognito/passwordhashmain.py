from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, create_engine, Session, select
from contextlib import asynccontextmanager
from typing import Annotated
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from passwordhash.models import (
    User,
    CreateUser,
    LoginUser,
    UserResponse
)

# -------------------- DATABASE --------------------

DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, echo=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# -------------------- PASSWORD HASHING (CORRECT) --------------------

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# -------------------- REGISTER --------------------

@app.post("/register", response_model=UserResponse)
def register(user_data: CreateUser, session: SessionDep):
    try:
        hashed_pwd = hash_password(user_data.password)

        user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_pwd
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return user

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

# -------------------- LOGIN --------------------

@app.post("/login", response_model=UserResponse)
def login(login_user: LoginUser, session: SessionDep):
    user = session.exec(
        select(User).where(User.email == login_user.email)
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(login_user.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return user
