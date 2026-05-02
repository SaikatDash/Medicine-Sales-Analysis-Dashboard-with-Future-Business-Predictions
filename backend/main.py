from datetime import datetime
from typing import Generator

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from database_model import Base, User
from model import UserRegister, UserLogin, UserUpdate, UserResponse, loginresponse


# Ensure tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AISalesMitra:You Personal Sales Assistant API", version="1.0.0")

# Add CORS middleware to allow requests from Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    import hashlib

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/api/register", status_code=201)
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    db_user = User(
        email=user.email,
        full_name=user.full_name or "",
        password=hash_password(user.password),
        is_active=1,
        role="user",
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserResponse.model_validate(db_user)


@app.put("/api/user/{user_id}")
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.password is not None:
        user.password = hash_password(user_data.password)
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@app.get("/api/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@app.post("/api/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return loginresponse.model_validate(user)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
