import os
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Use mock email service for development
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@novasocial.com')
        self.enabled = True  # Always enabled for mock service
        logger.info("Using mock email service for development")

    def generate_verification_code(self, length: int = 6) -> str:
        """Generate a secure verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    def send_password_reset_email(self, to_email: str, verification_code: str, user_name: str = "User") -> bool:
        """Send password reset email with verification code"""
        if not self.enabled:
            logger.warning(f"Email service disabled. Would send password reset code {verification_code} to {to_email}")
            return True  # Return True in development mode
        
        subject = "Reset Your NovaSocial Password"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #1DA1F2; margin: 0;">NovaSocial</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #333; margin-bottom: 20px;">Password Reset Request</h2>
                    
                    <p style="color: #555; font-size: 16px; line-height: 1.6;">
                        Hi {user_name},
                    </p>
                    
                    <p style="color: #555; font-size: 16px; line-height: 1.6;">
                        We received a request to reset your password for your NovaSocial account. 
                        Use the verification code below to reset your password:
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="background: #1DA1F2; color: white; padding: 20px; border-radius: 8px; font-size: 32px; font-weight: bold; letter-spacing: 4px;">
                            {verification_code}
                        </div>
                    </div>
                    
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        This code will expire in 10 minutes for your security.
                    </p>
                    
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        If you didn't request this password reset, please ignore this email. 
                        Your password will remain unchanged.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #888; font-size: 12px;">
                        This is an automated email from NovaSocial. Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)
    
    def send_account_deletion_confirmation(self, to_email: str, user_name: str, deletion_date: datetime) -> bool:
        """Send account deletion confirmation email"""
        if not self.enabled:
            logger.warning(f"Email service disabled. Would send account deletion confirmation to {to_email}")
            return True
        
        subject = "Your NovaSocial Account Will Be Deleted"
        
        formatted_date = deletion_date.strftime("%B %d, %Y at %I:%M %p UTC")
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #1DA1F2; margin: 0;">NovaSocial</h1>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 30px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="color: #856404; margin-bottom: 20px;">Account Deletion Scheduled</h2>
                    
                    <p style="color: #856404; font-size: 16px; line-height: 1.6;">
                        Hi {user_name},
                    </p>
                    
                    <p style="color: #856404; font-size: 16px; line-height: 1.6;">
                        Your NovaSocial account is scheduled for permanent deletion on <strong>{formatted_date}</strong>.
                    </p>
                    
                    <p style="color: #856404; font-size: 16px; line-height: 1.6;">
                        You have until this date to reactivate your account if you change your mind. 
                        After this date, all your data will be permanently removed and cannot be recovered.
                    </p>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h3 style="color: #333; margin-bottom: 15px;">What happens next:</h3>
                    <ul style="color: #555; line-height: 1.8;">
                        <li>Your profile will be hidden from other users immediately</li>
                        <li>Your posts and content will be removed</li>
                        <li>Your account data will be permanently deleted on the scheduled date</li>
                        <li>You can reactivate anytime before the deletion date by logging in</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #888; font-size: 12px;">
                        This is an automated email from NovaSocial. Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)
    
    def send_password_change_confirmation(self, to_email: str, user_name: str) -> bool:
        """Send password change confirmation email"""
        if not self.enabled:
            logger.warning(f"Email service disabled. Would send password change confirmation to {to_email}")
            return True
        
        subject = "Your NovaSocial Password Has Been Changed"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #1DA1F2; margin: 0;">NovaSocial</h1>
                </div>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #155724; margin-bottom: 20px;">Password Successfully Changed</h2>
                    
                    <p style="color: #155724; font-size: 16px; line-height: 1.6;">
                        Hi {user_name},
                    </p>
                    
                    <p style="color: #155724; font-size: 16px; line-height: 1.6;">
                        Your NovaSocial account password has been successfully changed at {datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")}.
                    </p>
                    
                    <p style="color: #155724; font-size: 16px; line-height: 1.6;">
                        If you did not make this change, please contact our support team immediately 
                        and change your password as soon as possible.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #888; font-size: 12px;">
                        This is an automated email from NovaSocial. Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Mock email sending for development"""
        try:
            logger.info(f"MOCK EMAIL SENT to {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Content preview: {html_content[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Error in mock email service: {str(e)}")
            return False

# Global email service instance
email_service = EmailService()