from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='related_images',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='검증된 청크 기반으로 조회된 이미지 메타데이터 리스트',
                verbose_name='관련 이미지',
            ),
        ),
    ]
