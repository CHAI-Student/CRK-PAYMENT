import logging

from .payment_types import (
    DeviceCheckData,
    TxSPayApprovalData,
    TxSPayCancelData,
    TxTokenApprovalData,
    TxTokenCancelData,
    TxTokenData,
)

from .const import AuthorizationType, MessageType, ServiceCode
from .manager import Communication
from .payload import (
    DeviceCheckRequest,
    DeviceCheckResponse,
    TransactionSPayApproveRequest,
    TransactionSPayApproveResponse,
    TransactionSPayCancelRequest,
    TransactionSPayCancelResponse,
    TransactionSPayInitilizeRequest,
    TransactionTokenApproveRequest,
    TransactionTokenApproveResponse,
    TransactionTokenCancelRequest,
    TransactionTokenCancelResponse,
    TransactionTokenGenerateRequest,
    TransactionTokenGenerateResponse,
    TransactionTokenInitilizeRequest,
    TransactionRFIDInitilizeRequest,
)
from .structure import Protocol

logger = logging.getLogger(__name__)


async def retrieve_request(comm: Communication):
    while True:
        message = await comm.read_request()

        if not message.service_code in ServiceCode:
            logger.error("Unknown service code: %s", message.service_code)
            continue

        service_code = ServiceCode(message.service_code)

        if service_code == ServiceCode.TX_TOKEN_REQUEST:
            payload_struct = TransactionTokenInitilizeRequest
        if service_code == ServiceCode.TX_SPAY_INIT:
            payload_struct = TransactionSPayInitilizeRequest
        if service_code == ServiceCode.TX_RFID_INIT:
            payload_struct = TransactionRFIDInitilizeRequest
        else:
            logger.error("Service code %s not implemented yet", service_code)
            continue

        break

    payload = payload_struct.parse(message.payload)

    return message, payload


async def send_tx_token_generate(comm: Communication) -> TxTokenData:
    request_payload = TransactionTokenGenerateRequest.build(
        {
            "message": "",
        }
    )
    request = Protocol.build(
        {
            "service_code": ServiceCode.TX_TOKEN_GENERATE.value,
            "message_type": MessageType.REQUEST,
            "payload": request_payload,
        }
    )
    response = await comm.fetch(request)
    assert response.service_code == ServiceCode.TX_TOKEN_GENERATE.value
    assert response.message_type == MessageType.RESPONSE
    response_payload = TransactionTokenGenerateResponse.parse(response.payload)
    return TxTokenData(
        status=response_payload.status,
        vankey_hash=(
            response_payload.vankey_hash if response_payload.status == "Y" else None
        ),
        card_info=(
            response_payload.card_info if response_payload.status == "Y" else None
        ),
        response_code=response_payload.response_code,
        message=response_payload.message,
    )


async def send_tx_token_approve(
    comm: Communication, amount: str, vankey_hash: bytes
) -> TxTokenApprovalData:
    # TODO: implement amount assertion for digit 0-9 only
    request_payload = TransactionTokenApproveRequest.build(
        {
            "amount": amount,
            "vankey_hash": vankey_hash,
            "message": "",
        }
    )
    request = Protocol.build(
        {
            "service_code": ServiceCode.TX_TOKEN_APPROVE.value,
            "message_type": MessageType.REQUEST,
            "payload": request_payload,
        }
    )
    response = await comm.fetch(request)
    assert response.service_code == ServiceCode.TX_TOKEN_APPROVE.value
    assert response.message_type == MessageType.RESPONSE
    response_payload = TransactionTokenApproveResponse.parse(response.payload)
    return TxTokenApprovalData(
        status=response_payload.status,
        authorization_number=(
            response_payload.authorization_number
            if response_payload.status == "Y"
            else None
        ),
        card_info=(
            response_payload.card_info if response_payload.status == "Y" else None
        ),
        vankey=response_payload.vankey if response_payload.status == "Y" else None,
        response_code=response_payload.response_code,
        message=response_payload.message,
    )


async def send_tx_token_cancel(
    comm: Communication,
    amount: str,
    original_authorization_number: bytes,
    original_authorization_date: str,
    vankey_hash: bytes,
) -> TxTokenCancelData:
    # TODO: implement amount assertion for digit 0-9 only
    request_payload = TransactionTokenCancelRequest.build(
        {
            "amount": amount,
            "original_authorization_number": original_authorization_number,
            "original_authorization_date": original_authorization_date,
            "vankey_hash": vankey_hash,
        }
    )
    request = Protocol.build(
        {
            "service_code": ServiceCode.TX_TOKEN_CANCEL.value,
            "message_type": MessageType.REQUEST,
            "payload": request_payload,
        }
    )
    response = await comm.fetch(request)
    assert response.service_code == ServiceCode.TX_TOKEN_CANCEL.value
    assert response.message_type == MessageType.RESPONSE
    response_payload = TransactionTokenCancelResponse.parse(response.payload)
    return TxTokenCancelData(
        status=response_payload.status,
        card_info=(
            response_payload.card_info if response_payload.status == "Y" else None
        ),
        vankey=response_payload.vankey if response_payload.status == "Y" else None,
        response_code=response_payload.response_code,
        message=response_payload.message,
    )


async def send_tx_spay_approval(
    comm: Communication, amount: str, authorization_type: AuthorizationType
) -> TxSPayApprovalData:
    # TODO: implement amount assertion for digit 0-9 only
    request_payload = TransactionSPayApproveRequest.build(
        {
            "amount": amount,
            "authorization_type": authorization_type,
        }
    )
    request = Protocol.build(
        {
            "service_code": ServiceCode.TX_SPAY_APPROVE.value,
            "message_type": MessageType.REQUEST,
            "payload": request_payload,
        }
    )
    response = await comm.fetch(request)
    assert response.service_code == ServiceCode.TX_SPAY_APPROVE.value
    assert response.message_type == MessageType.RESPONSE
    response_payload = TransactionSPayApproveResponse.parse(response.payload)
    return TxSPayApprovalData(
        status=response_payload.status,
        authorization_number=(
            response_payload.authorization_number
            if response_payload.status == "Y"
            else None
        ),
        card_info=(
            response_payload.card_info if response_payload.status == "Y" else None
        ),
        vankey=response_payload.vankey if response_payload.status == "Y" else None,
        response_code=response_payload.response_code,
        message=response_payload.message,
    )


async def send_tx_spay_cancel(
    comm: Communication,
    amount: str,
    original_authorization_number: bytes,
    original_authorization_date: str,
    vankey: bytes,
) -> TxSPayCancelData:
    # TODO: implement amount assertion for digit 0-9 only
    request_payload = TransactionSPayCancelRequest.build(
        {
            "amount": amount,
            "original_authorization_number": original_authorization_number,
            "original_authorization_date": original_authorization_date,
            "vankey": vankey,
        }
    )
    request = Protocol.build(
        {
            "service_code": ServiceCode.TX_SPAY_CANCEL.value,
            "message_type": MessageType.REQUEST,
            "payload": request_payload,
        }
    )
    response = await comm.fetch(request)
    assert response.service_code == ServiceCode.TX_SPAY_CANCEL.value
    assert response.message_type == MessageType.RESPONSE
    response_payload = TransactionSPayCancelResponse.parse(response.payload)
    return TxSPayCancelData(
        status=response_payload.status,
        card_info=(
            response_payload.card_info if response_payload.status == "Y" else None
        ),
        vankey=response_payload.vankey if response_payload.status == "Y" else None,
        response_code=response_payload.response_code,
        message=response_payload.message,
    )


async def send_device_check(comm: Communication) -> DeviceCheckData:
    request_payload = DeviceCheckRequest.build(
        {
            "message": "",
        }
    )
    request = Protocol.build(
        {
            "service_code": ServiceCode.DEVICE_CHECK.value,
            "message_type": MessageType.REQUEST,
            "payload": request_payload,
        }
    )
    response = await comm.fetch(request)
    assert response.service_code == ServiceCode.DEVICE_CHECK.value
    assert response.message_type == MessageType.RESPONSE
    response_payload = DeviceCheckResponse.parse(response.payload)
    return DeviceCheckData(
        response_code=response_payload.response_code,
    )
