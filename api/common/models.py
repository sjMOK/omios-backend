from django.db.models import Model, CharField


class TemporaryImage(Model):
    image_url = CharField(primary_key=True, max_length=200)

    class Meta:
        db_table = 'temporary_image'
