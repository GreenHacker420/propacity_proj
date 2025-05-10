from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/public-ws")
async def public_websocket_endpoint(websocket: WebSocket):
    """
    Public WebSocket endpoint with no authentication.
    """
    logger.info("Public WebSocket connection attempt")
    await websocket.accept()
    logger.info("Public WebSocket connection accepted")
    
    try:
        # Send a welcome message
        welcome_message = {
            "type": "connection_established",
            "message": "Public WebSocket connection established successfully"
        }
        await websocket.send_text(json.dumps(welcome_message))
        logger.info("Welcome message sent")
        
        # Keep the connection open
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message: {data}")
            await websocket.send_text(f"Echo: {data}")
            
    except WebSocketDisconnect:
        logger.info("Public WebSocket disconnected")
    except Exception as e:
        logger.error(f"Public WebSocket error: {str(e)}")
