import logging
import os
import platform
import sys
import time
import urllib3
import requests
import traceback
import json

# 关闭验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 定义请求头
headers = {
    'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/88.0.4324.104 Safari/537.36'
}

# 执行环境判断 建议统一使用secrets以免KEY泄露
if platform.system() == 'Linux':
    qywx_token = os.environ["QYWX"]
    UID = os.environ["UID"]
else:
    qywx_token = 'default'
    UID = 'default'

# api
apiroot = 'http://help.tencentbot.top'

# 默认间隔
long_invl = 300
short_invl = 10

# 设置日志格式
logger_raw = logging.getLogger()
logger_raw.setLevel(logging.INFO)
formatter1 = logging.Formatter("[%(levelname)s]: %(message)s")
console_handler = logging.StreamHandler(stream=sys.stdout)  # 输出到控制台
console_handler.setFormatter(formatter1)
logger_raw.addHandler(console_handler)

# 推送
def qywx_pusher_send(qywx_token, t, cont):
    r = 'False'
    try:
        qywx = {}
        tmp = qywx_token.split(';')
        if len(tmp) >= 3:
            qywx[u'企业ID'] = tmp[0]
            qywx[u'应用ID'] = tmp[1]
            qywx[u'应用密钥'] = tmp[2]
        else:
            raise Exception(u'企业微信token错误')
        
        get_access_token_res = requests.get('https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={id}&corpsecret={secret}'.format(id=qywx[u'企业ID'], secret=qywx[u'应用密钥']), 
                            verify=False).json()
        if (get_access_token_res['access_token'] != '' and get_access_token_res['errmsg'] == 'ok'):
            msgUrl = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={0}'.format(get_access_token_res['access_token'])
            postData = {"touser" : "@all",
                        "msgtype" : "news",
                        "agentid" : qywx[u'应用ID'],
                        "news" : {
                            "articles" : [
                                    {
                                        "title" : t,
                                        "description" : cont,
                                        "url" : "URL"
                                    }
                                ]
                        }
            }
            msg_res = requests.post(msgUrl, data=json.dumps(postData), verify=False)
            tmp = msg_res.json()
            if (tmp['errmsg'] == 'ok' and tmp['errcode'] == 0):
                r = 'True'

    except Exception as e:
        r = traceback.format_exc()
        print(r)
    return r


def get_rank() -> dict:

    # 获取rid,有异常则返回false(大概率为dns解析失败导致的与服务器连接不成功)
    try:
        rid = requests.get(
            f'{apiroot}/enqueue?target_viewer_id={UID}', headers=headers, verify=False)
    except:
        logging.warning('连接失败，重试')
        return {'status': 'false'}

    # 与服务器成功连接后，判断响应码
    rid_response = rid.status_code
    if rid_response != 200:
        logging.warning('未取得rid,重试')
        return {'status': 'false'}

    else:
        rid_char = rid.json()['reqeust_id']
        # 成功获得rid
        while True:
            # 获取rank信息，有异常则返回false
            try:
                query = requests.get(f'{apiroot}/query?request_id={rid_char}', headers=headers, verify=False)
            except:
                logging.warning('连接失败，重试')
                return {'status': 'false'}

            query_response = query.status_code
            if query_response != 200:
                logging.warning('未取得排名，重试')
                return {'status': 'false'}

            else:
                logging.info(query.json()['status'])
                status = query.json()['status']

                # 查询rank，成功获得返回json，进行对key'status'的判断(done,queue,notfound)
                if status == 'done':
                    return query.json()

                elif status == 'queue':
                    logging.info('排队中')
                    time.sleep(short_invl)

                elif status == 'notfound':
                    logging.warning('rid过期，重试')
                    return {'status': 'false'}


# 初始化jjc排名
origin_arena_ranks = 15001
origin_grand_arena_ranks = 15001


# 排名变化相关的逻辑处理
def on_arena_schedule():
    # 全局变量,保存排名信息
    global origin_arena_ranks
    global origin_grand_arena_ranks

    # 循环调用get_rank()直到正确获得排名信息
    while True:
        data = get_rank()
        time.sleep(2)
        if data['status'] != 'false':
            break
        else:
            logging.warning('retrying')
            time.sleep(short_invl)

    # 即时查询到的最新排名信息
    new_arena_ranks = int(data['data']['user_info']['arena_rank'])
    new_grand_arena_ranks = int(data['data']['user_info']['grand_arena_rank'])

    # jjc排名
    if origin_arena_ranks == new_arena_ranks:
        origin_arena_ranks = new_arena_ranks
        logging.info('jjc:' + str(origin_arena_ranks))

    else:
        temp_arena_ranks = origin_arena_ranks
        origin_arena_ranks = new_arena_ranks
        t =  '竞技场排名变化'
        cont = f'{temp_arena_ranks}->{new_arena_ranks}'
        logging.info(f'竞技场排名发生变化：{temp_arena_ranks}->{new_arena_ranks}')
        qywx_pusher_send(qywx_token, t, cont)

    # pjjc排名
    if origin_grand_arena_ranks == new_grand_arena_ranks:
        origin_grand_arena_ranks = new_grand_arena_ranks
        logging.info('pjjc:' + str(origin_grand_arena_ranks))

    else:
        temp_grand_arena_ranks = origin_grand_arena_ranks
        origin_grand_arena_ranks = new_grand_arena_ranks
        t = '公主竞技场排名变化'
        cont = f'{temp_grand_arena_ranks}->{new_grand_arena_ranks}'
        logging.info(f'公主竞技场排名发生变化：{temp_grand_arena_ranks}->{new_grand_arena_ranks}')
        qywx_pusher_send(qywx_token, t, cont)


def main():
    start_time = time.time()
    while True:
        logging.info(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        duration = time.time() - start_time
        if duration >= 21300:
            break
        else:
            on_arena_schedule()
            time.sleep(long_invl)


if __name__ == '__main__':
    main()
