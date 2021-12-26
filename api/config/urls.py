from django.conf.urls import handler403, handler404, handler500, handler400
from django.contrib import admin
from django.urls import path, include, re_path

from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

handler400 = 'common.views.custom_400_view'
handler403 = 'common.views.custom_403_view'
handler404 = 'common.views.custom_404_view'
handler500 = 'common.views.custom_500_view'

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API", # API 제목
      default_version='v1', # API 버전, Swagger 버전과 다름
      description="Test description", # API 설명, markdown 지원
      terms_of_service="https://www.google.com/policies/terms/", #서비스 약관
      contact=openapi.Contact(email="contact@snippets.local"), #contact 오브젝트
      license=openapi.License(name="BSD License"), # license 오브젝트
   ),
   public=True,
   permission_classes=(AllowAny,),
)

urlpatterns = [
   re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
   path('user/', include('user.urls')),
   path('product/', include('product.urls'))
]
