from django.core.management.base import BaseCommand
from lostfound.models import SystemSettings

class Command(BaseCommand):
    help = 'Create default system settings for the lost and found system'

    def handle(self, *args, **options):
        default_settings = [
            {
                'key': 'lost_match_threshold',
                'value': '0.4',
                'description': 'Similarity threshold for lost item matches (0.0-1.0) - Lower for better matching'
            },
            {
                'key': 'found_match_threshold',
                'value': '0.35',
                'description': 'Similarity threshold for found item matches (0.0-1.0) - Lower for better matching'
            },
            {
                'key': 'match_days_back',
                'value': '14',
                'description': 'Number of days to look back for potential matches - Extended window'
            },
            {
                'key': 'task_match_threshold',
                'value': '0.5',
                'description': 'Similarity threshold for background task matches (0.0-1.0)'
            },
            {
                'key': 'task_match_days_back',
                'value': '14',
                'description': 'Number of days back for background matching tasks - Extended window'
            },
            {
                'key': 'generate_match_threshold',
                'value': '0.3',
                'description': 'Similarity threshold for manual match generation (0.0-1.0) - Lower for comprehensive results'
            },
            {
                'key': 'print_match_threshold',
                'value': '0.4',
                'description': 'Similarity threshold for printing match receipts (0.0-1.0)'
            },
            {
                'key': 'auto_print_lost_receipt',
                'value': 'true',
                'description': 'Automatically print receipts when lost items are reported (true/false)'
            },
            {
                'key': 'auto_print_found_receipt',
                'value': 'true',
                'description': 'Automatically print receipts when found items are reported (true/false)'
            },
            {
                'key': 'email_notifications_enabled',
                'value': 'true',
                'description': 'Enable email notifications for matches (true/false)'
            },
            {
                'key': 'max_image_size_mb',
                'value': '5',
                'description': 'Maximum image file size in MB for uploads'
            },
            {
                'key': 'acknowledgment_email_subject',
                'value': 'Lost Item Report Confirmation - Parklands Sports Club',
                'description': 'Subject line for lost item acknowledgment emails'
            },
            {
                'key': 'acknowledgment_email_template',
                'value': '''Hello {owner_name},

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
Powered by PSC ICT''',
                'description': 'Template for lost item acknowledgment emails (supports placeholders)'
            },
            {
                'key': 'match_notification_email_subject',
                'value': 'Potential Match Found - Parklands Sports Club',
                'description': 'Subject line for match notification emails'
            },
            {
                'key': 'match_notification_email_template',
                'value': '''Hello {owner_name},

We have found {match_count} potential match(es) for your lost item (Tracking ID: {tracking_id}).

{match_details}

Please log in to our system or visit the club reception to review matches.

Best regards,
Parklands Sports Club
Powered by PSC ICT''',
                'description': 'Template for match notification emails (supports placeholders)'
            },
            {
                'key': 'max_auto_emails_per_day',
                'value': '50',
                'description': 'Maximum number of auto-sent emails per day'
            },
            {
                'key': 'max_auto_emails_per_item',
                'value': '3',
                'description': 'Maximum number of auto-sent emails per lost item'
            }
        ]

        created_count = 0
        updated_count = 0

        for setting_data in default_settings:
            setting, created = SystemSettings.objects.get_or_create(
                key=setting_data['key'],
                defaults={
                    'value': setting_data['value'],
                    'description': setting_data['description']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created setting: {setting.key} = {setting.value}')
                )
            else:
                # Update description if it has changed
                if setting.description != setting_data['description']:
                    setting.description = setting_data['description']
                    setting.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated description for: {setting.key}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {created_count + updated_count} settings '
                f'({created_count} created, {updated_count} updated)'
            )
        )