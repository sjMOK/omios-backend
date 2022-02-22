from datetime import datetime

from freezegun import freeze_time

from rest_framework.exceptions import APIException

from common.utils import datetime_to_iso
from common.test.test_cases import ModelTestCase, FREEZE_TIME, FREEZE_TIME_FORMAT, FREEZE_TIME_AUTO_TICK_SECONDS
from ..models import Membership, User, Shopper, Wholesaler


class MembershipTestCase(ModelTestCase):
    _model_class = Membership

    def setUp(self):
        self._test_data = {
            'name': 'diamond',
        }

    def test_create(self):
        membership = self._get_model_after_creation()

        self.assertEqual(membership.name, self._test_data['name'])


class UserTestCase(ModelTestCase):
    _model_class = User

    @classmethod
    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def setUpTestData(cls):
        cls._test_data = {
            'username': 'username',
            'password': 'password',
        }
        cls._user = cls._get_default_model_after_creation()

    def test_create(self):
        self.assertTrue(self._user.check_password(self._test_data['password']))
        self.assertIsNone(self._user.last_login)
        self.assertEqual(self._user.username, self._test_data['username'])
        self.assertTrue(not self._user.is_admin)
        self.assertTrue(self._user.is_active)
        self.assertEqual(self._user.created_at, self._user.last_update_password)
        self.assertEqual(datetime_to_iso(self._user.created_at), FREEZE_TIME)
        self.assertIsNone(self._user.deleted_at)
        
    def test_default_save(self):
        self.assertRaisesRegex(APIException, r'^User model save method requires force_insert or update_fields.$', self._get_model().save)

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_save_using_force_insert(self):
        self._test_data['username'] = 'new_username'
        user = self._get_model()
        user.save(force_insert=True)

        self.assertTrue(user.check_password(self._test_data['password']))
        self.assertEqual(datetime_to_iso(user.created_at), FREEZE_TIME)
        self.assertEqual(user.created_at, user.last_update_password)

    def test_change_password(self):
        self._user.password = self._test_data['password'] = 'new_password'
        self._user.save(update_fields=['password'])
        user = self._model_class.objects.get(id=self._user.id)

        self.assertTrue(user.check_password(self._test_data['password']))
        self.assertGreater(user.last_update_password, user.created_at)
        
    @freeze_time(FREEZE_TIME)
    def test_delete(self):
        self._user.is_active = False
        self._user.save(update_fields=['is_active'])
        user = self._model_class.objects.get(id=self._user.id)

        self.assertTrue(not user.is_active)
        self.assertEqual(datetime_to_iso(user.deleted_at), FREEZE_TIME)

    def test_save_after_public_set_password(self):
        self._user.set_password('new_password')

        self.assertRaisesRegex(APIException, r'^The save method cannot be used when the public set_password method is used.$', self._user.save)
    


from django.test import tag

@tag('test')
class ShopperTestCase(ModelTestCase):
    fixtures = ['membership']
    _model_class = Shopper

    @classmethod
    def setUpTestData(cls):
        cls._test_data = {
            "name": "test",
            "birthday": "2017-01-01",
            "gender": 1,
            "email": "testemail@naver.com",
            "phone": "01012345678",
            "username": "shopper",
            "password": "password",
        }
        cls._shopper = cls._get_default_model_after_creation()

    def test_create(self):
        self.assertIsInstance(self._shopper.user, User)
        self.assertTrue(self._shopper.membership)
        self.assertEqual(self._shopper.name, self._test_data['name'])
        self.assertEqual(self._shopper.nickname, self._test_data['username'])
        self.assertEqual(self._shopper.phone, self._test_data['phone'])
        self.assertEqual(self._shopper.email, self._test_data['email'])
        self.assertEqual(self._shopper.gender, self._test_data['gender'])
        self.assertEqual(self._shopper.birthday, self._test_data['birthday'])
        self.assertIsNone(self._shopper.height)
        self.assertIsNone(self._shopper.weight)

    def test_default_nickname(self):
        self._shopper.nickname = self._test_data['username'] = 'shopper2'
        self._test_data['phone'] = '01012341234'
        self._shopper.save(update_fields=['nickname'])
        shopper = self._get_model_after_creation()

        self.assertEqual(self._shopper.nickname, self._test_data['username'])
        self.assertTrue(shopper.nickname.startswith('omios_'))


class WholesalerTestCase(ModelTestCase):
    pass