# Generated by Django 2.0.5 on 2018-06-05 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='language',
            field=models.CharField(blank=True, choices=[('EN', 'English'), ('CN', 'Chinese'), ('FR', 'French')], default='EN', max_length=2),
        ),
    ]
