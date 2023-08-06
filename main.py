import os
import time

import requests
import requests.utils
from loguru import logger

import push

# 从环境变量获取 LOGIN_COOKIE 的值
login_cookie = os.getenv('LOGIN_COOKIE')
login_url = os.getenv('LOGIN_URL')
login_url_payload = os.getenv('LOGIN_URL_PAYLOADLOAD')
PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN')


def load_cookie_dict_from_str():
    try:
        cookie_dict = {}
        cookie_str = login_cookie
        cookie_list = cookie_str.split(';')

        for item in cookie_list:
            contents = item.strip().split('=', 1)
            if len(contents) == 2:
                key = contents[0]
                value = contents[1]
                cookie_dict[key] = value
            else:
                logger.warning("cookie拼接出错了，键值对中有多余的=")
        logger.debug('cookie_dict=' + str(cookie_dict))
        return cookie_dict
    except Exception as e:
        logger.error(e)
        exit(-1)


def tencent_video_login():
    login_headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Content-Length': '644',
        'Content-Type': 'application/json',
        'Origin': 'https://v.qq.com',
        'Referer': 'https://v.qq.com/',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Cookie': login_cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    try:
        body = login_url_payload
        login_rsp = requests.post(url=login_url, data=body, headers=login_headers)
        if login_rsp.status_code == 200:
            logger.info("登录成功")
            logger.debug("登录数据：" + login_rsp.text)
            logger.debug(f"获取到的cookies：{login_rsp.cookies}", )
            return login_rsp
        else:
            logger.error("登录失败：" + login_rsp.text)
    except Exception as e:
        logger.exception("可能是请求出错")
        exit(-1)


def get_cookies():
    try:
        login_cookie_dict = load_cookie_dict_from_str()
        login_rsp = tencent_video_login()
        login_cookie_dict.update(login_rsp.cookies.get_dict())
        auth_cookie = "; ".join([f"{key}={value}" for key, value in login_cookie_dict.items()])
        logger.info('auth_cookie:' + auth_cookie)

        return auth_cookie
    except Exception as e:
        logger.error(e)
        exit(-1)


def tencent_video_sign_in():
    auth_cookie = get_cookies()
    sign_in_url = "https://vip.video.qq.com/rpc/trpc.new_task_system.task_system.TaskSystem/CheckIn?rpc_data={}"
    sign_headers = {
        'Referer': 'https://film.video.qq.com/x/vip-center/?entry=common&hidetitlebar=1&aid=V0%24%241%3A0%242%3A8%243%3A8.7.85.27058%244%3A3%245%3A%246%3A%247%3A%248%3A4%249%3A%2410%3A&isDarkMode=0',
        'Host': 'vip.video.qq.com',
        'Origin': 'https://film.video.qq.com',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; M2104K10AC Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.0.4389.72 MQQBrowser/6.2 TBS/046237 Mobile Safari/537.36 QQLiveBrowser/8.7.85.27058',
        'Accept-Encoding': 'gzip, deflate, br',
        "Cookie": auth_cookie
    }
    sign_rsp = requests.get(url=sign_in_url, headers=sign_headers)

    logger.debug("签到响应内容：" + sign_rsp.text)

    sign_rsp_json = sign_rsp.json()

    if sign_rsp_json['ret'] == 0:
        score = sign_rsp_json['check_in_score']
        if score == '0':
            log = f'Cookie有效!当天已签到'
        else:
            log = f'Cookie有效!签到成功,获得经验值{score}'
    elif sign_rsp_json['ret'] == -2002:
        log = f'Cookie有效!当天已签到'
    else:
        log = sign_rsp_json['msg']
        logger.error(log)
    logger.debug('签到状态：' + log)

    # requests.get('https://sc.ftqq.com/自己的sever酱号.send?text=' + quote('签到积分：' + str(rsp_score)))
    push.pushplus(log, PUSHPLUS_TOKEN)


if __name__ == '__main__':
    try:
        logger.info("腾讯视频自动签到启动成功")
        tencent_video_sign_in()
        logger.info("10秒之后退出程序")
        time.sleep(10)
    except Exception as e:
        logger.error(e)
