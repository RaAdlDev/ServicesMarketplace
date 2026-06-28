
from fastapi import WebSocket
from models.notification import Notification


class ConnectionManager():
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def create_connection(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()

        self.active_connections.setdefault(conversation_id, []).append(websocket)

    def disconect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)

            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def send_message(self, conversation_id: str, notification: Notification ):
        if conversation_id in self.active_connections:
            recipients = self.active_connections.get(conversation_id, [])
            for conn in recipients:
                    await conn.send_json({
                        "sender_id": notification.sender_id,
                        "created_at": notification.created_at,
                        "message": notification.message
                    })
            from services.websockets_services import mark_as_read
            if len(recipients) > 1:
                mark_as_read(notification.notification_id)

manager = ConnectionManager()




