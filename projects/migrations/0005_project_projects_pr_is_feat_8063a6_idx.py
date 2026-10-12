from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_automatic_ordering'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['is_featured', 'order', '-created_at'], name='projects_pr_is_feat_8063a6_idx'),
        ),
    ]
