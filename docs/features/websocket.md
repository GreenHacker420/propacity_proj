# WebSocket Support

The Product Review Analyzer includes WebSocket support for real-time progress updates during batch processing operations. This document provides detailed information about the WebSocket implementation, usage, and integration with the frontend.

## Table of Contents

1. [Overview](#overview)
2. [WebSocket Endpoints](#websocket-endpoints)
3. [Message Format](#message-format)
4. [Frontend Integration](#frontend-integration)
5. [Backend Implementation](#backend-implementation)
6. [Configuration](#configuration)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

## Overview

WebSockets provide a persistent connection between the client and server, allowing for real-time bidirectional communication. In the Product Review Analyzer, WebSockets are used to:

- Send real-time progress updates during batch processing
- Provide estimated completion times for long-running operations
- Notify clients when processing is complete
- Report processing statistics (items per second, memory usage, etc.)

This improves the user experience by providing immediate feedback during time-consuming operations without requiring polling.

## WebSocket Endpoints

The application provides the following WebSocket endpoints:

### Batch Processing Progress

```
ws://localhost:8000/ws/batch-progress
```

This endpoint provides real-time updates on batch processing operations, including:
- Current batch number
- Total number of batches
- Items processed
- Total items
- Estimated time remaining
- Processing speed (items per second)

### Sentiment Analysis Progress

```
ws://localhost:8000/ws/sentiment-progress
```

This endpoint provides real-time updates on sentiment analysis operations, including:
- Number of reviews processed
- Total number of reviews
- Current sentiment distribution
- Estimated time remaining
- Processing speed (reviews per second)

## Message Format

WebSocket messages use JSON format for both client-to-server and server-to-client communication.

### Progress Update Message

```json
{
  "type": "progress",
  "data": {
    "operation": "batch_processing",
    "current": 45,
    "total": 100,
    "percent_complete": 45.0,
    "estimated_time_remaining": 120,
    "items_per_second": 2.5,
    "current_batch": 3,
    "total_batches": 10,
    "memory_usage_mb": 256
  }
}
```

### Completion Message

```json
{
  "type": "complete",
  "data": {
    "operation": "batch_processing",
    "total_processed": 100,
    "total_time": 240,
    "average_speed": 2.4
  }
}
```

### Error Message

```json
{
  "type": "error",
  "data": {
    "operation": "batch_processing",
    "error_code": "RATE_LIMIT_EXCEEDED",
    "message": "Gemini API rate limit exceeded, switching to local processing",
    "recoverable": true
  }
}
```

## Frontend Integration

The frontend uses a custom WebSocket hook to connect to the WebSocket endpoints and handle messages:

```javascript
import { useEffect, useState } from 'react';

export const useWebSocket = (url) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prev) => [...prev, message]);
    };

    ws.onerror = (event) => {
      setError(event);
      setIsConnected(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [url]);

  const sendMessage = (message) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(message));
    }
  };

  return { isConnected, messages, sendMessage, error };
};
```

## Backend Implementation

The WebSocket implementation in the backend uses FastAPI's WebSocket support:

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: Dict[str, Any], client_id: str):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/batch-progress")
async def websocket_batch_progress(websocket: WebSocket, client_id: str = None):
    await manager.connect(websocket, client_id or "anonymous")
    try:
        while True:
            data = await websocket.receive_text()
            # Process received data if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id or "anonymous")
```

## Configuration

WebSocket support can be enabled or disabled using the `ENABLE_WEBSOCKETS` environment variable:

```
ENABLE_WEBSOCKETS=True  # Enable WebSocket support (default)
```

## Error Handling

The WebSocket implementation includes error handling for:

- Connection failures
- Disconnections
- Message parsing errors
- Authentication errors

When an error occurs, the client will receive an error message with details about the error and whether it's recoverable.

## Examples

### Tracking Batch Processing Progress

```javascript
import { useWebSocket } from '../hooks/useWebSocket';
import { useEffect, useState } from 'react';

const BatchProcessingComponent = () => {
  const { isConnected, messages } = useWebSocket('ws://localhost:8000/ws/batch-progress');
  const [progress, setProgress] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(null);

  useEffect(() => {
    if (messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      
      if (latestMessage.type === 'progress') {
        setProgress(latestMessage.data.percent_complete);
        setTimeRemaining(latestMessage.data.estimated_time_remaining);
      }
    }
  }, [messages]);

  return (
    <div>
      <h2>Batch Processing Progress</h2>
      <div>Connection Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      <progress value={progress} max="100" />
      <div>{progress.toFixed(1)}% Complete</div>
      {timeRemaining && <div>Estimated time remaining: {timeRemaining} seconds</div>}
    </div>
  );
};
```
