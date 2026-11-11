import hashlib
from decimal import Decimal

def crc16_ccitt(data: str) -> str:
    """
    Computes CRC-16/CCITT-FALSE (Polynomial 0x1021, Initial 0xFFFF).
    Standard checksum calculation for EMVCo / NBC Bakong KHQR Tag 63.
    """
    crc = 0xFFFF
    for byte in data.encode('utf-8'):
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"

def format_tlv(tag: str, value: str) -> str:
    """Formats Tag-Length-Value according to EMVCo Merchant-Presented Mode specifications."""
    value_str = str(value)
    length = len(value_str.encode('utf-8'))
    return f"{tag}{length:02d}{value_str}"

def generate_khqr_payload(
    bakong_account_id: str,
    merchant_name: str,
    merchant_city: str,
    amount: Decimal,
    currency: str = "USD",
    bill_number: str = "",
    store_label: str = "Clothes"
) -> str:
    """
    Constructs an EMVCo-compliant Dynamic Bakong KHQR string payload.
    Supports both USD (Currency Code 840) and KHR (Currency Code 116).
    """
    # Root Tag 00: Payload Format Indicator (Fixed to "01")
    payload = format_tlv("00", "01")

    # Root Tag 01: Point of Initiation Method (12 = Dynamic QR with pre-locked amount)
    payload += format_tlv("01", "12")

    # Root Tag 29: Merchant Account Information for Bakong
    sub_tag_00 = format_tlv("00", bakong_account_id)
    sub_tag_01 = format_tlv("01", store_label)
    payload += format_tlv("29", sub_tag_00 + sub_tag_01)

    # Root Tag 52: Merchant Category Code (5999 for miscellaneous retail / apparel)
    payload += format_tlv("52", "5999")

    # Root Tag 53: Transaction Currency (840 = USD, 116 = KHR)
    currency_code = "840" if currency.upper() == "USD" else "116"
    payload += format_tlv("53", currency_code)

    # Root Tag 54: Transaction Amount
    if currency_code == "840":
        amount_str = f"{amount:.2f}"
    else:
        amount_str = f"{int(amount)}"
    payload += format_tlv("54", amount_str)

    # Root Tag 58: Country Code (Fixed to "KH")
    payload += format_tlv("58", "KH")

    # Root Tag 59: Merchant Name
    payload += format_tlv("59", merchant_name[:25])

    # Root Tag 60: Merchant City
    payload += format_tlv("60", merchant_city[:15])

    # Root Tag 62: Additional Data Field (Bill/Order Number, Mobile, Purpose)
    add_data = ""
    if bill_number:
        add_data += format_tlv("01", bill_number[:25])
    add_data += format_tlv("03", store_label[:25])
    payload += format_tlv("62", add_data)

    # Root Tag 63: Checksum placeholder and CRC16 calculation
    pre_crc = payload + "6304"
    crc_hex = crc16_ccitt(pre_crc)

    return pre_crc + crc_hex

def generate_khqr_md5(payload: str) -> str:
    """
    Generates MD5 hash of the raw KHQR payload.
    Used by the NBC Bakong Open API for checking transaction confirmation via `check_transaction_by_md5`.
    """
    return hashlib.md5(payload.encode('utf-8')).hexdigest()
