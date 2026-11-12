import hashlib
import time
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

def get_acquiring_bank(account_id: str) -> str:
    """
    Maps Bakong participant domain suffix to official acquiring institution name.
    Required by Cambodian banking apps (e.g. ABA Mobile, Bakong, Wing) in Tag 29 sub-tag 02
    to correctly resolve cross-bank routing.
    """
    if "@" in account_id:
        domain = account_id.split("@")[1].strip().lower()
        mapping = {
            "bkrt": "Bakong",
            "abaa": "ABA Bank",
            "wing": "Wing Bank",
            "aclb": "ACLEDA Bank",
            "cani": "Canadia Bank",
            "stpc": "Sathapana Bank",
            "ftbc": "FTB Bank",
            "vdbc": "Vattanac Bank",
            "ppcb": "PPCBank",
        }
        return mapping.get(domain, "Bakong")
    return "Bakong"

def generate_khqr_payload(
    bakong_account_id: str,
    merchant_name: str,
    merchant_city: str,
    amount: Decimal,
    currency: str = "USD",
    bill_number: str = "",
    store_label: str = "Clothes",
    phone_number: str = "",
    terminal_label: str = "",
    acquiring_bank: str = "",
    expiration_days: int = 1,
) -> str:
    """
    Constructs an EMVCo-compliant Dynamic Bakong KHQR string payload.
    Conforms strictly to National Bank of Cambodia (NBC) KHQR standards:
    - Root Tag 00: EMVCo Payload Format Indicator ('01')
    - Root Tag 01: Initiation method ('12' = Dynamic QR)
    - Root Tag 29: Merchant Account Info with Sub-tag 00 (Account ID) & Sub-tag 02 (Acquiring Bank)
    - Root Tag 52: MCC 5999 (Apparel & Retail)
    - Root Tag 53: Currency (840 = USD, 116 = KHR)
    - Root Tag 54: Amount without trailing zero padding
    - Root Tag 58: Country 'KH'
    - Root Tag 59: Merchant Name
    - Root Tag 60: Merchant City
    - Root Tag 62: Additional Data Field (Store label, Bill/Order number, Mobile)
    - Root Tag 99: NBC Timestamp & Expiry timestamp in milliseconds
    - Root Tag 63: CRC-16/CCITT checksum
    """
    account_id = bakong_account_id.strip()
    bank_name = (acquiring_bank or get_acquiring_bank(account_id)).strip()

    # Root Tag 00 & Tag 01
    payload = format_tlv("00", "01")
    payload += format_tlv("01", "12")

    # Tag 29: Account Identifier with Acquiring Bank (Sub-tag 00 and Sub-tag 02)
    sub_tag_00 = format_tlv("00", account_id)
    sub_tag_02 = format_tlv("02", bank_name)
    payload += format_tlv("29", sub_tag_00 + sub_tag_02)

    # Tag 52: Merchant Category Code (5999)
    payload += format_tlv("52", "5999")

    # Tag 53: Transaction Currency (840 = USD, 116 = KHR)
    currency_code = "840" if currency.upper() == "USD" else "116"
    payload += format_tlv("53", currency_code)

    # Tag 54: Transaction Amount (stripped trailing zeros per NBC spec)
    amount_float = float(amount)
    amount_str = f"{amount_float:.2f}".rstrip("0").rstrip(".")
    if not amount_str or amount_str == "0":
        amount_str = "1"
    payload += format_tlv("54", amount_str)

    # Tag 58: Country Code (Fixed to 'KH')
    payload += format_tlv("58", "KH")

    # Tag 59: Merchant Name
    clean_name = (merchant_name or "Clothes Apparel Co")[:25].strip()
    payload += format_tlv("59", clean_name)

    # Tag 60: Merchant City
    clean_city = (merchant_city or "Phnom Penh")[:15].strip()
    payload += format_tlv("60", clean_city)

    # Tag 62: Additional Data Field
    add_data = ""
    clean_store = (store_label or clean_name)[:25].strip()
    if clean_store:
        add_data += format_tlv("03", clean_store)
    if bill_number:
        add_data += format_tlv("01", bill_number[:25].strip())
    if phone_number:
        add_data += format_tlv("02", phone_number[:25].strip())
    if add_data:
        payload += format_tlv("62", add_data)

    # Tag 99: NBC Timestamp & Expiry in milliseconds
    now_ms = int(time.time() * 1000)
    exp_ms = now_ms + (expiration_days * 86400 * 1000)
    tag_99_sub00 = format_tlv("00", str(now_ms))
    tag_99_sub01 = format_tlv("01", str(exp_ms))
    payload += format_tlv("99", tag_99_sub00 + tag_99_sub01)

    # Tag 63: Checksum
    pre_crc = payload + "6304"
    crc_hex = crc16_ccitt(pre_crc)
    return pre_crc + crc_hex

def generate_khqr_md5(payload: str) -> str:
    """
    Generates MD5 hash of the raw KHQR payload.
    Used by the NBC Bakong Open API for checking transaction confirmation via `check_transaction_by_md5`.
    """
    return hashlib.md5(payload.encode('utf-8')).hexdigest()
