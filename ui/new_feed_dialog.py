from PyQt5 import Qt, QtCore, uic
import xml.etree.ElementTree as ET
import syndicate


class NewFeedDialog(Qt.QDialog):
    def __init__(self, feed, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialize_component()
        self.xml_text = ""
        self.feed = feed

    def _initialize_component(self):
        uic.loadUi("ui/new_feed_dialog.ui", self)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setFixedSize(self.width(), self.height())
        self.button_load.clicked.connect(lambda: self._load_clicked())
        self.accepted.connect(lambda: self._ok_clicked())

    def show(self):
        self.edit_title.setEnabled(False)
        self.label_message.setText("")
        self.edit_title.setText("")
        self.edit_url.setText("")
        self.xml_text = ""
        super().show()

    def _ok_clicked(self):
        if self.xml_text != "":
            url = self.edit_url.text()
            title = self.edit_title.text().strip()
            # FIXME: this is threadblocking and the
            # files are huge
            # FIXME: add an option to not be notified if a new item added
            # since this will add a lot of items
            syndicate.parse_rss(self.feed, self.xml_text, url, title)

    def _load_clicked(self):
        url = self.edit_url.text()
        try:
            self.xml_text = syndicate.fetch_rss(url)
            root = ET.fromstring(self.xml_text)
        except Exception as e:
            # TODO: make proper error handling for better messages
            self.label_message.setText(str(e))
        else:
            self.label_message.setText("")
            self.edit_title.setEnabled(True)
            self.edit_title.setText(root.find("channel").find("title").text)
