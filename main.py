import json
import os
import re
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
    auth_cookies = get_cookies()
    sign_in_url = "https://vip.video.qq.com/rpc/trpc.new_task_system.task_system.TaskSystem/CheckIn?rpc_data={}"
    sign_headers = {
        'Referer': 'https://film.video.qq.com/x/vip-center/?entry=common&hidetitlebar=1&aid=V0%24%241%3A0%242%3A8%243%3A8.7.85.27058%244%3A3%245%3A%246%3A%247%3A%248%3A4%249%3A%2410%3A&isDarkMode=0',
        'Host': 'vip.video.qq.com',
        'Origin': 'https://film.video.qq.com',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; M2104K10AC Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.0.4389.72 MQQBrowser/6.2 TBS/046237 Mobile Safari/537.36 QQLiveBrowser/8.7.85.27058',
        'Accept-Encoding': 'gzip, deflate, br',
        "Cookie": auth_cookies
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
    if PUSHPLUS_TOKEN:
        push.pushplus(log, PUSHPLUS_TOKEN)
    tencent_video_get_vip_info(auth_cookies)


def tencent_video_task_status(auth_cookies):
    # 任务状态
    task_url = 'https://vip.video.qq.com/rpc/trpc.new_task_system.task_system.TaskSystem/ReadTaskList?rpc_data=%7B%22business_id%22:%221%22,%22platform%22:3%7D'
    task_headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 11; M2104K10AC Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.0.4389.72 MQQBrowser/6.2 TBS/046237 Mobile Safari/537.36 QQLiveBrowser/8.7.85.27058',
        'Content-Type': 'application/json',
        'referer': 'https://film.video.qq.com/x/vip-center/?entry=common&hidetitlebar=1&aid=V0%24%241%3A0%242%3A8%243%3A8.7.85.27058%244%3A3%245%3A%246%3A%247%3A%248%3A4%249%3A%2410%3A&isDarkMode=0',
        'cookie': auth_cookies
    }
    response = requests.get(url=task_url, headers=task_headers)
    try:
        res = json.loads(response.text)
        logger.debug(f"任务状态详细内容：{res}")
        lis = res["task_list"]
        log = '\n============v力值任务完成状态============'
        for i in lis:
            if i["task_button_desc"] == '已完成':
                log = log + '\n标题:' + i["task_maintitle"] + '\n状态:' + i["task_subtitle"]
        return log
    except Exception as e:
        log = "获取状态异常，可能是cookie失效"
        logger.warning(log)
        logger.exception(e)
        return log


def tencent_video_get_score(auth_cookies):
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log = "\n--------------腾讯视频会员信息--------------\n" + now
    # 积分查询
    get_score_url = 'https://vip.video.qq.com/fcgi-bin/comm_cgi?name=spp_vscore_user_mashup&cmd=&otype=xjson&type=1'
    score_headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 11; M2104K10AC Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.0.4389.72 MQQBrowser/6.2 TBS/046237 Mobile Safari/537.36 QQLiveBrowser/8.7.85.27058',
        'Content-Type': 'application/json',
        'cookie': auth_cookies
    }
    score_resp = requests.get(get_score_url, headers=score_headers)
    try:
        qq_nick = re.search(r"qq_nick=([^\n;]*);", auth_cookies).group(1)
        res_3 = json.loads(score_resp.text)
        log = log + "\n用户：" + qq_nick + "\n会员等级:" + str(res_3['lscore_info']['level']) + "\n积分:" + str(
            res_3['cscore_info']['vip_score_total']) + "\nV力值:" + str(res_3['lscore_info']['score'])
        return log
    except Exception as e:
        try:
            res_3 = json.loads(score_resp.text)
            log = log + "\n腾讯视频领获取积分异常,返回内容:\n" + str(res_3)
            logger.warning(log)
            logger.exception(e)
            return log
        except Exception as e:
            log = log + "\n腾讯视频获取积分异常,无法返回内容"
            logger.warning(log)
            logger.exception(e)
            return log


def tencent_video_get_look(auth_cookies):
    # 观看
    look_url = 'https://vip.video.qq.com/rpc/trpc.new_task_system.task_system.TaskSystem/ProvideAward?rpc_data=%7B%22task_id%22:1%7D'
    look_headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 11; M2104K10AC Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.0.4389.72 MQQBrowser/6.2 TBS/046237 Mobile Safari/537.36 QQLiveBrowser/8.7.85.27058',
        'Content-Type': 'application/json',
        'referer': 'https://film.video.qq.com/x/vip-center/?entry=common&hidetitlebar=1&aid=V0%24%241%3A0%242%3A8%243%3A8.7.85.27058%244%3A3%245%3A%246%3A%247%3A%248%3A4%249%3A%2410%3A&isDarkMode=0',
        'cookie': auth_cookies
    }
    response_2 = requests.get(look_url, headers=look_headers)
    try:
        res_2 = json.loads(response_2.text)
        log = "\n观看获得v力值:" + str(res_2['provide_value'])
        logger.debug(f"v力值响应内容：{res_2}")
        logger.info(log)
        return log
    except Exception as e:
        try:
            res_2 = json.loads(response_2.text)
            log = "\n腾讯视频领取观看v力值异常,返回内容:\n" + str(res_2)
            logger.warning(log)
            logger.exception(e)
            return log
        except Exception as e:
            log = "\n腾讯视频领取观看v力值异常,无法返回内容"
            logger.warning(log)
            logger.exception(e)
            return log


def tencent_video_get_vip_info(auth_cookies):
    log = tencent_video_get_score(auth_cookies)
    log_status = tencent_video_task_status(auth_cookies) + tencent_video_get_look(auth_cookies)
    get_vip_info_url_payload = os.getenv("GET_VIP_INFO_URL_PAYLOAD")
    vip_info_headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Content-Length': '46',
        'Content-Type': 'text/plain;charset=UTF-8',
        'Origin': 'https://film.qq.com',
        'Referer': 'https://film.qq.com/vip/my/',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Cookie': auth_cookies,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    get_vip_info_url = 'https://vip.video.qq.com/rpc/trpc.query_vipinfo.vipinfo.QueryVipInfo/GetVipUserInfoH5'
    body = get_vip_info_url_payload
    vip_info_rsp = requests.post(get_vip_info_url, data=body, headers=vip_info_headers)
    if vip_info_rsp.status_code == 200:
        logger.debug("获取会员信息状态：" + vip_info_rsp.text)
        try:
            res_3 = json.loads(vip_info_rsp.text)
            log = log + "\n开始时间:" + str(res_3['beginTime']) + "\n到期时间:" + str(
                res_3['endTime'])
            if res_3['endmsg'] != '':
                log = log + '\nendmsg:' + res_3['endmsg']
            log += log_status
            logger.info(log)
            return log
        except Exception as e:
            try:
                res_3 = json.loads(vip_info_rsp.text)
                log = log + "\n腾讯视频领获取积分异常,返回内容:\n" + str(res_3)
                log += log_status
                logger.warning(log)
                logger.exception(e)
                return log
            except Exception as e:
                log = log + "\n腾讯视频获取积分异常,无法返回内容"
                log += log_status
                logger.warning(log)
                logger.exception(e)
                return log
        finally:
            if PUSHPLUS_TOKEN:
                push.pushplus(log, PUSHPLUS_TOKEN)
    else:
        logger.error("获取会员信息响应失败")


if __name__ == '__main__':
    try:
        logger.info("腾讯视频自动签到启动成功")
        tencent_video_sign_in()
        logger.info("10秒之后退出程序")
        time.sleep(10)
    except Exception as e:
        logger.error(e)
