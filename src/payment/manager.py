import asyncio
import logging

from construct import ConstructError

from .payload import PayloadStructures
from .structure import Length, Protocol

logger = logging.getLogger(__name__)


async def _read_and_parse(reader: asyncio.StreamReader):
    stx_byte = await reader.readexactly(1)
    if stx_byte != b"\x02":
        raise ValueError(f"Invalid STX byte: {repr(stx_byte)}")

    length_bytes = await reader.readexactly(2)
    try:
        length = Length.parse(length_bytes)
    except ConstructError as e:
        raise ValueError(f"Length parse error: {e}")

    remaining_bytes = await reader.readexactly(length - 3)

    raw_request = stx_byte + length_bytes + remaining_bytes
    try:
        request = Protocol.parse(raw_request)
    except ConstructError as e:
        raise ValueError(f"Protocol parse error: {e}")

    return request


def _parse_payload(service_code, message_type, raw_payload):
    try:
        payload_structure = PayloadStructures[service_code][message_type]
    except KeyError:
        logger.error(
            "Unknown service code or message type (%s, %s)",
            service_code,
            message_type,
        )
        return None

    try:
        payload = payload_structure.parse(raw_payload)
    except ConstructError as e:
        logger.error("Payload parse error: %s", e)
        return None

    logger.debug("Parsed payload: %s", repr(payload))
    return payload


class CommunicationManager:
    def __init__(self):
        self.reader = None
        self.writer = None

        self.reading_task = None
        self.writing_task = None

        self.rx_request_queue = asyncio.Queue()

        self.lock = asyncio.Lock()
        self.tx_request_queue = asyncio.Queue()
        self.rx_response_queue = asyncio.Queue()

    async def run(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

        self.reading_task = asyncio.create_task(self._read())
        self.writing_task = asyncio.create_task(self._write())

        try:
            await asyncio.gather(self.reading_task, self.writing_task)
        except Exception as e:
            logger.error("Error in CommunicationHandler: %s", e)
        finally:
            self.reading_task.cancel()
            self.writing_task.cancel()
            await asyncio.gather(
                self.reading_task, self.writing_task, return_exceptions=True
            )
            self.writer.close()
            await self.writer.wait_closed()

    async def _read(self):
        if self.reader is None:
            raise RuntimeError("Reader not initialized")

        try:
            while True:
                try:
                    try:
                        request = await _read_and_parse(self.reader)
                    except ValueError as e:
                        logger.error("Read and parse error: %s", e)
                        continue

                    logger.debug("Received request: %s", repr(request))

                    service_code = request.service_code
                    message_type = request.message_type
                    raw_payload = request.payload

                    if message_type == 0:
                        rx_queue = self.rx_request_queue
                    else:
                        rx_queue = self.rx_response_queue

                    payload = _parse_payload(service_code, message_type, raw_payload)

                    await rx_queue.put(
                        {
                            "service_code": service_code,
                            "message_type": message_type,
                            "payload": payload,
                            "raw_payload": raw_payload,
                        }
                    )
                except asyncio.IncompleteReadError:
                    raise
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error("Error during reading: %s", e)
        except asyncio.IncompleteReadError:
            pass
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("Closing reading task")

    async def _write(self):
        if self.writer is None:
            raise RuntimeError("Writer not initialized")

        try:
            while True:
                try:
                    tx_item = await self.tx_request_queue.get()

                    logger.debug("Sending item: %s", tx_item)

                    service_code = tx_item["service_code"]
                    message_type = tx_item["message_type"]

                    if not "raw_payload" in tx_item or tx_item["raw_payload"] is None:
                        payload = tx_item["payload"]
                        try:
                            payload_structure = PayloadStructures[service_code][
                                message_type
                            ]
                        except KeyError:
                            logger.error(
                                "Unknown service code or message type for building (%s, %s)",
                                service_code,
                                message_type,
                            )
                            continue
                        try:
                            raw_payload = payload_structure.build(payload)
                        except ConstructError as e:
                            logger.error("Payload build error: %s", e)
                            continue
                    else:
                        raw_payload = tx_item["raw_payload"]

                    raw_request = Protocol.build(
                        {
                            "service_code": service_code,
                            "message_type": message_type,
                            "payload": raw_payload,
                        }
                    )

                    self.writer.write(raw_request)
                    await self.writer.drain()
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error("Error during writing: %s", e)
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("Closing writing task")

    async def read_request(self):
        return await self.rx_request_queue.get()

    async def fetch(self, service_code, payload=None, raw_payload=None):
        if payload is None and raw_payload is None:
            raise ValueError("Either payload or raw_payload must be provided")
        async with self.lock:
            await self.tx_request_queue.put(
                {
                    "service_code": service_code,
                    "message_type": 0,
                    "payload": payload,
                    "raw_payload": raw_payload,
                }
            )
            while True:
                response = await self.rx_response_queue.get()
                if (
                    response["service_code"] == service_code
                    and response["message_type"] == 1
                ):
                    return response
