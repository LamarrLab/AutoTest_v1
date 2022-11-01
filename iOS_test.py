import wda
import time

bundle_id = 'com.skyjos.ftpmanagerfree'
# c = wda.Client('http://169.254.84.208:8100')
c = wda.USBClient()
s = c.session(bundle_id)
time.sleep(1)
print('1111')
s(label=u'搜索').tap()
print('2222')
s(type='XCUIElementTypeSearchField').set_text('东方甄选直播间')
print('3333')
s(label='搜索', name='搜索').tap()
print('4444')
time.sleep(3)
s.click(0.5, 0.5)


# 无线局域网与蜂窝网络
# 个人信息保护指引 -- 同意
# 发送通知 --不允许
# 跳过广告



