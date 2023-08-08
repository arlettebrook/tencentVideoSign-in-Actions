import os
import time

from loguru import logger

from config import TencentVideo, IQY


def main():
    try:
        logger.success("autoCheck-in启动成功")
        if os.getenv('LOGIN_COOKIE'):
            tencentVideo = TencentVideo()
            logger.success("腾讯视频自动签到启动成功")
            tencentVideo.tencent_video_sign_in()
            logger.success("腾讯视频任务已完成")
        if os.getenv("IQY_COOKIE"):
            iqy = IQY()
            logger.success("爱奇艺任务启动成功")
            iqy.get_rewards()
            time.sleep(3)
            iqy.get_user_info()
            logger.success("爱奇艺任务已完成")
        logger.info("所有任务已完成")
        logger.success("10秒之后退出程序")
        time.sleep(10)
    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    main()
