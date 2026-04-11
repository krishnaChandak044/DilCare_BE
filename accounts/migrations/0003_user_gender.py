from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_usersettings_userdevice"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="gender",
            field=models.CharField(
                blank=True,
                default="",
                help_text="male, female, other, or prefer_not_say",
                max_length=20,
            ),
        ),
    ]
