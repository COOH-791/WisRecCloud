import json
import pandas as pd
from django import http
from django.views import View
import redis

# Create your views here.
from apps.recall.models import ClientInfo


class RecommendView(View):
    def get(self, request):
        # 接收参数
        app_id, api_key, secret_key, rem_id = request.GET.get("app_id"), request.GET.get("api_key"), request.GET.get(
            "secret_key"), request.GET.get("rem_id")
        if not all([app_id, api_key, secret_key, rem_id]):  # 认证数据
            return http.JsonResponse({"code": '3001', "statement": "Missing the necessary parameters"})
        _user = ClientInfo.objects.filter(app_id=app_id).filter(api_key=api_key).filter(secret_key=secret_key)
        if not _user:
            return http.JsonResponse({"code": '3002', "statement": "Have no right to access"})
        if not str(rem_id).isdigit():  # 判断是否是一个id
            return http.JsonResponse({"code": '3004', "statement": "The transmitted data is abnormal"})

        # 链接redis
        pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True, db=8)
        conn = redis.StrictRedis(connection_pool=pool)
        result = list()

        for redis_name in conn.keys():  # 匹配数据
            if api_key == json.loads(conn.get(redis_name))["result"]["api_key"]:
                result = json.loads(conn.get(redis_name))["result"]["result"]

        a = pd.DataFrame(result, columns=["U", "V", "score"])  # 排序
        result = a[a["U"] == int(rem_id)].sort_values(by="score", ascending=False)["V"].to_list()

        if not result:
            return http.JsonResponse({"code": "400", "content": "No corresponding recommendation was found"})
        return http.JsonResponse({"code": "200", "content": result})
