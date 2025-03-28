# Generated by Django 4.2 on 2025-03-23 13:56

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SeasonalSignal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("magic_number", models.IntegerField(unique=True)),
                ("symbol", models.CharField(max_length=20)),
                (
                    "month",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(12),
                        ]
                    ),
                ),
                ("stoploss", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "stoploss_type",
                    models.CharField(
                        choices=[("POINTS", "Points"), ("PERCENTAGE", "Percentage")],
                        default="POINTS",
                        max_length=10,
                    ),
                ),
                ("risk", models.DecimalField(decimal_places=2, max_digits=5)),
                (
                    "direction",
                    models.CharField(
                        choices=[("LONG", "Long"), ("SHORT", "Short")],
                        default="LONG",
                        max_length=5,
                    ),
                ),
                (
                    "entry_month",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(12),
                        ]
                    ),
                ),
                (
                    "entry_day",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(31),
                        ]
                    ),
                ),
                (
                    "takeprofit_month",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(12),
                        ]
                    ),
                ),
                (
                    "takeprofit_day",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(31),
                        ]
                    ),
                ),
                ("open_time", models.TimeField()),
                ("close_time", models.TimeField()),
            ],
            options={
                "ordering": ["-id"],
                "abstract": False,
            },
        ),
    ]
