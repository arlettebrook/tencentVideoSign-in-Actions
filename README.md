<p align="center">
  <h2 align="center"><storng>腾讯视频自动签到</storng></h2>
  <p align="center">
    Github Action版
    <br/>
    <br/>
    <br/>
  </p>
</p>



## 今日签到状态

![tencnetVideoAutoCheck](https://github.com/arlettebrook/tencentVideoAutoCheck/actions/workflows/main.yml/badge.svg)

---



## 使用说明



### 配置流程



1. Fork 本仓库，然后点击你的仓库右上角的 Settings，找到 Secrets 这一项actions，添加 LOGIN_COOKIE 、LOGIN_URL、 LOGIN_URL_PAYLOADLOAD、PUSHPLUS_TOKEN四个变量。

   ![image-20230806202139340](README.assets/image-20230806202139340.png)

2. 设置好环境变量后点击你的仓库上方的 `Actions` 选项，第一次打开需要点击 `I understand...` 按钮，确认在 Fork 的仓库上启用 GitHub Actions 。

3. 任意发起一次commit，可以参考下图流程修改readme文件。

   - 打开`README.md`，点击修改按钮

   - 修改任意内容，这里在末尾插入了空格。移动到最下面，点击提交。


4. 至此自动签到就搭建完毕了。



### login_cookie等参数的获取



1. 网页登录 [腾讯视频](v.qq.com)
2. 进入该网页：https://vip.video.qq.com/fcgi-bin/comm_cgi?name=hierarchical_task_system&cmd=2
3. F12 输入在控制台输入document.cookie然后回车，得到的全部信息就是login_cookie；
5. 获取配置信息的效果图如下：
![获取配置信息](./img/1.jpg)

5. 或者登录成功之后F12，F5依次输入，然后搜索NewRefresh，这个url就是`LOGIN_URL`， `LOGIN_URL_PAYLOADLOAD`就是这个url的请求体。
6. `PUSHPLUS_TOKEN`公众号pushplus获取

> 注意：如果报错没有通过图像验证，需要在cookie中加入vdevice_qimei36='...'[使用常用手机打开获取](https://m.v.qq.com/schemerul)

​	

### 配置workflow执行信息写入到run.log



1. 仓库左上方settings
![配置workflow执行信息写入到run.log](./img/2.jpg)
2. 如图
![配置workflow执行信息写入到run.log](img/3.jpg)
3. 如图，保存
![配置workflow执行信息写入到run.log](/img/4.jpg)



### 查看运行状态

进入jobs查看check-in-status步骤即可查看输出日志

![image-20230806204758646](README.assets/image-20230806204758646.png)
