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
import threading as th
import wda

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
        d = wda.USBClient(sn)  # sn为iOS终端的uuid
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
        self._d.unlock()
        time.sleep(0.5)
        self._d.home()

    def _prepare_watchers(self):
        pass

    def _start(self):
        self._prepare_wait()
        if self._app_activity == '':
            self._d.app_start(self._app_name)
        else:
            self._d.app_start(self._app_name, self._app_activity)
        self.app_current_pid = self._d.app_current()['pid']  # 获取当前app在终端上的pid，用来判断是否启动成功
        if not self.app_current_pid:
            print('%s is not running' % self._app_name)
        else:
            print('%s is running' % self._app_name)

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
        while True:
            try:
                self._start()
                self._prepare_watchers()
                self.add_extra_watchers()
                self._last_time = time.time()
                self.do_once_operation()
                self._d.device_info()
                while True:
                    self.do_loop_operation()

                    # if self._duration_max > 0 and (time.time() - self._begin) > self._duration_max:
                    #     self._d.watcher.stop()
                    #     self._d.watcher.remove()
                    #     self._d.app_stop(self._app_name)
                    #     # print('%s pid %d exit' % (self._app_name, self._pid))
                    #     print('device %s app %s exit' % (self._d.device_info['model'], self._app_name))
                    #     return
                    # elif time.time() - self._last_report > 10:
                    #     self._last_report = time.time()
                    #     stat = self._get_device_stat()
                    #     self._put_stat_data(stat)

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
        device['wlan_ip'] = self._d.status()['ios']['ip']
        device['device_info'] = self._d.device_info
        device['app_current'] = self._d.app_current()
        return device

    def _get_wlan_stat(self):
        pass

    def _put_stat_data(self, data):
        self._q.put(pickle.dumps(data))

class FTPmanager(App):
    def __init__(self, adb_type, sn, q, ppid, app_parameter):
        super(FTPmanager, self).__init__(adb_type, sn, 0, q, 'com.skyjos.ftpmanagerfree', '', ppid, app_parameter)

    def do_loop_operation(self):
        pass

class BiliBili(App):
    def __init__(self, adb_type, sn, q, ppid, app_parameter):
        super(BiliBili, self).__init__(adb_type, sn, 0, q, 'tv.danmaku.bilianime', '', ppid, app_parameter)

    def do_loop_operation(self):
        print('app tid: ', th.current_thread().name)
        self._d.swipe(0.5, 0.5, 0.5, 0.3)

class Kuaishou(App):
    def __init__(self, adb_type, sn, q, ppid, app_parameter):
        super(Kuaishou, self).__init__(adb_type, sn, 0, q, 'com.jiangjia.gif', '', ppid, app_parameter)
        self.start_time = time.time()
        self.last_time = time.time()

    def do_loop_operation(self):
        print('app tid: ', th.current_thread().name)
        print('11111')
        self.start_time = time.time()
        self._d.swipe(0.5, 0.5, 0.5, 0.3)
        print('time cost: ', time.time()-self.start_time)
        print('time slot: ', time.time()-self.last_time)
        self.last_time = time.time()

# 抖音暂时无法使用，iOS端同时启动wda和抖音后会卡死
class Douyin(App):
    def __init__(self, adb_type, sn, q, ppid, app_parameter):
        super(Douyin, self).__init__(adb_type, sn, 0, q, 'com.ss.iphone.ugc.Aweme ', '', ppid, app_parameter)

    def do_once_operation(self):
        self._d.swipe(0.5, 0.8, 0.5, 0.3)
        time.sleep(2)

class Douyinlive(App):
    def __init__(self, adb_type, sn, q, ppid, app_parameter):
        super(Douyinlive, self).__init__(adb_type, sn, 0, q, 'com.ss.iphone.ugc.Aweme', '', ppid, app_parameter)

    def do_once_operation(self):
        # liveRoom = input("请输入直播间名：")
        self._d(label=u'搜索').tap()
        self._d(type='XCUIElementTypeSearchField').set_text('东方甄选直播间')
        self._d(label='搜索', name='搜索').tap()
        time.sleep(1)
        # self._d(text="直播中，东方甄选的头像，按钮").click()
        # print("已进入直播间")
        # time.sleep(3)
        # self.switchLiveDefinition()

    def do_loop_operation(self):
        print('app tid: ', th.current_thread().name)
        self._d.swipe(0.5, 0.5, 0.5, 0.3)

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
        cmd = r'idevice_id -l'
        pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        pr.wait()
        out = pr.stdout.readlines()
        devices = []
        for i in out:
            device = str(i, encoding='utf-8').split('\n')[0]
            print(device)
            if ':' not in device:
                devices.append(device)
                print('add device')
        return devices

    def _launch_wda(self):
        for device in self._all_devices:
            cmd = r'tidevice - u[{}] wdaproxy - B[com.wnight.WebDriverAgentRunner.xctrunner ] --port 8100'.format(device)
            pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            pr.wait()


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

        # 随机选择一个具体的APP
        #app_name = apps[randrange(len(apps))]
        app_name = 'FTPmanager'

        # 根据当前sn判断是否需要启动指定app
        app_parameter = ''
        value = self._sn_app.get(sn)
        if value:
            app_name = value[0]
            app_parameter = value[1]

        app = None
        pid = os.getpid()
        if app_name == 'FTPmanager':
            app = FTPmanager(self._adb_type, sn, self._q, pid, app_parameter)
        elif app_name == 'kuaishou':
            app = Kuaishou(self._adb_type, sn, self._q, pid, app_parameter)
        elif app_name == 'bilibili':
            app = BiliBili(self._adb_type, sn, self._q, pid, app_parameter)
        elif app_name == 'douyin':
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
            print('fun tid: ', th.current_thread().name)
            agent_info = {}
            agent_info['agent_state'] = self._state
            if self._state == S_A_USB_INIT or self._state == S_A_WIFI_IDLE:
                if self._adb_type == 'usb':
                    print('try get devices')
                    agent_info['devices'] = self._get_device_list()
                    self._all_devices = agent_info['devices']
                    self._launch_wda()
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
