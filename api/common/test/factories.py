from django.utils import timezone

from factory import LazyFunction
from factory.django import DjangoModelFactory


class TemporaryImageFactory(DjangoModelFactory):
    class Meta:
        model = 'common.TemporaryImage'

    image_url = LazyFunction(lambda: '{}.jpeg'.format(timezone.now().strftime("%Y%m%d_%H%M%S%f")))
