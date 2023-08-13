
# -*- coding: utf8 -*-
# 爱奇艺（IQIYI）官网，加载主页面，
# 开发者工具搜索获取P00001，P00003参数
# skey 为酷推 密钥，绑定发送qq
# 修改200、201、202行代码，其中202行的skey是酷推的skey。200和201行是获取Cookie中的P0001和P0003
import time
import requests


class IQY:
    '''
    爱奇艺签到、抽奖、做日常任务(签到、任务仅限VIP)
    *奖励：签7天奖1天，14天奖2天，28天奖7天；日常任务；随机成长值
    '''

    def __init__(self, P00001, psp_uid):
        '''
        :param P00001: 签到，任务，抽奖必要参数
        :param psp_uid: 抽奖必要参数
        '''
        self.P00001 = P00001
        self.psp_uid = psp_uid

        self.taskList = []
        self.growthTask = 0

    def userInformation(self):
        '''
        用户信息查询
        '''
        time.sleep(3)
        url = "http://serv.vip.iqiyi.com/vipgrowth/query.action"
        params = {
            "P00001": self.P00001,
        }
        res = requests.get(url, params=params)
        if res.json()["code"] == "A00000":
            try:
                res_data = res.json()["data"]
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
                msg = f"VIP等级：{level}\n当前成长值：{growthvalue}\n升级需成长值：{distance}\n今日成长值:  +{todayGrowthValue}\nVIP到期时间:{deadline}"
            except:
                msg = res.json()
        else:
            # print("（iqy）签到错误", res.content.decode())
            msg = res.json()
        print(msg)
        return msg

    def sign(self):
        '''
        VIP签到
        '''
        url = "https://tc.vip.iqiyi.com/taskCenter/task/queryUserTask"
        params = {
            "P00001": self.P00001,
            "autoSign": "yes"
        }
        res = requests.get(url, params=params)
        if res.json()["code"] == "A00000":
            try:
                growth = res.json()[
                    "data"]["signInfo"]["data"]["rewardMap"]["growth"]
                continueSignDaysSum = res.json(
                )["data"]["signInfo"]["data"]["continueSignDaysSum"]
                #vipStatus = res.json()["data"]["userInfo"]["vipStatus"]
                rewardDay = 7 if continueSignDaysSum % 28 <= 7 else (
                    14 if continueSignDaysSum % 28 <= 14 else 28)
                rouund_day = 28 if continueSignDaysSum % 28 == 0 else continueSignDaysSum % 28
                # VIP等级：{vipStatus}\n签到：
                msg = f"+{growth}成长值\n连续签到：{continueSignDaysSum}天\n签到周期：{rouund_day}天/{rewardDay}天"
            except:
                msg = res.json()["data"]["signInfo"]["msg"]
        else:
            # print("（iqy）签到错误", res.content.decode())
            msg = res.json()["msg"]
        print(msg)
        return msg

    def queryTask(self):
        '''
        获取VIP日常任务 和 taskCode(任务状态)
        '''
        url = "https://tc.vip.iqiyi.com/taskCenter/task/queryUserTask"
        params = {
            "P00001": self.P00001
        }
        res = requests.get(url, params=params)
        if res.json()["code"] == "A00000":
            for item in res.json()["data"]["tasks"]["daily"]:
                self.taskList.append({
                    "name": item["name"],
                    "taskCode": item["taskCode"],
                    "status": item["status"],
                    "taskReward": item["taskReward"]["task_reward_growth"]
                })
        else:
            # print("（iqy）获取任务失败")
            pass
        return self

    def joinTask(self):
        """
        遍历完成任务
        """
        url = "https://tc.vip.iqiyi.com/taskCenter/task/joinTask"
        params = {
            "P00001": self.P00001,
            "taskCode": "",
            "platform": "bb136ff4276771f3",
            "lang": "zh_CN"
        }
        # 遍历任务，仅做一次
        for item in self.taskList:
            if item["status"] == 2:
                params["taskCode"] = item["taskCode"]
                res = requests.get(url, params=params)
                print(res.text)

    def getReward(self):
        """
        获取任务奖励
        :return: 返回信息
        """
        url = "https://tc.vip.iqiyi.com/taskCenter/task/getTaskRewards"
        params = {
            "P00001": self.P00001,
            "taskCode": "",
            "platform": "bb136ff4276771f3",
            "lang": "zh_CN"
        }
        # 遍历任务，领取奖励
        for item in self.taskList:
            if item["status"] == 0:
                params["taskCode"] = item["taskCode"]
                res = requests.get(url, params=params)
                if res.json()["code"] == "A00000":
                    self.growthTask += item["taskReward"]
        msg = f"+{self.growthTask}成长值"
        print(msg)
        return msg

    def draw(self, type):
        '''
        查询抽奖次数(必),抽奖
        :param type: 类型。0查询次数；1抽奖
        :return: {status, msg, chance}
        '''
        url = "https://iface2.iqiyi.com/aggregate/3.0/lottery_activity"
        params = {
            "lottery_chance": 1,
            "app_k": "b398b8ccbaeacca840073a7ee9b7e7e6",
            "app_v": "11.6.5",
            "platform_id": 10,
            "dev_os": "8.0.0",
            "dev_ua": "FRD-AL10",
            "net_sts": 1,
            "qyid": "2655b332a116d2247fac3dd66a5285011102",
            "psp_uid": self.psp_uid,
            "psp_cki": self.P00001,
            "psp_status": 3,
            "secure_v": 1,
            "secure_p": "GPhone",
            "req_sn": round(time.time()*1000)
        }
        # 抽奖删除lottery_chance参数
        if type == 1:
            del params["lottery_chance"]
        res = requests.get(url, params=params)
        # print("（iqy）抽奖信息", res.json())
        if not res.json().get('code'):
            chance = int(res.json().get('daysurpluschance'))
            msg = res.json().get("awardName")
            return {"status": True, "msg": msg, "chance": chance}
        else:
            try:
                msg = res.json().get("kv", {}).get("msg")
            except:
                msg = res.json()["errorReason"]
        print(msg)
        return {"status": False, "msg": msg, "chance": 0}