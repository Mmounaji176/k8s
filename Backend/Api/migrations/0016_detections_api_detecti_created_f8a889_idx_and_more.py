# Generated by Django 5.0.1 on 2024-10-17 16:39


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Api', '0015_alter_imageproc_taskid'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='detections',
            index=models.Index(fields=['created'], name='Api_detecti_created_f8a889_idx'),
        ),
        migrations.AddIndex(
            model_name='detections',
            index=models.Index(fields=['video_source'], name='Api_detecti_video_s_c7a608_idx'),
        ),
    ]
