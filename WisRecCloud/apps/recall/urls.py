from django.conf.urls import url

from .views import RecallData

urlpatterns = [
    url(r'wisRecCloud/api/zhaopin/recall_jcd', RecallData.as_view(), name="jieCard"),  # 杰卡德数据召回
]
