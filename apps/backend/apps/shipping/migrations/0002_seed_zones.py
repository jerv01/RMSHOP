from django.db import migrations

INITIAL_ZONES = [
    ("Cali", 5000),
    ("Palmira", 10000),
    ("Jamundí", 10000),
    ("Yumbo", 10000),
]


def seed_zones(apps, schema_editor):
    ShippingZone = apps.get_model("shipping", "ShippingZone")
    for municipality, fee in INITIAL_ZONES:
        ShippingZone.objects.get_or_create(municipality=municipality, defaults={"fee": fee})


def unseed_zones(apps, schema_editor):
    ShippingZone = apps.get_model("shipping", "ShippingZone")
    ShippingZone.objects.filter(
        municipality__in=[municipality for municipality, _ in INITIAL_ZONES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("shipping", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_zones, unseed_zones),
    ]
