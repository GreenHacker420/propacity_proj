from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Any
import logging
import json
import asyncio
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set specific logger level for this module to filter out ping/pong messages
# The root logger will still be at INFO level, but this specific logger will be at WARNING level
# This means DEBUG and INFO messages from this module won't be logged unless explicitly changed
logger.setLevel(logging.WARNING)

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
    # Use WARNING level to ensure this is always logged
    logger.warning(f"WebSocket connection established for user {user_id}")

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
        # Use WARNING level to ensure this is always logged
        logger.warning(f"Sent welcome message to user {user_id}")

        # Listen for messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Use debug level for ping messages, info for other messages
                if message.get("type") == "ping":
                    logger.debug(f"Received ping from user {user_id}")
                else:
                    logger.info(f"Received message from user {user_id}: {message}")

                # Handle message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    # Use debug level for ping/pong messages to avoid cluttering logs
                    logger.debug(f"Sent pong response to user {user_id}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        # Use WARNING level to ensure this is always logged
        logger.warning(f"WebSocket disconnected for user {user_id}")
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

            # Only log detailed info for non-ping messages or significant updates
            if status.get("type") != "ping" and (
                status.get("type") != "batch_progress" or
                status.get("current_batch") == 1 or
                status.get("current_batch") == status.get("total_batches") or
                status.get("current_batch", 0) % 5 == 0
            ):
                logger.info(f"Sent batch status to user {user_id}")
            else:
                logger.debug(f"Sent batch status to user {user_id}")
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

    # Log the status for debugging - only log detailed info for significant progress updates
    if current_batch == 1 or current_batch == total_batches or current_batch % 5 == 0:
        logger.info(f"Sending batch progress update: {status}")
    else:
        logger.debug(f"Sending batch progress update: {status}")

    # Send status asynchronously
    asyncio.create_task(send_batch_status(user_id, status))

    # Also send to all connections (for development)
    for connection_id in active_connections:
        asyncio.create_task(send_batch_status(connection_id, status))

@router.websocket("/ws-public")
async def websocket_endpoint_public(websocket: WebSocket):
    """
    Public WebSocket endpoint with no authentication.
    """
    # Accept the connection immediately
    await websocket.accept()

    # Use a fixed user ID
    user_id = "public_user"
    logger.info(f"Public WebSocket connection established for user {user_id}")

    try:
        # Send a welcome message
        welcome_message = {
            "type": "connection_established",
            "message": "Public WebSocket connection established successfully",
            "user_id": user_id
        }
        await websocket.send_text(json.dumps(welcome_message))

        # Keep the connection open
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.info(f"Received message from public user: {message}")

                # Echo back the message
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "original": message
                }))

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))

    except WebSocketDisconnect:
        logger.info(f"Public WebSocket disconnected")
    except Exception as e:
        logger.error(f"Public WebSocket error: {str(e)}")
