from typing import TypedDict, Literal, Optional

from .const import CardInfoData, ResponseCode

class TxTokenData(TypedDict):
    status: Literal['Y', 'N']
    vankey_hash: Optional[bytes]
    card_info: Optional[CardInfoData]
    response_code: int
    message: str

class TxTokenApprovalData(TypedDict):
    status: Literal['Y', 'N']
    authorization_number: Optional[bytes]
    card_info: Optional[CardInfoData]
    vankey: Optional[bytes]
    response_code: int
    message: str

class TxTokenCancelData(TypedDict):
    status: Literal['Y', 'N']
    card_info: Optional[CardInfoData]
    vankey: Optional[bytes]
    response_code: int
    message: str

class TxSPayApprovalData(TypedDict):
    status: Literal['Y', 'N']
    authorization_number: Optional[bytes]
    card_info: Optional[CardInfoData]
    vankey: Optional[bytes]
    response_code: int
    message: str

class TxSPayCancelData(TypedDict):
    status: Literal['Y', 'N']
    card_info: Optional[CardInfoData]
    vankey: Optional[bytes]
    response_code: int
    message: str

class DeviceCheckData(TypedDict):
    response_code: ResponseCode