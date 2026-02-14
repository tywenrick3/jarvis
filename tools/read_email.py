import os
import imaplib
import email
import email.message
from email.header import decode_header

BODY_TRUNCATE = 2000

schema = {
    "name": "read_email",
    "description": (
        "Read recent emails from the operator's mailbox via IMAP. "
        "Returns sender, date, subject, and a truncated plain-text body for each message. "
        "Does NOT mark emails as read. Attachment filenames are listed but not downloaded."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "folder": {
                "type": "string",
                "description": "Mailbox folder to read (default: INBOX). Examples: INBOX, [Gmail]/Sent Mail, [Gmail]/Drafts"
            },
            "count": {
                "type": "integer",
                "description": "Number of recent emails to fetch (default: 5, max: 25)"
            },
            "search": {
                "type": "string",
                "description": "Optional IMAP search filter. Examples: ALL, UNSEEN, FROM \"alice@example.com\", SUBJECT \"invoice\""
            },
        },
        "required": []
    }
}


def _decode_header_value(value: str) -> str:
    """Decode MIME-encoded header values."""
    if value is None:
        return ""
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _extract_text_body(msg: email.message.Message) -> str:
    """Extract plain-text body, falling back to stripped HTML."""
    if msg.is_multipart():
        plain = None
        html = None
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                continue
            if content_type == "text/plain" and plain is None:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    plain = payload.decode(charset, errors="replace")
            elif content_type == "text/html" and html is None:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html = payload.decode(charset, errors="replace")
        if plain:
            return plain
        if html:
            import re
            return re.sub(r"<[^>]+>", "", html)
        return "(no text body)"
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
        return "(no text body)"


def _list_attachments(msg: email.message.Message) -> list[str]:
    attachments = []
    for part in msg.walk():
        disposition = str(part.get("Content-Disposition", ""))
        if "attachment" in disposition:
            filename = part.get_filename()
            if filename:
                attachments.append(_decode_header_value(filename))
    return attachments


def execute(folder: str = "INBOX", count: int = 5, search: str = "ALL") -> str:
    address = os.environ.get("EMAIL_ADDRESS")
    password = os.environ.get("EMAIL_APP_PASSWORD")
    imap_host = os.environ.get("EMAIL_IMAP_HOST", "imap.gmail.com")

    if not address or not password:
        return "Error: EMAIL_ADDRESS and EMAIL_APP_PASSWORD must be set in .env"

    count = max(1, min(count, 25))

    try:
        conn = imaplib.IMAP4_SSL(imap_host)
        conn.login(address, password)
        status, _ = conn.select(f'"{folder}"', readonly=True)
        if status != "OK":
            conn.logout()
            return f"Error: could not open folder '{folder}'"

        status, data = conn.search(None, search)
        if status != "OK":
            conn.logout()
            return f"Error: search failed with filter '{search}'"

        msg_ids = data[0].split()
        if not msg_ids:
            conn.logout()
            return f"No emails found in '{folder}' matching '{search}'."

        # take the most recent N
        msg_ids = msg_ids[-count:]
        msg_ids.reverse()  # newest first

        results = []
        for i, mid in enumerate(msg_ids, 1):
            # BODY.PEEK so we don't mark as read
            status, msg_data = conn.fetch(mid, "(BODY.PEEK[])")
            if status != "OK":
                results.append(f"--- Email {i} ---\n(failed to fetch)\n")
                continue

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            from_addr = _decode_header_value(msg.get("From", ""))
            to_addr = _decode_header_value(msg.get("To", ""))
            date = msg.get("Date", "")
            subject = _decode_header_value(msg.get("Subject", "(no subject)"))
            body = _extract_text_body(msg)
            attachments = _list_attachments(msg)

            if len(body) > BODY_TRUNCATE:
                body = body[:BODY_TRUNCATE] + "\n... (truncated)"

            header = (
                f"--- Email {i} ---\n"
                f"From:    {from_addr}\n"
                f"To:      {to_addr}\n"
                f"Date:    {date}\n"
                f"Subject: {subject}\n"
            )
            if attachments:
                header += f"Attachments: {', '.join(attachments)}\n"
            header += f"\n{body.strip()}\n"
            results.append(header)

        conn.logout()
        return "\n".join(results)

    except imaplib.IMAP4.error as e:
        return f"IMAP error: {e}"
    except Exception as e:
        return f"Error reading email: {e}"
