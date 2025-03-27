# Generated by Django 4.2 on 2025-03-26 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("signals", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="seasonalsignal",
            name="magic_number",
            field=models.IntegerField(
                error_messages={"unique": "Сигнал с таким Magic Number уже существует"},
                unique=True,
            ),
        ),
    ]
