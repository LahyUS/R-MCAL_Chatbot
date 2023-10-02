from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from typing import Union


SECRET_KEY = "ebf95a16d513c913d1121cc7025b5491d5d36cf1d56d7fcbc404891b48920869"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data:dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()

    # Check if to_encode data is login(id, password) data or not
    if "token" in to_encode and "user_id" not in to_encode:
        if expires_delta: # Check for expiration
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire}) # Update expiration

    # Utilize jwt to encode the data with specific key and algorithm
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) 
    return encoded_jwt

def get_current_token(token:str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],)
    token = payload.get("token")
    if not token:
        return ""
    return token
    
def get_latest_title(token:str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],)
    title = payload.get("title")
    if not title:
        return ""
    return title
    
def decodeToken(token:str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],)
    token = payload.get("token")
    user_id = payload.get("user_id")
    if not token or not user_id:
        return ""
    return user_id, token
