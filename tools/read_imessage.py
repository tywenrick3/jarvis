import sqlite3
import os

from tools._contacts import resolve_contact, reverse_lookup, _normalize_phone

DB_PATH = os.path.expanduser("~/Library/Messages/chat.db")

# Apple's cocoa epoch offset: seconds between 1970-01-01 and 2001-01-01
COCOA_EPOCH = 978307200

schema = {
    "name": "read_imessage",
    "description": (
        "Read iMessages from the local Messages database. "
        "Can filter by contact name or phone number and limit results. "
        "Returns messages with timestamps, contact names, and text content. "
        "Phone numbers are automatically resolved to contact names when possible."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "contact": {
                "type": "string",
                "description": "Contact name to filter by (e.g. 'Noah', 'Mom'). Looked up in macOS Contacts.",
            },
            "phone_number": {
                "type": "string",
                "description": "Phone number to filter by (e.g. '+15551234567'). Use contact name instead when possible.",
            },
            "limit": {
                "type": "integer",
                "description": "Max number of messages to return. Defaults to 20.",
            },
            "search": {
                "type": "string",
                "description": "Optional text to search for in message bodies.",
            },
        },
        "required": [],
    },
}


def execute(contact: str = None, phone_number: str = None, limit: int = 20, search: str = None) -> str:
    try:
        # Resolve contact name to phone number(s)
        phone_filter: list[str] = []
        contact_label = None

        if contact:
            matches = resolve_contact(contact)
            if not matches:
                return f"No contact found matching '{contact}'."
            if len(matches) == 1:
                phone_filter = [matches[0]["phone"]]
                contact_label = matches[0]["name"]
            else:
                phone_filter = [m["phone"] for m in matches]
                names = list({m["name"] for m in matches})
                contact_label = names[0] if len(names) == 1 else None
        elif phone_number:
            phone_filter = [_normalize_phone(phone_number)]

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        query = """
            SELECT
                datetime(m.date / 1000000000 + ?, 'unixepoch', 'localtime') AS timestamp,
                m.is_from_me,
                h.id AS phone,
                m.text
            FROM message m
            LEFT JOIN handle h ON m.handle_id = h.ROWID
            WHERE m.text IS NOT NULL
        """
        params: list = [COCOA_EPOCH]

        if phone_filter:
            placeholders = ",".join("?" for _ in phone_filter)
            query += f" AND h.id IN ({placeholders})"
            params.extend(phone_filter)

        if search:
            query += " AND m.text LIKE ?"
            params.append(f"%{search}%")

        query += " ORDER BY m.date DESC LIMIT ?"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return "No messages found."

        # Resolve all phone numbers to contact names
        unique_phones = list({r["phone"] for r in rows if r["phone"] and not r["is_from_me"]})
        phone_to_name = reverse_lookup(unique_phones) if not contact_label else {}

        lines = []
        for r in rows:
            if r["is_from_me"]:
                sender = "me"
            elif contact_label:
                sender = contact_label
            else:
                phone = r["phone"] or "unknown"
                sender = phone_to_name.get(phone, phone)
            lines.append(f"[{r['timestamp']}] {sender}: {r['text']}")

        lines.reverse()
        return "\n".join(lines)

    except Exception as e:
        return f"Error reading iMessages: {e}"
