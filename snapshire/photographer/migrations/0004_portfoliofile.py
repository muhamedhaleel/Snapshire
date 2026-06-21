from django.db import migrations, models
import photographer.models


class Migration(migrations.Migration):

    dependencies = [
        ('photographer', '0003_photographerprofile_profile_image_portfoliolink'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortfolioFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=photographer.models.portfolio_file_path)),
                ('original_name', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('profile', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='portfolio_files', to='photographer.photographerprofile')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
