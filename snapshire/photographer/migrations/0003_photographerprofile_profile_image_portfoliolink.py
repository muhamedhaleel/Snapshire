from django.db import migrations, models
import photographer.models


class Migration(migrations.Migration):

    dependencies = [
        ('photographer', '0002_photographerprofile_plan_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='photographerprofile',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to=photographer.models.photographer_profile_image_path),
        ),
        migrations.CreateModel(
            name='PortfolioLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('profile', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='portfolio_links', to='photographer.photographerprofile')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
