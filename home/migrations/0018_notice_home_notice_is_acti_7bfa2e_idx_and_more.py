from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0017_automatic_ordering'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='notice',
            index=models.Index(fields=['is_active', '-created_at'], name='home_notice_is_acti_7bfa2e_idx'),
        ),
        migrations.AddIndex(
            model_name='notice',
            index=models.Index(fields=['is_important', 'is_active', '-created_at'], name='home_notice_is_impo_4821d2_idx'),
        ),
        migrations.AddIndex(
            model_name='service',
            index=models.Index(fields=['is_primary', 'order', 'title'], name='home_servic_is_prim_0d48bf_idx'),
        ),
        migrations.AddIndex(
            model_name='teammember',
            index=models.Index(fields=['group', 'order', 'name'], name='home_teamme_group_e2dd5a_idx'),
        ),
    ]
