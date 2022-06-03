from django.utils import timezone
from django.forms import model_to_dict
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser

from rest_framework.exceptions import APIException

from freezegun import freeze_time

from common.utils import datetime_to_iso
from common.storage import MediaStorage
from common.test.test_cases import FREEZE_TIME, FREEZE_TIME_AUTO_TICK_SECONDS, ModelTestCase
from product.test.factories import ProductFactory, OptionFactory
from order.test.factories import OrderFactory
from .factories import MembershipFactory, ShopperFactory, BuildingFactory, FloorFactory, WholesalerFactory
from ..models import (
    is_shopper, is_wholesaler,
    Membership, User, Shopper, ShopperShippingAddress, Wholesaler, Building, Floor, BuildingFloor,
    ProductLike, PointHistory, Cart,
)


class CheckUserTypeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.shopper = ShopperFactory()
        cls.wholesaler = WholesalerFactory()
        cls.anonymous_user = AnonymousUser()

    def test_shopper_is_shopper(self):
        self.assertTrue(is_shopper(self.shopper))

    def test_shopper_is_not_wholesaler(self):
        self.assertTrue(not is_wholesaler(self.shopper))

    def test_wholesaler_is_not_shopper(self):
        self.assertTrue(not is_shopper(self.wholesaler))
    
    def test_wholeslaer_is_wholesaler(self):
        self.assertTrue(is_wholesaler(self.wholesaler))

    def test_anonymous_user_is_not_shopper(self):
        self.assertTrue(not is_shopper(self.anonymous_user))

    def test_anonymous_user_is_not_wholesaler(self):
        self.assertTrue(not is_wholesaler(self.anonymous_user))


class MembershipTestCase(ModelTestCase):
    _model_class = Membership

    def setUp(self):
        self._test_data = {
            'name': 'diamond',
            'discount_rate': 5,
            'qualification': 'diamond' ,
        }

    def test_create(self):
        membership = self._get_model_after_creation()

        self.assertEqual(membership.name, self._test_data['name'])
        self.assertEqual(membership.discount_rate, self._test_data['discount_rate'])
        self.assertEqual(membership.qualification, self._test_data['qualification'])


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

    def test_user_type(self):
        self.assertTrue(not is_shopper(self._user))
        self.assertTrue(not is_wholesaler(self._user))

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

    def test_fake_delete(self):
        self._user.delete()

        self.assertTrue(not self._user.is_active)        


class ShopperTestCase(ModelTestCase):
    _model_class = Shopper

    @classmethod
    def setUpTestData(cls):
        MembershipFactory(id=1)
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

    def test_user_type(self):
        self.assertTrue(self._shopper.is_shopper)
        self.assertTrue(not self._shopper.is_wholesaler)

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
        self.assertEqual(self._shopper.point, 0)

    def test_default_nickname(self):
        self._shopper.nickname = self._test_data['username'] = 'shopper2'
        self._test_data['mobile_number'] = '01012341234'
        self._shopper.save(update_fields=['nickname'])
        shopper = self._get_model_after_creation()

        self.assertEqual(self._shopper.nickname, self._test_data['username'])
        self.assertTrue(shopper.nickname.startswith('omios_'))
    
    def test_delete(self):
        self._shopper.delete()

        self.assertTrue(not self._shopper.is_active)
        self.assertTrue(not self._shopper.question_answers.all().exists())

    def test_update_point(self):
        point = 1000
        content = 'test_update_point'
        self._shopper.update_point(point, content)

        self.assertEqual(self._shopper.point, point)
        self.assertTrue(PointHistory.objects.get(shopper=self._shopper, point=point, content=content))

    def test_update_point_including_order_items(self):
        order = OrderFactory(shopper=self._shopper)
        order_items = [
            {
                'product_name': 'product1',
                'point': 200,
            },
            {
                'product_name': 'product2',
                'point': 300,
            },
        ]
        total_point = sum([order_item['point'] for order_item in order_items])
        self._shopper.update_point(total_point, 'test_update_point', order.id, order_items)

        self.assertEqual(self._shopper.point, total_point)
        self.assertTrue([PointHistory.objects.get(
            order=order, 
            product_name=order_item['product_name'], 
            point=order_item['point'],
        ) for order_item in order_items])


class ProductLikeTestCase(ModelTestCase):
    _model_class = ProductLike

    @freeze_time(FREEZE_TIME)
    def test_create(self):
        self._test_data = {
            'shopper': ShopperFactory(),
            'product': ProductFactory()
        }
        product_like = self._get_model_after_creation()

        self.assertEqual(product_like.shopper, self._test_data['shopper'])
        self.assertEqual(product_like.product, self._test_data['product'])
        self.assertEqual(datetime_to_iso(product_like.created_at), FREEZE_TIME)


class WholesalerTestCase(ModelTestCase):
    _model_class = Wholesaler

    @classmethod
    def setUpTestData(cls):
        cls._test_data = {
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
        cls._wholesaler = cls._get_default_model_after_creation()

    def test_user_type(self):
        self.assertTrue(not self._wholesaler.is_shopper)
        self.assertTrue(self._wholesaler.is_wholesaler)

    def test_create(self):
        self.assertIsInstance(self._wholesaler.user, User)
        self.assertEqual(self._wholesaler.name, self._test_data['name'])
        self.assertEqual(self._wholesaler.mobile_number, self._test_data['mobile_number'])
        self.assertEqual(self._wholesaler.phone_number, self._test_data['phone_number'])
        self.assertEqual(self._wholesaler.email, self._test_data['email'])
        self.assertEqual(self._wholesaler.company_registration_number, self._test_data['company_registration_number'])
        self.assertIsInstance(self._wholesaler.business_registration_image_url.storage, MediaStorage)
        self.assertEqual(self._wholesaler.business_registration_image_url.name, self._test_data['business_registration_image_url'])
        self.assertEqual(self._wholesaler.zip_code, self._test_data['zip_code'])
        self.assertEqual(self._wholesaler.base_address, self._test_data['base_address'])
        self.assertEqual(self._wholesaler.detail_address, self._test_data['detail_address'])
        self.assertTrue(not self._wholesaler.is_approved)


class CartTestCase(ModelTestCase):
    _model_class = Cart

    def test_create(self):
        self._test_data = {
            'option': OptionFactory(),
            'shopper': ShopperFactory(),
            'count': 1,
        }
        cart = self._get_model_after_creation()

        self.assertEqual(cart.option, self._test_data['option'])
        self.assertEqual(cart.shopper, self._test_data['shopper'])
        self.assertEqual(cart.count, self._test_data['count'])


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


class ShopperShippingAddressTestCase(ModelTestCase):
    _model_class = ShopperShippingAddress

    @classmethod
    def setUpTestData(cls):
        cls._test_data = {
            'shopper': ShopperFactory(),
            'receiver_name': '수령자',
            'receiver_mobile_number': '01012345678',
            'zip_code': '05009',
            'base_address': '서울시 광진구 능동로19길 47',
            'detail_address': '화양타워 518호',
            'is_default': True,
        }

    def test_create(self):
        shipping_address = self._get_model_after_creation()

        self.assertEqual(shipping_address.shopper, self._test_data['shopper'])
        self.assertIsNone(shipping_address.name)
        self.assertEqual(shipping_address.receiver_name, self._test_data['receiver_name'])
        self.assertEqual(shipping_address.receiver_mobile_number, self._test_data['receiver_mobile_number'])
        self.assertIsNone(shipping_address.receiver_phone_number)
        self.assertEqual(shipping_address.zip_code, self._test_data['zip_code'])
        self.assertEqual(shipping_address.base_address, self._test_data['base_address'])
        self.assertEqual(shipping_address.detail_address, self._test_data['detail_address'])
        self.assertEqual(shipping_address.is_default, self._test_data['is_default'])

    def test_create_initial_shipping_address(self):
        self._test_data['is_default'] = False
        shipping_address = self._get_model_after_creation()

        self.assertTrue(shipping_address.is_default)

    def test_create_default_shipping_address(self):
        self._model_class.objects.create(**self._test_data)
        shipping_address = self._get_model_after_creation()

        self.assertTrue(shipping_address.is_default)
        self.assertTrue(
            not self._model_class.objects.exclude(id=shipping_address.id).filter(is_default=True).exists()
        )

    def test_update_to_default_shipping_address(self):
        self._model_class.objects.create(**self._test_data)
        self._test_data['is_default'] = False

        shipping_address = self._get_model_after_creation()
        shipping_address.is_default = True
        shipping_address.save()

        self.assertTrue(shipping_address.is_default)
        self.assertTrue(
            not self._model_class.objects.exclude(id=shipping_address.id).filter(is_default=True).exists()
        )


class PointHistoryTestCase(ModelTestCase):
    _model_class = PointHistory

    @classmethod
    def setUpTestData(cls):
        cls._test_data = {
            'shopper': ShopperFactory(),
            'point': -1000,
            'content': '적립금 결제',
        }

    @freeze_time(FREEZE_TIME)
    def test_create(self):
        point_history = model_to_dict(self._get_model_after_creation(), exclude=['id'])

        self.assertDictEqual(point_history, {
            **self._test_data,
            'shopper': self._test_data['shopper'].user_id,
            'order': None,
            'product_name': None,
        })

    def test_create_including_order(self):
        self._test_data['order'] = OrderFactory(shopper=self._test_data['shopper'])
        self._test_data['product_name'] = 'test_product_name'
        point_history = self._get_model_after_creation()

        self.assertEqual(point_history.order, self._test_data['order'])
        self.assertEqual(point_history.product_name, self._test_data['product_name'])