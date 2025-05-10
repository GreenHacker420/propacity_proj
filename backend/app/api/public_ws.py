from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set specific logger level for this module to filter out ping/pong messages
# The root logger will still be at INFO level, but this specific logger will be at WARNING level
# This means DEBUG and INFO messages from this module won't be logged unless explicitly changed
logger.setLevel(logging.WARNING)

router = APIRouter()

@router.websocket("/public-ws")
async def public_websocket_endpoint(websocket: WebSocket):
    """
    Public WebSocket endpoint with no authentication.
    """
    # Use WARNING level to ensure this is always logged
    logger.warning("Public WebSocket connection attempt")
    await websocket.accept()
    logger.warning("Public WebSocket connection accepted")

    try:
        # Send a welcome message
        welcome_message = {
            "type": "connection_established",
            "message": "Public WebSocket connection established successfully"
        }
        await websocket.send_text(json.dumps(welcome_message))
        # Use WARNING level to ensure this is always logged
        logger.warning("Welcome message sent")

        # Keep the connection open
        while True:
            data = await websocket.receive_text()

            # Try to parse as JSON
            try:
                message = json.loads(data)
                # Use debug level for ping messages, info for other messages
                if message.get("type") == "ping":
                    logger.debug(f"Received ping message")
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    logger.debug("Sent pong response")
                else:
                    logger.info(f"Received message: {message}")
                    await websocket.send_text(f"Echo: {data}")
            except json.JSONDecodeError:
                # Not JSON, treat as plain text
                logger.info(f"Received text message: {data}")
                await websocket.send_text(f"Echo: {data}")

    except WebSocketDisconnect:
        # Use WARNING level to ensure this is always logged
        logger.warning("Public WebSocket disconnected")
    except Exception as e:
        logger.error(f"Public WebSocket error: {str(e)}")
