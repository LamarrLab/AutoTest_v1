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
# a2.connect()
a1._d.unlock()
# a2._d.unlock()
a1._d.home()
a1._d.app_start('com.skyjos.ftpmanagerfree')
print(a1._d.status()['ios']['ip'])
# bundle_id = 'com.skyjos.ftpmanagerfree'
# # c = wda.Client('http://169.254.84.208:8100')
# c = wda.USBClient()
# s = c.session(bundle_id)
# time.sleep(1)
# s(label=u'搜索').tap()
# s(type='XCUIElementTypeSearchField').set_text('东方甄选直播间')
# s(label='搜索', name='搜索').tap()
# time.sleep(3)
# s.click(0.5, 0.5)




