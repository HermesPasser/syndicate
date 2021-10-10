from window import Window
from PyQt5.QtWidgets import QApplication
from syndicate import feed
import sys

if __name__ == '__main__':
    feed.open()
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    code = app.exec_()
    feed.close()
    sys.exit(code)
