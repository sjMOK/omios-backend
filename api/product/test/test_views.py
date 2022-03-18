import random
from django.db.models.query import Prefetch
from django.db.models import Avg, Max, Min

from faker import Faker

from common.test.test_cases import ViewTestCase, FunctionTestCase
from common.utils import levenshtein
from user.test.factory import WholesalerFactory
from user.models import Wholesaler
from .factory import (
    ColorFactory, LaundryInformationFactory, MainCategoryFactory, OptionFactory, ProductColorFactory, ProductFactory, ProductImagesFactory, 
    ProductMaterialFactory, SizeFactory, SubCategoryFactory, KeyWordFactory, TagFactory,
)
from ..views import sort_keywords_by_levenshtein_distance
from ..models import (
    Flexibility, LaundryInformation, MainCategory, SeeThrough, SubCategory, Keyword, Color, Material, Style, Age, Thickness,
    Product, ProductColor,
)
from ..serializers import (
    FlexibilitySerializer, LaundryInformationSerializer, MainCategorySerializer, ProductReadSerializer, SeeThroughSerializer, SizeSerializer, 
    SubCategorySerializer, ColorSerializer, MaterialSerializer, StyleSerializer, AgeSerializer, ThicknessSerializer, ProductWriteSerializer,
)


class SortKeywordsByLevenshteinDistance(FunctionTestCase):
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


class GetSearchboxDataTestCase(ViewTestCase):
    _url = '/product/searchbox/'

    @classmethod
    def setUpTestData(cls):
        fake = Faker()

        cls.search_query = fake.word()
        main_category = MainCategoryFactory(name=cls.search_query)

        for _ in range(3):
            SubCategoryFactory(
                main_category=main_category, name=fake.word()+cls.search_query+fake.word()
            )

        for _ in range(5):
            KeyWordFactory(name=fake.word()+cls.search_query+fake.word())

    def test_success(self):
        self._get({'query': self.search_query})
        main_categories = MainCategory.objects.filter(name__contains=self.search_query)
        sub_categories = SubCategory.objects.filter(name__contains=self.search_query)
        keywords = list(Keyword.objects.filter(name__contains=self.search_query).values_list('name', flat=True))
        expected_response_data = {
            'main_category': MainCategorySerializer(main_categories, many=True, allow_fields=('id', 'name')).data,
            'sub_category': SubCategorySerializer(sub_categories, many=True).data,
            'keyword': sort_keywords_by_levenshtein_distance(keywords, self.search_query),
        }

        self._assert_success()
        self.assertDictEqual(self._response_data, expected_response_data)
        
    def test_get_without_search_word(self):
        self._get()

        self._assert_failure(400, 'Unable to search with empty string.')


class GetCommonRegistrationDataTestCase(ViewTestCase):
    _url = '/product/registry-common/'

    def test_get(self):
        expected_response_data = {
            'color': ColorSerializer(Color.objects.all(), many=True).data,
            'material': MaterialSerializer(Material.objects.all(), many=True).data,
            'style': StyleSerializer(Style.objects.all(), many=True).data,
            'age': AgeSerializer(Age.objects.all(), many=True).data,
        }
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, expected_response_data)


class GetDynamicRegistrationDataTestCase(ViewTestCase):
    _url = '/product/registry-dynamic/'

    @classmethod
    def setUpTestData(cls):
        cls.sizes = SizeFactory.create_batch(size=3)

    def test_get_with_sub_category_require_nothing(self):
        sub_category = SubCategoryFactory(
            require_product_additional_information=False, 
            require_laundry_information=False
        )
        sub_category.sizes.add(*self.sizes)
        expected_response_data = {
            'size': SizeSerializer(sub_category.sizes.all(), many=True).data,
            'thickness': [],
            'see_through': [],
            'flexibility': [],
            'lining': [],
            'laundry_inforamtion': []
        }
        self._get({'sub_category': sub_category.id})

        self._assert_success()
        self.assertDictEqual(self._response_data, expected_response_data)

    def test_get_with_sub_category_require_product_additional_information(self):
        sub_category = SubCategoryFactory(
            require_product_additional_information=True, 
            require_laundry_information=False
        )
        sub_category.sizes.add(*self.sizes)
        expected_response_data = {
            'size': SizeSerializer(sub_category.sizes.all(), many=True).data,
            'thickness': ThicknessSerializer(Thickness.objects.all(), many=True).data,
            'see_through': SeeThroughSerializer(SeeThrough.objects.all(), many=True).data,
            'flexibility': FlexibilitySerializer(Flexibility.objects.all(), many=True).data,
            'lining': [
                {'name': '있음', 'value': True},
                {'name': '없음', 'value': False},
            ],
            'laundry_inforamtion': []
        }
        self._get({'sub_category': sub_category.id})

        self._assert_success()
        self.assertDictEqual(self._response_data, expected_response_data)

    def test_get_with_sub_category_require_laundry_information(self):
        sub_category = SubCategoryFactory(
            require_product_additional_information=False, 
            require_laundry_information=True
        )
        sub_category.sizes.add(*self.sizes)
        expected_response_data = {
            'size': SizeSerializer(sub_category.sizes.all(), many=True).data,
            'thickness': [],
            'see_through': [],
            'flexibility': [],
            'lining': [],
            'laundry_inforamtion': LaundryInformationSerializer(LaundryInformation.objects.all(), many=True).data,
        }
        self._get({'sub_category': sub_category.id})

        self._assert_success()
        self.assertDictEqual(self._response_data, expected_response_data)

    def test_get_with_sub_category_require_all_information(self):
        sub_category = SubCategoryFactory()
        sub_category.sizes.add(*self.sizes)
        expected_response_data = {
            'size': SizeSerializer(sub_category.sizes.all(), many=True).data,
            'thickness': ThicknessSerializer(Thickness.objects.all(), many=True).data,
            'see_through': SeeThroughSerializer(SeeThrough.objects.all(), many=True).data,
            'flexibility': FlexibilitySerializer(Flexibility.objects.all(), many=True).data,
            'lining': [
                {'name': '있음', 'value': True},
                {'name': '없음', 'value': False},
            ],
            'laundry_inforamtion': LaundryInformationSerializer(LaundryInformation.objects.all(), many=True).data,
        }
        self._get({'sub_category': sub_category.id})

        self._assert_success()
        self.assertDictEqual(self._response_data, expected_response_data)

    def test_get_without_sub_category_id(self):
        self._get()

        self._assert_failure(400, 'This request should include sub_category.')


class GetAllCategoriesTestCase(ViewTestCase):
    _url = '/product/category/'

    def test_get(self):
        MainCategoryFactory.create_batch(size=3)
        main_categories = MainCategory.objects.all()
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data, MainCategorySerializer(main_categories, many=True).data)


class GetMainCategoriesTestCase(ViewTestCase):
    _url = '/product/main-category/'

    def test_get(self):
        MainCategoryFactory.create_batch(size=3)
        main_categories = MainCategory.objects.all()
        self._get()

        self._assert_success()
        self.assertListEqual(
            self._response_data, 
            MainCategorySerializer(main_categories, many=True, exclude_fields=('sub_category',)).data
        )


class GetSubCategoriesByMainCategoryTestCase(ViewTestCase):
    _url = '/product/main-category/'

    @classmethod
    def setUpTestData(cls):
        cls.main_category = MainCategoryFactory()
        SubCategoryFactory.create_batch(size=3, main_category=cls.main_category)

    def test_get(self):
        self._url += '{0}/sub-category/'.format(self.main_category.id)
        self._get()

        self._assert_success()
        self.assertListEqual(
            self._response_data, 
            SubCategorySerializer(self.main_category.sub_categories.all(), many=True).data
        )

    def test_get_raise_404(self):
        main_category_id = MainCategory.objects.latest('id').id + 1
        self._url += '{0}/sub-category/'.format(main_category_id)
        self._get()

        self._assert_failure(404, 'Not found.')


class GetColorsTestCase(ViewTestCase):
    _url = '/product/color/'

    def test_get(self):
        self._get()

        self.assertListEqual(
            self._response_data, 
            ColorSerializer(Color.objects.all(), many=True).data
        )


class ProductViewSetTestCase(ViewTestCase):
    _url = '/product/'

    @classmethod
    def setUpTestData(cls):
        cls.sub_categories = SubCategoryFactory.create_batch(size=3)
        cls.colors = ColorFactory.create_batch(size=10)

        product_num = 10
        for _ in range(product_num):
            wholesaler = cls._user if isinstance(cls._user, Wholesaler) else WholesalerFactory()
            product = ProductFactory(
                sub_category=random.choice(cls.sub_categories), 
                price=random.randint(10000, 50000),
                wholesaler=wholesaler
            )
            ProductColorFactory(product=product, color=random.choice(cls.colors))

        ProductFactory.create_batch(size=2, on_sale=False)

    def _get_product(self):
        wholesaler = self._user if isinstance(self._user, Wholesaler) else WholesalerFactory()
        product = ProductFactory(wholesaler=wholesaler)

        tags = TagFactory.create_batch(size=2)
        product.tags.add(*tags)

        laundry_informations = LaundryInformationFactory.create_batch(size=2)
        product.laundry_informations.add(*laundry_informations)

        ProductMaterialFactory.create_batch(size=2, product=product, mixing_rate=50)

        product_colors = ProductColorFactory.create_batch(size=2, product=product)
        for product_color in product_colors:
            OptionFactory.create_batch(size=2, product_color=product_color)

        ProductImagesFactory.create_batch(size=3, product=product)

        return product


class ProductViewSetForShopperTestCase(ProductViewSetTestCase):
    fixtures = ['membership']

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()
        super(ProductViewSetForShopperTestCase, cls).setUpTestData()

    def setUp(self):
        self._set_authentication()

    def __get_queryset(self):
        prefetch_images = Prefetch('images', to_attr='related_images')
        queryset = Product.objects.prefetch_related(prefetch_images).filter(on_sale=True).order_by('-created')

        return queryset

    def __test_list_response(self, queryset, max_price, data={}):
        allow_fields = ('id', 'name', 'price')
        serializer = ProductReadSerializer(queryset, many=True, allow_fields=allow_fields, context={'detail': False})
        self._get(data)

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)
        self.assertEqual(self._response_data['max_price'], max_price)

    def test_list(self):
        queryset = self.__get_queryset()
        max_price = queryset.aggregate(max_price=Max('price'))['max_price']

        self.__test_list_response(self.__get_queryset(), max_price)      

    def __test_filtering(self, query_params):
        filter_set = {}
        filter_mapping = {
            'main_category': 'sub_category__main_category_id',
            'sub_category': 'sub_category_id',
            'min_price': 'price__gte',
            'max_price': 'price__lte',
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
        max_price = aggregate_qs.aggregate(max_price=Max('price'))['max_price']

        for key, value in query_params.items():
            if isinstance(value, list):
                filter_set[filter_mapping[key] + '__in'] = value
            else:
                filter_set[filter_mapping[key]] = value

        queryset = self.__get_queryset().filter(**filter_set)
        self.__test_list_response(queryset, max_price, data=query_params)

        filtered_products_count = queryset.count()
        self.assertEqual(self._response_data['count'], filtered_products_count)

    def test_filter_main_category(self):
        main_category_id = random.choice(self.sub_categories).main_category_id

        self.__test_filtering({'main_category': main_category_id})

    def test_filter_sub_category(self):
        sub_category_id = random.choice(self.sub_categories).id

        self.__test_filtering({'sub_category': sub_category_id})

    def test_filter_minprice(self):
        price_avg = Product.objects.all().aggregate(avg=Avg('price'))['avg']

        self.__test_filtering({'min_price': int(price_avg)})

    def test_filter_maxprice(self):
        price_avg = Product.objects.all().aggregate(avg=Avg('price'))['avg']

        self.__test_filtering({'max_price': int(price_avg)})

    def test_filter_color(self):
        color_id = random.choice(self.colors).id

        self.__test_filtering({'color': color_id})

    def test_filter_color_list(self):
        colors = random.sample(self.colors, 3)
        color_id = [color.id for color in colors]

        self.__test_filtering({'color': color_id})

    def test_filter_multiple_key(self):
        aggregation = Product.objects.all().aggregate(
                                max_price=Max('price'), min_price=Min('price'), 
                                avg_price=Avg('price')
                            )

        product = Product.objects.all().last()
        color_list = random.sample(list(Color.objects.all()), 2)
        color_id_list = [color.id for color in color_list]
        query_params = {
            'main_category': product.sub_category.main_category_id,
            'sub_category': product.sub_category_id,
            'max_price': int((aggregation['max_price'] + aggregation['avg_price']) / 2),
            'min_price': int((aggregation['min_price'] + aggregation['avg_price']) / 2),
            'color': color_id_list,
        }

        self.__test_filtering(query_params)

    def __test_sorting(self, sort_key):
        sort_mapping = {
            'price_asc': 'price',
            'price_dsc': '-price',
        }

        products = self.__get_queryset().order_by(sort_mapping[sort_key])
        allow_fields = ('id', 'name', 'price')
        serializer = ProductReadSerializer(products, many=True, allow_fields=allow_fields, context={'detail': False})

        self._get({'sort': sort_key})

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)

    def test_sort_price_asc(self):
        self.__test_sorting('price_asc')

    def test_sort_price_desc(self):
        self.__test_sorting('price_dsc')

    def test_retrieve(self):
        product_id = self._get_product().id
        product = self.__get_queryset().get(id=product_id)
        allow_fields = (
            'id', 'name', 'price', 'main_category', 'sub_category', 'style', 'age', 'tags', 'laundry_informations',
            'thickness', 'see_through', 'flexibility', 'lining', 'materials', 'colors', 'images',
        )
        serializer = ProductReadSerializer(product, allow_fields=allow_fields, context={'detail': True})

        self._url += '{0}/'.format(product.id)
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, serializer.data)

    def test_search_without_search_word(self):
        self._url += 'search/'
        self._get()

        self._assert_failure(400, 'Unable to search with empty string.')


class ProductViewSetForWholesalerTestCase(ProductViewSetTestCase):
    _url = '/product/'

    @classmethod
    def setUpTestData(cls):
        cls._set_wholesaler()
        super(ProductViewSetForWholesalerTestCase, cls).setUpTestData()

        for _ in range(5):
            product = ProductFactory(
                sub_category=random.choice(cls.sub_categories), 
                price=random.randint(10000, 50000)
            )
            ProductColorFactory(product=product, color=random.choice(cls.colors))

        ProductFactory.create_batch(size=2, on_sale=False)

    def setUp(self):
        self._set_authentication()

    def __get_queryset(self):
        prefetch_images = Prefetch('images', to_attr='related_images')
        queryset = Product.objects.prefetch_related(prefetch_images).filter(wholesaler=self._user).order_by('-created')

        return queryset

    def test_list(self):
        queryset = self.__get_queryset()

        allow_fields = ('id', 'name', 'price', 'created')
        serializer = ProductReadSerializer(queryset, many=True, allow_fields=allow_fields, context={'detail': False})
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)

    def test_retrieve(self):
        product_id = self._get_product().id
        product = self.__get_queryset().get(id=product_id)
        allow_fields = (
            'id', 'name', 'price', 'colors', 'code', 'sub_category', 'created', 'on_sale', 'images', 'tags'
        )
        serializer = ProductReadSerializer(product, allow_fields=allow_fields, context={'detail': True})

        self._url += '{0}/'.format(product.id)
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, serializer.data)

    def test_create(self):
        tag_id_list = [tag.id for tag in TagFactory.create_batch(size=3)]
        tag_id_list.sort()
        laundry_information_id_list = [
            laundry_information.id for laundry_information in LaundryInformationFactory.create_batch(size=3)
        ]
        laundry_information_id_list.sort()
        color_id_list = [color.id for color in ColorFactory.create_batch(size=2)]

        self._test_data = {
            'name': 'name',
            'price': 50000,
            'sub_category': SubCategory.objects.last().id,
            'style': Style.objects.last().id,
            'age': Age.objects.last().id,
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
            'thickness': Thickness.objects.last().id,
            'see_through': SeeThrough.objects.last().id,
            'flexibility': Flexibility.objects.last().id,
            'lining': True,
            'images': [
                {
                    'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_11.jpg',
                    'sequence': 1
                },
                {
                    'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_12.jpg',
                    'sequence': 2
                },
                {
                    'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_13.jpg',
                    'sequence': 3
                }
            ],
            'colors': [
                {
                    'color': color_id_list[0],
                    'display_color_name': '다크',
                    'options': [
                        {
                            'size': 'Free',
                            'price_difference': 0
                        },
                        {
                            'size': 'S',
                            'price_difference': 0
                        }
                    ],
                    'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_21.jpg'
                },
                {
                    'color': color_id_list[1],
                    'display_color_name': None,
                    'options': [
                        {
                            'size': 'Free',
                            'price_difference': 0
                        },
                        {
                            'size': 'S',
                            'price_difference': 2000
                        }
                    ],
                    'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_22.jpg'
                }
            ]
        }
        self._post(format='json')

        self._assert_success_with_id_response()

    def test_partial_update(self):
        product = Product.objects.filter(wholesaler=self._user).last()
        self._test_data = {
            'name': 'name_update',
            'price': 15000
        }
        self._url += '{0}/'.format(product.id)
        self._patch(format='json')

        self._assert_success_with_id_response()
        updated_product = Product.objects.get(id=self._response_data['id'])
        self.assertEqual(self._response_data['id'], product.id)
        self.assertEqual(updated_product.name, self._test_data['name'])
        self.assertEqual(updated_product.price, self._test_data['price'])

    def test_destroy(self):
        product = Product.objects.filter(wholesaler=self._user).last()
        self._url += '{0}/'.format(product.id)
        self._delete()

        self._assert_success_with_id_response()
        deleted_product = Product.objects.get(id=self._response_data['id'])
        self.assertTrue(not deleted_product.on_sale)
        self.assertTrue(not ProductColor.objects.filter(product=deleted_product, on_sale=True).exists())

    def test_saler(self):
        product_id = self._get_product().id
        product = self.__get_queryset().get(id=product_id)
        serializer = ProductWriteSerializer(product)
        self._url += '{0}/saler/'.format(product.id)
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, serializer.data)