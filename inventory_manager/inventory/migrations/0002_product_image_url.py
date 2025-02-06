# filepath: /c:/Users/Taşdelen/Desktop/yeninesilevim/inventory_manager/inventory/migrations/0002_product_image_url.py
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image_url',
            field=models.CharField(max_length=1024, blank=True, null=True),
        ),
    ]