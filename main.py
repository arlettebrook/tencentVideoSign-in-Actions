import os
import sys
import time

from loguru import logger

import push
from config import TencentVideo, IQY, Tieba


@logger.catch
def _get_push_token():
    push_token = os.getenv('PUSHPLUS_TOKEN')
    if push_token:
        logger.success('PUSHPLUS_TOKEN已配置')
        return push_token
    else:
        logger.warning('建议配置PUSHPLUS_TOKEN，开启消息通知。')
        return None


@logger.catch
def run_tvd():
    tencentVideo = TencentVideo()
    logger.success("腾讯视频自动签到启动成功")
    return tencentVideo.tencent_video_sign_in()


@logger.catch
def run_aqy():
    iqy = IQY()
    logger.success("爱奇艺任务启动成功")
    return iqy.get_user_info()


@logger.catch
def run_tb():
    logger.success("贴吧任务签到成功")
    tb = Tieba()
    return tb.check_in()


@logger.catch
def send_notice(push_token, notice):
    push.pushplus(push_token, title='任务通知:autoCheck-in', content=notice)


@logger.catch
def main(log_level):
    logger.info(f"将使用{log_level}级别日志")
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    notice = ''
    push_token = _get_push_token()
    num = 0
    try:
        logger.success("autoCheck-in启动成功")
        if os.getenv('LOGIN_COOKIE'):
            notice += run_tvd()
            logger.success("腾讯视频任务已完成")
            num += 1
        if os.getenv("IQY_COOKIE"):
            notice += run_aqy()
            logger.success("爱奇艺任务已完成")
            num += 1
        if os.getenv('BDUSS'):
            notice += run_tb()
            logger.success("贴吧任务已完成")
            num += 1
        notice = f'{num}个任务执行了，结果如下：\n' + notice
        logger.info(notice)
        send_notice(push_token, notice)
        logger.info("所有任务已完成")
        logger.success("5秒之后退出程序")
        time.sleep(5)
    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    main(os.getenv('LOG_LEVEL') or "INFO")
