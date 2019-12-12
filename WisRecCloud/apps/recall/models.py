from django.db import models


# Create your models here.

class ClientInfo(models.Model):
    app_id = models.CharField(max_length=20, unique=True)
    api_key = models.CharField(max_length=20, unique=True)
    secret_key = models.CharField(max_length=20)
    user_name = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.app_id

    class Meta:
        db_table = 'client_info'
        verbose_name_plural = "客户数据表"


class JieCardData(models.Model):
    CHOICE = (('1', "完成"), ('0', "未完成"))
    client_id = models.ForeignKey(ClientInfo, related_name="Client")
    data_id = models.IntegerField()  # 整数
    # digest = models.CharField(max_length=2000)
    key_digest = models.CharField(max_length=500, blank=True)
    indexer = models.CharField(max_length=4, choices=CHOICE, default="0")

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'jie_card_data'
        verbose_name_plural = "杰卡德数据表"


class MovieCFData(models.Model):
    client_id = models.ForeignKey(ClientInfo, related_name="Client_id")
    user_id = models.IntegerField()  # 用户id
    movie_id = models.IntegerField()  # 电影id
    ratting = models.FloatField()  # 评分

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'movie_cf_data'
        verbose_name_plural = "杰卡德数据表"
