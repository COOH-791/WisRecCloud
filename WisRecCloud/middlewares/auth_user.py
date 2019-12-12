from django import http
from django.utils.deprecation import MiddlewareMixin
from apps.recall.models import ClientInfo


class AuthUser(MiddlewareMixin):
    def process_request(self, request):
        """
        用户认证
        :param request:
        :return:
        """
        app_id, api_key, secret_key = request.GET.get("app_id"), request.GET.get("api_key"), request.GET.get(
            "secret_key")
        if app_id and api_key and secret_key:
            if not all([app_id, api_key, secret_key]):  # 认证数据
                return http.JsonResponse({"code": '3001', "statement": "Missing the necessary parameters"})
            _user = ClientInfo.objects.filter(app_id=app_id).filter(api_key=api_key).filter(secret_key=secret_key)
            if not _user:
                return http.JsonResponse({"code": '3002', "statement": "Have no right to access"})