from django.utils import timezone

from factory import LazyFunction
from factory.django import DjangoModelFactory

from ..utils import IMAGE_DATETIME_FORMAT


class TemporaryImageFactory(DjangoModelFactory):
    class Meta:
        model = 'common.TemporaryImage'

    image_url = LazyFunction(lambda: '{}.jpeg'.format(timezone.now().strftime(IMAGE_DATETIME_FORMAT)))
