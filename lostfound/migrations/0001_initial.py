# Generated by Django 5.2 on 2025-05-16 08:42

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FoundItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('card', 'Card'), ('item', 'Item')], max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('found', 'Found'), ('claimed', 'Claimed')], default='pending', max_length=10)),
                ('owner_name', models.CharField(blank=True, max_length=100, null=True)),
                ('date_reported', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('item_name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('card_last_four', models.CharField(blank=True, max_length=4, null=True)),
                ('place_found', models.CharField(max_length=200)),
                ('finder_phone', models.CharField(max_length=20)),
                ('finder_name', models.CharField(max_length=100)),
                ('reported_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='found_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LostItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('card', 'Card'), ('item', 'Item')], max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('found', 'Found'), ('claimed', 'Claimed')], default='pending', max_length=10)),
                ('owner_name', models.CharField(blank=True, max_length=100, null=True)),
                ('date_reported', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('item_name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('card_last_four', models.CharField(blank=True, max_length=4, null=True)),
                ('place_lost', models.CharField(max_length=200)),
                ('reporter_phone', models.CharField(max_length=20)),
                ('reporter_member_id', models.CharField(blank=True, max_length=20, null=True)),
                ('reported_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lost_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PickupLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('picked_by_member_id', models.CharField(max_length=20)),
                ('picked_by_name', models.CharField(max_length=100)),
                ('picked_by_phone', models.CharField(max_length=20)),
                ('pickup_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pickup_logs', to='lostfound.founditem')),
                ('verified_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
