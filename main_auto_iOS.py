from core_robot_iOS import *
from sys import argv
# from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow
# from PyQt5.uic import loadUi
# from ui.Main_Window import Ui_Dialog
# from test import auto_dialog

APP_VIDEO = ['douyin']
APP_LIVE = ['douyinlive']
APP_WEB = ['toutiao', 'zhihu', 'taobao']
APP_DOWNLOAD = ['speedtest5g', 'speedtestv2']
# 可设置多组APP类型比例参数，每组比例和为1
APP_RATE = [[0, 1, 0, 0]]
# 随机启动终端数量的上下限，根据实际连接终端数设置
USER_NUM = [1, 15]
# 连接网络名称
WIFI_ALL = ['Test_mu']

# 指定手机启动指定APP
# QQ必须用QQ号不能用昵称，第二个参数是联系人QQ号，若不传参数，则为接听方
# SN_APP暂未使用
SN_APP = {'6HJ4C1981501035': ('qq', '1137312583'),
          'VBJDU18A0': ('qq', ''),
          'VBJDU18A30002': ('cloudcampus', ''),
          'MDX0220A28028124': ('qpython', ''),
          '2dd89402': ('catchfish', '')}

if __name__ == '__main__':
    # app = QApplication(argv)
    # dialog = QDialog()
    # auto = auto_dialog(dialog)
    # dialog.show()
    # app.exec()
    main(APP_VIDEO, APP_LIVE, APP_WEB, APP_DOWNLOAD, APP_RATE, SN_APP, USER_NUM, WIFI_ALL)
