# Generated manually to add low_stock_notified_at field to Product
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='low_stock_notified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

