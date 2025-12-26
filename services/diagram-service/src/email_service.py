"""Email notification service for diagram comments and mentions."""
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import aiosmtplib

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        """Initialize email service with SMTP configuration from environment."""
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
        self.from_email = os.getenv("FROM_EMAIL", "noreply@autograph.com")
        self.app_url = os.getenv("APP_URL", "http://localhost:3000")

        # Email sending can be disabled for testing
        self.enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"

    async def send_mention_notification(
        self,
        to_email: str,
        to_name: str,
        commenter_name: str,
        comment_content: str,
        diagram_id: str,
        diagram_name: str,
        comment_id: str
    ) -> bool:
        """
        Send email notification when a user is mentioned in a comment.

        Args:
            to_email: Recipient email address
            to_name: Recipient's name
            commenter_name: Name of user who wrote the comment
            comment_content: Content of the comment
            diagram_id: ID of the diagram
            diagram_name: Name of the diagram
            comment_id: ID of the comment

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email disabled, skipping mention notification to {to_email}")
            return True

        subject = f"{commenter_name} mentioned you in a comment"

        # Create HTML email body
        html_body = self._create_mention_email_html(
            to_name=to_name,
            commenter_name=commenter_name,
            comment_content=comment_content,
            diagram_name=diagram_name,
            diagram_id=diagram_id,
            comment_id=comment_id
        )

        # Create plain text fallback
        text_body = f"""
Hi {to_name},

{commenter_name} mentioned you in a comment on "{diagram_name}":

"{comment_content}"

View the comment: {self.app_url}/canvas/{diagram_id}#comment-{comment_id}

---
AutoGraph - Collaborative Diagramming
        """.strip()

        return await self._send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body
        )

    def _create_mention_email_html(
        self,
        to_name: str,
        commenter_name: str,
        comment_content: str,
        diagram_name: str,
        diagram_id: str,
        comment_id: str
    ) -> str:
        """Create HTML email body for mention notification."""
        comment_url = f"{self.app_url}/canvas/{diagram_id}#comment-{comment_id}"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            color: #1f2937;
            font-size: 24px;
        }}
        .mention-badge {{
            display: inline-block;
            background-color: #dbeafe;
            color: #1e40af;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 20px;
        }}
        .comment-box {{
            background-color: #f9fafb;
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .commenter {{
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 10px;
        }}
        .comment-content {{
            color: #4b5563;
            line-height: 1.8;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .diagram-info {{
            background-color: #f3f4f6;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .diagram-name {{
            font-weight: 600;
            color: #1f2937;
        }}
        .button {{
            display: inline-block;
            background-color: #3b82f6;
            color: #ffffff !important;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: 500;
            margin-top: 20px;
        }}
        .button:hover {{
            background-color: #2563eb;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 14px;
            color: #6b7280;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💬 New Mention</h1>
        </div>

        <p>Hi {to_name},</p>

        <div class="mention-badge">@mention</div>

        <p><strong>{commenter_name}</strong> mentioned you in a comment:</p>

        <div class="comment-box">
            <div class="commenter">{commenter_name}</div>
            <div class="comment-content">{comment_content}</div>
        </div>

        <div class="diagram-info">
            <div style="color: #6b7280; font-size: 14px; margin-bottom: 4px;">On diagram:</div>
            <div class="diagram-name">{diagram_name}</div>
        </div>

        <a href="{comment_url}" class="button">View Comment</a>

        <div class="footer">
            <p>You received this email because you were mentioned in a comment on AutoGraph.</p>
            <p>AutoGraph - Collaborative Diagramming</p>
        </div>
    </div>
</body>
</html>
        """.strip()

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            text_body: Plain text email body
            html_body: Optional HTML email body

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = self.from_email
            message['To'] = to_email
            message['Subject'] = subject

            # Add text part
            text_part = MIMEText(text_body, 'plain')
            message.attach(text_part)

            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user if self.smtp_user else None,
                password=self.smtp_password if self.smtp_password else None,
                use_tls=self.smtp_use_tls
            )

            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


# Global instance
_email_service = None


def get_email_service() -> EmailService:
    """Get or create the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
