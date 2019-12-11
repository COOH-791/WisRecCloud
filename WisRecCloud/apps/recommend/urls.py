from django.conf.urls import url

from .views import RecommendView

urlpatterns = [
    url(r'wisRecCloud/api/recommend/', RecommendView.as_view(), name="Rem"),  # 杰卡德数据召回
]
