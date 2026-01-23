"""FastAPI application for payment gateway."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
)
from fastapi.responses import StreamingResponse
from uvicorn.config import Config
from uvicorn.server import Server

from api.schemas import (
    PaymentTokenApproveRequest,
    PaymentTokenApproveResponse,
    PaymentTokenCancelRequest,
    PaymentTokenCancelResponse,
    SamsungPayApproveRequest,
    SamsungPayApproveResponse,
    SamsungPayCancelRequest,
    SamsungPayCancelResponse,
)
from payment.const import AuthorizationType, StatusCode
from payment.manager import Communication
from payment.command import (
    send_device_check,
    send_tx_spay_approve,
    send_tx_spay_cancel,
    send_tx_token_approve,
    send_tx_token_cancel,
)

logger = logging.getLogger(__name__)

# Global state
_comm: Communication | None = None
_sse_queue: asyncio.Queue | None = None
_shutdown_event: asyncio.Event | None = None


def get_communication() -> Communication:
    """FastAPI dependency for communication."""
    if _comm is None:
        raise RuntimeError("Communication not initialized")
    return _comm


# ============================================================================
# FastAPI Application Setup
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting FastAPI application")
    global _shutdown_event
    _shutdown_event = asyncio.Event()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application")
    if _shutdown_event:
        _shutdown_event.set()
    

app = FastAPI(lifespan=lifespan)
sse_queue = asyncio.Queue()


# ============================================================================
# Status & Health Endpoints
# ============================================================================


@app.get("/status", tags=["Status"])
async def get_status(comm: Communication = Depends(get_communication)):
    """Get device status check."""
    try:
        result = await send_device_check(comm)
        return {
            "status": "ok",
            "response_code": result["response_code"].value,
            "message": result["response_code"].name,
        }
    except Exception as e:
        logger.error(f"Device check failed: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


# ============================================================================
# Token Payment Endpoints
# ============================================================================


@app.post(
    "/payment/token/approve",
    response_model=PaymentTokenApproveResponse,
    tags=["Token Payment"],
)
async def approve_payment_token(
    request: PaymentTokenApproveRequest,
    comm: Communication = Depends(get_communication),
) -> PaymentTokenApproveResponse:
    """
    Approve a token payment.
    
    Returns success after device approval.
    """
    try:
        response = await send_tx_token_approve(
            comm,
            amount=request.amount,
            vankey_hash=request.vankey_hash,
        )
        
        authorization_date = datetime.now().strftime("%y%m%d")
        
        return PaymentTokenApproveResponse(
            status='Y' if response["status"] == StatusCode.Y else 'N',
            authorization_number=response["authorization_number"],
            authorization_date=authorization_date,
            card_info=response["card_info"],
            vankey=response["vankey"],
            response_code=response["response_code"].value,
            message=response["message"],
        )
    except Exception as e:
        logger.error(f"Token approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/payment/token/cancel",
    response_model=PaymentTokenCancelResponse,
    tags=["Token Payment"],
)
async def cancel_payment_token(
    request: PaymentTokenCancelRequest,
    comm: Communication = Depends(get_communication),
) -> PaymentTokenCancelResponse:
    """
    Cancel a token payment.
    
    Returns success after device cancellation.
    """
    try:
        response = await send_tx_token_cancel(
            comm,
            amount=request.amount,
            original_authorization_number=request.original_authorization_number,
            original_authorization_date=request.original_authorization_date,
            vankey_hash=request.vankey_hash,
        )
        
        return PaymentTokenCancelResponse(
            status='Y' if response["status"] == StatusCode.Y else 'N',
            card_info=response["card_info"],
            vankey=response["vankey"],
            response_code=response["response_code"].value,
            message=response["message"],
        )
    except Exception as e:
        logger.error(f"Token cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Samsung Pay Endpoints
# ============================================================================


@app.post(
    "/payment/samsung/approve",
    response_model=SamsungPayApproveResponse,
    tags=["Samsung Pay"],
)
async def approve_samsung_payment(
    request: SamsungPayApproveRequest,
    comm: Communication = Depends(get_communication),
) -> SamsungPayApproveResponse:
    """
    Approve a Samsung Pay payment.
    
    Returns success immediately; persistence is handled asynchronously.
    """
    try:
        # Map authorization_type to protocol value
        auth_type_map = {"PRE_AUTH": 0x00, "PURCHASE": 0x01}
        auth_type_byte = auth_type_map.get(request.authorization_type, 0x01)
        
        # Encode display message to EUC-KR if needed
        display_msg = request.display_message or "삼성페이 결제"
        
        response = await send_tx_spay_approve(
            comm,
            amount=request.amount,
            authorization_type=AuthorizationType(auth_type_byte),
            display_message=display_msg,
        )
        
        authorization_date = datetime.now().strftime("%y%m%d")
        
        return SamsungPayApproveResponse(
            status='Y' if response["status"] == StatusCode.Y else 'N',
            authorization_number=response["authorization_number"],
            authorization_date=authorization_date,
            card_info=response["card_info"],
            vankey=response["vankey"],
            response_code=response["response_code"].value,
            message=response["message"],
        )
    except Exception as e:
        logger.error(f"Samsung Pay approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/payment/samsung/cancel",
    response_model=SamsungPayCancelResponse,
    tags=["Samsung Pay"],
)
async def cancel_samsung_payment(
    request: SamsungPayCancelRequest,
    comm: Communication = Depends(get_communication),
) -> SamsungPayCancelResponse:
    """
    Cancel a Samsung Pay payment.
    
    Returns success immediately; persistence is handled asynchronously.
    """
    try:
        response = await send_tx_spay_cancel(
            comm,
            amount=request.amount,
            original_authorization_number=request.original_authorization_number,
            original_authorization_date=request.original_authorization_date,
            vankey=request.vankey,
        )
        
        # Queue persistence as background task
        return SamsungPayCancelResponse(
            status='Y' if response["status"] == StatusCode.Y else 'N',
            card_info=response["card_info"],
            vankey=response["vankey"],
            response_code=response["response_code"].value,
            message=response["message"],
        )
    except Exception as e:
        logger.error(f"Samsung Pay cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SSE Endpoint
# ============================================================================


@app.get("/sse", tags=["Streaming"])
async def sse_endpoint():
    """
    Server-sent events stream for real-time payment notifications.
    """
    async def event_generator():
        while not (_shutdown_event and _shutdown_event.is_set()):
            try:
                # Wait for event or shutdown signal
                event = await asyncio.wait_for(sse_queue.get(), timeout=5.0)
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
            except asyncio.TimeoutError:
                # Keep connection alive with comment
                yield ": keepalive\n\n"
            except Exception as e:
                logger.error(f"SSE error: {e}")
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ============================================================================
# Server Initialization
# ============================================================================


async def serve_api(
    comm: Communication,
    host: str = "127.0.0.1",
    port: int = 8001,
    log_level: str = "info",
):
    """
    Start the FastAPI server.
    
    Args:
        comm: Communication instance for device interaction
        host: Server host
        port: Server port
        log_level: Uvicorn log level
    """
    global _comm, _sse_queue
    
    _comm = comm
    _sse_queue = sse_queue
    
    config = Config(app=app, host=host, port=port, log_level=log_level)
    server = Server(config=config)
    server.force_exit = True
    await server.serve()
