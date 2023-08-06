import os
import time

import requests
import requests.utils
from loguru import logger

import push

login_cookie = 'video_platform=2; video_guid=64df242b475e272d; pgv_pvid=8204789012; RK=wS3gS7kMcG; ptcz=b4fe5fa05228fdf1d55eaf8de974ac5beb9292dbeb13624fc1111975f9f2f7ef; qq_domain_video_guid_verify=64df242b475e272d; main_login=qq; vqq_access_token=C8A76D88989C712DBEC66C77CE71B627; vqq_appid=101483052; vqq_openid=5CAF661D0FEE4676AA99900760B7F10E; vqq_vuserid=1208820857; vqq_refresh_token=F5B96C4152AFD012169FA55D65DA68AE; qq_nick=Arlettebrook; qq_head=https%3A%2F%2Fcommunity.image.video.qpic.cn%2F1234_bda48d-0_545698057_1672575460967170; vqq_vusession=xAQhbtCjlCXEeM7bm0HfPg.M; vqq_next_refresh_time=6600; vqq_login_time_init=1690952477; pgv_info=ssid=s7865864995; vdevice_qimei36=822e46d42fddb0a22a9411ff10001b016309; login_time_last=2023-8-2 13:1:19'
login_url = 'https://pbaccess.video.qq.com/trpc.video_account_login.web_login_trpc.WebLoginTrpc/NewRefresh?g_tk=&g_vstk=167733934&g_actk=1590963589'
login_url_payload = """{"type": "qq", "si": {"h38": "b885b12b67288e7dcc0183f30200000b31771b", "q36": "", "s": "000000014068b89153f4562362f80aafc61a5f261f1bbe9f47f26dad070abd34edb2085eefbcbd8999bea9fd5e612dcfa466e132725b168151744f5683ca9b054eb4904d071de80c3c931c306beda187500b50f609b9fd4b0ec83d6db51719869479e9b9630b6bcc1e81329be0dbc36103739ebff1d91c0f0205c08041a2771cf25bdd18525e661da11a4825de788b5c90f99f65a5c3adecc909485c9fe813aa88bd65c212227b0525df84e1754191cb74aac19de74043edb0f4058c2e5ee988f186283ab73eb5b93e1b1d5774404ac7f0a8d563a9d72cd9278956163ce989302b5132e64ce0b0d92c84596cbbb47863d7603be0c6d3f91b543db0", "o_data": "g=64df242b475e272d&t=1690455867510&r=5cFXlb4OTc"}}"""

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
