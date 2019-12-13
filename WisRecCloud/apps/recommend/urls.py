from django.conf.urls import url

from .views import RecommendViewJcd, RecommendViewCF

urlpatterns = [
    url(r'wisRecCloud/api/recommend/jcd/', RecommendViewJcd.as_view(), name="Rem"),  # 杰卡德数据召回
    url(r'wisRecCloud/api/recommend/user_cf/', RecommendViewCF.as_view(), name="User-CF"),
]
