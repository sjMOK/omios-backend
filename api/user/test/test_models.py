from datetime import datetime
from rest_framework.test import APITestCase
from rest_framework.exceptions import APIException
from freezegun import freeze_time

from common.utils import FREEZE_TIME, FREEZE_TIME_FORMAT, FREEZE_TIME_AUTO_TICK_SECONDS
from ..models import Membership, User, Shopper, Wholesaler


class MembershipTest(APITestCase):
    __model_class = Membership

    def test_create(self):
        test_data = {
            'name': 'diamond',
        }

        membership = self.__model_class.objects.create(**test_data)
        self.assertEqual(membership.name, test_data['name'])


class UserTest(APITestCase):
    __model_class = User

    def setUp(self):
        self.test_data = {
            'username': 'username',
            'password': 'password',
        }

    def __get_model(self):
        return self.__model_class(**self.test_data)

    def __get_model_after_creation(self):
        return self.__model_class.objects.create(**self.test_data)

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_create(self):
        user = self.__get_model_after_creation()

        self.assertEqual(user.username, self.test_data['username'])
        self.assertTrue(user.check_password(self.test_data['password']))
        self.assertTrue(user.is_active)
        self.assertTrue(not user.is_admin)
        self.assertEqual(user.created_at, datetime.strptime(FREEZE_TIME, FREEZE_TIME_FORMAT))
        self.assertEqual(user.created_at, user.last_update_password)
        
    def test_default_save(self):
        self.assertRaises(APIException, self.__get_model().save)

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_save_using_force_insert(self):
        user = self.__get_model()
        user.save(force_insert=True)

        self.assertTrue(user.check_password(self.test_data['password']))
        self.assertEqual(user.created_at, datetime.strptime(FREEZE_TIME, FREEZE_TIME_FORMAT))
        self.assertEqual(user.created_at, user.last_update_password)

    def test_save_using_update_fields(self):
        user = self.__get_model_after_creation()
        user.password = self.test_data['password'] = 'new_password'
        user.save(update_fields=['password'])

        self.assertTrue(user.check_password(self.test_data['password']))
        self.assertGreater(user.last_update_password, user.created_at)

    def test_public_set_password(self):
        self.assertRaises(APIException, self.__get_model().set_password, self.test_data['password'])
    

class ShopperTest(APITestCase):
    fixtures = ['membership']
    __model_class = Shopper

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

    def __get_model_after_creation(self):
        return self.__model_class.objects.create(**self.test_data)

    def test_create(self):
        shopper = self.__get_model_after_creation()
        
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
        self.__get_model_after_creation()

        self.test_data.pop('nickname')
        self.test_data['username'] = 'shopper2'
        self.test_data['phone'] = '01012341234'
        shopper = self.__get_model_after_creation()

        self.assertTrue(shopper.nickname.startswith('omios_'))


class WholesalerTest(APITestCase):
    pass