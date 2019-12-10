import json

from django.db import DatabaseError
from django.views import View
from django import http
from apps.recall.models import ClientInfo, JieCardData


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
        if not ClientInfo.objects.filter(app_id=app_id).filter(api_key=api_key).filter(secret_key=secret_key):
            return http.JsonResponse({"code": '3002', "statement": "Have no right to access"})

        _data = json.loads(request.body.decode())  # 判断数据
        temp_id, digest = _data["id"], _data["digest"]
        if not all([temp_id, digest]):
            return http.JsonResponse({"code": '3003', "statement": "The transmitted data is abnormal"})
        if not str(temp_id).isdigit():
            return http.JsonResponse({"code": '3004', "statement": "The transmitted data is abnormal"})

        try:
            databases = JieCardData(
                data_id=temp_id,
                digest=digest,
                client_id_id=ClientInfo.objects.get(app_id=app_id).id
            )
            databases.save()
        except DatabaseError:
            return http.JsonResponse({'code': "3008", "statement": "Data insert failed"})

        return http.JsonResponse({"code": '2001', "statement": "successful"})
