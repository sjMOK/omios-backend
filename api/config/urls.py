from django.conf.urls import handler403, handler404, handler500, handler400
from django.urls import path, include, re_path
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from user.urls import token_urlpatterns

handler400 = 'common.views.custom_400_view'
handler403 = 'common.views.custom_403_view'
handler404 = 'common.views.custom_404_view'
handler500 = 'common.views.custom_500_view'

schema_view = get_schema_view(
   openapi.Info(
      # todo 서비스 약관(terms_of_service), 컨텍센터(contact)
      title="Deepy API", # API 제목
      default_version='v1', # API 버전, Swagger 버전과 다름
      description="Deepy REST API 문서", # API 설명, markdown 지원
      license=openapi.License(name="BSD License"), # license 오브젝트
   ),
   # url="http://13.209.244.41",
   public=True,
   permission_classes=(AllowAny,),
)

urlpatterns = [
   re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
   path('token/', include(token_urlpatterns)),
   path('user/', include('user.urls')),
   path('product/', include('product.urls')),
]
