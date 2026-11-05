from django.db import migrations

INITIAL_CATEGORIES = [
    ("Camisetas / Tops", "camisetas-tops"),
    ("Buzos / Sacos", "buzos-sacos"),
    ("Pantalones / Jeans", "pantalones-jeans"),
    ("Conjuntos", "conjuntos"),
]


def seed_initial_categories(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    for name, slug in INITIAL_CATEGORIES:
        Category.objects.get_or_create(slug=slug, defaults={"name": name})


def unseed_initial_categories(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    slugs = [slug for _, slug in INITIAL_CATEGORIES]
    Category.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_initial_categories, unseed_initial_categories),
    ]
