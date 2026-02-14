import subprocess

from tools._contacts import resolve_contact, _normalize_phone

schema = {
    "name": "send_imessage",
    "description": (
        "Send an iMessage using the Messages app. "
        "Accepts a contact name (looked up in Contacts) or a phone number."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "contact": {
                "type": "string",
                "description": "Contact name to send to (e.g. 'Mom', 'Noah King'). Looked up in macOS Contacts.",
            },
            "phone_number": {
                "type": "string",
                "description": "Recipient phone number (e.g. '+15551234567'). Use contact name instead when possible.",
            },
            "message": {
                "type": "string",
                "description": "The message text to send.",
            },
        },
        "required": ["message"],
    },
}


def execute(message: str, contact: str = None, phone_number: str = None) -> str:
    if not contact and not phone_number:
        return "Error: provide either 'contact' or 'phone_number'."

    try:
        # Resolve who we're sending to
        if contact:
            matches = resolve_contact(contact)
            if not matches:
                return f"No contact found matching '{contact}'."
            if len(matches) > 1:
                names = list({m["name"] for m in matches})
                if len(names) > 1:
                    listing = "\n".join(f"  - {m['name']}: {m['phone']}" for m in matches)
                    return f"Multiple contacts match '{contact}':\n{listing}\nPlease be more specific or use phone_number."
            target = matches[0]
            recipient = target["phone"]
            display = f"{target['name']} ({recipient})"
        else:
            recipient = _normalize_phone(phone_number)
            display = recipient

        # Escape backslashes and double quotes for AppleScript string
        safe_msg = message.replace("\\", "\\\\").replace('"', '\\"')
        safe_num = recipient.replace("\\", "\\\\").replace('"', '\\"')

        script = f'''
            tell application "Messages"
                set targetService to 1st account whose service type = iMessage
                set targetBuddy to participant "{safe_num}" of targetService
                send "{safe_msg}" to targetBuddy
            end tell
        '''

        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode != 0:
            return f"Failed to send: {result.stderr.strip()}"

        return f"Message sent to {display}."

    except Exception as e:
        return f"Error sending iMessage: {e}"
