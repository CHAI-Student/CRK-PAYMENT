from construct import (Byte, Const, GreedyBytes, GreedyString, If, Mapping,
                       NullTerminated, PaddedString, Struct)

from .const import (FS, RS, Construct_AuthorizationType,
                    Construct_ResponseCode, Construct_StatusCode)

Error = Struct(
    "status" / Const(b"N"),
    Const(b"\x1c"),
    "response_code" / Construct_ResponseCode,
    Const(b"\x1e"),
    "message" / NullTerminated(GreedyString("euc-kr"), term=b"\x1c"),
    # Const(b"\x1c"),
)

CardInfo = Struct(
    "serial_number" / NullTerminated(GreedyString("ascii"), term=b"\x1e"),
    # Const(b"\x1e"),
    "acquirer_id" / PaddedString(3, "ascii"),
    Const(b"\x1e"),
    "acquirer_name" / NullTerminated(GreedyString("euc-kr"), term=b"\x1e"),
    # Const(b"\x1e"),
    "issuer_id" / PaddedString(3, "ascii"),
    Const(b"\x1e"),
    "issuer_name" / NullTerminated(GreedyString("euc-kr"), term=b"\x1e"),
    # Const(b"\x1e"),
    "merchant_id" / GreedyString("ascii"),
)

AgeCheckRequest = Struct(
    Const(FS),
)
AgeCheckResponse = Struct(
    Const(FS),
    "qr_data" / NullTerminated(GreedyBytes, term=FS),
    # Const(b"\x1c"),
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(b"\x1c"),
)

TransactionTokenInitilizeRequest = Struct(
    Const(FS),
)
TransactionTokenInitilizeResponse = Struct(
    Const(FS),
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(b"\x1c"),
)

TransactionTokenGenerateRequest = Struct(
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(b"\x1c"),
)
TransactionTokenGenerateResponse = Struct(
    "status" / Construct_StatusCode,
    Const(FS),
    "vankey_hash" / If(lambda ctx: ctx.status == "Y", Byte[24]),
    Const(FS),
    "card_info" / NullTerminated(If(lambda ctx: ctx.status == "Y", CardInfo), term=FS),
    # Const(FS),
    "response_code" / Construct_ResponseCode,
    Const(RS),
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(FS),
)

TransactionTokenApproveRequest = Struct(
    "amount" / NullTerminated(GreedyString("ascii"), term=FS),
    # Const(FS),
    "vankey_hash" / Byte[24],
    Const(FS),
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(FS),
)
TransactionTokenApproveResponse = Struct(
    "status" / Construct_StatusCode,
    Const(FS),
    "authorization_number" / If(lambda ctx: ctx.status == "Y", Byte[8]),
    Const(FS),
    "card_info" / NullTerminated(If(lambda ctx: ctx.status == "Y", CardInfo), term=FS),
    # Const(FS),
    "vankey" / If(lambda ctx: ctx.status == "Y", Byte[16]),
    Const(FS),
    "response_code" / Construct_ResponseCode,
    Const(RS),
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(FS),
)

TransactionTokenCancelRequest = Struct(
    "amount" / NullTerminated(GreedyString("ascii"), term=FS),
    # Const(FS),
    "original_authorization_number" / Byte[8],
    Const(FS),
    "original_authorization_date" / PaddedString(6, "ascii"),
    Const(FS),
    "vankey_hash" / Byte[24],
    Const(FS),
)
TransactionTokenCancelResponse = Struct(
    "status" / Construct_StatusCode,
    Const(FS),
    "card_info" / NullTerminated(If(lambda ctx: ctx.status == "Y", CardInfo), term=FS),
    # Const(FS),
    "vankey" / If(lambda ctx: ctx.status == "Y", Byte[16]),
    Const(FS),
    "response_code" / Construct_ResponseCode,
    Const(RS),
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(FS),
)

TransactionRFIDInitilizeRequest = Struct(
    "data" / PaddedString(10, "ascii"),
    Const(FS),
)

TransactionSPayInitilizeRequest = Struct(
    Const(FS),
)
TransactionSPayInitilizeResponse = Struct(
    Const(FS),
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(b"\x1c"),
)

TransactionSPayApproveRequest = Struct(
    "amount" / NullTerminated(GreedyString("ascii"), term=FS),
    # Const(FS),
    "authorization_type" / Construct_AuthorizationType,
    Const(FS),
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(FS),
)
TransactionSPayApproveResponse = Struct(
    "status" / Construct_StatusCode,
    Const(FS),
    "authorization_number" / If(lambda ctx: ctx.status == "Y", Byte[8]),
    Const(FS),
    "vankey" / If(lambda ctx: ctx.status == "Y", Byte[16]),
    Const(FS),
    "card_info" / NullTerminated(If(lambda ctx: ctx.status == "Y", CardInfo), term=FS),
    # Const(FS),
    "response_code" / Construct_ResponseCode,
    Const(RS),
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(FS),
)

TransactionSPayCancelRequest = Struct(
    "amount" / NullTerminated(GreedyString("ascii"), term=FS),
    # Const(FS),
    "original_authorization_number" / Byte[8],
    Const(FS),
    "original_authorization_date" / PaddedString(6, "ascii"),
    Const(FS),
    "vankey" / Byte[16],
    Const(FS),
)
TransactionSPayCancelResponse = Struct(
    "status" / Construct_StatusCode,
    Const(FS),
    "card_info" / NullTerminated(If(lambda ctx: ctx.status == "Y", CardInfo), term=FS),
    # Const(FS),
    "vankey" / If(lambda ctx: ctx.status == "Y", Byte[16]),
    Const(FS),
    "response_code" / Construct_ResponseCode,
    Const(RS),
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(FS),
)

DeviceCheckRequest = Struct(
    "message" / NullTerminated(GreedyString("euc-kr"), term=FS),
    # Const(b"\x1c"),
)
DeviceCheckResponse = Struct(
    "response_code" / Construct_ResponseCode,
    Const(FS),
)
