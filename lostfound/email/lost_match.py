# emails/lost_items.py
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from ..models import SystemSettings, EmailLog

def send_report_acknowledgment(lost_item):
    """
    Send a customizable acknowledgment email with tracking ID and item details.
    """
    # Check if emails are enabled
    if SystemSettings.get_setting('email_notifications_enabled', 'true').lower() != 'true':
        return False, "Email notifications disabled"

    # Check limits
    can_send, reason = EmailLog.can_send_email('acknowledgment', lost_item.reporter_email, lost_item)
    if not can_send:
        return False, reason

    subject = SystemSettings.get_setting('acknowledgment_email_subject', 'Lost Item Report Confirmation - Parklands Sports Club')
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [lost_item.reporter_email]

    # Get template and replace placeholders
    template = SystemSettings.get_setting('acknowledgment_email_template', '')
    if not template:
        # Fallback to default
        template = """Hello {owner_name},

Thank you for reporting your lost item at Parklands Sports Club.
Your report has been received and is being processed.

Tracking ID: {tracking_id}

Report Details:
- Item Name: {item_name}
- Description: {description}
- Place Lost: {place_lost}
- Reporter Member ID: {reporter_member_id}
- Reporter Phone: {reporter_phone}
- Reporter Email: {reporter_email}

Please keep this ID safe for future reference.
If you find a match, please visit the club reception.

Best regards,
Parklands Sports Club
Powered by PSC ICT"""

    # Replace placeholders
    text_content = template.format(
        owner_name=lost_item.owner_name or 'Valued Member',
        tracking_id=lost_item.tracking_id,
        item_name=lost_item.item_name or lost_item.card_last_four or 'N/A',
        description=lost_item.description or 'N/A',
        place_lost=lost_item.place_lost or 'N/A',
        reporter_member_id=lost_item.reporter_member_id or 'N/A',
        reporter_phone=lost_item.reporter_phone or 'N/A',
        reporter_email=lost_item.reporter_email
    )

    # Simple HTML version
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 10px; padding: 20px;">
          <h2 style="color: #2b6cb0;">Lost Item Report Confirmation</h2>
          <pre style="white-space: pre-wrap;">{text_content}</pre>
          <hr style="margin: 30px 0;">
          <p style="font-size: 12px; text-align: center; color: #888;">
            Powered by PSC ICT | Parklands Sports Club
          </p>
        </div>
      </body>
    </html>
    """

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        # Log the email
        EmailLog.objects.create(
            email_type='acknowledgment',
            recipient=lost_item.reporter_email,
            lost_item=lost_item,
            subject=subject
        )
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)


def send_match_notification(lost_item, matches):
    """
    Send a customizable email if there are potential matches for a reported lost item.
    """
    # Check if emails are enabled
    if SystemSettings.get_setting('email_notifications_enabled', 'true').lower() != 'true':
        return False, "Email notifications disabled"

    # Check limits
    can_send, reason = EmailLog.can_send_email('match_notification', lost_item.reporter_email, lost_item)
    if not can_send:
        return False, reason

    subject = SystemSettings.get_setting('match_notification_email_subject', 'Potential Match Found - Parklands Sports Club')
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [lost_item.reporter_email]

    # Build match details
    match_details = ""
    for match in matches:
        found_item = match["found_item"]
        score = match["match_score"]
        match_details += f"- {found_item['item_name'] or found_item['card_last_four'] or 'Unknown'} (Match Score: {score:.0%})\n"
        if match.get("match_reasons"):
            match_details += f"  Reasons: {', '.join(match['match_reasons'])}\n"

    # Get template and replace placeholders
    template = SystemSettings.get_setting('match_notification_email_template', '')
    if not template:
        # Fallback to default
        template = """Hello {owner_name},

We have found {match_count} potential match(es) for your lost item (Tracking ID: {tracking_id}).

{match_details}

Please log in to our system or visit the club reception to review matches.

Best regards,
Parklands Sports Club
Powered by PSC ICT"""

    # Replace placeholders
    text_content = template.format(
        owner_name=lost_item.owner_name or 'Valued Member',
        match_count=len(matches),
        tracking_id=lost_item.tracking_id,
        match_details=match_details.strip()
    )

    # Simple HTML version
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 10px; padding: 20px;">
          <h2 style="color: #d9534f;">Potential Match Found</h2>
          <pre style="white-space: pre-wrap;">{text_content}</pre>
          <hr style="margin: 30px 0;">
          <p style="font-size: 12px; text-align: center; color: #888;">
            Powered by PSC ICT | Parklands Sports Club
          </p>
        </div>
      </body>
    </html>
    """

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        # Log the email
        EmailLog.objects.create(
            email_type='match_notification',
            recipient=lost_item.reporter_email,
            lost_item=lost_item,
            subject=subject
        )
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)
