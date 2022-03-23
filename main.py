from ui.window import Window
from PyQt5.QtWidgets import QApplication
from syndicate import ChannelList
import sys

def main():
    feed = ChannelList()
    feed.open()
    app = QApplication(sys.argv)
    win = Window(feed)
    win.show()
    code = app.exec_()
    feed.close()
    sys.exit(code)

if __name__ == '__main__':
	main()
