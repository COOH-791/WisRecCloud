from django.conf.urls import url

from .views import RecallData, RecallWeiBo

urlpatterns = [
    url(r'wisRecCloud/api/zhaopin/recall_jcd', RecallData.as_view(), name="jieCard"),  # 招聘数据召回
    url(r'wisRecCloud/api/wenzhang/recall_jcd', RecallWeiBo.as_view(), name="jieCardWeiBo")  # 文章咨询召回接口
]
