import glob
import os
import re
import sqlite3

ADDRESSBOOK_DIR = os.path.expanduser("~/Library/Application Support/AddressBook/Sources")


def _normalize_phone(number: str) -> str:
    """Strip a phone number down to digits (with leading +)."""
    digits = re.sub(r"[^\d+]", "", number)
    # Ensure US numbers have +1 prefix
    if digits and not digits.startswith("+"):
        if len(digits) == 10:
            digits = "+1" + digits
        elif len(digits) == 11 and digits.startswith("1"):
            digits = "+" + digits
    return digits


def resolve_contact(name: str) -> list[dict]:
    """Search all AddressBook sources for contacts matching `name`.

    Returns a list of {"name": str, "phone": str} dicts, deduplicated by
    normalized phone number.
    """
    pattern = os.path.join(ADDRESSBOOK_DIR, "*/AddressBook-v22.abcddb")
    db_paths = glob.glob(pattern)

    seen_phones: set[str] = set()
    results: list[dict] = []

    for db_path in db_paths:
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            # Search first name, last name, or combined
            cur.execute(
                """
                SELECT
                    COALESCE(r.ZFIRSTNAME, '') || ' ' || COALESCE(r.ZLASTNAME, '') AS full_name,
                    p.ZFULLNUMBER
                FROM ZABCDRECORD r
                JOIN ZABCDPHONENUMBER p ON p.ZOWNER = r.Z_PK
                WHERE r.ZFIRSTNAME LIKE ? OR r.ZLASTNAME LIKE ?
                   OR (COALESCE(r.ZFIRSTNAME, '') || ' ' || COALESCE(r.ZLASTNAME, '')) LIKE ?
                """,
                (f"%{name}%", f"%{name}%", f"%{name}%"),
            )
            for full_name, phone in cur.fetchall():
                normalized = _normalize_phone(phone)
                if normalized and normalized not in seen_phones:
                    seen_phones.add(normalized)
                    results.append({"name": full_name.strip(), "phone": normalized})
            conn.close()
        except Exception:
            continue

    return results


def reverse_lookup(phone_numbers: list[str]) -> dict[str, str]:
    if not phone_numbers:
        return {}

    pattern = os.path.join(ADDRESSBOOK_DIR, "*/AddressBook-v22.abcddb")
    db_paths = glob.glob(pattern)

    results: dict[str, str] = {}

    for db_path in db_paths:
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    COALESCE(r.ZFIRSTNAME, '') || ' ' || COALESCE(r.ZLASTNAME, '') AS full_name,
                    p.ZFULLNUMBER
                FROM ZABCDRECORD r
                JOIN ZABCDPHONENUMBER p ON p.ZOWNER = r.Z_PK
                WHERE p.ZFULLNUMBER IS NOT NULL
                """
            )
            for full_name, phone in cur.fetchall():
                normalized = _normalize_phone(phone)
                if normalized and normalized not in results:
                    results[normalized] = full_name.strip()
            conn.close()
        except Exception:
            continue

    return {num: results[num] for num in phone_numbers if num in results}
