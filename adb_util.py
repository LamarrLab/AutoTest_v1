import uiautomator2 as u2
import time
import subprocess

def get_wifi_device_list():
    cmd = r'adb devices'
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    pr.wait()
    out = pr.stdout.readlines()
    devices_wifi = []
    for i in out[1:-1]:
        device = str(i, encoding='utf-8').split('\t')[0]

        d = u2.connect(device) # usb方式连接设备
        devices_wifi.append(d.wlan_ip)  # 获取wifi ip地址
        cmd = r'adb connect' + d.wlan_ip + ':5555'  # 建立tcp连接
        pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True) # 发送命令
        pr.wait()
    return devices_wifi
