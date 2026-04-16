import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TestRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('total_tests', models.IntegerField(default=0)),
                ('passed', models.IntegerField(default=0)),
                ('failed', models.IntegerField(default=0)),
                ('errors', models.IntegerField(default=0)),
                ('skipped', models.IntegerField(default=0)),
                ('current_test', models.CharField(blank=True, default='', max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_runs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_id', models.CharField(max_length=500)),
                ('module', models.CharField(max_length=255)),
                ('class_name', models.CharField(max_length=255)),
                ('method', models.CharField(max_length=255)),
                ('description', models.CharField(blank=True, default='', max_length=500)),
                ('status', models.CharField(choices=[('pass', 'Pass'), ('fail', 'Fail'), ('error', 'Error'), ('skipped', 'Skipped')], max_length=20)),
                ('duration_ms', models.FloatField(default=0)),
                ('output', models.TextField(blank=True, default='')),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('test_run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='admin_panel.testrun')),
            ],
        ),
    ]
