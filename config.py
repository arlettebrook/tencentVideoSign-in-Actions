import hashlib
import json
import os
import random
import re
import time
from hashlib import md5
from string import digits, ascii_lowercase, ascii_uppercase

import requests
from fake_useragent import UserAgent
from loguru import logger
from requests import Session

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
            logger.warning('建议配置PUSHPLUS_TOKEN，开启消息通知。')
            return None

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

    def _get_login_cookie(self):
        login_cookie = os.getenv('LOGIN_COOKIE')
        if login_cookie:
            logger.success("LOGIN_COOKIE已配置")
            return login_cookie
        else:
            self._exit("LOGIN_COOKIE未配置，任务未完成。")

    def _get_login_url(self):
        login_url = os.getenv('LOGIN_URL')
        if login_url:
            logger.success("LOGIN_URL已配置")
            return login_url
        else:
            self._exit("LOGIN_URL未配置，任务未完成.")

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

    def get_cookies(self):
        try:
            login_cookie_dict = self.load_cookie_dict_from_str()
            login_rsp = self.tencent_video_login()
            login_cookie_dict.update(login_rsp.cookies.get_dict())
            auth_cookie = "; ".join([f"{key}={value}" for key, value in login_cookie_dict.items()])
            logger.debug('auth_cookie:' + auth_cookie)
            return auth_cookie
        except Exception as e:
            logger.error(e)

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
        logger.info('签到状态：' + log)

        info = self.tencent_video_get_vip_info(auth_cookies)
        log = info + f"\n签到任务状态：{log}\n"
        # requests.get('https://sc.ftqq.com/自己的sever酱号.send?text=' + quote('签到积分：' + str(rsp_score)))
        # if self.PUSHPLUS_TOKEN:
        #     push.pushplus(title="腾讯视频自动签到通知", content=log, token=self.PUSHPLUS_TOKEN)
        return log

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
            logger.info(f"v力值响应内容：{res_2}")
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
            logger.info("获取会员信息状态：" + vip_info_rsp.text)
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
            # finally:
            # if self.PUSHPLUS_TOKEN:
            #     push.pushplus(title="腾讯视频会员信息", content=log, token=self.PUSHPLUS_TOKEN)
        else:
            e = "获取会员信息响应失败"
            logger.error(e)
            self._exit(e)


class IQY:
    def __init__(self):
        self.push_token = self._get_push_token()
        self.iqy_cookie = os.getenv('IQY_COOKIE')
        self.task_list = []
        self.growthTask = 0
        self.sign_in_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Host': 'tc.vip.iqiyi.com',
            'Proxy-Connection': 'keep-alive',
            'Sec-Ch-Ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Cookie': self.iqy_cookie
        }

        self.user_agent = UserAgent().chrome
        try:
            self.P00001 = re.search(r"P00001=(.*?);", self.iqy_cookie).group(1)
            self.dfp = re.search(r'__dfp=(.*?)@', self.iqy_cookie).group(1)
        except Exception as e:
            logger.error(e)
        self.session = Session()
        self.headers = {
            "User-Agent": self.user_agent,
            "Cookie": f"P00001={self.P00001}",
            "Content-Type": "application/json"
        }
        self.uid = ''
        self.qyid = self.md5(self.uuid(16))

    @staticmethod
    def uuid(num, upper=False):
        uuid = ''
        if upper:
            for i in range(num):
                uuid += random.choice(digits + ascii_lowercase + ascii_uppercase)
        else:
            for i in range(num):
                uuid += random.choice(digits + ascii_lowercase)
        return uuid

    @staticmethod
    def md5(uuid):
        m = md5(uuid.encode(encoding='utf-8'))
        return m.hexdigest()

    @staticmethod
    def _get_push_token():
        push_token = os.getenv('PUSHPLUS_TOKEN')
        if push_token:
            logger.success('PUSHPLUS_TOKEN已配置')
            return push_token
        else:
            logger.warning('建议配置PUSHPLUS_TOKEN，开启消息通知。')
            return None

    def req(self, url, req_method="GET", body=None):
        data = {}
        if req_method.upper() == "GET":
            try:
                data = self.session.get(url, headers=self.headers, params=body).json()
            except Exception as e:
                logger.error("请求发送失败,可能为网络异常")
                logger.error(e)
            #     data = self.session.get(url, headers=self.headers, params=body).text
            return data
        elif req_method.upper() == "POST":
            try:
                data = self.session.post(url, headers=self.headers, data=json.dumps(body)).json()
            except Exception as e:
                logger.error("请求发送失败,可能为网络异常")
                logger.error(e)
            #     data = self.session.post(url, headers=self.headers, data=dumps(body)).text
            return data
        elif req_method.upper() == "OTHER":
            try:
                self.session.get(url, headers=self.headers, params=json.dumps(body))
            except Exception as e:
                logger.error("请求发送失败,可能为网络异常")
                logger.error(e)
        else:
            logger.error("您当前使用的请求方式有误,请检查")

    @staticmethod
    def timestamp(short=False):
        if short:
            return int(time.time())
        return int(time.time() * 1000)

    def getUid(self):
        url = f'https://passport.iqiyi.com/apis/user/info.action?authcookie={self.P00001}&fields=userinfo%2Cqiyi_vip&timeout=15000'
        data = self.req(url)
        logger.debug(f'getUid响应:{data}')
        if data.get("code") == 'A00000':
            self.uid = data['data']['userinfo']['pru']
        else:
            info = f"请求api失败 最大可能是cookie失效了 也可能是网络问题:getUid响应:{data}"
            logger.error(info)
            if self.push_token:
                push.pushplus(self.push_token, content="爱奇艺每日任务:" + info)

    def get_check_in_url(self):
        time_stamp = self.timestamp()
        self.getUid()
        if self.uid == "":
            logger.error("获取用户id失败 可能为cookie设置错误或者网络异常,请重试或者检查cookie")
        data = f'agentType=1|agentversion=1|appKey=basic_pcw|authCookie={self.P00001}|qyid={self.qyid}|task_code=natural_month_sign|timestamp={time_stamp}|typeCode=point|userId={self.uid}|UKobMjDMsDoScuWOfp6F'
        url = f'https://community.iqiyi.com/openApi/task/execute?agentType=1&agentversion=1&appKey=basic_pcw&authCookie={self.P00001}&qyid={self.qyid}&sign={self.md5(data)}&task_code=natural_month_sign&timestamp={time_stamp}&typeCode=point&userId={self.uid}'
        return url

    def check_in(self):
        url = self.get_check_in_url()
        body = {
            "natural_month_sign": {
                "taskCode": "iQIYI_mofhr",
                "agentType": 1,
                "agentversion": 1,
                "authCookie": self.P00001,
                "qyid": self.qyid,
                "verticalCode": "iQIYI"
            }
        }
        info = 'null'
        data = self.req(url, "post", body)
        logger.info(f'签到返回信息：{data}')
        if data.get('code') == 'A00000':
            try:
                msg = data['data']['msg']
                # msg为None表示成功执行
                if msg:
                    info = f"签到执行成功, {msg}"
                else:
                    signDays = data['data']['data']['signDays']
                    rewardCount = data['data']['data']['rewards'][0]['rewardCount']
                    info = f"签到执行成功, +{rewardCount}签到成长值,连续签到{signDays}天。"
                logger.success(info)
            except Exception as e:
                logger.error(e)
            # if self.push_token:
            #     push.pushplus(self.push_token, title="爱奇艺签到通知", content=info)
            return info
        else:
            logger.error("签到失败，原因可能是签到接口又又又又改了")
            return f'签到返回信息：{data}'

    def get_user_info(self):
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        check_in = self.check_in()
        time.sleep(3)
        task_rewards = self.get_rewards()
        time.sleep(10)
        user_info_url = "http://serv.vip.iqiyi.com/vipgrowth/query.action"
        params = {
            "P00001": self.P00001,
        }
        # user_info_headers = {
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        #     'Accept-Encoding': 'gzip,deflate',
        #     'Accept-Language': 'zh-CN,zh;q=0.9',
        #     'Cache-Control': 'max-age=0',
        #     'Host': 'serv.vip.iqiyi.com',
        #     'Proxy-Connection': 'keep-alive',
        #     'Upgrade-Insecure-Requests': '1',
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        #     'Cookie': self.iqy_cookie
        # }
        user_info_resp = requests.get(url=user_info_url, params=params)
        msg = ''
        resp_json = user_info_resp.json()
        if resp_json["code"] == "A00000":
            try:
                res_data = resp_json["data"]
                # VIP等级
                level = res_data["level"]
                # 当前VIP成长值
                growthvalue = res_data["growthvalue"]
                # 升级需要成长值
                distance = res_data["distance"]
                # VIP到期时间
                deadline = res_data["deadline"]
                # 今日成长值
                todayGrowthValue = res_data["todayGrowthValue"]
                msg = f"\n--------------爱奇艺会员信息--------------\n{now}\nVIP等级：{level}\n当前成长值：{growthvalue}\n升级需成长值：{distance}\n今日成长值:  +{todayGrowthValue}\nVIP到期时间:{deadline}\n"
                logger.success("爱奇艺获取会员信息成功")
            except Exception as e:
                logger.warning(resp_json)
                logger.error(e)
        else:
            msg = '\n爱奇艺获取会员信息失败：' + str(resp_json)
            logger.error(msg)
        msg = f"\n=============爱奇艺任务状态=============\n签到：{check_in}\n日常任务：{task_rewards}" + msg
        logger.info(msg)
        # if self.push_token:
        #     push.pushplus(self.push_token, title='爱奇艺自动签到通知', content=msg)
        return msg

    def sign_in(self):
        sign_url = "https://tc.vip.iqiyi.com/taskCenter/task/queryUserTask"
        params = {
            "P00001": self.P00001,
            "autoSign": "yes"
        }
        check_in_resp = requests.get(url=sign_url, params=params)
        resp_json = check_in_resp.json()
        logger.debug(f'登录成功，响应的数据：{resp_json}')
        if resp_json["code"] == "A00000":
            logger.success("登录任务中心成功")
            return resp_json
        else:
            logger.warning("登录任务中心失败")
            msg = resp_json["msg"]
            return msg

    def query_tasks(self):
        resp_json = self.sign_in()
        if resp_json["code"] == "A00000":
            for item in resp_json["data"]["tasks"]["daily"]:
                self.task_list.append({
                    "name": item["name"],
                    "taskCode": item["taskCode"],
                    "status": item["status"],
                    "taskReward": item["taskReward"]["task_reward_growth"]
                })
        else:
            logger.warning("查询任务状态失败：" + resp_json["msg"])
        logger.success(f"查询任务成功：{self.task_list}")
        return self

    def join_task(self):
        # 遍历完成任务
        join_task_url = "https://tc.vip.iqiyi.com/taskCenter/task/joinTask"
        params = {
            "P00001": self.P00001,
            "taskCode": "",
            "platform": "bb136ff4276771f3",
            "lang": "zh_CN",
            "app_lm": "cn"
        }
        self.query_tasks()
        logger.info(f"任务列表：{self.task_list}")
        # 遍历任务，仅做一次
        for item in self.task_list:
            params["taskCode"] = item["taskCode"]
            logger.info(f"正在执行{item['name']}...")
            res = self.req(url=join_task_url, body=params)
            if res['code'] == 'A00000':
                logger.info(f"加入任务{item['name']}响应:{res}")
                time.sleep(11)
                logger.info(f"加入任务{item['name']}状态：{res}")
            else:
                logger.error(f"加入任务{item['name']}响应:{res}")

            # 完成任务
            url = f'https://tc.vip.iqiyi.com/taskCenter/task/notify?taskCode={item["taskCode"]}&P00001={self.P00001}&platform=97ae2982356f69d8&lang=cn&bizSource=component_browse_timing_tasks&_={self.timestamp()}'
            if res := self.req(url)['code'] == 'A00000':
                time.sleep(2)
                logger.info(f"完成任务{item['name']}响应：{res}")

    def get_rewards(self):
        # 获取任务奖励
        rewards_url = "https://tc.vip.iqiyi.com/taskCenter/task/getTaskRewards"
        params = {
            "P00001": self.P00001,
            "taskCode": "",
            "platform": "bb136ff4276771f3",
            "lang": "zh_CN"
        }
        self.join_task()
        logger.info(f'可完成的任务：{self.task_list}')
        # 遍历任务，领取奖励
        for item in self.task_list:
            params["taskCode"] = item["taskCode"]
            res = self.req(url=rewards_url, body=params)
            time.sleep(1)
            logger.info(f"领取任务{item['name']}状态:{res}")
            if res["code"] == "A00000":
                try:
                    self.growthTask += int(res['data'][0]['成长值'][1])
                except Exception as e:
                    logger.warning(e)
                    pass
        msg = f"日常任务执行成功，+{self.growthTask}日常任务成长值"
        logger.info(msg)
        # if self.push_token:
        #     push.pushplus(self.push_token, title='爱奇艺领取通知', content=msg)
        return msg


class Tieba:
    def __init__(self):
        self.BDUSS = os.getenv('BDUSS')
        self.session = requests.session()
        self.headers = {
            'Host': 'tieba.baidu.com',
            'User-Agent': UserAgent().chrome,
            'Connection': 'keep-alive',
            'Cookie': f'BDUSS={self.BDUSS}',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }

        self.check_in_list = []
        self.checked_in_list = []
        self.tbs = self._get_tbs()

    @logger.catch
    def _get_tbs(self):
        # 获取用户的tbs
        # 签到的时候需要用到这个参数
        TBS_URL = "http://tieba.baidu.com/dc/common/tbs"
        tbs_rsp = self.session.get(url=TBS_URL, headers=self.headers)
        logger.debug(f'获取用户的tbs响应：{tbs_rsp.text}')
        content = tbs_rsp.json()
        if content['is_login'] == 1:
            logger.success('成功获取用户的tbs')
            return content['tbs']
        else:
            logger.error('获取tbs失败，用户未登录成功。')

    @logger.catch
    # 获取用户所关注的贴吧列表
    def get_follows(self):
        # 获取用户所有关注贴吧
        LIKE_URL = "https://tieba.baidu.com/mo/q/newmoindex"
        follow_rsp = self.session.get(url=LIKE_URL, headers=self.headers)
        logger.debug(f'获取用户所关注的贴吧列表响应:{follow_rsp.text}')
        content = follow_rsp.json()
        if content['error'] == 'success':
            logger.success('成功获取用户所关注的贴吧列表')
            for item in content['data']['like_forum']:
                if item['is_sign'] == 0:
                    self.check_in_list.append(item)
                else:
                    self.checked_in_list.append(item)

        logger.debug(f'签到列表：{self.check_in_list}')
        logger.info(f'未签到列表：共{len(self.check_in_list)}个-{self.check_in_list}')

    @logger.catch
    def check_in(self):
        self.get_follows()
        # 贴吧签到接口
        SIGN_URL = "http://c.tieba.baidu.com/c/c/forum/sign"
        num = 0
        for item in self.check_in_list:
            logger.info(f"正在签到{item['forum_name']}吧...")
            SIGN_DATA = {
                '_client_type': '2',
                '_client_version': '9.7.8.0',
                '_phone_imei': '000000000000000',
                'model': 'MI+5',
                "net_type": "1",
                'BDUSS': self.BDUSS,
                'fid': item['forum_id'],
                'kw': item['forum_name'],
                'tbs': self.tbs,
                'timestamp': str(int(time.time()))
            }
            data = self.encodeByMd5(SIGN_DATA)
            check_in_rsp = self.session.post(url=SIGN_URL, headers=self.headers, data=data)
            logger.debug(f"执行{item['forum_name']}吧签到，响应：{check_in_rsp.text}")
            content = check_in_rsp.json()
            if content['error_code'] == '0':
                logger.success(f"执行{item['forum_name']}吧签到成功")
                num += 1
            else:
                logger.warning(f"执行{item['forum_name']}吧签到失败，失败消息：{content}")

            time.sleep(random.randint(1, 5))
        return self.notice(num)

    @staticmethod
    def encodeByMd5(data):
        s = ""
        keys = data.keys()

        # 遍历键，并根据键进行排序
        for i in sorted(keys):
            s += i + "=" + str(data[i])
        logger.debug(f'未加密数据：{s}')
        # 将排序后的字符串和 SIGN_KEY 进行拼接，然后进行 MD5 加密
        sign = hashlib.md5((s + 'tiebaclient!!!').encode('utf-8')).hexdigest().upper()
        # 将加密结果添加到原始字典中，键为 SIGN，值为加密结果
        data.update({'sign': str(sign)})
        logger.debug(f'加密后的数据：{data}')
        return data

    @logger.catch
    def notice(self, num):
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        count = len(self.checked_in_list) + len(self.check_in_list)
        info = f'\n-------------贴吧签到任务情况-------------\n{now}\n共关注{count}个吧~\n' \
               f'今日还剩{len(self.check_in_list)}个吧未签到~\n通过自动任务成功签到{num}个吧~\n还剩{len(self.check_in_list) - num}个吧未签到~\n'
        logger.info(info)
        return info
