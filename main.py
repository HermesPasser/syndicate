from window import Window
from PyQt5.QtWidgets import QApplication
from syndicate import ChannelList
import sys

if __name__ == '__main__':
    feed = ChannelList()
    feed.open()
    app = QApplication(sys.argv)
    win = Window(feed)
    win.show()
    code = app.exec_()
    feed.close()
    sys.exit(code)
