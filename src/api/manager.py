import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from uvicorn.config import Config
from uvicorn.server import Server

from payment.const import CardInfoData
from payment.manager import Communication
from payment.parse import send_device_check, send_tx_spay_approve, send_tx_spay_cancel, send_tx_token_approve, send_tx_token_cancel

_comm: Communication | None = None

app = FastAPI()

sse_queue = asyncio.Queue()


@app.get("/status")
async def get_status():
    if _comm is None:
        return {"status": "not initialized"}
    result = await send_device_check(_comm)
    return {
        "response_code": result["response_code"].value,
        "message": result["response_code"].name,
    }

class PaymentTokenApproveRequest(BaseModel):
    amount: str
    vankey_hash: str
    message: str
class PaymentTokenApproveResponse(BaseModel):
    status: str
    authorization_number: bytes | None
    authorization_date: str | None # YYMMDD, this should be generated in the python side
    card_info: CardInfoData | None
    vankey: bytes | None
    response_code: int
    message: str
@app.post("/payment/token/approve")
async def approve_payment_token(request: PaymentTokenApproveRequest) -> PaymentTokenApproveResponse:
    assert _comm is not None
    response = await send_tx_token_approve(
        _comm,
        amount=request.amount,
        vankey_hash=request.vankey_hash,
    )
    return PaymentTokenApproveResponse(
        status=response["status"],
        authorization_number=response["authorization_number"],
        authorization_date="",  # TODO: generate authorization date
        card_info=response["card_info"],
        vankey=response["vankey"] if response["status"] == 'Y' else None,
        response_code=response["response_code"].value,
        message=response["message"],
    )

class PaymentTokenCancelRequest(BaseModel):
    amount: str
    original_authorization_number: str
    original_authorization_date: str  # YYMMDD
    vankey_hash: str
class PaymentTokenCancelResponse(BaseModel):
    status: str
    card_info: dict | None
    vankey: str | None
    response_code: int
    message: str
@app.post("/payment/token/cancel")
async def cancel_payment_token(request: PaymentTokenCancelRequest):
    # Placeholder for payment token cancellation logic
    assert _comm is not None
    response = await send_tx_token_cancel(
        _comm,
        amount=request.amount,
        original_authorization_number=request.original_authorization_number,
        original_authorization_date=request.original_authorization_date,
        vankey_hash=request.vankey_hash,
    ) 
    return PaymentTokenCancelResponse(
        status=response["status"],
        card_info=response["card_info"],
        vankey=response["vankey"],
        response_code=response["response_code"].value,
        message=response["message"],
    )


class SamsungPaymentApproveRequest(BaseModel):
    amount: str
    vankey: bytes
    message: str
class SamsungPaymentApproveResponse(BaseModel):
    status: str
    authorization_number: bytes | None
    authorization_date: str | None  # YYMMDD
    vankey: bytes | None
    card_info: dict | None
    response_code: str
    message: str
@app.post("/payment/samsung/approve")
async def approve_samsung_payment(request: SamsungPaymentApproveRequest):
    # Placeholder for Samsung payment approval logic
    return {"result": "Samsung payment approved"}

class SamsungPaymentCancelRequest(BaseModel):
    amount: str
    original_authorization_number: bytes
    original_authorization_date: str  # YYMMDD
    vankey: bytes
class SamsungPaymentCancelResponse(BaseModel):
    status: str
    card_info: dict | None
    vankey: bytes | None
    response_code: str
    message: str
@app.post("/payment/samsung/cancel")
async def cancel_samsung_payment(request: SamsungPaymentCancelRequest):
    # Placeholder for Samsung payment cancellation logic
    return {"result": "Samsung payment cancelled"}


@app.get("/sse")
async def sse_endpoint():
    async def event_generator():
        while True:
            event = await sse_queue.get()
            yield f"event: {event['event']}\ndata: {event['data']}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def serve_api(
    comm: Communication,
    host: str = "0.0.0.0",
    port: int = 7000,
    log_level: str = "info",
):
    global _comm
    _comm = comm
    config = Config(app=app, host=host, port=port, log_level=log_level)
    server = Server(config=config)
    await server.serve()
