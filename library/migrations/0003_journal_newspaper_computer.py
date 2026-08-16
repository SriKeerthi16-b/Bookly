from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0002_profile"),
    ]

    operations = [
        migrations.CreateModel(
            name="Computer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("system_number", models.CharField(max_length=50, unique=True)),
                ("status", models.CharField(choices=[("working", "Working"), ("in_use", "In Use"), ("maintenance", "Maintenance")], default="working", max_length=20)),
                ("location", models.CharField(default="Computer Library", max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Journal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("publisher", models.CharField(blank=True, max_length=200)),
                ("volume", models.CharField(blank=True, max_length=50)),
                ("issue", models.CharField(blank=True, max_length=50)),
                ("publication_date", models.DateField(blank=True, null=True)),
                ("category", models.CharField(blank=True, max_length=100)),
                ("available", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Newspaper",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("language", models.CharField(blank=True, max_length=100)),
                ("publication_date", models.DateField(blank=True, null=True)),
                ("copies", models.PositiveIntegerField(default=1)),
                ("available", models.BooleanField(default=True)),
            ],
        ),
    ]
