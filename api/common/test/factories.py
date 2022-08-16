from random import randint

from django.utils import timezone

from factory import LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from ..utils import IMAGE_DATETIME_FORMAT


class FuzzyRandomLengthText(FuzzyText):
    def __init__(self, min_length=3, max_length=6, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.min_length = min(min_length, max_length)
        self.max_length = max_length

    def fuzz(self):
        self.length = randint(self.min_length, self.max_length)

        return super().fuzz()


class TemporaryImageFactory(DjangoModelFactory):
    class Meta:
        model = 'common.TemporaryImage'

    image_url = LazyFunction(lambda: '{}.jpeg'.format(timezone.now().strftime(IMAGE_DATETIME_FORMAT)))


class SettingGroupFactory(DjangoModelFactory):
    class Meta:
        model = 'common.SettingGroup'

    app = Sequence(lambda num: f'app{num}')
    name = Sequence(lambda num: f'name{num}')
    main_key = FuzzyText()


class SettingItemFactory(DjangoModelFactory):
    class Meta:
        model = 'common.SettingItem'

    group = SubFactory(SettingGroupFactory)
    name = Sequence(lambda num: f'name{num}')
