from jose import jwt, JWTError
from core.security import oauth
from fastapi import Depends, HTTPException, Query, WebSocketException, WebSocket
from sqlalchemy.orm import Session
from database.connection import get_db, engine
from core.settings import settings
from models.user import User
from sqlalchemy.orm import sessionmaker
LocalSession = sessionmaker(bind=engine, autoflush=False, autocommit= False)

def get_user(token: str = Depends(oauth), db:Session = Depends(get_db)):
    try:
        token_data = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm] )
        user_id = token_data["sub"]
        if not user_id:
            raise HTTPException(status_code=401, detail="User Not Found")
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User Not Found")
        if user.is_active == False:
            raise HTTPException(status_code=409, detail="Inactive User")
        return user
    except JWTError:
        raise HTTPException(status_code=403, detail="You're Not Allowed")
    
async def get_user_websocket(websocket: WebSocket, token: str =  Query(None)):
    if not token:
        await websocket.close(code=1008)
        raise WebSocketException(code=1008, reason="Token Missing")
    try:
        token_data = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm] )
        user_id = token_data["sub"]
        if not user_id:
            raise WebSocketException(code=1008, reason="Invalid Token")
        db = LocalSession()
        user = db.get(User, user_id)
        db.close()
        if not user:
            raise WebSocketException(code=1008, reason="User Not Found")
        if user.is_active == False:
            raise WebSocketException(code=1008, reason="User Not Found")
        return user
    except JWTError:
        await websocket.close(code=1008)
        raise WebSocketException(code=1008, reason="User Not Found")
