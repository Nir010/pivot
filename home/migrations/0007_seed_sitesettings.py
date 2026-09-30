from django.db import migrations

SITE = {
    "site_name": "Pivot Risk Pvt. Ltd.",
    "tagline": "Risk management, actuarial and advisory services",
    "email": "info@pivotrisks.com",
    "phone": "+977 9843653691",
    "address": "Kupandole, Lalitpur, Nepal",
}

def seed_settings(apps, schema_editor):
    # Same get-or-create trick as the team/services seeds:
    SiteSettings = apps.get_model("home", "SiteSettings")
    SiteSettings.objects.get_or_create(pk=1, defaults=SITE)

def unseed_settings(apps, schema_editor):
    apps.get_model("home", "SiteSettings").objects.filter(pk=1).delete()

class Migration(migrations.Migration):
    dependencies = [
        ("home", "0006_remove_teammember_bio"),   # the CURRENT latest home migration
    ]
    operations = [
        migrations.RunPython(seed_settings, unseed_settings),
    ]