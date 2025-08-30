from django.core.management.base import BaseCommand
from lostfound.models import SystemSettings

class Command(BaseCommand):
    help = 'Create default system settings for the lost and found system'

    def handle(self, *args, **options):
        default_settings = [
            {
                'key': 'lost_match_threshold',
                'value': '0.6',
                'description': 'Similarity threshold for lost item matches (0.0-1.0)'
            },
            {
                'key': 'found_match_threshold',
                'value': '0.5',
                'description': 'Similarity threshold for found item matches (0.0-1.0)'
            },
            {
                'key': 'match_days_back',
                'value': '7',
                'description': 'Number of days to look back for potential matches'
            },
            {
                'key': 'task_match_threshold',
                'value': '0.7',
                'description': 'Similarity threshold for background task matches (0.0-1.0)'
            },
            {
                'key': 'task_match_days_back',
                'value': '7',
                'description': 'Number of days back for background matching tasks'
            },
            {
                'key': 'generate_match_threshold',
                'value': '0.5',
                'description': 'Similarity threshold for manual match generation (0.0-1.0)'
            },
            {
                'key': 'print_match_threshold',
                'value': '0.5',
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