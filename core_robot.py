#!/usr/bin/python
# -*- coding:utf-8 -*-

import uiautomator2 as u2
import multiprocessing as mp
import subprocess
import time
import socket
import queue
import fcntl
import pickle
import sys
import os
import psutil
import lz4.frame
from random import randrange, random, uniform, choice
from uiautomator2 import Direction
import numpy as np
import json
import gzip
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from string import digits
import  threading as th

S_A_WIFI_IDLE = 'state_adb_over_wifi_idle'
S_A_USB_INIT = 'state_adb_over_usb_init'
S_A_WIFI_APP_RUNNING = 'state_adb_over_wifi_app_running'
S_A_USB_APP_RUNNING = 'state_adb_over_usb_app_running'
SERVER_CMD_RUN_APP = 'cmd_run_app'
SERVER_CMD_OK = 'cmd_run_ok'
DATA_PATH = 'data'


class App(th.Thread):
    def __init__(self, adb_type, sn, duration, q, app_name, app_activity, ppid=None, app_parameter=''):
        super(App, self).__init__()
        d = u2.connect(sn)  # connect()无需区分usb还是wifi连接
        self._adb_type = adb_type
        self._d = d
        self._duration_max = duration
        self._q = q
        self._app_name = app_name
        self._app_activity = app_activity
        self._pid = None
        self._ppid = ppid
        self._sn = sn  # 测温，需要重新连接，需要sn号
        self._app_parameter = app_parameter
        self._last_time = time.time()

    def _prepare_wait(self):
        self._d.app_stop_all()
        time.sleep(0.5)
        self._d.screen_off()
        time.sleep(0.5)
        self._d.screen_on()
        time.sleep(0.5)
        # 向上滑动翻页，建议不要动作太大，可能触及屏幕上方功能区。
        # self._d.swipe(0.5, 0.75, 0.5, 0.25, 0.1)
        self._d.swipe(0.5, 0.8, 0.5, 0.25, 0.1)
        time.sleep(0.5)
        # 静音
        # self._d.press("volume_up")
        # self._d.press("volume_mute")
        # time.sleep(0.5)
        for i in range(15):
            self._d.press("volume_down")
        # 下拉打开快速设置栏
        self._d.open_quick_settings()
        time.sleep(0.5)
        self._d(text="WLAN").click_exists()
        time.sleep(0.5)
        self._d.press("home")
        time.sleep(0.5)

    def _prepare_watchers(self):
        # self._d.watcher.when("跳过").click()
        # self._d.watcher.when("取消").click()
        # self._d.watcher.when("知道了").click()
        # self._d.watcher.when("知道啦").click()
        # self._d.watcher.when("我知道了").click()
        # self._d.watcher.when("我知道啦").click()
        # self._d.watcher.when("以后再说").click()
        # self._d.watcher.when("拒绝").click()
        # self._d.watcher.when('飞行模式。').call(self.restart_watcher)
        pass

    def _start(self):
        self._prepare_wait()
        if self._app_activity == '':
            self._d.app_start(self._app_name)
        else:
            self._d.app_start(self._app_name, self._app_activity)
        self._pid = self._d.app_wait(self._app_name, front=True)
        if not self._pid:
            print('%s is not running' % self._app_name)
            return  # TODO
        else:
            # print('%s pid is %d' % (self._app_name,self._pid))
            print('device %s app %s pid is %d' % (self._d.device_info['model'], self._app_name, self._pid))

    def add_extra_watchers(self):
        print('base class add_extra_watchers()')
        pass

    def do_once_operation(self):
        print('base class do_once_operation()')
        pass

    def do_loop_operation(self):
        print('base class do_loop_operation()')
        pass

    def send_email(self, image_path):
        sender = 'lydi1993@163.com'
        receivers = ['lydi1993@163.com']
        message = MIMEMultipart()
        message['Subject'] = '测试工具卡死问题'
        message['From'] = sender
        message['To'] = receivers[0]
        filename = image_path.split('\\')[1]
        content = MIMEText('测试工具卡死, ' + filename, 'plain', 'utf-8')
        # 添加照片附件
        with open(image_path, 'rb')as fp:
            picture = MIMEImage(fp.read())
            picture['Content-Type'] = 'application/octet-stream'
            picture['Content-Disposition'] = 'attachment;filename="' + filename + '"'
        # 将内容附加到邮件主体中
        message.attach(content)
        message.attach(picture)
        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect('smtp.163.com', 25)
            smtpObj.login('lydi1993@163.com', '邮箱SMTP功能授权码')
            smtpObj.sendmail(sender, receivers, message.as_string())
            smtpObj.quit()
            print('send email success!')
        except smtplib.SMTPException as e:
            print('send email error:', e)

    def run(self):
        self._begin = time.time()
        self._last_report = self._begin
        app_cnt = 0
        while True:
            app_cnt= app_cnt+1
            print("app_cnt: {}".format(app_cnt))
            # print('main_app_run:', os.getpid())
            try:
                self._d = u2.connect(self._sn)
                self._start()
                self._prepare_watchers()
                self.add_extra_watchers()
                # self._d.watcher.reset()
                self._d.watcher.start()
                self._last_time = time.time()
                self.do_once_operation()
                interface_last = [i.text.translate(str.maketrans('', '', digits)) for i in
                                  self._d.xpath('//android.widget.TextView').all()]
                while True:
                    self.do_loop_operation()
                    # 此方法获取的温度不变，必须重新连接设备才会获取最新温度（需优化）
                    temperature = self._d.device_info['battery']['temperature']
                    # 手机温度高于38，停止app运行，手机休息10分钟
                    if temperature >= 380:
                        self._d.watcher.stop()
                        self._d.app_stop_all()
                        self._d.screen_off()
                        print('device %s app %s temporary exit, temperature %d, sleep 10min' % (
                            self._d.device_info['model'], self._app_name, temperature))
                        time.sleep(600)
                        break
                    # 每隔5分钟通过页面的text是否与之前相等来判断APP是否卡死,不同app判断时间不同
                    if time.time() - self._last_time > 120 and self._app_name not in [
                        'com.tuyoo.fish3d.nearme.gamecenter', 'com.tencent.mobileqq', 'cn.nokia.speedtest5g',
                        'com.example.speedtest_v20', 'com.huawei.acceptance']:
                        self._last_time = time.time()
                        interface_cur = [i.text.translate(str.maketrans('', '', digits)) for i in
                                         self._d.xpath('//android.widget.TextView').all()]
                        if interface_cur == interface_last:
                            image = self._d.screenshot()
                            img_name = self._d.device_info['brand'] + '_' + self._d.device_info[
                                'serial'] + '_' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '.png'
                            if not os.path.isdir('image'):
                                os.makedirs('image')
                            img_path = os.path.join('image', img_name)
                            image.save(img_path)
                            # self.send_email(img_path)
                            print('device %s app %s terminate, send email!' % (
                                self._d.device_info['model'], self._app_name))
                            break
                        else:
                            interface_last = interface_cur

                    if self._duration_max > 0 and (time.time() - self._begin) > self._duration_max:
                        self._d.watcher.stop()
                        self._d.watcher.remove()
                        self._d.app_stop(self._app_name)
                        # print('%s pid %d exit' % (self._app_name, self._pid))
                        print('device %s app %s exit' % (self._d.device_info['model'], self._app_name))
                        return
                    elif time.time() - self._last_report > 10:
                        self._last_report = time.time()
                        stat = self._get_device_stat()
                        self._put_stat_data(stat)

            # except u2.UiObjectNotFoundError:
            # except:
            except Exception as e:
                time.sleep(1)
                print('device %s app %s' % (self._d.device_info['model'], self._app_name))
                print('error:', e.__class__.__name__, e)
                if self._ppid in psutil.pids():
                    # print('%s pid %d error, restart !' % (self._app_name, self._pid))
                    print('device %s app %s restart' % (self._d.device_info['model'], self._app_name))
                    time.sleep(5)
                    continue
                else:
                    # print('ppid %d not found, %s exit!' % (self._ppid, self._app_name))
                    print('ppid %s not found, device %s app %s exit' % (
                        self._ppid, self._d.device_info['model'], self._app_name))
                    self._d.watcher.stop()
                    self._d.watcher.remove()
                    self._d.app_stop_all()
                    return

    def _get_device_stat(self):
        device = {}
        device['wlan_ip'] = self._d.wlan_ip
        device['device_info'] = self._d.device_info
        device['app_current'] = self._d.app_current()
        device['wlan_stat'] = self._get_wlan_stat()
        return device

    def _get_wlan_stat(self):
        stat = {}
        stat['time'] = time.time()
        output, exit_code = self._d.shell('cat /proc/net/dev', timeout=5)
        if exit_code == 0:
            stat['/proc/net/dev'] = output
        output, exit_code = self._d.shell('cat /proc/net/wireless', timeout=5)
        if exit_code == 0:
            stat['/proc/net/wireless'] = output
        output, exit_code = self._d.shell('cat /proc/net/wifipro_tcp_stat', timeout=5)
        if exit_code == 0:
            stat['/proc/net/wifipro_tcp_stat'] = output
        return stat

    def _put_stat_data(self, data):
        self._q.put(pickle.dumps(data))

class Douyin(App):
    def __init__(self, adb_type, sn, q, ppid, app_parameter):
        super(Douyin, self).__init__(adb_type, sn, 0, q, 'com.ss.android.ugc.aweme',
                                     'com.ss.android.ugc.aweme.splash.SplashActivity', ppid, app_parameter)

    def do_once_operation(self):
        print('douyin class do_once_operation()')
        self._d(text='推荐').click_exists()

    def do_loop_operation(self):
        if self._d.app_current()['package'] != 'com.ss.android.ugc.aweme':
            raise
        # self._d(text='推荐').click()
        self._d.swipe(0.5, 0.75, 0.5, 0.25, 0.1)
        time.sleep(5 + randrange(5))
        # time.sleep(2 + randrange(3))

    def add_extra_watchers(self):
        print('Douyin class add_extra_watchers()')
        self._d.watcher.when("跳过").click()
        self._d.watcher.when("取消").click()
        self._d.watcher.when("知道了").click()
        self._d.watcher.when("知道啦").click()
        self._d.watcher.when("我知道了").click()
        self._d.watcher.when("我知道啦").click()
        self._d.watcher.when("以后再说").click()
        self._d.watcher.when("拒绝").click()
        self._d.watcher.when("登录后即可点赞喜欢的内容").when('//*[@resource-id="com.ss.android.ugc.aweme:id/f7i"]').click()
        self._d.watcher.when("登录后即可点赞喜欢的内容").when('//*[@resource-id="com.ss.android.ugc.aweme:id/gdp"]').click()
        self._d.watcher.when('登录后即可点赞喜欢的内容').when('//*[@resource-id="com.ss.android.ugc.aweme:id/gdr"]').click()
        self._d.watcher.when("抖音登录").when('//*[@resource-id="com.ss.android.ugc.aweme:id/ddz"]').click()
        self._d.watcher.when("抖音登录").when('//*[@resource-id="com.ss.android.ugc.aweme:id/dy0"]').click()
        self._d.watcher.when("抖音登录").when('//*[@resource-id="com.ss.android.ugc.aweme:id/dwx"]').click()
        self._d.watcher.when('抖音登录').when('//*[@resource-id="com.ss.android.ugc.aweme:id/da0"]').click()
        self._d.watcher.when('抖音登录').when('//*[@resource-id="com.ss.android.ugc.aweme:id/dax"]').click()
        self._d.watcher.when('抖音登录').when('//*[@resource-id="com.ss.android.ugc.aweme:id/d0s"]').click()
        self._d.watcher.when('抖音登录').when('//*[@resource-id="com.ss.android.ugc.aweme:id/dpg"]').click()
        self._d.watcher.when('个人信息保护指引').when('同意').click()
        self._d.watcher.when('“抖音”需要使用电话权限，您是否允许？').when('始终允许').click()
        self._d.watcher.when('禁止').click()
        self._d.watcher.when('不感兴趣').click()
        self._d.watcher.when('检测到更新').when('以后再说').click()

class Douyinlive(App):
    def __init__(self, adb_type, sn, q, ppid, app_parameter):
        super(Douyinlive, self).__init__(adb_type, sn, 0, q, 'com.ss.android.ugc.aweme',
                                     'com.ss.android.ugc.aweme.splash.SplashActivity', ppid, app_parameter)

    def do_once_operation(self):
        print('douyin class do_once_operation()')
        # liveRoom = input("请输入直播间名：")
        self._d(description="搜索").click()
        # self._d.send_keys(liveRoom)
        self._d.send_keys("东方甄选直播间")
        time.sleep(1)
        info_text = [i.text for i in self._d.xpath('//android.widget.TextView').all()]
        if '搜索' in info_text:
            self._d(text="搜索").click_exists()
        else:
            try:
                self._d.send_action("search")
            except:
                self._d.click(0.9, 0.94)
        # time.sleep(1)

        self._d(text="直播中，东方甄选的头像，按钮").click()
        print("已进入直播间")
        time.sleep(3)
        self.switchLiveDefinition()

    def switchLiveDefinition(self):
        ##切换直播清晰度
        self._d(description="更多面板 按钮").click()
        self._d(text="清晰度").click()
        #self._d.xpath('//*[@resource-id="com.ss.android.ugc.aweme:id/jti"]/android.widget.FrameLayout[1]').click()
        self._d(text="高清").click()

    def do_loop_operation(self):
        if self._d.app_current()['package'] != 'com.ss.android.ugc.aweme':
            raise


    def add_extra_watchers(self):
        print('Douyin class add_extra_watchers()')
        self._d.watcher.when("跳过").click()
        self._d.watcher.when("取消").click()
        self._d.watcher.when("知道了").click()
        self._d.watcher.when("知道啦").click()
        self._d.watcher.when("我知道了").click()
        self._d.watcher.when("我知道啦").click()
        self._d.watcher.when("以后再说").click()
        self._d.watcher.when("拒绝").click()
        self._d.watcher.when("登录后即可点赞喜欢的内容").when('//*[@resource-id="com.ss.android.ugc.aweme:id/f7i"]').click()
        self._d.watcher.when("登录后即可点赞喜欢的内容").when('//*[@resource-id="com.ss.android.ugc.aweme:id/gdp"]').click()
        self._d.watcher.when('登录后即可点赞喜欢的内容').when('//*[@resource-id="com.ss.android.ugc.aweme:id/gdr"]').click()
        self._d.watcher.when("抖音登录").when('//*[@resource-id="com.ss.android.ugc.aweme:id/ddz"]').click()
        self._d.watcher.when("抖音登录").when('//*[@resource-id="com.ss.android.ugc.aweme:id/dy0"]').click()
        self._d.watcher.when("抖音登录").when('//*[@resource-id="com.ss.android.ugc.aweme:id/dwx"]').click()
        self._d.watcher.when('抖音登录').when('//*[@resource-id="com.ss.android.ugc.aweme:id/da0"]').click()
        self._d.watcher.when('抖音登录').when('//*[@resource-id="com.ss.android.ugc.aweme:id/dax"]').click()
        self._d.watcher.when('抖音登录').when('//*[@resource-id="com.ss.android.ugc.aweme:id/d0s"]').click()
        self._d.watcher.when('抖音登录').when('//*[@resource-id="com.ss.android.ugc.aweme:id/dpg"]').click()
        self._d.watcher.when('个人信息保护指引').when('同意').click()
        self._d.watcher.when('“抖音”需要使用电话权限，您是否允许？').when('始终允许').click()
        self._d.watcher.when('禁止').click()
        # self._d.watcher.when('不感兴趣').click()
        self._d.watcher.when('检测到更新').when('以后再说').click()
        self._d.watcher.when('青少年模式').when('我知道了').click()
        self._d.watcher.when('跳过广告').click()

class Agent(th.Thread):
    def __init__(self, adb_type, server_ip, server_port, app_video, app_live, app_web, app_download, app_rate, sn_app,
                 user_num, wifi_all):
        super(Agent, self).__init__()
        self._adb_type = adb_type
        self._server_ip = server_ip
        self._server_port = server_port
        self._app_video = app_video
        self._app_live = app_live
        self._app_web = app_web
        self._app_download = app_download
        self._app_rate_list = app_rate
        self._app_rate = choice(self._app_rate_list)
        self._sn_app = sn_app
        self._user_num = user_num
        self._wifi_all = wifi_all
        self._q = mp.Queue(maxsize=-1)
        if adb_type == 'wifi':
            self._state = S_A_WIFI_IDLE
        else:
            self._state = S_A_USB_INIT
        self._apps = []
        self._all_devices = []
        self._last_time = time.time()
        self._restart_interval = 1800
        # self._restart_interval = randrange(2400, 3600)


    def _get_device_list(self):
        cmd = r'adb devices'
        pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        pr.wait()
        out = pr.stdout.readlines()
        devices = []
        for i in (out)[1:-1]:
            device = str(i, encoding='utf-8').split('\t')[0]
            if ':' not in device:
                devices.append(device)
        return devices

    def _udp_send_reply(self, data):
        data = lz4.frame.compress(pickle.dumps(data))
        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.sendto(data, (self._server_ip, self._server_port))
        # s.settimeout(2)
        # try:
        #     data = s.recv(256 * 1024)
        # except socket.timeout:
        #     print('time out')
        #     s.close()
        #     return None
        try:
            data = pickle.loads(data)
        except:
            data = None
        # s.close()
        return data

    def _proc_recv(self, data):
        decompress_data = lz4.frame.decompress(data)
        msg = pickle.loads(decompress_data)
        reply = {}
        if msg['agent_state'] == S_A_USB_INIT:
            reply['cmd'] = SERVER_CMD_RUN_APP
            reply['devices'] = []
            for i in range(len(msg['devices'])):
                reply['devices'].append(msg['devices'][i])
            return reply

        if msg['agent_state'] == S_A_WIFI_IDLE:
            reply['cmd'] = SERVER_CMD_RUN_APP
            print('msg:', msg)
            reply['devices'] = []
            for i in range(len(msg['devices'])):
                reply['devices'].append(msg['devices'][i])
            print('reply:', reply)
            return reply

        elif msg['agent_state'] == S_A_USB_APP_RUNNING or msg['agent_state'] == S_A_WIFI_APP_RUNNING:

            stat = msg['device_stat']
            file_name = str(int(stat['wlan_stat']['time'])) + '-' + stat['device_info']['serial'] + '-' + stat[
                'wlan_ip'] + '.json'
            json_str = json.dumps(stat)

            full_path = os.path.join(DATA_PATH, file_name + '.gz')
            with gzip.open(full_path, 'w') as fout:
                fout.write(json_str.encode('utf-8'))

            reply['cmd'] = SERVER_CMD_OK
            reply['serial'] = stat['device_info']['serial']
            reply['wlan_ip'] = stat['wlan_ip']
            return reply

    def _start_apps(self, device):
        # 随机启动APP，设置随机运行时间
        sn = device
        # apps = device[1]
        # 按比例启动不同类型APP
        type_rate = random()
        if type_rate < self._app_rate[0]:
            apps = self._app_video
        elif type_rate < sum(self._app_rate[:2]):
            apps = self._app_live
        elif type_rate < sum(self._app_rate[:3]):
            apps = self._app_web
        else:
            apps = self._app_download

        #随机选择一个具体的APP
        #app_name = apps[randrange(len(apps))]
        app_name = 'douyinlive'

        # 根据当前sn判断是否需要启动指定app
        app_parameter = ''
        value = self._sn_app.get(sn)
        if value:
            app_name = value[0]
            app_parameter = value[1]

        app = None
        pid = os.getpid()
        if app_name == 'douyin':
            app = Douyin(self._adb_type, sn, self._q, pid, app_parameter)
        elif app_name == 'douyinlive':
            app = Douyinlive(self._adb_type, sn, self._q, pid, app_parameter)

        if app:
            self._apps.append([app, time.time(), 3600, device])
            # self._apps.append([app, time.time(), randrange(1200, 1800), device])
            with open('app_type_rate.log', 'a') as f:
                f.write("cur_time: %s, device: %s, app_name: %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), device, app_name) + '\n')
            app.start()

    # 关闭单个手机
    def _close_device(self, device):
        d = u2.connect(device)
        d.open_quick_settings()  # 下拉打开快速设置栏
        time.sleep(2)
        for i in d.xpath('//android.widget.TextView').all():
            if i.text in self._wifi_all:
                d(text=i.text).click_exists()
                break
        time.sleep(1)
        d.press("home")
        time.sleep(0.5)
        # d.watcher.stop()
        # d.watcher.remove()
        # time.sleep(0.5)
        d.app_stop_all()
        time.sleep(0.5)
        d.screen_off()

    # 所有手机重启，重新选择业务比例以及启动手机个数
    def _restart_all_devices(self):
        for app in self._apps:
            cur_app = app[0]
            temp_device = app[3]
            print('all device restart! device %s, cur_app %s' % (temp_device, cur_app))
            cur_app.terminate()
            cur_app.join()
        self._apps.clear()
        restart_num = randrange(self._user_num[0], self._user_num[1])
        restart_num = len(self._all_devices) if restart_num > len(self._all_devices) else restart_num
        cur_restart_devices = np.random.choice(self._all_devices, restart_num, replace=False)
        cur_close_devices = [one_device for one_device in self._all_devices if one_device not in cur_restart_devices]

        # 修改APP类型比例
        self._app_rate = choice(self._app_rate_list)
        print('current_app_rate:%s, cur_restart_devices:%s, cur_close_devices:%s, self._apps:%s' % (
            self._app_rate, cur_restart_devices, cur_close_devices, self._apps))

        # 打流手机不关闭
        for key, value in self._sn_app.items():
            if key in cur_close_devices and (value[0] == 'qpython' or value[0] == ' '):
                cur_close_devices.remove(key)

        with open('app_type_rate.log', 'a') as f:
            f.write("all device restart! cur_time: %s, cur_app_rate: %s, cur_restart_devices: %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self._app_rate, cur_restart_devices) + '\n')

        for device_close in cur_close_devices:
            self._close_device(device_close)
        for device_restart in cur_restart_devices:
            self._start_apps(device_restart)

    def run(self):
        while True:  ## 需要不断刷新设备列表
            # print('main_fun_run:', os.getpid())
            agent_info = {}
            agent_info['agent_state'] = self._state
            if self._state == S_A_USB_INIT or self._state == S_A_WIFI_IDLE:
                if self._adb_type == 'usb':
                    agent_info['devices'] = self._get_device_list()
                    self._all_devices = agent_info['devices']
                    # print("got usb devices!")

                # reply = self._udp_send_reply(agent_info)
                data = lz4.frame.compress(pickle.dumps(agent_info))
                reply = self._proc_recv(data)
                if reply and reply['cmd'] == SERVER_CMD_RUN_APP:
                    print('all devices:', reply['devices'])
                    with open('app_type_rate.log', 'a') as f:
                        f.write("all device restart! cur_time: %s, cur_app_rate: %s, cur_restart_devices: %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self._app_rate, reply['devices']) + '\n')
                    for device in reply['devices']:
                        self._start_apps(device)
                    if self._state == S_A_USB_INIT:
                        self._state = S_A_USB_APP_RUNNING
                    else:
                        self._state = S_A_WIFI_APP_RUNNING
            # elif self._state == S_A_USB_APP_RUNNING or self._state == S_A_WIFI_APP_RUNNING:
            # try:
            #     agent_info['device_stat'] = pickle.loads(self._q.get(timeout=1))
            # except queue.Empty:
            #     continue
            # reply = self._udp_send_reply(agent_info)
            # data = lz4.frame.compress(pickle.dumps(agent_info))
            # reply = self._proc_recv(data)
            # if reply and reply['cmd']:
            #     print(reply)


            '''
            # 间隔40-60min,所有手机，整体重启
            if time.time() - self._last_time >= self._restart_interval:
                self._restart_all_devices()
                self._last_time = time.time()
            '''

            '''
            # 判断每个手机是否到APP终止时间，终止以后重新启动别的APP
            restart_list = []
            for app in self._apps:
                if time.time() - app[1] >= app[2]:
                    cur_app = app[0]
                    temp_device = app[3]
                    restart_list.append(temp_device)
                    print('app exit and restart! time interval %.2f, target time %d, device %s, cur_app %s' % (
                        time.time() - app[1], app[2], temp_device, cur_app))
                    cur_app.terminate()
                    cur_app.join()
            
            if restart_list:
                self._apps = [remain_app for remain_app in self._apps if remain_app[3] not in restart_list]
                print('restart_list:%s, self._apps:%s' % (restart_list, self._apps))
                for restart_app in restart_list:
                    self._start_apps(restart_app)
            '''
            time.sleep(5)


def main(app_video, app_live, app_web, app_download, app_rate, sn_app, user_num, wifi_all):
    agent = Agent('usb', '127.0.0.1', 12345, app_video, app_live, app_web, app_download, app_rate, sn_app, user_num,
                  wifi_all)
    agent.start()

    start_time = time.time()
    while True:
        # while time.time() - start_time <= 3600:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            agent.terminate()
            agent.join()
            print(' agent exit!')
            sys.exit(0)
