import wda
import time
import tidevice as ti
import threading as th
import os

class App(th.Thread):
    def __init__(self, sn):
        self.sn = sn
    def connect(self):
        self._d = wda.USBClient(self.sn)

a1 = App('00008110-001A79D10CE1401E')
# a2 = App('00008110-001E3C3E0E2A401E')
a1.connect()
a1._d.unlock()
a1._d.home()
a1._d.app_stop('com.ujweng.ftpspritefree')
a1._d.app_start('com.ujweng.ftpspritefree')
# print(a1._d.status()['ios']['ip'])
a1._d.press_duration('volumeDown', 1.5)
a1._d(type='Button', label='FTP服务器').tap()
a1._d(type='XCUIElementTypeButton', label='添加 FTP服务器').tap()
if(a1._d(predicate='label == "FTP精灵" AND name == "FTP精灵" AND value == "FTP精灵"').exists==True):
    a1._d(predicate='label == "以后再说"').tap()
    a1._d.swipe(0.8, 0.2, 0, 0.2)
    # a1._d(classChain='**/XCUIElementTypeButton[`label == "编辑"`][2]').tap()
    # a1._d(predicate='label == "删除“7.247.44.212, abc”"').tap()
    # a1._d(predicate='label == "删除" AND name == "删除" AND type == "XCUIElementTypeButton"').tap()
a1._d(type='XCUIElementTypeButton', label='添加 FTP服务器').tap()
a1._d(type='TextField', value='My FTP site').get().set_text('7.247.44.212')
a1._d(type='TextField', value='ftp.company.com').get().set_text('abc')
a1._d(type='XCUIElementTypeButton', label='完成').tap()
a1._d(type='StaticText', label='7.247.44.212').tap()





