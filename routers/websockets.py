from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from ws.manager import manager
from models.user import User
from sqlalchemy.orm import sessionmaker
from dependencies.auth import get_user_websocket
from database.connection import engine
from services.websockets_services import get_conversation, verify_conversation, save_message, pending_notifications, mark_as_read

LocalSession = sessionmaker(bind=engine, autoflush=False, autocommit= False)
router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/{user_id}")
async def websocket(user_id: str, websocket: WebSocket, current_user: User = Depends(get_user_websocket)):
    db = LocalSession()   
    conversation_id = verify_conversation(db, user_id, current_user.user_id)
    if not conversation_id:
        await websocket.close()
        return
    notifications = pending_notifications(db, conversation_id, current_user.user_id)
    for n in notifications:
        await websocket.send_json(
            {"sender_id": n.sender_id,
             "message": n.message,
             "created_at": n.created_at}
        )
        mark_as_read(n.notification_id)

    await manager.create_connection(websocket, conversation_id)
    try:
        while True:

            message = await websocket.receive_text()
            notification = save_message(db, conversation_id, message, current_user.user_id)
            await manager.send_message(conversation_id, notification)
            


    except WebSocketDisconnect:
        manager.disconect(websocket, conversation_id)
    finally:
        db.close()

