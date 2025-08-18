# emails/lost_items.py
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_report_acknowledgment(lost_item):
    """
    Send an HTML acknowledgment email with tracking ID and item details.
    """
    subject = "Lost Item Report Confirmation - Parklands Sports Club"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [lost_item.reporter_email]

    text_content = (
        f"Hello {lost_item.owner_name},\n\n"
        "Thank you for reporting your lost item at Parklands Sports Club.\n"
        "Your report has been received and is being processed.\n\n"
        f"Tracking ID: {lost_item.tracking_id}\n\n"
        "Report Details:\n"
        f"- Item Name: {lost_item.item_name}\n"
        f"- Description: {lost_item.description}\n"
        f"- Place Lost: {lost_item.place_lost}\n"
        f"- Reporter Member ID: {lost_item.reporter_member_id}\n"
        f"- Reporter Phone: {lost_item.reporter_phone}\n"
        f"- Reporter Email: {lost_item.reporter_email}\n\n"
        "Please keep this ID safe for future reference.\n"
        "If you find a match, please visit the club reception.\n\n"
        "Best regards,\nParklands Sports Club\nPowered by PSC ICT"
    )

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 10px; padding: 20px;">
          <div style="text-align: center;">
            <img src="https://yourclubdomain.com/static/images/logo.png" alt="Parklands Sports Club" style="max-height: 80px; margin-bottom: 20px;">
          </div>
          <h2 style="color: #2b6cb0;">Lost Item Report Confirmation</h2>
          <p>Hello <strong>{lost_item.owner_name}</strong>,</p>
          <p>Thank you for reporting your lost item at <strong>Parklands Sports Club</strong>.</p>
          <p>Your report has been received and is being processed.</p>
          <p><strong>Tracking ID:</strong> {lost_item.tracking_id}</p>

          <h3>Report Details</h3>
          <ul>
            <li><strong>Item Name:</strong> {lost_item.item_name}</li>
            <li><strong>Description:</strong> {lost_item.description}</li>
            <li><strong>Place Lost:</strong> {lost_item.place_lost}</li>
            <li><strong>Reporter Member No:</strong> {lost_item.reporter_member_id}</li>
            <li><strong>Reporter Phone:</strong> {lost_item.reporter_phone}</li>
            <li><strong>Reporter Email:</strong> {lost_item.reporter_email}</li>
          </ul>

          <p>Please keep this tracking ID safe for future reference.</p>
          <p>If a match is found, we will email you with further instructions.</p>

          <hr style="margin: 30px 0;">
          <p style="font-size: 12px; text-align: center; color: #888;">
            Powered by PSC ICT | Parklands Sports Club
          </p>
        </div>
      </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_match_notification(lost_item, matches):
    """
    Send an HTML email if there are potential matches for a reported lost item.
    """
    subject = "Potential Match Found - Parklands Sports Club"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [lost_item.reporter_email]

    text_content = (
        f"Hello {lost_item.owner_name},\n\n"
        f"We have found {len(matches)} potential match(es) for your lost item (Tracking ID: {lost_item.tracking_id}).\n"
        "Details:\n"
    )
    for match in matches:
        found_item = match["found_item"]
        score = match["match_score"]
        text_content += f"- {found_item['item_name']} (Match Score: {score:.0%})\n"
        if match.get("match_reasons"):
            text_content += f"  Reasons: {', '.join(match['match_reasons'])}\n"

    text_content += (
        "\nPlease log in to our system or visit the club reception to review matches.\n"
        "Best regards,\nParklands Sports Club\nPowered by PSC ICT"
    )

    # Build HTML
    match_items_html = "".join([
        f"<li><strong>{m['found_item']['item_name']}</strong> (Match Score: {m['match_score']:.0%})<br>"
        f"Reasons: {', '.join(m.get('match_reasons', []))}</li>"
        for m in matches
    ])

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 10px; padding: 20px;">
          <div style="text-align: center;">
            <img src="https://yourclubdomain.com/static/images/logo.png" alt="Parklands Sports Club" style="max-height: 80px; margin-bottom: 20px;">
          </div>
          <h2 style="color: #d9534f;">Potential Match Found</h2>
          <p>Hello <strong>{lost_item.owner_name}</strong>,</p>
          <p>We have found <strong>{len(matches)}</strong> potential match(es) for your lost item report.</p>
          <p><strong>Tracking ID:</strong> {lost_item.tracking_id}</p>

          <h3>Matches</h3>
          <ul>
            {match_items_html}
          </ul>

          <p>Please visit the <strong>Club Reception</strong> to review the matches.</p>

          <hr style="margin: 30px 0;">
          <p style="font-size: 12px; text-align: center; color: #888;">
            Powered by PSC ICT | Parklands Sports Club
          </p>
        </div>
      </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
