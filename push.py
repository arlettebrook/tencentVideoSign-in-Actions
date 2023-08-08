import json

import requests
from loguru import logger


@logger.catch
def pushplus(token, title='Notifications', content='', template='txt'):
    if token == -1:
        logger.warning("建议配置PUSHPLUS_TOKEN，开启消息通知。")
        return
    title = title
    url = 'http://www.pushplus.plus/send/'
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": template
    }
    body = json.dumps(data).encode(encoding='utf-8')
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=body, headers=headers)
    content = response.text
    loads = json.loads(content)
    if loads['code'] != 200:
        logger.error("PUSHPLUS_TOKEN:" + loads['msg'])
    else:
        logger.info(title + ":消息发送成功-" + loads['msg'])
        return loads
