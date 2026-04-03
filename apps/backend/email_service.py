from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass
class EmailResult:
    status: str
    error: str | None = None


def _render_message(template: str, candidate_name: str, course_name: str, expiry_label: str, test_link: str) -> str:
    body = template or (
        "Dear {name},\n\n"
        "Please complete your training assessment for {course} using the secure link below.\n\n"
        "{link}\n\n"
        "Link expiry: {expiry}\n\n"
        "Regards,\nAziro L&D Team"
    )
    return (
        body.replace("{name}", candidate_name)
        .replace("{course}", course_name)
        .replace("{expiry}", expiry_label or "No Expiry")
        .replace("{link}", test_link)
    )


def send_assignment_email(
    *,
    candidate_name: str,
    candidate_email: str,
    course_name: str,
    test_link: str,
    expiry_label: str,
    custom_message: str,
) -> EmailResult:
    tenant_id = os.getenv("MICROSOFT_TENANT_ID")
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    sender_email = os.getenv("MICROSOFT_SENDER_EMAIL")

    if not all([tenant_id, client_id, client_secret, sender_email]):
        return EmailResult(
            status="skipped",
            error="Microsoft Graph email settings are not configured in environment variables.",
        )

    try:
        token_body = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://graph.microsoft.com/.default",
            }
        ).encode("utf-8")
        token_request = urllib.request.Request(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data=token_body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(token_request, timeout=20) as response:
            token_payload = json.loads(response.read().decode("utf-8"))
        access_token = token_payload["access_token"]

        message = {
            "message": {
                "subject": f"Aziro Assessment: {course_name}",
                "body": {
                    "contentType": "Text",
                    "content": _render_message(
                        custom_message,
                        candidate_name,
                        course_name,
                        expiry_label,
                        test_link,
                    ),
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": candidate_email,
                            "name": candidate_name,
                        }
                    }
                ],
            },
            "saveToSentItems": "true",
        }

        send_request = urllib.request.Request(
            f"https://graph.microsoft.com/v1.0/users/{urllib.parse.quote(sender_email)}/sendMail",
            data=json.dumps(message).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(send_request, timeout=20):
            pass

        return EmailResult(status="sent")
    except Exception as exc:
        return EmailResult(status="failed", error=str(exc))
