from django.urls import path
from .views import *

urlpatterns = [
    path('home/', home),
    path('list-item/<item_type>/', ItemList.as_view()),
    path('get-item/<item_type>/<pk>/', ItemDetail.as_view()),
    path('import-file/<item_type>/', import_json_file),
    path('import-api/', import_api),
    path('get-recommend-api/', get_recommend_api),
    path('get-recommend-info/', get_recommend_info),
    path('get-configure-info/', get_configure_info),
    path('get-recommendation/', get_recommendation),
    path('train-similar-recommend/', train_similar_recommend),
    path('get-import-info/<item_type>/', get_import_info),
    path('get-mapping-templates/<item_type>/', get_mapping_templates),
    path('delete-multiple-items/<item_type>/<pk>/', delete_multiple_items),
    path('get-reports/', get_reports),
    path('update-activity-weight/', update_activity_weight),
]
