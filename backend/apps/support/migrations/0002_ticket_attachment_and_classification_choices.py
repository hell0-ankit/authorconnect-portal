from django.db import migrations, models
import apps.support.models
import apps.support.storage


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='attachment',
            field=models.FileField(
                blank=True,
                null=True,
                storage=apps.support.storage.PrivateTicketAttachmentStorage(),
                upload_to=apps.support.models.ticket_attachment_upload_to,
            ),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='category',
            field=models.CharField(
                choices=[
                    ('ROYALTY', 'Royalty & Payouts'),
                    ('PUBLISHING', 'Publishing & Editorial'),
                    ('DISTRIBUTION', 'Distribution & Sales'),
                    ('ACCOUNT', 'Account & General Support'),
                    ('TECHNICAL', 'Technical Issue'),
                    ('ROYALTY_PAYMENTS', 'Royalty & Payments'),
                    ('ISBN_METADATA', 'ISBN & Metadata Issues'),
                    ('PRINTING_QUALITY', 'Printing & Quality'),
                    ('BOOK_STATUS', 'Book Status & Production Updates'),
                    ('GENERAL_INQUIRY', 'General Inquiry'),
                ],
                default='ACCOUNT',
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='ai_category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ROYALTY', 'Royalty & Payouts'),
                    ('PUBLISHING', 'Publishing & Editorial'),
                    ('DISTRIBUTION', 'Distribution & Sales'),
                    ('ACCOUNT', 'Account & General Support'),
                    ('TECHNICAL', 'Technical Issue'),
                    ('ROYALTY_PAYMENTS', 'Royalty & Payments'),
                    ('ISBN_METADATA', 'ISBN & Metadata Issues'),
                    ('PRINTING_QUALITY', 'Printing & Quality'),
                    ('BOOK_STATUS', 'Book Status & Production Updates'),
                    ('GENERAL_INQUIRY', 'General Inquiry'),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='ai_priority',
            field=models.CharField(
                blank=True,
                choices=[
                    ('LOW', 'Low'),
                    ('MEDIUM', 'Medium'),
                    ('HIGH', 'High'),
                    ('CRITICAL', 'Critical'),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
