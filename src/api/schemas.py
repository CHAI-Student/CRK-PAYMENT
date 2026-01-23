"""Pydantic schemas for payment API request/response models."""

from typing import Optional

from pydantic import BaseModel, Field

from payment.const import CardInfoData


# ============================================================================
# Token Payment Models
# ============================================================================


class PaymentTokenApproveRequest(BaseModel):
    """Token payment approval request.
    
    Fields:
        amount: Transaction amount as 9-digit numeric string
        vankey_hash: VAN key hash (24 characters)
    """
    amount: str = Field(..., description="Amount as 9-digit numeric string")
    vankey_hash: str = Field(..., description="VAN key hash (24 characters)")


class PaymentTokenApproveResponse(BaseModel):
    """Token payment approval response.
    
    Fields:
        status: Transaction status ('Y' for success, 'N' for failure)
        authorization_number: Authorization number from device
        authorization_date: Authorization date in YYMMDD format
        card_info: Card information from device
        vankey: VAN key from device
        response_code: Device response code
        message: Human-readable message
    """
    status: str
    authorization_number: Optional[str]
    authorization_date: str
    card_info: Optional[CardInfoData]
    vankey: Optional[str]
    response_code: int
    message: str


class PaymentTokenCancelRequest(BaseModel):
    """Token payment cancellation request.
    
    Fields:
        amount: Transaction amount as 9-digit numeric string
        original_authorization_number: Original authorization number from approval
        original_authorization_date: Original authorization date in YYMMDD format
        vankey_hash: VAN key hash from original approval
    """
    amount: str = Field(..., description="Amount as 9-digit numeric string")
    original_authorization_number: str
    original_authorization_date: str = Field(..., description="Original date as YYMMDD")
    vankey_hash: str


class PaymentTokenCancelResponse(BaseModel):
    """Token payment cancellation response.
    
    Fields:
        status: Transaction status ('Y' for success, 'N' for failure)
        card_info: Card information from device
        vankey: VAN key from device
        response_code: Device response code
        message: Human-readable message
    """
    status: str
    card_info: Optional[CardInfoData]
    vankey: Optional[str]
    response_code: int
    message: str


# ============================================================================
# Samsung Pay Models
# ============================================================================


class SamsungPayApproveRequest(BaseModel):
    """Samsung Pay approval request.
    
    Fields:
        amount: Transaction amount as 9-digit numeric string
        authorization_type: Type of authorization ('PRE_AUTH' or 'PURCHASE')
        display_message: Display message in EUC-KR encoding (optional, defaults to Korean)
    """
    amount: str = Field(..., description="Amount as 9-digit numeric string")
    authorization_type: str = Field(
        ...,
        description="Type: 'PRE_AUTH' (0x00) or 'PURCHASE' (0x01)",
    )
    display_message: Optional[str] = Field(
        default="삼성페이 결제",
        description="Display message in EUC-KR encoding",
    )


class SamsungPayApproveResponse(BaseModel):
    """Samsung Pay approval response.
    
    Fields:
        status: Transaction status ('Y' for success, 'N' for failure)
        authorization_number: Authorization number from device
        authorization_date: Authorization date in YYMMDD format
        card_info: Card information from device
        vankey: VAN key from device
        response_code: Device response code
        message: Human-readable message
    """
    status: str
    authorization_number: Optional[str]
    authorization_date: str
    card_info: Optional[CardInfoData]
    vankey: Optional[str]
    response_code: int
    message: str


class SamsungPayCancelRequest(BaseModel):
    """Samsung Pay cancellation request.
    
    Fields:
        amount: Transaction amount as 9-digit numeric string
        original_authorization_number: Original authorization number from approval
        original_authorization_date: Original authorization date in YYMMDD format
        vankey: VAN key from original approval
    """
    amount: str = Field(..., description="Amount as 9-digit numeric string")
    original_authorization_number: str
    original_authorization_date: str = Field(..., description="Original date as YYMMDD")
    vankey: str = Field(..., description="VAN key from original approval")


class SamsungPayCancelResponse(BaseModel):
    """Samsung Pay cancellation response.
    
    Fields:
        status: Transaction status ('Y' for success, 'N' for failure)
        card_info: Card information from device
        vankey: VAN key from device
        response_code: Device response code
        message: Human-readable message
    """
    status: str
    card_info: Optional[CardInfoData]
    vankey: Optional[str]
    response_code: int
    message: str

# ============================================================================

class TokenGeneratedStream(BaseModel):
    status: str
    vankey_hash: Optional[str]
    card_info: Optional[CardInfoData]
    response_code: int
    message: str

class RFIDStream(BaseModel):
    data: str