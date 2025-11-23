"""
Email Utility Functions
Handles sending transactional emails using Resend
"""

import os
import resend
from typing import Optional
from logger import setup_logger

logger = setup_logger(__name__)

# Initialize Resend
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@orla3.com")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
else:
    logger.warning("⚠️  RESEND_API_KEY not configured. Email sending will be skipped.")


def send_verification_email(to_email: str, verification_token: str) -> bool:
    """
    Send email verification link to user

    Args:
        to_email: Recipient email address
        verification_token: Unique verification token

    Returns:
        True if email sent successfully, False otherwise
    """
    if not RESEND_API_KEY:
        logger.warning(f"Skipping verification email to {to_email} (Resend not configured)")
        return False

    verification_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"

    try:
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Verify your Orla³ account",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #0f172a;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0f172a; padding: 40px 0;">
                    <tr>
                        <td align="center">
                            <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #1e293b 0%, #4c1d95 100%); border-radius: 16px; padding: 40px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);">
                                <!-- Header -->
                                <tr>
                                    <td align="center" style="padding-bottom: 30px;">
                                        <h1 style="margin: 0; font-size: 48px; font-weight: 900; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                                            ORLA³
                                        </h1>
                                        <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 14px;">Marketing Automation Suite</p>
                                    </td>
                                </tr>

                                <!-- Content -->
                                <tr>
                                    <td style="padding: 30px; background: rgba(255, 255, 255, 0.05); border-radius: 12px; backdrop-filter: blur(10px);">
                                        <h2 style="margin: 0 0 20px 0; color: #ffffff; font-size: 24px; font-weight: 700;">
                                            Welcome to Orla³!
                                        </h2>
                                        <p style="margin: 0 0 20px 0; color: #cbd5e1; font-size: 16px; line-height: 1.6;">
                                            Thank you for signing up. Please verify your email address to activate your account and start creating amazing content.
                                        </p>

                                        <!-- CTA Button -->
                                        <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                            <tr>
                                                <td align="center">
                                                    <a href="{verification_link}"
                                                       style="display: inline-block; padding: 16px 32px; background: linear-gradient(to right, #3b82f6, #8b5cf6); color: #ffffff; text-decoration: none; font-weight: 700; font-size: 16px; border-radius: 8px; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);">
                                                        Verify Email Address
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>

                                        <p style="margin: 20px 0 0 0; color: #94a3b8; font-size: 14px; line-height: 1.5;">
                                            This link will expire in 7 days. If you didn't create an account, you can safely ignore this email.
                                        </p>
                                    </td>
                                </tr>

                                <!-- Footer -->
                                <tr>
                                    <td align="center" style="padding-top: 30px;">
                                        <p style="margin: 0; color: #64748b; font-size: 12px;">
                                            © 2024 Orla³ Studio. All rights reserved.
                                        </p>
                                        <p style="margin: 8px 0 0 0; color: #64748b; font-size: 12px;">
                                            <a href="{FRONTEND_URL}" style="color: #60a5fa; text-decoration: none;">Visit Dashboard</a> |
                                            <a href="https://orla3.com" style="color: #60a5fa; text-decoration: none;">Learn More</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
        }

        response = resend.Emails.send(params)
        logger.info(f"✅ Verification email sent to {to_email} (ID: {response.get('id')})")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send verification email to {to_email}: {str(e)}")
        return False


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Send password reset link to user

    Args:
        to_email: Recipient email address
        reset_token: Unique reset token

    Returns:
        True if email sent successfully, False otherwise
    """
    if not RESEND_API_KEY:
        logger.warning(f"Skipping password reset email to {to_email} (Resend not configured)")
        return False

    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    try:
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Reset your Orla³ password",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #0f172a;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0f172a; padding: 40px 0;">
                    <tr>
                        <td align="center">
                            <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #1e293b 0%, #4c1d95 100%); border-radius: 16px; padding: 40px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);">
                                <!-- Header -->
                                <tr>
                                    <td align="center" style="padding-bottom: 30px;">
                                        <h1 style="margin: 0; font-size: 48px; font-weight: 900; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                                            ORLA³
                                        </h1>
                                        <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 14px;">Marketing Automation Suite</p>
                                    </td>
                                </tr>

                                <!-- Content -->
                                <tr>
                                    <td style="padding: 30px; background: rgba(255, 255, 255, 0.05); border-radius: 12px; backdrop-filter: blur(10px);">
                                        <h2 style="margin: 0 0 20px 0; color: #ffffff; font-size: 24px; font-weight: 700;">
                                            Reset Your Password
                                        </h2>
                                        <p style="margin: 0 0 20px 0; color: #cbd5e1; font-size: 16px; line-height: 1.6;">
                                            We received a request to reset your password. Click the button below to create a new password.
                                        </p>

                                        <!-- CTA Button -->
                                        <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                            <tr>
                                                <td align="center">
                                                    <a href="{reset_link}"
                                                       style="display: inline-block; padding: 16px 32px; background: linear-gradient(to right, #3b82f6, #8b5cf6); color: #ffffff; text-decoration: none; font-weight: 700; font-size: 16px; border-radius: 8px; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);">
                                                        Reset Password
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>

                                        <p style="margin: 20px 0 0 0; color: #94a3b8; font-size: 14px; line-height: 1.5;">
                                            This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.
                                        </p>
                                    </td>
                                </tr>

                                <!-- Security Notice -->
                                <tr>
                                    <td style="padding: 20px 30px; background: rgba(239, 68, 68, 0.1); border-radius: 8px; border-left: 4px solid #ef4444; margin-top: 20px;">
                                        <p style="margin: 0; color: #fca5a5; font-size: 13px; font-weight: 600;">
                                            Security Reminder
                                        </p>
                                        <p style="margin: 8px 0 0 0; color: #cbd5e1; font-size: 13px; line-height: 1.5;">
                                            Never share your password with anyone. Orla³ support will never ask for your password.
                                        </p>
                                    </td>
                                </tr>

                                <!-- Footer -->
                                <tr>
                                    <td align="center" style="padding-top: 30px;">
                                        <p style="margin: 0; color: #64748b; font-size: 12px;">
                                            © 2024 Orla³ Studio. All rights reserved.
                                        </p>
                                        <p style="margin: 8px 0 0 0; color: #64748b; font-size: 12px;">
                                            <a href="{FRONTEND_URL}" style="color: #60a5fa; text-decoration: none;">Visit Dashboard</a> |
                                            <a href="https://orla3.com" style="color: #60a5fa; text-decoration: none;">Learn More</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
        }

        response = resend.Emails.send(params)
        logger.info(f"✅ Password reset email sent to {to_email} (ID: {response.get('id')})")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send password reset email to {to_email}: {str(e)}")
        return False


def send_welcome_email(to_email: str, user_name: str) -> bool:
    """
    Send welcome email to newly verified user

    Args:
        to_email: Recipient email address
        user_name: User's name

    Returns:
        True if email sent successfully, False otherwise
    """
    if not RESEND_API_KEY:
        logger.warning(f"Skipping welcome email to {to_email} (Resend not configured)")
        return False

    try:
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Welcome to Orla³ - Let's create something amazing!",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #0f172a;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0f172a; padding: 40px 0;">
                    <tr>
                        <td align="center">
                            <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #1e293b 0%, #4c1d95 100%); border-radius: 16px; padding: 40px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);">
                                <!-- Header -->
                                <tr>
                                    <td align="center" style="padding-bottom: 30px;">
                                        <h1 style="margin: 0; font-size: 48px; font-weight: 900; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                                            ORLA³
                                        </h1>
                                        <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 14px;">Marketing Automation Suite</p>
                                    </td>
                                </tr>

                                <!-- Content -->
                                <tr>
                                    <td style="padding: 30px; background: rgba(255, 255, 255, 0.05); border-radius: 12px; backdrop-filter: blur(10px);">
                                        <h2 style="margin: 0 0 20px 0; color: #ffffff; font-size: 24px; font-weight: 700;">
                                            Welcome, {user_name}!
                                        </h2>
                                        <p style="margin: 0 0 20px 0; color: #cbd5e1; font-size: 16px; line-height: 1.6;">
                                            Your account is now active! You're ready to start creating amazing content with AI-powered tools.
                                        </p>

                                        <!-- Features -->
                                        <div style="margin: 30px 0;">
                                            <p style="margin: 0 0 15px 0; color: #60a5fa; font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                                                What you can do:
                                            </p>
                                            <ul style="margin: 0; padding: 0; list-style: none;">
                                                <li style="padding: 10px 0; color: #cbd5e1; font-size: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                                    ✍️ <strong>Blog Writer</strong> - AI-powered long-form content
                                                </li>
                                                <li style="padding: 10px 0; color: #cbd5e1; font-size: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                                    🎨 <strong>Carousel Maker</strong> - Engaging social carousels
                                                </li>
                                                <li style="padding: 10px 0; color: #cbd5e1; font-size: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                                    📱 <strong>Social Manager</strong> - Unified social posting
                                                </li>
                                                <li style="padding: 10px 0; color: #cbd5e1; font-size: 15px;">
                                                    🎯 <strong>Brand Voice</strong> - Consistent messaging
                                                </li>
                                            </ul>
                                        </div>

                                        <!-- CTA Button -->
                                        <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                            <tr>
                                                <td align="center">
                                                    <a href="{FRONTEND_URL}/dashboard"
                                                       style="display: inline-block; padding: 16px 32px; background: linear-gradient(to right, #3b82f6, #8b5cf6); color: #ffffff; text-decoration: none; font-weight: 700; font-size: 16px; border-radius: 8px; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);">
                                                        Go to Dashboard
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>

                                <!-- Footer -->
                                <tr>
                                    <td align="center" style="padding-top: 30px;">
                                        <p style="margin: 0; color: #64748b; font-size: 12px;">
                                            © 2024 Orla³ Studio. All rights reserved.
                                        </p>
                                        <p style="margin: 8px 0 0 0; color: #64748b; font-size: 12px;">
                                            Need help? <a href="mailto:support@orla3.com" style="color: #60a5fa; text-decoration: none;">Contact Support</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
        }

        response = resend.Emails.send(params)
        logger.info(f"✅ Welcome email sent to {to_email} (ID: {response.get('id')})")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send welcome email to {to_email}: {str(e)}")
        return False


def send_team_invitation_email(to_email: str, invitation_token: str, organization_name: str, inviter_name: str, role: str) -> bool:
    """
    Send team invitation email to non-existing user

    Args:
        to_email: Recipient email address
        invitation_token: Unique invitation token
        organization_name: Name of the organization
        inviter_name: Name of the person who sent the invite
        role: The role being offered (viewer, member, admin)

    Returns:
        True if email sent successfully, False otherwise
    """
    if not RESEND_API_KEY:
        logger.warning(f"Skipping team invitation email to {to_email} (Resend not configured)")
        return False

    invitation_link = f"{FRONTEND_URL}/invite/accept?token={invitation_token}"

    role_descriptions = {
        'viewer': 'View content and analytics',
        'member': 'Create and manage content',
        'admin': 'Full access including team management'
    }
    role_description = role_descriptions.get(role, 'Access to the platform')

    try:
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"You're invited to join {organization_name} on Orla³",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #0f172a;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0f172a; padding: 40px 0;">
                    <tr>
                        <td align="center">
                            <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #1e293b 0%, #4c1d95 100%); border-radius: 16px; padding: 40px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);">
                                <!-- Header -->
                                <tr>
                                    <td align="center" style="padding-bottom: 30px;">
                                        <h1 style="margin: 0; font-size: 48px; font-weight: 900; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                                            ORLA³
                                        </h1>
                                        <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 14px;">Marketing Automation Suite</p>
                                    </td>
                                </tr>

                                <!-- Content -->
                                <tr>
                                    <td style="padding: 30px; background: rgba(255, 255, 255, 0.05); border-radius: 12px; backdrop-filter: blur(10px);">
                                        <h2 style="margin: 0 0 20px 0; color: #ffffff; font-size: 24px; font-weight: 700;">
                                            You're Invited!
                                        </h2>
                                        <p style="margin: 0 0 20px 0; color: #cbd5e1; font-size: 16px; line-height: 1.6;">
                                            <strong>{inviter_name}</strong> has invited you to join <strong>{organization_name}</strong> on Orla³.
                                        </p>

                                        <!-- Role Info -->
                                        <div style="margin: 20px 0; padding: 16px; background: rgba(59, 130, 246, 0.1); border-radius: 8px; border-left: 4px solid #3b82f6;">
                                            <p style="margin: 0; color: #60a5fa; font-size: 14px; font-weight: 600;">
                                                Your Role: {role.capitalize()}
                                            </p>
                                            <p style="margin: 8px 0 0 0; color: #cbd5e1; font-size: 14px;">
                                                {role_description}
                                            </p>
                                        </div>

                                        <!-- CTA Button -->
                                        <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                            <tr>
                                                <td align="center">
                                                    <a href="{invitation_link}"
                                                       style="display: inline-block; padding: 16px 32px; background: linear-gradient(to right, #3b82f6, #8b5cf6); color: #ffffff; text-decoration: none; font-weight: 700; font-size: 16px; border-radius: 8px; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);">
                                                        Accept Invitation
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>

                                        <p style="margin: 20px 0 0 0; color: #94a3b8; font-size: 14px; line-height: 1.5;">
                                            This invitation expires in 7 days. If you didn't expect this invitation, you can safely ignore this email.
                                        </p>
                                    </td>
                                </tr>

                                <!-- Footer -->
                                <tr>
                                    <td align="center" style="padding-top: 30px;">
                                        <p style="margin: 0; color: #64748b; font-size: 12px;">
                                            © 2024 Orla³ Studio. All rights reserved.
                                        </p>
                                        <p style="margin: 8px 0 0 0; color: #64748b; font-size: 12px;">
                                            <a href="https://orla3.com" style="color: #60a5fa; text-decoration: none;">Learn More</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
        }

        response = resend.Emails.send(params)
        logger.info(f"✅ Team invitation email sent to {to_email} (ID: {response.get('id')})")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send team invitation email to {to_email}: {str(e)}")
        return False
