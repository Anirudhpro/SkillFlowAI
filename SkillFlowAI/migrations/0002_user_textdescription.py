# Generated by Django 5.1.7 on 2025-03-15 17:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SkillFlowAI', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='textDescription',
            field=models.CharField(default='', max_length=5000),
        ),
    ]
