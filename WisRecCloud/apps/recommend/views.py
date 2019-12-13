import json
import pandas as pd
from django import http
from django.views import View
import redis

from apps.recall.models import MovieCFData, ClientInfo


class RecommendViewJcd(View):
    def get(self, request):
        # 接收参数
        app_id, api_key, secret_key, rem_id = request.GET.get("app_id"), request.GET.get("api_key"), request.GET.get(
            "secret_key"), request.GET.get("rem_id")

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


class RecommendViewCF(View):
    def get(self, request):
        # 接收参数
        app_id, api_key, secret_key, rem_id = request.GET.get("app_id"), request.GET.get("api_key"), request.GET.get(
            "secret_key"), request.GET.get("rem_id")

        if not str(rem_id).isdigit():  # 判断是否是一个id
            return http.JsonResponse({"code": '3004', "statement": "The transmitted data is abnormal"})

        # 链接redis
        pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True, db=8)
        conn = redis.StrictRedis(connection_pool=pool)
        users_sim = dict()
        for redis_name in conn.keys():  # 匹配用户相似度矩阵
            if api_key == json.loads(conn.get(redis_name))["result"]["api_key"]:
                users_sim = json.loads(conn.get(redis_name))["result"]["result"]
        # print(userSim)
        # 1.加载原数据集
        client_id = ClientInfo.objects.get(api_key=api_key).id
        data = MovieCFData.objects.filter(client_id_id=str(client_id))
        data = [(x.user_id, x.movie_id, x.ratting) for x in data]
        new_data = dict()
        for user, item, record in data:
            new_data.setdefault(user, {})
            new_data[user][item] = record
        # 计算推荐结果
        result = dict()
        have_score_items = new_data.get(int(rem_id), {})
        for v, wuv in sorted(users_sim[rem_id].items(), key=lambda x: x[1], reverse=True)[:8]:
            for i, rvi in new_data[int(v)].items():
                if i in have_score_items:
                    continue
                result.setdefault(i, 0)
                result[i] += wuv * rvi
        a = [x for x in dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[0:40]).keys()]
        result = {
            "code": 200,
            "result": a
        }
        return http.JsonResponse(result)
