import random

from django.db.models.query import Prefetch
from django.db.models import Avg, Max, Min, Count, Q, Case, When

from rest_framework_simplejwt.tokens import RefreshToken
from faker import Faker

from common.test.test_cases import ViewTestCase, FunctionTestCase
from common.test.factories import SettingItemFactory
from common.utils import levenshtein, BASE_IMAGE_URL
from common.models import TemporaryImage
from coupon.models import Coupon
from user.test.factories import WholesalerFactory
from user.models import Wholesaler
from .factories import (
    AgeFactory, ColorFactory, LaundryInformationFactory, MainCategoryFactory, MaterialFactory, OptionFactory, 
    ProductColorFactory, ProductFactory, ProductImageFactory, ProductMaterialFactory, SizeFactory, StyleFactory, 
    SubCategoryFactory, KeyWordFactory, TagFactory, ProductQuestionAnswerFactory, ProductQuestionAnswerClassificationFactory,
    create_product_additional_information,
)
from .test_serializers import get_product_registration_test_data
from ..views import sort_keywords_by_levenshtein_distance
from ..models import (
    LaundryInformation, MainCategory, SubCategory, Keyword, Color, Material, Style, Age,
    Product, Tag, Option, ProductQuestionAnswer,
)
from ..serializers import (
    LaundryInformationSerializer, MainCategorySerializer, ProductReadSerializer, SizeSerializer, 
    SubCategorySerializer, ColorSerializer, MaterialSerializer, StyleSerializer, AgeSerializer, TagSerializer,
    ProductQuestionAnswerSerializer, ProductQuestionAnswerClassificationSerializer, ProductWriteSerializer,
    ProductRegistrationSerializer,
)


class SortKeywordsByLevenshteinDistanceTestCase(FunctionTestCase):
    _function = sort_keywords_by_levenshtein_distance

    def test(self):
        fake = Faker()
        keywords = [fake.word() for _ in range(10)]
        search_word = fake.word()

        keywords_leven_distances = [levenshtein(keyword, search_word) for keyword in keywords]
        keywords_leven_distances.sort()

        result = self._call_function(keywords, search_word)
        result_leven_distances = [levenshtein(keyword, search_word) for keyword in result]

        self.assertListEqual(keywords_leven_distances, result_leven_distances)


class GetAllCategoriesTestCase(ViewTestCase):
    _url = '/products/categories'

    def test_get(self):
        main_categories = MainCategoryFactory.create_batch(size=3)
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data, MainCategorySerializer(main_categories, many=True).data)


class GetMainCategoriesTestCase(ViewTestCase):
    _url = '/products/main-categories'

    def test_get(self):
        main_categories = MainCategoryFactory.create_batch(size=3)
        self._get()

        self._assert_success()
        self.assertListEqual(
            self._response_data, 
            MainCategorySerializer(main_categories, many=True, exclude_fields=('sub_categories',)).data
        )


class GetSubCategoriesByMainCategoryTestCase(ViewTestCase):
    _url = '/products/main-categories'

    @classmethod
    def setUpTestData(cls):
        cls.__main_category = MainCategoryFactory()
        cls.__sub_categories = SubCategoryFactory.create_batch(size=3, main_category=cls.__main_category)

    def test_get(self):
        self._url += '/{0}/sub-categories'.format(self.__main_category.id)
        self._get()

        self._assert_success()
        self.assertListEqual(
            self._response_data, 
            SubCategorySerializer(self.__sub_categories, many=True).data
        )

    def test_get_raise_404(self):
        main_category_id = MainCategory.objects.latest('id').id + 1
        self._url += '/{0}/sub-categories'.format(main_category_id)
        self._get()

        self._assert_failure(404, 'Not found.')


class GetColorsTestCase(ViewTestCase):
    _url = '/products/colors'

    def test_get(self):
        colors = ColorFactory.create_batch(size=3)
        self._get()

        self._assert_success()
        self.assertListEqual(
            self._response_data, 
            ColorSerializer(colors, many=True).data
        )


class GetTagSearchResultTest(ViewTestCase):
    _url = '/products/tags'

    def test_get(self):
        fake = Faker()
        search_word = fake.word()
        TagFactory.create_batch(size=3)
        TagFactory(name=search_word)
        TagFactory(name=(fake.word() + search_word))
        TagFactory(name=(search_word + fake.word()))
        TagFactory(name=(fake.word() + search_word + fake.word()))

        self._get({'search_word': search_word})
        tags = Tag.objects.filter(name__contains=search_word).alias(cnt=Count('product')).order_by('-cnt')

        self._assert_success()
        self.assertListEqual(
            TagSerializer(tags, many=True).data,
            self._response_data
        )

    def test_search_without_search_word(self):
        self._get()

        self._assert_failure(400, 'Unable to search with empty string.')

    def test_search_with_empty_string(self):
        self._get({'search_word': ''})

        self._assert_failure(400, 'Unable to search with empty string.')


class GetRelatedSearchWordsTestCase(ViewTestCase):
    _url = '/products/related-search-words'

    @classmethod
    def setUpTestData(cls):
        fake = Faker()

        cls.__search_query = fake.word()
        main_category = MainCategoryFactory(name=cls.__search_query)

        for i in range(3):
            SubCategoryFactory(
                main_category=main_category, name=fake.word() + cls.__search_query + str(i)
            )

        for i in range(3):
            KeyWordFactory(name=fake.word() + cls.__search_query + str(i))

    def test_success(self):
        self._get({'search_word': self.__search_query})
        main_categories = MainCategory.objects.filter(name__contains=self.__search_query)
        sub_categories = SubCategory.objects.filter(name__contains=self.__search_query)
        keywords = list(Keyword.objects.filter(name__contains=self.__search_query).values_list('name', flat=True))
        expected_response_data = {
            'main_category': MainCategorySerializer(main_categories, many=True, exclude_fields=('sub_categories',)).data,
            'sub_category': SubCategorySerializer(sub_categories, many=True).data,
            'keyword': sort_keywords_by_levenshtein_distance(keywords, self.__search_query),
        }

        self._assert_success()
        self.assertDictEqual(self._response_data, expected_response_data)
        
    def test_get_without_search_word(self):
        self._get()

        self._assert_failure(400, 'Unable to search with empty string.')

    def test_search_with_empty_string(self):
        self._get({'search_word': ''})

        self._assert_failure(400, 'Unable to search with empty string.')


class GetProductRegistrationTestCase(ViewTestCase):
    _url = '/products/registration-datas'

    def test(self):
        self._set_wholesaler()
        self._set_authentication()
        SettingItemFactory(group__app='not_product')
        instances = get_product_registration_test_data({'app': 'product'})
        instances['setting_groups'] = instances['setting_groups'].filter(app='product')
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, ProductRegistrationSerializer(instances).data)


class GetProductQuestionAnswerClassificationTestCase(ViewTestCase):
    _url = '/products/question-answers/classifications'

    def test_get(self):
        classifications = ProductQuestionAnswerClassificationFactory.create_batch(size=3)
        self._get()

        self._assert_success()
        self.assertListEqual(
            self._response_data,
            ProductQuestionAnswerClassificationSerializer(classifications, many=True).data
        )


class ProductViewSetTestCase(ViewTestCase):
    _url = '/products'
    _batch_size = 2

    @classmethod
    def setUpTestData(cls):
        wholesaler = cls._user if isinstance(cls._user, Wholesaler) else WholesalerFactory()

        cls._product = ProductFactory(wholesaler=wholesaler, additional_information=create_product_additional_information(True))
        cls._sub_categories = SubCategoryFactory.create_batch(size=cls._batch_size)
        cls._colors = ColorFactory.create_batch(size=cls._batch_size)

        for i in range(cls._batch_size):
            product = ProductFactory(
                product = cls._product,
                sub_category=cls._sub_categories[i], 
                wholesaler=wholesaler
            )
            ProductColorFactory(product=product, color=cls._colors[i])

        ProductFactory(product=cls._product, on_sale=False, wholesaler=WholesalerFactory())

        cls._product.tags.add(TagFactory())
        cls._product.laundry_informations.add(LaundryInformationFactory())
        OptionFactory(product_color=ProductColorFactory(product=cls._product))
        ProductImageFactory(product=cls._product)
        ProductMaterialFactory(product=cls._product)


class ProductViewSetForShopperTestCase(ProductViewSetTestCase):
    __default_sorting = '-created_at'
    fixtures = ['coupon', 'coupon_classification']

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()
        super(ProductViewSetForShopperTestCase, cls).setUpTestData()

    def setUp(self):
        self._set_authentication()

    def __get_list_allow_fields(self):
        return ('id', 'created_at', 'name', 'price', 'sale_price', 'base_discount_rate', 'base_discounted_price')

    def __get_queryset(self):
        prefetch_images = Prefetch('images', to_attr='related_images')
        queryset = Product.objects.prefetch_related(
            prefetch_images
        ).filter(on_sale=True).order_by('-created_at').alias(Count('id'))

        return queryset

    def __test_list_response(self, queryset, query_params={}, context={}):
        context.update({'detail': False})
        serializer = ProductReadSerializer(
            queryset, many=True, allow_fields=self.__get_list_allow_fields(), context=context
        )
        self._get(query_params)

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)
        self.assertEqual(self._response_data['count'], queryset.count())

    def test_search(self):
        fake = Faker()
        search_word = fake.word()

        for _ in range(3):
            ProductFactory(product=self._product, name=search_word + fake.word())

        for i in range(3):
            tag = TagFactory(name=fake.word() + search_word + str(i))
            product = Product.objects.order_by('?').first()
            product.tags.add(tag)

        tag_id_list = list(Tag.objects.filter(name__contains=search_word).values_list('id', flat=True))
        condition = Q(tags__id__in=tag_id_list) | Q(name__contains=search_word)

        queryset = self.__get_queryset().filter(condition)
        max_price = queryset.aggregate(max_price=Max('sale_price'))['max_price']

        self.__test_list_response(queryset, query_params={'search_word': search_word})
        self.assertEqual(self._response_data['max_price'], max_price)

    def test_failure_invalid_integer_format(self):
        self._get({'main_category': '1a'})

        self._assert_failure(400, 'Query parameter main_category must be integer format.')

    def test_failure_id_length_more_than_limit(self):
        id_num_limit = 30
        self._get({'id': list(range(id_num_limit + 1))})
        
        self._assert_failure(400, 'The number of id must not be more than 30.')

    def test_failure_search_with_empty_string(self):
        self._get({'search_word': ''})

        self._assert_failure(400, 'Unable to search with empty string.')

    def test_failure_filter_with_main_category_and_sub_category_at_once(self):
        self._get({'main_category': 1, 'sub_category': 1})

        self._assert_failure(400, 'You cannot filter main_category and sub_category at once.')  

    def test_list(self):
        queryset = self.__get_queryset()
        max_price = queryset.aggregate(max_price=Max('sale_price'))['max_price']

        self.__test_list_response(self.__get_queryset())
        self.assertEqual(self._response_data['max_price'], max_price)

    def test_list_like_products(self):
        self._unset_authentication()
        refresh = RefreshToken.for_user(self._user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        self._user.shopper.like_products.add(self._product)
        queryset = self.__get_queryset().filter(like_shoppers=self._user.shopper)
        shoppers_like_products_id_list = list(self._user.shopper.like_products.all().values_list('id', flat=True))
        context = {'detail': False, 'shoppers_like_products_id_list': shoppers_like_products_id_list}

        self.__test_list_response(queryset, {'like': ''}, context)

    def test_recently_viewed_products(self):
        id_list = list(Product.objects.all()[:2].values_list('id', flat=True))
        order_condition = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(id_list)])
        queryset= self.__get_queryset().filter(id__in=id_list).order_by(order_condition)

        self.__test_list_response(queryset, {'id': id_list})

    def __test_filtering(self, query_params):
        filter_set = {}
        filter_mapping = {
            'main_category': 'sub_category__main_category_id',
            'sub_category': 'sub_category_id',
            'min_price': 'sale_price__gte',
            'max_price': 'sale_price__lte',
            'color': 'colors__color_id',
        }

        aggregate_qs = self.__get_queryset()
        if 'main_category' in query_params:
            aggregate_qs = aggregate_qs.filter(
                                **{filter_mapping['main_category']: query_params['main_category']}
                            )
        if 'sub_category' in query_params:
            aggregate_qs = aggregate_qs.filter(
                                **{filter_mapping['sub_category']: query_params['sub_category']}
                            )
        max_price = aggregate_qs.aggregate(max_price=Max('sale_price'))['max_price']

        for key, value in query_params.items():
            if isinstance(value, list):
                filter_set[filter_mapping[key] + '__in'] = value
            else:
                filter_set[filter_mapping[key]] = value

        queryset = self.__get_queryset().filter(**filter_set)
        filtered_products_count = queryset.count()

        self.__test_list_response(queryset, query_params=query_params)
        self.assertEqual(self._response_data['max_price'], max_price)
        self.assertEqual(self._response_data['count'], filtered_products_count)

    def test_filter_main_category(self):
        main_category_id = random.choice(self._sub_categories).main_category_id

        self.__test_filtering({'main_category': main_category_id})

    def test_filter_sub_category(self):
        sub_category_id = random.choice(self._sub_categories).id

        self.__test_filtering({'sub_category': sub_category_id})

    def test_filter_minprice(self):
        price_avg = self.__get_queryset().aggregate(avg=Avg('sale_price'))['avg']

        self.__test_filtering({'min_price': int(price_avg)})

    def test_filter_maxprice(self):
        price_avg = self.__get_queryset().aggregate(avg=Avg('sale_price'))['avg']

        self.__test_filtering({'max_price': int(price_avg)})

    def test_filter_color(self):
        color_id = random.choice(self._colors).id

        self.__test_filtering({'color': color_id})

    def test_filter_color_list(self):
        color_id = [color.id for color in self._colors]

        self.__test_filtering({'color': color_id})

    def test_filter_multiple_key(self):
        aggregation = self.__get_queryset().aggregate(
                                max_price=Max('sale_price'), min_price=Min('sale_price'), 
                                avg_price=Avg('sale_price')
                            )

        color_list = random.sample(list(Color.objects.all()), 2)
        color_id_list = [color.id for color in color_list]
        query_params = {
            'main_category': self._product.sub_category.main_category_id,
            'max_price': aggregation['max_price'] - 1,
            'min_price': aggregation['min_price'] + 1,
            'color': color_id_list,
        }

        self.__test_filtering(query_params)

    def test_filter_all_products_coupon(self):
        coupon = Coupon.objects.filter(classification_id=1).first()
        queryset = self.__get_queryset()

        self.__test_list_response(queryset, {'coupon': coupon.id})

    def test_filter_partial_products_coupon(self):
        coupon = Coupon.objects.filter(classification_id=2).first()
        queryset = self.__get_queryset()[1:]
        coupon.products.add(*queryset)

        self.__test_list_response(queryset, {'coupon': coupon.id})

    def test_filter_sub_category_coupon(self):
        coupon = Coupon.objects.filter(classification_id=3).first()

        sub_category = SubCategoryFactory()
        ProductFactory.create_batch(size=3, sub_category=sub_category, product=self._product)
        coupon.sub_categories.add(sub_category)

        queryset = self.__get_queryset().filter(sub_category=sub_category)

        self.__test_list_response(queryset, {'coupon': coupon.id})

    def test_filter_signup_products_coupon(self):
        coupon = Coupon.objects.filter(classification_id=5).first()
        queryset = self.__get_queryset()

        self.__test_list_response(queryset, {'coupon': coupon.id})

    def __test_sorting(self, sort_key):
        sort_mapping = {
            'price_asc': 'sale_price',
            'price_desc': '-sale_price',
        }
        sort_fields = [sort_mapping[sort_key], self.__default_sorting]
        queryset = self.__get_queryset().order_by(*sort_fields)

        self.__test_list_response(queryset, {'sort': sort_key})

    def test_sort_price_asc(self):
        self.__test_sorting('price_asc')

    def test_sort_price_desc(self):
        self.__test_sorting('price_desc')

    def test_retrieve(self):
        product_id = self._product.id
        product = self.__get_queryset().annotate(total_like=Count('like_shoppers')).get(id=product_id)
        allow_fields = '__all__'
        serializer = ProductReadSerializer(product, allow_fields=allow_fields, context={'detail': True})

        self._url += '/{0}'.format(product.id)
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, serializer.data)


class ProductViewSetForWholesalerTestCase(ProductViewSetTestCase):
    fixtures = ['temporary_image']

    @classmethod
    def setUpTestData(cls):
        cls._set_wholesaler()
        super(ProductViewSetForWholesalerTestCase, cls).setUpTestData()

    def setUp(self):
        self._set_authentication()

    def __get_queryset(self):
        prefetch_images = Prefetch('images', to_attr='related_images')
        queryset = Product.objects.prefetch_related(prefetch_images).filter(wholesaler=self._user).order_by('-created_at')

        return queryset

    def test_list(self):
        queryset = self.__get_queryset()

        allow_fields = ('id', 'name', 'created_at', 'price', 'sale_price', 'base_discount_rate', 'base_discounted_price')
        serializer = ProductReadSerializer(queryset, many=True, allow_fields=allow_fields, context={'detail': False})
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)

    def test_retrieve(self):
        product_id = self._product.id
        product = self.__get_queryset().annotate(total_like=Count('like_shoppers')).get(id=product_id)
        serializer = ProductReadSerializer(product, allow_fields='__all__', context={'detail': True})

        self._url += '/{0}'.format(product.id)
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, serializer.data)

    def test_create(self):
        tag_id_list = [tag.id for tag in TagFactory.create_batch(size=self._batch_size)]
        laundry_information_id_list = [
            laundry_information.id for laundry_information in LaundryInformationFactory.create_batch(size=self._batch_size)
        ]
        image_url_list = list(TemporaryImage.objects.all()[:5].values_list('image_url', flat=True))
        
        self._test_data = {
            'name': 'name',
            'price': 50000,
            'sub_category': self._product.sub_category.id,
            'style': self._product.style.id,
            'age': self._product.age.id,
            'tags': tag_id_list,
            'materials': [
                {
                    'material': '가죽',
                    'mixing_rate': 80,
                },
                {
                    'material': '면', 
                    'mixing_rate': 20,
                },
            ],
            'laundry_informations': laundry_information_id_list,
            'additional_information': {
                'thickness': self._product.additional_information.thickness.id,
                'see_through': self._product.additional_information.see_through.id,
                'flexibility': self._product.additional_information.flexibility.id,
                'lining': self._product.additional_information.lining_id,
            },
            'manufacturing_country': '대한민국',
            'images': [
                {
                    'image_url': BASE_IMAGE_URL + image_url_list.pop(),
                    'sequence': 1,
                },
                {
                    'image_url': BASE_IMAGE_URL + image_url_list.pop(),
                    'sequence': 2,
                },
                {
                    'image_url': BASE_IMAGE_URL + image_url_list.pop(),
                    'sequence': 3,
                }
            ],
            'colors': [
                {
                    'color': self._colors[0].id,
                    'display_color_name': '다크',
                    'options': [
                        {'size': 'Free'},
                        {'size': 'S'},
                    ],
                    'image_url': BASE_IMAGE_URL + image_url_list.pop(),
                },
                {
                    'color': self._colors[1].id,
                    'display_color_name': '블랙',
                    'options': [
                        {'size': 'Free'},
                        {'size': 'S'},
                    ],
                    'image_url': BASE_IMAGE_URL + image_url_list.pop(),
                }
            ]
        }
        self._post(format='json')

        self._assert_success_with_id_response()
        self.assertTrue(Product.objects.filter(id=self._response_data['id']).exists())

    def test_partial_update(self):
        product = Product.objects.filter(wholesaler=self._user).last()
        self._test_data = {
            'name': 'name_update',
            'price': 15000
        }
        self._url += '/{0}'.format(product.id)
        self._patch()

        self._assert_success_and_serializer_class(ProductWriteSerializer)
        self.assertEqual(self._response_data['id'], product.id)

    def test_destroy(self):
        product = Product.objects.filter(wholesaler=self._user).last()
        self._url += '/{0}'.format(product.id)
        self._delete()
        deleted_product = Product.objects.get(id=self._response_data['id'])

        self._assert_success_with_id_response()
        self.assertTrue(not deleted_product.on_sale)
        self.assertTrue(not deleted_product.colors.filter(on_sale=True).exists())
        self.assertTrue(not Option.objects.filter(product_color__product=deleted_product, on_sale=True).exists())
        self.assertTrue(not deleted_product.question_answers.all().exists())


class ProductQuestionAnswerViewSetTestCase(ViewTestCase):
    _url = '/products/{0}/question-answers'

    @classmethod
    def setUpTestData(cls):
        cls.__product = ProductFactory()
        cls._url = cls._url.format(cls.__product.id)

        cls._test_data = {
            'question': 'question',
            'is_secret': True,
            'classification': ProductQuestionAnswerClassificationFactory().id,
        }

    def setUp(self):
        self._set_shopper()
        self._set_authentication()
        self.__question_answer = ProductQuestionAnswerFactory(shopper=self._user, product=self.__product)

    def test_get(self):
        ProductQuestionAnswerFactory.create_batch(size=3, product=self.__product)
        serializer = ProductQuestionAnswerSerializer(ProductQuestionAnswer.objects.all(), many=True)
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)

    def test_create(self):
        self._post()

        self._assert_success_with_id_response()
        self.assertTrue(ProductQuestionAnswer.objects.filter(id=self._response_data['id']).exists())

    def test_partial_update(self):
        self._url += '/{}'.format(self.__question_answer.id)
        self._patch({'question': 'question_update'})

        self._assert_success_and_serializer_class(ProductQuestionAnswerSerializer)
        self.assertEqual(self._response_data['id'], self.__question_answer.id)

    def test_destroy(self):
        self._url += '/{}'.format(self.__question_answer.id)
        self._delete()

        self._assert_success_with_id_response()
        self.assertTrue(not ProductQuestionAnswer.objects.filter(id=self._response_data['id']).exists())
