import uvicorn
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the SSE GTPlanner API
from gtplanner.agent.api.agent_api import SSEGTPlanner

# Import the index manager
from gtplanner.agent.utils.startup_init import initialize_application

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management: startup and shutdown events"""
    # Run on startup
    logger.info("🚀 GTPlanner API starting...")
    
    try:
        # Initialize the application, including preloading the prefab index
        result = await initialize_application(
            preload_index=True
        )

        if result["success"]:
            logger.info("✅ Application initialized successfully")
            if "prefab_index" in result["components"]:
                index_info = result["components"]["prefab_index"]
                logger.info(f"📦 Prefab index ready: {index_info.get('index_name', 'N/A')}")
        else:
            logger.error("❌ Application initialization failed")
            for error in result["errors"]:
                logger.error(f"  - {error}")

    except Exception as e:
        logger.error(f"❌ Initialization failed at startup: {str(e)}")
        # Don't block startup, but log the error
    
    yield  # While the application is running
    
    # Run on shutdown (clean up resources if needed)
    logger.info("👋 GTPlanner API shutting down...")

app = FastAPI(
    title="GTPlanner API",
    description="""
Intelligent planning assistant API with streaming responses and real-time tool calls

## Core Features
- ✅ Streaming SSE responses
- ✅ Real-time tool calls
- ✅ Multimodal input (text + images)
- ✅ Multilingual support (Chinese, English, Japanese, Spanish, French)

## Multimodal Support 🖼️
Users can send images (architecture diagrams, screenshots, design mockups, flowcharts, etc.):
- Image format: HTTP URL or Base64 Data URL
- Image types: JPEG, PNG, GIF, WebP, etc.
- Detail level: auto (default), low (fast), high (high precision)

See the /api/chat/agent endpoint documentation for details.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should be restricted to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routes removed; only the SSE Agent route is kept

# Create the global SSE API instance
sse_api = SSEGTPlanner(verbose=True)

# Request models
class AgentContextRequest(BaseModel):
    """
    AgentContext request model (maps directly to the backend AgentContext)
    
    Supports multimodal messages (text + images):
    The content field of each message in dialogue_history can be:
    1. A plain text string:
       {"role": "user", "content": "Design a system", "timestamp": "..."}
    
    2. A multimodal list (text + images):
       {
           "role": "user",
           "content": [
               {"type": "text", "text": "Analyze this architecture diagram"},
               {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,...", "detail": "high"}}
           ],
           "timestamp": "..."
       }
    
    Supported image formats:
    - HTTP/HTTPS URL: "https://example.com/image.jpg"
    - Base64 Data URL: "data:image/jpeg;base64,/9j/4AAQ..."
    
    Image detail level (detail):
    - "auto": automatic (default, balances speed and accuracy)
    - "low": low detail mode (faster, cheaper, good for simple images)
    - "high": high detail mode (slower, more expensive, good for complex images such as architecture diagrams and mockups)
    """
    session_id: str
    dialogue_history: List[Dict[str, Any]]
    tool_execution_results: Dict[str, Any] = {}
    session_metadata: Dict[str, Any] = {}
    last_updated: Optional[str] = None
    is_compressed: bool = False
    language: Optional[str] = None  # New: language selection field, supports 'zh', 'en', 'ja', 'es', 'fr'

    # SSE configuration options (not part of AgentContext, but used for API configuration)
    include_metadata: bool = False
    buffer_events: bool = False
    heartbeat_interval: float = 30.0

# Web UI
WEB_UI_FILE = Path(__file__).parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
async def web_ui():
    """Serve the GTPlanner web UI"""
    return FileResponse(WEB_UI_FILE, media_type="text/html")


class PRDRequest(BaseModel):
    """Quick PRD generation request"""
    request: str
    language: str = "auto"  # "auto" = same language as the request, or en/id/zh/ja/es/fr
    previous_prd: Optional[str] = None  # When set, the PRD is revised according to `request`
    template: str = "fullstack_nextjs"  # "fullstack_nextjs" (Starter Next JS framework) or "general"


@app.post("/api/prd/stream")
async def prd_stream(body: PRDRequest):
    """Generate (or revise) a complete PRD in one streaming call"""
    from gtplanner.agent.prd_generator import stream_prd

    if not body.request.strip():
        raise HTTPException(status_code=400, detail="request is required")

    async def generate():
        try:
            async for event in stream_prd(body.request, body.language, body.previous_prd, body.template):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"PRD generation error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# Health check endpoint (enhanced)
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint including API status information"""
    api_status = sse_api.get_api_status()
    return {
        "status": "healthy",
        "service": "gtplanner",
        "timestamp": datetime.now().isoformat(),
        "api_status": api_status
    }

@app.get("/api/status")
async def api_status():
    """Get detailed API status information"""
    return sse_api.get_api_status()

# Test page endpoint removed

# Plain chat API removed; only the SSE Agent API is kept

@app.post("/api/chat/agent")
async def chat_agent_stream(request: AgentContextRequest):
    """SSE streaming chat endpoint - GTPlanner Agent"""
    try:
        # Validate AgentContext data
        if not request.session_id.strip():
            raise HTTPException(status_code=400, detail="session_id is required")

        if not request.dialogue_history:
            raise HTTPException(status_code=400, detail="dialogue_history cannot be empty")

        logger.info(f"Starting SSE stream for session: {request.session_id}, messages: {len(request.dialogue_history)}")

        # Parse multimodal message content (if content is a JSON string, parse it into a list)
        def parse_message_content(message: Dict[str, Any]) -> Dict[str, Any]:
            """Parse message content, supporting multimodal format"""
            content = message.get("content")
            if isinstance(content, str) and content.strip().startswith('['):
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, list):
                        message["content"] = parsed
                        logger.debug(f"Parsed multimodal content: {len(parsed)} parts")
                except json.JSONDecodeError:
                    # Parsing failed, keep the original string
                    pass
            return message
        
        # Process all messages in dialogue_history
        parsed_history = [parse_message_content(msg.copy()) for msg in request.dialogue_history]
        request.dialogue_history = parsed_history

        async def generate_sse_stream():
            """Generate the SSE data stream"""
            try:
                # Send the conversation start event (using the standard conversation_start event type)
                conversation_start_event = {
                    "event_type": "conversation_start",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": request.session_id,
                    "data": {
                        "user_input": request.dialogue_history[-1].get("content", "") if request.dialogue_history else "",
                        "dialogue_history_length": len(request.dialogue_history),
                        "config": {
                            "include_metadata": request.include_metadata,
                            "buffer_events": request.buffer_events,
                            "heartbeat_interval": request.heartbeat_interval
                        }
                    }
                }
                yield f"event: conversation_start\ndata: {json.dumps(conversation_start_event, ensure_ascii=False)}\n\n"

                # Create a queue to collect SSE data
                import asyncio
                sse_queue = asyncio.Queue()
                processing_complete = False

                async def queue_sse_data(data: str):
                    """Put SSE data into the queue"""
                    await sse_queue.put(data)

                # Start the processing task
                async def process_request():
                    nonlocal processing_complete
                    try:
                        # Build AgentContext data (redundant user_input removed)
                        agent_context = {
                            "session_id": request.session_id,
                            "dialogue_history": request.dialogue_history,
                            "tool_execution_results": request.tool_execution_results,
                            "session_metadata": request.session_metadata,
                            "last_updated": request.last_updated,
                            "is_compressed": request.is_compressed
                        }

                        language = request.language or request.session_metadata.get('language') or 'en'

                        result = await sse_api.process_request_stream(
                            agent_context=agent_context,
                            language=language,  # Pass the language selection as a separate parameter
                            response_writer=queue_sse_data,
                            include_metadata=request.include_metadata,
                            buffer_events=request.buffer_events,
                            heartbeat_interval=request.heartbeat_interval
                        )

                        # Send the conversation end event (using the standard conversation_end event type)
                        conversation_end_event = {
                            "event_type": "conversation_end",
                            "timestamp": datetime.now().isoformat(),
                            "session_id": result.get('session_id'),
                            "data": result
                        }
                        await sse_queue.put(f"event: conversation_end\ndata: {json.dumps(conversation_end_event, ensure_ascii=False)}\n\n")

                        logger.info(f"SSE stream completed successfully for session: {result.get('session_id', 'unknown')}")

                    except Exception as e:
                        logger.error(f"SSE processing error: {e}", exc_info=True)
                        # Send the error event
                        error_event = {
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "timestamp": datetime.now().isoformat()
                        }
                        await sse_queue.put(f"event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n")
                    finally:
                        processing_complete = True
                        await sse_queue.put(None)  # End marker

                # Start the processing task
                task = asyncio.create_task(process_request())

                # Read data from the queue and send it
                heartbeat_counter = 0
                while True:
                    try:
                        # Wait for data, using a short timeout to detect completion quickly
                        data = await asyncio.wait_for(sse_queue.get(), timeout=0.1)
                        if data is None:  # End marker
                            break
                        yield data
                    except asyncio.TimeoutError:
                        # Check whether processing is complete
                        if processing_complete:
                            break
                        # Send a heartbeat every 100 timeouts (every 10 seconds)
                        heartbeat_counter += 1
                        if heartbeat_counter >= 100:
                            heartbeat = f"event: heartbeat\ndata: {{\"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n"
                            yield heartbeat
                            heartbeat_counter = 0

                # Make sure the task is complete
                if not task.done():
                    await task

            except Exception as e:
                logger.error(f"SSE stream error: {e}", exc_info=True)
                # Send the error event
                error_event = {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate_sse_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable Nginx buffering
            }
        )

    except Exception as e:
        logger.error(f"Chat agent stream error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("fastapi_main:app", host="0.0.0.0", port=11211, reload=True)
