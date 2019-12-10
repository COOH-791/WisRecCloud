from django.db import models


# Create your models here.

class ClientInfo(models.Model):
    app_id = models.CharField(max_length=20, unique=True)
    api_key = models.CharField(max_length=20, unique=True)
    secret_key = models.CharField(max_length=20)

    def __str__(self):
        return self.app_id

    class Meta:
        db_table = 'client_info'
        verbose_name_plural = "客户数据表"


class JieCardData(models.Model):
    client_id = models.ForeignKey(ClientInfo, related_name="Client")
    data_id = models.IntegerField()  # 整数
    digest = models.CharField(max_length=2000)
    key_digest = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'jie_card_data'
        verbose_name_plural = "杰卡德数据表"
