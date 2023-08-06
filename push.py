import json

import requests
from loguru import logger


@logger.catch()
def pushplus(content, token, template='markdown'):
    title = '腾讯视频签到提醒'
    url = 'http://www.pushplus.plus/send/'
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "markdown"
    }
    body = json.dumps(data).encode(encoding='utf-8')
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=body, headers=headers)
    content = response.text
    loads = json.loads(content)
    if loads['code'] != 200:
        logger.error("PUSHPLUS_TOKEN:" + loads['msg'])
    else:
        logger.info(title+":消息发送成功-"+loads['msg'])
        return loads
