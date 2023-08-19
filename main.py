import os
import sys
import time

from loguru import logger

from config import TencentVideo, IQY


def run_tvd():
    tencentVideo = TencentVideo()
    logger.success("腾讯视频自动签到启动成功")
    tencentVideo.tencent_video_sign_in()
    logger.success("腾讯视频任务已完成")


def run_aqy():
    iqy = IQY()
    logger.success("爱奇艺任务启动成功")
    iqy.get_user_info()
    logger.success("爱奇艺任务已完成")


def main(log_level):
    logger.info(f"将使用{log_level}级别日志")
    logger.remove()
    logger.add(sys.stderr, level=log_level)

    try:
        logger.success("autoCheck-in启动成功")
        if os.getenv('LOGIN_COOKIE'):
            run_tvd()
        if os.getenv("IQY_COOKIE"):
            run_aqy()
        logger.info("所有任务已完成")
        logger.success("5秒之后退出程序")
        time.sleep(5)
    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    main(os.getenv('LOG_LEVEL') or "INFO")
