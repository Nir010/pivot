from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['is_published', '-is_pinned', '-created_at'], name='blog_post_is_publ_4ddc19_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['is_published', '-created_at'], name='blog_post_is_publ_1d5edc_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['slug'], name='blog_post_slug_cdb902_idx'),
        ),
    ]
