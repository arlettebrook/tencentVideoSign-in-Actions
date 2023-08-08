import json
import os
import re
import time

import requests
from loguru import logger

import push


class TencentVideo:

    def __init__(self):
        # 从环境变量获取 LOGIN_COOKIE 的值
        self.PUSHPLUS_TOKEN = self._get_push_token()
        self.login_cookie = self._get_login_cookie()
        self.login_url = self._get_login_url()
        self.login_url_payload = self._get_login_url_payload()
        self.get_vip_info_url_payload = self._get_login_url_payload()

    @staticmethod
    def _get_push_token():
        push_token = os.getenv('PUSHPLUS_TOKEN')
        if push_token:
            logger.success('PUSHPLUS_TOKEN已配置')
            return push_token
        else:
            logger.warning('未开消息通知功能')
            return -1

    @staticmethod
    def _get_vip_info_url_payload():
        vip_info_url_payload = os.getenv('GET_VIP_INFO_URL_PAYLOAD')
        if vip_info_url_payload:
            logger.success('GET_VIP_INFO_URL_PAYLOAD已配置')
            return vip_info_url_payload
        else:
            logger.warning('GET_VIP_INFO_URL_PAYLOAD未配置，将使用默认值。')
            return """{"geticon": 1, "viptype": "svip", "platform": 1000}"""

    @staticmethod
    def _get_login_url_payload():
        login_rul_payload = os.getenv("LOGIN_URL_PAYLOADLOAD")
        if login_rul_payload:
            logger.success('LOGIN_URL_PAYLOADLOAD已配置')
            return login_rul_payload
        else:
            logger.warning('LOGIN_URL_PAYLOADLOAD未配置，将使用默认值。')
            return """{"type": "qq", "si": {"h38": "b885b12b67288e7dcc0183f30200000b31771b", "q36": "", "s": "000000014068b89153f4562362f80aafc61a5f261f1bbe9f47f26dad070abd34edb2085eefbcbd8999bea9fd5e612dcfa466e132725b168151744f5683ca9b054eb4904d071de80c3c931c306beda187500b50f609b9fd4b0ec83d6db51719869479e9b9630b6bcc1e81329be0dbc36103739ebff1d91c0f0205c08041a2771cf25bdd18525e661da11a4825de788b5c90f99f65a5c3adecc909485c9fe813aa88bd65c212227b0525df84e1754191cb74aac19de74043edb0f4058c2e5ee988f186283ab73eb5b93e1b1d5774404ac7f0a8d563a9d72cd9278956163ce989302b5132e64ce0b0d92c84596cbbb47863d7603be0c6d3f91b543db0", "o_data": "g=64df242b475e272d&t=1690455867510&r=5cFXlb4OTc"}}"""

    def _exit(self, e):
        logger.error(e)
        push.pushplus(token=self.PUSHPLUS_TOKEN, content=e)
        exit(-1)

    def _get_login_cookie(self):
        login_cookie = os.getenv('LOGIN_COOKIE')
        if login_cookie:
            logger.success("LOGIN_COOKIE已配置")
            return login_cookie
        else:
            self._exit("LOGIN_COOKIE未配置，程序已退出。")

    def _get_login_url(self):
        login_url = os.getenv('LOGIN_URL')
        if login_url:
            logger.success("LOGIN_URL已配置")
            return login_url
        else:
            self._exit("LOGIN_URL未配置，程序已退出")

    def load_cookie_dict_from_str(self):
        try:
            cookie_dict = {}
            cookie_str = self.login_cookie
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

    def tencent_video_login(self):
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
            'Cookie': self.login_cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        try:
            body = self.login_url_payload
            login_rsp = requests.post(url=self.login_url, data=body, headers=login_headers)
            if login_rsp.status_code == 200:
                logger.success("登录成功")
                logger.debug("登录数据：" + login_rsp.text)
                logger.debug(f"获取到的cookies：{login_rsp.cookies}", )
                return login_rsp
            else:
                logger.error("登录失败：" + login_rsp.text)
        except Exception as e:
            logger.exception("可能是请求出错" + e.__str__())
            exit(-1)

    def get_cookies(self):
        try:
            login_cookie_dict = self.load_cookie_dict_from_str()
            login_rsp = self.tencent_video_login()
            login_cookie_dict.update(login_rsp.cookies.get_dict())
            auth_cookie = "; ".join([f"{key}={value}" for key, value in login_cookie_dict.items()])
            logger.success('auth_cookie:' + auth_cookie)
            return auth_cookie
        except Exception as e:
            logger.error(e)
            exit(-1)

    def tencent_video_sign_in(self):
        auth_cookies = self.get_cookies()
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
        if self.PUSHPLUS_TOKEN:
            push.pushplus(title="腾讯视频签到提醒", ccontent=log, token=self.PUSHPLUS_TOKEN)
        self.tencent_video_get_vip_info(auth_cookies)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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
            logger.success(log)
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

    def tencent_video_get_vip_info(self, auth_cookies):
        log = self.tencent_video_get_score(auth_cookies)
        log_status = self.tencent_video_task_status(auth_cookies) + self.tencent_video_get_look(auth_cookies)

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
        body = self.get_vip_info_url_payload
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
                logger.success(log)
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
                if self.PUSHPLUS_TOKEN:
                    push.pushplus(title="腾讯视频会员信息", content=log, token=self.PUSHPLUS_TOKEN)
        else:
            e = "获取会员信息响应失败"
            logger.error(e)
            self._exit(e)
