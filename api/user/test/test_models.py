from datetime import datetime

from freezegun import freeze_time

from rest_framework.exceptions import APIException

from common.utils import datetime_to_iso
from common.storage import MediaStorage
from common.test.test_cases import FREEZE_TIME, FREEZE_TIME_AUTO_TICK_SECONDS, ModelTestCase
from .factory import ShopperFactory, BuildingFactory, FloorFactory
from ..models import Membership, User, Shopper, ShopperAddress, Wholesaler, Building, Floor, BuildingFloor


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


class ShopperTestCase(ModelTestCase):
    fixtures = ['membership']
    _model_class = Shopper

    @classmethod
    def setUpTestData(cls):
        cls._test_data = {
            "username": "shopper",
            "password": "password",
            "name": "test",
            "birthday": "2017-01-01",
            "gender": 1,
            "email": "testemail@naver.com",
            "mobile_number": "01012345678",
        }
        cls._shopper = cls._get_default_model_after_creation()

    def test_create(self):
        self.assertIsInstance(self._shopper.user, User)
        self.assertTrue(self._shopper.membership)
        self.assertEqual(self._shopper.name, self._test_data['name'])
        self.assertEqual(self._shopper.nickname, self._test_data['username'])
        self.assertEqual(self._shopper.mobile_number, self._test_data['mobile_number'])
        self.assertEqual(self._shopper.email, self._test_data['email'])
        self.assertEqual(self._shopper.gender, self._test_data['gender'])
        self.assertEqual(self._shopper.birthday, self._test_data['birthday'])
        self.assertIsNone(self._shopper.height)
        self.assertIsNone(self._shopper.weight)

    def test_default_nickname(self):
        self._shopper.nickname = self._test_data['username'] = 'shopper2'
        self._test_data['mobile_number'] = '01012341234'
        self._shopper.save(update_fields=['nickname'])
        shopper = self._get_model_after_creation()

        self.assertEqual(self._shopper.nickname, self._test_data['username'])
        self.assertTrue(shopper.nickname.startswith('omios_'))


class ShopperAddressTestCase(ModelTestCase):
    fixtures = ['membership']
    _model_class = ShopperAddress

    def setUp(self):
        self.__shopper = ShopperFactory()
        self._test_data = {
            'shopper': self.__shopper,
            'receiver': '수령자',
            'mobile_number': '01012345678',
            'zip_code': '05009',
            'base_address': '서울시 광진구 능동로19길 47',
            'detail_address': '화양타워 518호',
            'is_default': True,
        }

    def test_create(self):
        address = self._get_model_after_creation()

        self.assertEqual(address.shopper, self.__shopper)
        self.assertIsNone(address.name)
        self.assertEqual(address.receiver, self._test_data['receiver'])
        self.assertEqual(address.mobile_number, self._test_data['mobile_number'])
        self.assertIsNone(address.phone_number)
        self.assertEqual(address.zip_code, self._test_data['zip_code'])
        self.assertEqual(address.base_address, self._test_data['base_address'])
        self.assertEqual(address.detail_address, self._test_data['detail_address'])
        self.assertEqual(address.is_default, self._test_data['is_default'])


class WholesalerTestCase(ModelTestCase):
    _model_class = Wholesaler

    def setUp(self):
        self._test_data = {
            'username': 'wholesaler',
            'password': 'password',
            'name': 'wholesaler_name',
            'mobile_number': '01012345678',
            'phone_number': '0212345678',
            'email': 'testemail@naver.com',
            'company_registration_number': '111122223333',
            'business_registration_image_url': 'business_registration/test_image.png',
            'zip_code': '05009',
            'base_address': '서울시 광진구 능동로19길 47',
            'detail_address': '화양타워 518호',
        }

    def test_create(self):
        wholesaler = self._get_model_after_creation()

        self.assertIsInstance(wholesaler.user, User)
        self.assertEqual(wholesaler.name, self._test_data['name'])
        self.assertEqual(wholesaler.mobile_number, self._test_data['mobile_number'])
        self.assertEqual(wholesaler.phone_number, self._test_data['phone_number'])
        self.assertEqual(wholesaler.email, self._test_data['email'])
        self.assertEqual(wholesaler.company_registration_number, self._test_data['company_registration_number'])
        self.assertIsInstance(wholesaler.business_registration_image_url.storage, MediaStorage)
        self.assertEqual(wholesaler.business_registration_image_url.name, self._test_data['business_registration_image_url'])
        self.assertEqual(wholesaler.zip_code, self._test_data['zip_code'])
        self.assertEqual(wholesaler.base_address, self._test_data['base_address'])
        self.assertEqual(wholesaler.detail_address, self._test_data['detail_address'])
        self.assertTrue(not wholesaler.is_approved)


class BuildingTestCase(ModelTestCase):
    _model_class = Building

    def setUp(self):
        self._test_data = {
            'name': '오미오스',
            'zip_code': '05009',
            'base_address': '서울시 광진구 능동로19길 47',
        }

    def test_create(self):
        building = self._get_model_after_creation()

        self.assertEqual(building.name, self._test_data['name'])
        self.assertEqual(building.zip_code, self._test_data['zip_code'])
        self.assertEqual(building.base_address, self._test_data['base_address'])


class FloorTestCase(ModelTestCase):
    _model_class = Floor

    def setUp(self):
        self._test_data = {
            'name': '1층',
        }

    def test_create(self):
        floor = self._get_model_after_creation()

        self.assertEqual(floor.name, self._test_data['name'])


class BuildingFloorTestCase(ModelTestCase):
    _model_class = BuildingFloor

    def setUp(self):
        self.__building = BuildingFactory()
        self.__floor = FloorFactory()
        self._test_data = {
            'building': self.__building,
            'floor': self.__floor,
        }

    def test_create(self):
        building_floor = self._get_model_after_creation()

        self.assertEqual(building_floor.building, self.__building)
        self.assertEqual(building_floor.floor, self.__floor)
