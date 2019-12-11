import json
from celery import Celery
from django.db import DatabaseError
from django.views import View
from django import http
from apps.recall.models import ClientInfo, JieCardData
from apps.recall.utils import get_key_words

# Create your views here.


class RecallData(View):
    def get(self, request):
        pass

    def put(self, request):
        """
        接收召回数据
        :param request:
        :return:
        """
        app_id, api_key, secret_key = request.GET.get("app_id"), request.GET.get("api_key"), request.GET.get(
            "secret_key")

        if not all([app_id, api_key, secret_key]):  # 认证数据
            return http.JsonResponse({"code": '3001', "statement": "Missing the necessary parameters"})
        _user = ClientInfo.objects.filter(app_id=app_id).filter(api_key=api_key).filter(secret_key=secret_key)
        if not _user:
            return http.JsonResponse({"code": '3002', "statement": "Have no right to access"})

        _data = json.loads(request.body.decode())  # 判断数据
        temp_id, digest = _data["id"], _data["digest"]
        if not all([temp_id, digest]):
            return http.JsonResponse({"code": '3003', "statement": "The transmitted data is abnormal"})
        if not str(temp_id).isdigit():
            return http.JsonResponse({"code": '3004', "statement": "The transmitted data is abnormal"})

        try:  # 保存数据
            databases = JieCardData(
                data_id=temp_id,
                key_digest=get_key_words(digest),
                client_id_id=ClientInfo.objects.get(app_id=app_id).id
            )
            databases.save()
        except DatabaseError:
            return http.JsonResponse({'code': "3008", "statement": "Data insert failed"})
        # 若积累的用户数据大于10则启动异步计算
        key_words_num = JieCardData.objects.filter(client_id_id=1).filter(indexer=0).count()
        if key_words_num >= 5:
            user_api_key = ClientInfo.objects.get(app_id=app_id).id
            app = Celery(
                # broker='amqp://guest@lo4calhost//',  # 消息队列的url
                # backend='amqp://guest@localhost//',  # 将调用的结果存储到MQ中
                backend='redis://localhost:6379/8'  # 将调用的结果存储到Redis中
            )
            ret = app.send_task('task.get_key', args=[user_api_key, api_key])
            print(ret)
        return http.JsonResponse({"code": '2001', "statement": "successful"})
