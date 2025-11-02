import requests
from flask import current_app, url_for


def send_password_reset_email(user_email: str, reset_token: str) -> bool:
    """
    Send a password reset email to the user.
    """
    try:
        api_key = current_app.config["MAILGUN_API_KEY"]
        domain = current_app.config["MAILGUN_DOMAIN"]
        from_email = current_app.config["MAILGUN_FROM_EMAIL"]

        if not api_key:
            current_app.logger.error("MAILGUN_API_KEY not configured")
            return False

        reset_url = url_for("web.reset_password", token=reset_token, _external=True)

        # Email content
        subject = "Reset Your Briefen Password"
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #111827;
            background-color: #fafbfc;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 40px auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: #0284c7;
            padding: 32px;
            text-align: center;
        }}
        .logo {{
            font-size: 32px;
            font-weight: 800;
            color: white;
        }}
        .content {{
            padding: 40px 32px;
        }}
        h1 {{
            color: #111827;
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 16px 0;
        }}
        p {{
            color: #4b5563;
            margin: 0 0 24px 0;
        }}
        .button {{
            display: inline-block;
            padding: 14px 32px;
            background: #0284c7;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin: 16px 0;
        }}
        .button:hover {{
            background: #0369a1;
        }}
        .footer {{
            background: #f9fafb;
            padding: 24px 32px;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
        }}
        .warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 16px;
            margin: 24px 0;
            border-radius: 4px;
        }}
        .code {{
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">✨ Briefen</div>
        </div>

        <div class="content">
            <h1>Reset Your Password</h1>
            <p>Hi there,</p>
            <p>We received a request to reset your password for your Briefen account. Click the button below to create a new password:</p>

            <center>
                <a href="{reset_url}" class="button">Reset Password</a>
            </center>

            <p>Or copy and paste this link into your browser:</p>
            <p class="code">{reset_url}</p>

            <div class="warning">
                <strong>⚠️ Security Notice:</strong><br>
                This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.
            </div>

            <p>If you have any questions, feel free to reach out to us.</p>
            <p>Best regards,<br>The Briefen Team</p>
        </div>

        <div class="footer">
            <p>Briefen - AI that makes your links speak</p>
            <p>You received this email because a password reset was requested for your account.</p>
        </div>
    </div>
</body>
</html>
        """

        text_body = f"""
Reset Your Password

Hi there,

We received a request to reset your password for your Briefen account.

Click the link below to create a new password:
{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, you can safely ignore this email.

Best regards,
The Briefen Team

---
Briefen - AI that makes your links speak
        """

        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": from_email,
                "to": user_email,
                "subject": subject,
                "text": text_body,
                "html": html_body,
            },
            timeout=10,
        )

        try:
            if response.status_code == 200:
                current_app.logger.info(f"Password reset email sent to {user_email}")
                return True
            else:
                current_app.logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
        finally:
            response.close()

    except Exception as e:
        current_app.logger.error(f"Error sending password reset email: {str(e)}")
        return False
