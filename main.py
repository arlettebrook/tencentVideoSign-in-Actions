import os
import time

from loguru import logger

from config import TencentVideo


def main():
    try:
        if os.getenv('LOGIN_COOKIE'):
            tencentVideo = TencentVideo()
            logger.success("腾讯视频自动签到启动成功")
            tencentVideo.tencent_video_sign_in()
        logger.success("10秒之后退出程序")
        time.sleep(10)
    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    main()
