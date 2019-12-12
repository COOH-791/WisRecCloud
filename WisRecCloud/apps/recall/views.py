import json
from celery import Celery
from django.db import DatabaseError
from django.views import View
from django import http
from apps.recall.models import ClientInfo, JieCardData, MovieCFData
from apps.recall.utils import get_info_words, get_key_words


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

        _data = json.loads(request.body.decode())  # 判断数据
        temp_id, digest = _data["id"], _data["digest"]
        if not all([temp_id, digest]):
            return http.JsonResponse({"code": '3003', "statement": "The transmitted data is abnormal"})
        if not str(temp_id).isdigit():
            return http.JsonResponse({"code": '3004', "statement": "The transmitted data is abnormal"})

        try:  # 保存数据
            databases = JieCardData(
                data_id=temp_id,
                key_digest=get_info_words(digest),  # 使用文章专用分词器提取关键字
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
        return http.JsonResponse({"code": '2001', "statement": "successful"})


class RecallWeiBo(View):
    def put(self, request):
        """
        接收召回数据
        :param request:
        :return:
        """
        app_id, api_key, secret_key = request.GET.get("app_id"), request.GET.get("api_key"), request.GET.get(
            "secret_key")
        _data = json.loads(request.body.decode())  # 判断数据
        temp_id, digest = _data["id"], _data["digest"]
        if not all([temp_id, digest]):  # 判断数据是否齐全
            return http.JsonResponse({"code": '3003', "statement": "The transmitted data is abnormal"})
        if not str(temp_id).isdigit():  # 判断id是否有效
            return http.JsonResponse({"code": '3004', "statement": "The transmitted data is abnormal"})

        try:  # 入库
            databases = JieCardData(
                data_id=temp_id,
                key_digest=get_key_words(digest),  # 使用招聘专用分词器提取关键字
                client_id_id=ClientInfo.objects.get(app_id=app_id).id
            )
            databases.save()
        except DatabaseError:
            return http.JsonResponse({'code': "3008", "statement": "Data insert failed"})

        # 若积累的用户数据大于10则启动异步计算
        user_api_key = ClientInfo.objects.get(app_id=app_id).id
        app = Celery(
            # broker='amqp://guest@lo4calhost//',  # 消息队列的url
            # backend='amqp://guest@localhost//',  # 将调用的结果存储到MQ中
            backend='redis://localhost:6379/8'  # 将调用的结果存储到Redis中
        )
        ret = app.send_task('task.get_key', args=[user_api_key, api_key])
        return http.JsonResponse({"code": "200", "statement": "successful"})


class RecallMovie(View):
    def put(self, request):
        """
        UserCF ItemCF 数据源召回接口
        :param request:
        :return:
        """
        # 1.获取数据
        api_key = request.GET.get("api_key")
        _data = json.loads(request.body.decode())
        user_id, movie_id, ratting = _data["user_id"], _data["movie_id"], _data["ratting"]
        # 2.判断数据是否符合规格
        if not all([user_id, movie_id, ratting]):
            return http.JsonResponse({"code": '3003', "statement": "The transmitted data is abnormal"})
        if not str(user_id).isdigit():
            return http.JsonResponse({"code": '3004', "statement": "The transmitted data is abnormal"})
        if not str(movie_id).isdigit():
            return http.JsonResponse({"code": '3004', "statement": "The transmitted data is abnormal"})
        try:  # 判断是否为小数
            _ = int(ratting)
        except ValueError:
            return http.JsonResponse({"code": '3004', "statement": "The transmitted data is abnormal"})
        # 3.入库
        try:  # 入库
            databases = MovieCFData(
                user_id=user_id,
                movie_id=movie_id,
                ratting=ratting,
                client_id_id=ClientInfo.objects.get(api_key=api_key).id
            )
            databases.save()
        except DatabaseError:
            return http.JsonResponse({'code': "3008", "statement": "Data insert failed"})
        # 4.计算
        return http.JsonResponse({"code": "200", "statement": "successful"})
