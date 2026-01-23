import asyncio
import logging

from api.manager import sse_queue
from api.schemas import RFIDStream, TokenGeneratedStream
from payment.const import ServiceCode, StatusCode
from payment.manager import Communication
from payment.command import retrieve_request, send_tx_token_generate

logger = logging.getLogger(__name__)

class Action:
    def __init__(self, comm: Communication):
        self.comm = comm
        self.task: asyncio.Task | None = None
    
    async def run(self):
        while True:
            message, payload = await retrieve_request(self.comm)

            if message.service_code == ServiceCode.TX_TOKEN_INIT.value:
                # Process payment token request
                tx_token_data = await send_tx_token_generate(self.comm)
                # TODO: check if status is 'Y' and handle errors accordingly
                await sse_queue.put({
                    "event": "tx_token_generate",
                    "data": TokenGeneratedStream(
                        status='Y' if tx_token_data["status"] == StatusCode.Y else 'N',
                        vankey_hash=tx_token_data["vankey_hash"],
                        card_info=tx_token_data["card_info"],
                        response_code=tx_token_data["response_code"],
                        message=tx_token_data["message"],
                    ).model_dump(),
                })
            
            elif message.service_code == ServiceCode.TX_SPAY_INIT.value:
                await sse_queue.put({
                    "event": "samsung_pay_init",
                    "data": None,
                })
            
            elif message.service_code == ServiceCode.TX_RFID_INIT.value:
                await sse_queue.put({
                    "event": "rfid_init",
                    "data": RFIDStream(data=payload.data).model_dump(),
                })
            
            else:
                # Unknown service code; log and ignore
                logger.error("Unhandled service code: %s", message.service_code)
                continue