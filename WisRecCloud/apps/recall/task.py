import json
import redis
from celery import Celery
import pandas as pd
import math
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


def load_data(user_api_key):
    """
    加载数据库中的数据集
    :param user_api_key:
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
    _temp = pd.read_sql("select user_id, movie_id, ratting from movie_cf_data where client_id_id = %s" % user_api_key,
                        conn)

    data, new_data = list(), dict()
    for user_id, item_id, record in zip(_temp["user_id"], _temp["movie_id"], _temp["ratting"]):
        data.append((user_id, item_id, record))
    for user, item, record in data:
        new_data.setdefault(user, {})
        new_data[user][item] = record
    return new_data


@app.task
def UserSimilarityBest(user_api_key, api_key):
    """
    计算用户之间的相似度
    :return:
    """
    data = load_data(user_api_key)
    item_users = dict()  # 存储哪些item被用户评价过
    for u, items in data.items():  # user_id {item_id: rating}
        for i in items.keys():  # 得到每个item被哪些user评价过
            item_users.setdefault(i, set())
            if data[u][i] > 0:
                item_users[i].add(u)  # {'1193': {'1', '15', '2', '28', '18', '19', '24', '12', '33', '17'}}

    count, user_item_count = dict(), dict()
    for i, users in item_users.items():  # item_id, set(user_id1, user_id2)
        for u in users:  # user_id
            user_item_count.setdefault(u, 0)  # user_id: 0
            user_item_count[u] += 1
            count.setdefault(u, {})  # user_id: {}
            for v in users:  # user_id
                count[u].setdefault(v, 0)
                if u == v:
                    continue
                count[u][v] += 1 / math.log(1 + len(users))  # {'33': 391, '19': 255, '28': 107, '12': 23}

    userSim = dict()
    for u, related_users in count.items():
        userSim.setdefault(u, {})
        for v, cuv in related_users.items():
            if u == v:
                continue
            userSim[u].setdefault(v, 0.0)
            userSim[u][v] = cuv / math.sqrt(user_item_count[u] * user_item_count[v])

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
        "result": userSim
    }
    return result


@app.task
def ItemSimilarityBest(user_api_key, api_key):
    data = load_data(user_api_key)
    itemSim, item_user_count, count = dict(), dict(), dict()  # 构造共现矩阵
    for user, _item in data.items():
        for i in _item.keys():
            item_user_count.setdefault(i, 0)
            if data[int(user)][i] > 0.0:
                item_user_count[i] += 1
            for j in _item.keys():
                count.setdefault(i, {}).setdefault(j, 0)
                if data[int(user)][i] > 0.0 and data[int(user)][j] > 0.0 and i != j:
                    count[i][j] += 1
    for i, related_items in count.items():
        itemSim.setdefault(i, dict())
        for j, cuv in related_items.items():
            itemSim[i].setdefault(j, 0)
            itemSim[i][j] = cuv / math.sqrt(item_user_count[i] * item_user_count[j])
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
        "result": itemSim
    }
    return result
