"""
Email notification module using Azure Communication Services.
Sends email alerts when the Odoo platform is offline or in error state.
"""
import os
from azure.communication.email import EmailClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_email_client() -> EmailClient:
    """Create and return an Azure EmailClient instance."""
    connection_string = os.getenv("AZURE_EMAIL_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("AZURE_EMAIL_CONNECTION_STRING not set in environment")
    return EmailClient.from_connection_string(connection_string)


def get_recipients() -> list[str]:
    """Get list of notification recipients from environment."""
    emails = os.getenv("NOTIFICATION_EMAILS", "")
    return [email.strip() for email in emails.split(",") if email.strip()]


def send_notification(subject: str, body_text: str, body_html: str = None, recipients_override: list[str] = None) -> str:
    """
    Send an email notification to all configured recipients.
    
    Args:
        subject: Email subject line
        body_text: Plain text body
        body_html: Optional HTML body (defaults to simple HTML wrapper)
        recipients_override: Optional list of recipients to override env config
    
    Returns:
        Message ID from Azure Email Service
    
    Raises:
        Exception: If email sending fails
    """
    sender_address = os.getenv("EMAIL_SENDER_ADDRESS")
    if not sender_address:
        raise ValueError("EMAIL_SENDER_ADDRESS not set in environment")
    
    recipients = recipients_override if recipients_override else get_recipients()
    if not recipients:
        raise ValueError("NOTIFICATION_EMAILS not set or empty in environment")
    
    # Ensure body_html is a proper string
    if body_html is None:
        body_html = f"""<html><body><p>{body_text}</p></body></html>"""
    
    # Ensure we have valid content strings
    if not subject or not isinstance(subject, str):
        raise ValueError("Subject must be a non-empty string")
    if not body_text or not isinstance(body_text, str):
        raise ValueError("body_text must be a non-empty string")
    
    client = get_email_client()
    
    message = {
        "senderAddress": sender_address,
        "recipients": {
            "to": [{"address": email} for email in recipients]
        },
        "content": {
            "subject": subject,
            "plainText": body_text,
            "html": body_html
        }
    }
    
    poller = client.begin_send(message)
    result = poller.result()
    # Handle both dict and object return types
    if isinstance(result, dict):
        return result.get("id", result.get("message_id", "sent"))
    return getattr(result, "message_id", "sent")


def send_odoo_alert(status: str, message: str, url: str, checked_at: str) -> str:
    """
    Send an Odoo health alert email.
    
    Args:
        status: Health status ("offline" or "error")
        message: Detailed message about the issue
        url: The monitored Odoo URL
        checked_at: Timestamp of the health check
    
    Returns:
        Message ID from Azure Email Service
    """
    subject = f"🚨 Odoo Platform Alert: {status.upper()}"
    
    body_text = f"""
Odoo Platform Health Alert

Status: {status.upper()}
URL: {url}
Checked At: {checked_at}

Details:
{message}

This is an automated alert from the Etihad Monitoring System.
"""
    
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background-color: #f44336; color: white; padding: 15px; border-radius: 5px;">
                <h1 style="margin: 0;">🚨 Odoo Platform Alert: {status.upper()}</h1>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd; margin-top: 10px; border-radius: 5px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Status:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; color: #f44336; font-weight: bold;">{status.upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>URL:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><a href="{url}">{url}</a></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Checked At:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{checked_at}</td>
                    </tr>
                </table>
                <div style="margin-top: 15px; padding: 15px; background-color: #fff3cd; border-radius: 5px;">
                    <strong>Details:</strong><br>
                    {message}
                </div>
            </div>
            <p style="color: #666; font-size: 12px; margin-top: 20px;">
                This is an automated alert from the Etihad Monitoring System.
            </p>
        </body>
    </html>
    """
    
    return send_notification(subject, body_text, body_html)


if __name__ == "__main__":
    # Test sending a notification
    print("Testing email notification...")
    try:
        msg_id = send_notification(
            subject="Test Email from Etihad Monitoring",
            body_text="This is a test email from the monitoring system."
        )
        print(f"Test email sent! Message ID: {msg_id}")
    except Exception as e:
        print(f"Error sending test email: {e}")
