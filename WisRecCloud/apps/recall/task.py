import json
import redis
from celery import Celery
import pandas as pd
import pymysql

app = Celery(
    'get_key_words',
    backend='redis://localhost:6379/8'
)


@app.task
def get_key(user_api_key, api_key):
    """
    :param user_api_key:
    :param api_key:
    :return:
    """
    conn = pymysql.connect(  # 链接MYSQL
        host='localhost',
        user='root',
        passwd='963369',
        db='wisreccloud',
        port=3306,
        charset='utf8'
    )
    # 到数据库查询所需要的数据
    _temp = pd.read_sql("select data_id, key_digest from jie_card_data where client_id_id = %s" % user_api_key, conn)
    _id = _temp["data_id"].to_list()
    _digest = _temp["key_digest"].to_list()
    _result = {temp_id: temp_digest for temp_id, temp_digest in zip(_id, _digest)}
    news_cor_list = list()
    # 计算相似度
    for new_id1 in _result.keys():
        id1_tags = set(_result[new_id1].split(","))
        for new_id2 in _result.keys():
            id2_tags = set(_result[new_id2].split(","))
            if new_id1 != new_id2:
                cor = (len(id1_tags & id2_tags)) / len(id1_tags | id2_tags)
                if cor > 0.1:
                    news_cor_list.append([new_id1, new_id2, format(cor, ".2f")])
    # 替换redis中推荐数据
    pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True, db=8)
    conn = redis.StrictRedis(connection_pool=pool)
    try:  # 如何未查询到数据,则是因为第一次创建则新建数据
        for redis_name in conn.keys():
            if api_key == json.loads(conn.get(redis_name))["result"]["api_key"]:
                conn.delete(redis_name)
    except KeyError:
        pass
    result = {
        "api_key": api_key,
        "result": news_cor_list
    }
    return result
