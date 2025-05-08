from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Any
import logging
import json
import asyncio
import os
from ..auth.mongo_auth import get_current_user_ws

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Store active connections
active_connections: Dict[str, WebSocket] = {}

# Store batch processing status
batch_status: Dict[str, Dict[str, Any]] = {}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    """
    await websocket.accept()

    # Always use development mode with a mock user
    user_id = "dev_user_123"
    logger.info(f"WebSocket connection established for user {user_id}")

    # Store the connection
    active_connections[user_id] = websocket

    try:
        # Send initial status if available
        if user_id in batch_status:
            logger.info(f"Sending initial batch status to user {user_id}")
            json_data = json.dumps(batch_status[user_id])
            await websocket.send_text(json_data)

        # Send a welcome message to confirm connection
        welcome_message = {
            "type": "connection_established",
            "message": "WebSocket connection established successfully",
            "user_id": user_id
        }
        await websocket.send_text(json.dumps(welcome_message))
        logger.info(f"Sent welcome message to user {user_id}")

        # Listen for messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.info(f"Received message from user {user_id}: {message}")

                # Handle message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    logger.info(f"Sent pong response to user {user_id}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
        if user_id in active_connections:
            del active_connections[user_id]
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if user_id in active_connections:
            del active_connections[user_id]

async def send_batch_status(user_id: str, status: Dict[str, Any]):
    """
    Send batch processing status to a specific user.

    Args:
        user_id: User ID to send status to
        status: Status information to send
    """
    # Store the status
    batch_status[user_id] = status

    # Send to user if connected
    if user_id in active_connections:
        try:
            # Convert to JSON string for better compatibility
            json_data = json.dumps(status)
            await active_connections[user_id].send_text(json_data)
            logger.info(f"Sent batch status to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending batch status to user {user_id}: {str(e)}")
            # Remove connection if it's broken
            del active_connections[user_id]

def batch_progress_callback(user_id: str, current_batch: int, total_batches: int,
                           batch_time: float, items_processed: int, total_items: int,
                           avg_speed: float, estimated_time_remaining: float):
    """
    Callback function for batch processing progress.

    Args:
        user_id: User ID to send status to
        current_batch: Current batch number
        total_batches: Total number of batches
        batch_time: Time taken for the current batch
        items_processed: Number of items processed so far
        total_items: Total number of items to process
        avg_speed: Average processing speed (items per second)
        estimated_time_remaining: Estimated time remaining in seconds
    """
    # Create status object
    status = {
        "type": "batch_progress",
        "current_batch": current_batch,
        "total_batches": total_batches,
        "batch_time": batch_time,
        "items_processed": items_processed,
        "total_items": total_items,
        "avg_speed": avg_speed,
        "estimated_time_remaining": estimated_time_remaining,
        "progress_percentage": min(100, (items_processed / total_items) * 100) if total_items > 0 else 0
    }

    # Log the status for debugging
    logger.info(f"Sending batch progress update: {status}")

    # Send status asynchronously
    asyncio.create_task(send_batch_status(user_id, status))

    # Also send to all connections (for development)
    for connection_id in active_connections:
        asyncio.create_task(send_batch_status(connection_id, status))
