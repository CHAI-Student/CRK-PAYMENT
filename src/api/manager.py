from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from uvicorn.config import Config
from uvicorn.server import Server

from payment.manager import Communication
from payment.parse import send_device_check

_comm: Communication | None= None

app = FastAPI()


@app.get("/status")
async def get_status():
    if _comm is None:
        return {"status": "not initialized"}
    result = await send_device_check(_comm)
    return {"response_code": result["response_code"].value, "message": result["response_code"].name}

@app.post("/payment/token/approve")
async def approve_payment_token():
    # Placeholder for payment token approval logic
    return {"result": "Payment token approved"}

@app.post("/payment/token/cancel")
async def cancel_payment_token():
    # Placeholder for payment token cancellation logic
    return {"result": "Payment token cancelled"}

@app.post("/payment/samsung/approve")
async def approve_samsung_payment():
    # Placeholder for Samsung payment approval logic
    return {"result": "Samsung payment approved"}

@app.post("/payment/samsung/cancel")
async def cancel_samsung_payment():
    # Placeholder for Samsung payment cancellation logic
    return {"result": "Samsung payment cancelled"}

@app.get("/sse")
async def sse_endpoint():
    async def event_generator():
        for i in range(5):
            yield f"data: Event {i}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def serve_api(comm: Communication, host: str = "0.0.0.0", port: int = 7000, log_level: str = "info"):
    global _comm
    _comm = comm
    config = Config(app=app, host=host, port=port, log_level=log_level)
    server = Server(config=config)
    await server.serve()
