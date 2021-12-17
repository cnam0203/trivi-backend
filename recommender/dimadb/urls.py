from django.urls import path
from .views import DomainList, home, CulturalProductList, WebActivityList, CulturalProductDetail

urlpatterns = [
    path('domain/', DomainList.as_view()),
    path('product/', CulturalProductList.as_view()),
    path('activity/', WebActivityList.as_view()),
    path('home/', home),
    path('product/<type>/new-product', CulturalProductDetail.as_view()),
    path('product/<type>/<pk>/', CulturalProductDetail.as_view()),
]