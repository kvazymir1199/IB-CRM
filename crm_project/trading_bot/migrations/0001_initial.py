# Generated by Django 5.2 on 2025-04-07 15:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('signals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BotState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_running', models.BooleanField(default=False)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Bot state',
                'verbose_name_plural': 'Bot state',
            },
        ),
        migrations.CreateModel(
            name='BotSeasonalSignal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_date', models.DateTimeField(help_text='Date and time of entry into the position', verbose_name='Entry date')),
                ('exit_date', models.DateTimeField(help_text='Date and time of exit from the position', verbose_name='Exit date')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('status', models.CharField(choices=[('awaiting', 'Awaiting'), ('open', 'Trade Open'), ('close', 'Trade Close')], default='awaiting', max_length=10)),
                ('order_id', models.IntegerField(blank=True, help_text='Order ID in Interactive Brokers', null=True, verbose_name='Order ID')),
                ('stop_order_id', models.IntegerField(blank=True, help_text='Stop order ID in Interactive Brokers', null=True, verbose_name='Stop order ID')),
                ('signal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bot_signals', to='signals.seasonalsignal', verbose_name='Seasonal signal')),
            ],
            options={
                'verbose_name': 'Trading signal',
                'verbose_name_plural': 'Trading signals',
                'ordering': ['-created_at'],
            },
        ),
    ]
