from fastapi import FastAPI, HTTPException
import boto3
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# ================= FASTAPI =================
app = FastAPI()

# ================= AWS COGNITO =================
AWS_REGION = "eu-north-1"
USER_POOL_ID = "eu-north-1_v7502wNHH"
CLIENT_ID = "4n04p83m29pupn8ej4c57siv73"

cognito = boto3.client("cognito-idp", region_name=AWS_REGION)

# ================= DATABASE =================
DATABASE_URL = "mysql+pymysql://root:mohan%4028169@localhost/blogapplications"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ================= USER MODEL =================
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    cognito_user_id = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    age = Column(Integer)
    email = Column(String(255), unique=True)
    password = Column(String(255))

Base.metadata.create_all(bind=engine)

# ======================================================
# 1️⃣ SIGNUP → SEND OTP
# ======================================================
@app.post("/signup")
def signup(
    first_name: str,
    last_name: str,
    age: int,
    email: str,
    password: str,
    confirm_password: str
):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "given_name", "Value": first_name},
                {"Name": "family_name", "Value": last_name}
            ]
        )

        return {
            "message": "Signup successful. OTP sent to email. Please proceed to signin."
        }

    except cognito.exceptions.UsernameExistsException:
        raise HTTPException(status_code=400, detail="User already exists")

# ======================================================
# 2️⃣ SIGNIN → VALIDATE EMAIL + PASSWORD + OTP
# ======================================================
@app.post("/signin")
def signin(
    email: str,
    password: str,
    otp: str
):
    try:
        # ✅ Confirm OTP
        cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=email,
            ConfirmationCode=otp
        )

        # ✅ Authenticate user
        auth_response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password
            }
        )

        access_token = auth_response["AuthenticationResult"]["AccessToken"]

        # ✅ Fetch Cognito UUID
        user_info = cognito.get_user(AccessToken=access_token)

        cognito_user_id = next(
            attr["Value"] for attr in user_info["UserAttributes"]
            if attr["Name"] == "sub"
        )

        first_name = next(
            (a["Value"] for a in user_info["UserAttributes"] if a["Name"] == "given_name"),
            None
        )

        last_name = next(
            (a["Value"] for a in user_info["UserAttributes"] if a["Name"] == "family_name"),
            None
        )

        # ✅ Store in DB AFTER successful signin
        db = SessionLocal()
        existing_user = db.query(User).filter(User.email == email).first()

        if not existing_user:
            user = User(
                cognito_user_id=cognito_user_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )
            db.add(user)
            db.commit()

        return {
            "message": "Signin successful. User authorized and stored in DB."
        }

    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# ======================================================
# 3️⃣ LOGIN → AUTH ONLY (NO OTP, NO DB)
# ======================================================
@app.post("/login")
def login(email: str, password: str):
    try:
        response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password
            }
        )

        auth = response["AuthenticationResult"]

        return {
            "access_token": auth["AccessToken"],
            "id_token": auth["IdToken"],
            "refresh_token": auth["RefreshToken"]
        }

    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# ======================================================
# CRUD OPERATIONS
# ======================================================
@app.get("/users")
def get_users():
    db = SessionLocal()
    return db.query(User).all()

@app.put("/users/{user_id}")
def update_user(user_id: int, first_name: str | None = None, last_name: str | None = None):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name

    db.commit()
    return {"message": "User updated"}

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
