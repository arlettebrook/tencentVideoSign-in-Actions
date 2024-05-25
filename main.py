import os
import sys
import time

from loguru import logger

import push
from config import TencentVideo, IQY, Tieba, IQY2


def get_push_token():
    push_token = os.getenv('PUSHPLUS_TOKEN')
    if push_token:
        logger.success('PUSHPLUS_TOKEN已配置')
        return push_token
    else:
        logger.warning('建议配置PUSHPLUS_TOKEN，开启消息通知。')
        return None


def run_tvd():
    tencentVideo = TencentVideo()
    logger.success("腾讯视频自动签到启动成功")
    return tencentVideo.tencent_video_sign_in()


def run_aqy():
    iqy = IQY()
    iqy2 = IQY2()
    logger.success("爱奇艺任务启动成功")

    try:
        msg2 = iqy2.main()
    except Exception as e:
        info = f'爱奇艺签到运行失败：{e}'
        logger.error(info)
        msg2 = info

    msg1 = iqy.get_user_info()

    return msg1 + msg2


def run_tb():
    logger.success("贴吧任务启动成功")
    tb = Tieba()
    return tb.check_in()


def send_notice(push_token, notice):
    push.pushplus(push_token, title='任务通知:autoCheck-in', content=notice)


def change_log_level():
    try:
        log_level = os.getenv('LOG_LEVEL') or "INFO"
        logger.info(f"将使用{log_level}级别日志")
        logger.remove()
        logger.add(sys.stderr, level=log_level.upper())
    except Exception as e:
        logger.error(f'日志启动失败{e}')
        logger.exception(e)


@logger.catch
def main():
    change_log_level()
    push_token = get_push_token()
    tasks = []
    if os.getenv('LOGIN_COOKIE'):
        tasks.append((run_tvd, "腾讯视频任务"))
    if os.getenv("IQY_COOKIE"):
        tasks.append((run_aqy, "爱奇艺任务"))
    if os.getenv('BDUSS'):
        tasks.append((run_tb, "贴吧任务"))

    notice = ''
    result = ''

    for task, task_name in tasks:
        try:
            result = task()
            notice += f"\n{task_name}:\n{result}\n"
            logger.success(f"{task_name}已完成")
        except Exception as e:
            notice += f"\n{task_name}未完成：+{e}\n{result}\n"
            logger.error(f"{task_name}未完成！")
            logger.exception(e)

    notice = f'{len(tasks)}个任务执行了，结果如下：\n' + notice
    logger.info(notice)
    send_notice(push_token, notice)
    logger.info("所有任务已完成")
    logger.success("5秒之后退出程序")
    time.sleep(5)


if __name__ == '__main__':
    main()
