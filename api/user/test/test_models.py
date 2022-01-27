from datetime import datetime
from rest_framework.test import APITestCase, APITransactionTestCase
from rest_framework.exceptions import APIException
from freezegun import freeze_time

from common.utils import FREEZE_TIME, FREEZE_TIME_FORMAT, FREEZE_TIME_AUTO_TICK_SECONDS
from ..models import Membership, User, Shopper, Wholesaler


class MembershipTest(APITestCase):
    def test_create(self):
        test_data = {
            'name': 'diamond',
        }

        membership = Membership.objects.create(**test_data)
        self.assertEqual(membership.name, test_data['name'])


class UserTest(APITransactionTestCase):
    def setUp(self):
        self.test_data = {
            'username': 'username',
            'password': 'password',
        }
        self.user = User(**self.test_data)

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_create(self):
        user = User.objects.create(**self.test_data)

        self.assertEqual(user.username, self.test_data['username'])
        self.assertTrue(user.check_password(self.test_data['password']))
        self.assertTrue(user.is_active)
        self.assertTrue(not user.is_admin)
        self.assertEqual(user.created_at, datetime.strptime(FREEZE_TIME, FREEZE_TIME_FORMAT))
        self.assertEqual(user.created_at, user.last_update_password)
        
    def test_default_save(self):
        self.assertRaises(APIException, self.user.save)

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_save_using_force_insert(self):
        user = User(**self.test_data)
        user.save(force_insert=True)

        self.assertTrue(user.check_password(self.test_data['password']))
        self.assertEqual(user.created_at, datetime.strptime(FREEZE_TIME, FREEZE_TIME_FORMAT))
        self.assertEqual(user.created_at, user.last_update_password)

    def test_save_using_update_fields(self):
        self.user.save(force_insert=True)

        self.user.password = self.test_data['password'] = 'new_password'
        self.user.save(update_fields=['password'])

        self.assertTrue(self.user.check_password(self.test_data['password']))
        self.assertGreater(self.user.last_update_password, self.user.created_at)

    def test_public_set_password(self):
        self.assertRaises(APIException, self.user.set_password, self.test_data['password'])
    

class ShopperTest(APITransactionTestCase):
    fixtures = ['membership']

    def setUp(self):
        self.test_data = {
            "name": "test",
            "birthday": "2017-01-01",
            "gender": 1,
            "email": "testemail@naver.com",
            "phone": "01012345678",
            "username": "shopper",
            "password": "password",
        }

    def test_create(self):
        shopper = Shopper.objects.create(**self.test_data)
        
        self.assertTrue(shopper.user)
        self.assertTrue(shopper.membership)
        self.assertEqual(shopper.name, self.test_data['name'])
        self.assertEqual(shopper.birthday, self.test_data['birthday'])
        self.assertEqual(shopper.gender, self.test_data['gender'])
        self.assertEqual(shopper.email, self.test_data['email'])
        self.assertEqual(shopper.phone, self.test_data['phone'])
        self.assertEqual(shopper.nickname, self.test_data['username'])

    def test_default_nickname(self):
        self.test_data['nickname'] = 'shopper2'
        Shopper.objects.create(**self.test_data)

        self.test_data.pop('nickname')
        self.test_data['username'] = 'shopper2'
        self.test_data['phone'] = '01012341234'
        shopper = Shopper.objects.create(**self.test_data)

        self.assertTrue(shopper.nickname.startswith('omios_'))


class WholesalerTest(APITestCase):
    pass