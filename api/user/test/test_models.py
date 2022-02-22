from datetime import datetime

from freezegun import freeze_time

from rest_framework.exceptions import APIException

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

    def setUp(self):
        self._test_data = {
            'username': 'username',
            'password': 'password',
        }

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_create(self):
        user = self._get_model_after_creation()

        self.assertTrue(user.check_password(self._test_data['password']))
        self.assertIsNone(user.last_login)
        self.assertEqual(user.username, self._test_data['username'])
        self.assertTrue(not user.is_admin)
        self.assertTrue(user.is_active)
        self.assertEqual(user.created_at, user.last_update_password)
        self.assertEqual(user.created_at, datetime.strptime(FREEZE_TIME, FREEZE_TIME_FORMAT))
        self.assertIsNone(user.deleted_at)
        
    def test_default_save(self):
        self.assertRaisesRegex(APIException, r'^User model save method requires force_insert or update_fields.$', self._get_model().save)

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_save_using_force_insert(self):
        user = self._get_model()
        user.save(force_insert=True)

        self.assertTrue(user.check_password(self._test_data['password']))
        self.assertEqual(user.created_at, datetime.strptime(FREEZE_TIME, FREEZE_TIME_FORMAT))
        self.assertEqual(user.created_at, user.last_update_password)

    def test_change_password(self):
        user = self._get_model_after_creation()
        user.password = self._test_data['password'] = 'new_password'
        user.save(update_fields=['password'])
        user = self._model_class.objects.get(id=user.id)

        self.assertTrue(user.check_password(self._test_data['password']))
        self.assertGreater(user.last_update_password, user.created_at)
        
    @freeze_time(FREEZE_TIME)
    def test_delete(self):
        user = self._get_model_after_creation()
        user.is_active = False
        user.save(update_fields=['is_active'])
        user = self._model_class.objects.get(id=user.id)

        self.assertTrue(not user.is_active)
        self.assertEqual(user.deleted_at, datetime.strptime(FREEZE_TIME, FREEZE_TIME_FORMAT))

    def test_save_after_public_set_password(self):
        user = self._get_model_after_creation()
        user.set_password('new_password')

        self.assertRaisesRegex(APIException, r'^The save method cannot be used when the public set_password method is used.$', user.save)
    

class ShopperTestCase(ModelTestCase):
    fixtures = ['membership']
    _model_class = Shopper

    def setUp(self):
        self._test_data = {
            "name": "test",
            "birthday": "2017-01-01",
            "gender": 1,
            "email": "testemail@naver.com",
            "phone": "01012345678",
            "username": "shopper",
            "password": "password",
        }

    def test_create(self):
        shopper = self._get_model_after_creation()
        
        self.assertIsInstance(shopper.user, User)
        self.assertTrue(shopper.membership)
        self.assertEqual(shopper.name, self._test_data['name'])
        self.assertEqual(shopper.nickname, self._test_data['username'])
        self.assertEqual(shopper.phone, self._test_data['phone'])
        self.assertEqual(shopper.email, self._test_data['email'])
        self.assertEqual(shopper.gender, self._test_data['gender'])
        self.assertEqual(shopper.birthday, self._test_data['birthday'])
        self.assertIsNone(shopper.height)
        self.assertIsNone(shopper.weight)

    def test_default_nickname(self):
        self._test_data['nickname'] = 'shopper2'
        self._get_model_after_creation()
        self._test_data.pop('nickname')
        self._test_data['username'] = 'shopper2'
        self._test_data['phone'] = '01012341234'
        shopper = self._get_model_after_creation()

        self.assertTrue(shopper.nickname.startswith('omios_'))


class WholesalerTestCase(ModelTestCase):
    pass