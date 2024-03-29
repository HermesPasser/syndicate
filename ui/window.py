import os
from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic
from ui.new_feed_dialog import NewFeedDialog
from ui.system_tray import SystemTray
from syndicate import fetch_rss, parse_rss


class Window(Qt.QMainWindow):
    def __init__(self, feed, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feed = feed
        self.list_item_metadata = []  # [{}, ...]
        self.channel_list_metadata = []  # [(id, title), ...]
        self._show_notifications = True
        self._prev_rect = None
        self._initialize_component()
        self._load_channel()

        feed.subscribe(lambda item: self._on_new_item_added(item))
        self.timer.start(10000 * 2)

    def _initialize_component(self):
        uic.loadUi("ui/window.ui", self)
        self.setFixedSize(self.width(), self.height())
        self.button_new.clicked.connect(lambda: self._new_clicked())
        self.button_save.clicked.connect(lambda: self._save_clicked())
        self.button_mark_read.clicked.connect(lambda: self._mark_read_clicked())
        self.button_mark_all_read.clicked.connect(lambda: self._mark_all_read_clicked())
        self.button_refresh.clicked.connect(lambda: self._refresh_clicked())
        self.tree_view_channels.itemClicked.connect(self._tree_item_selected)
        self.new_feed_dialog = NewFeedDialog(self.feed)
        self.new_feed_dialog.finished.connect(lambda: self._refresh_clicked())
        self.tray = SystemTray()
        self.tray.open_action.triggered.connect(self.show)
        self.tray.exit_action.triggered.connect(self.close)
        self.timer = QtCore.QTimer(self)
        # self.timer.timeout.connect(self._look_for_updates)

        # TODO: if i'm really going to deal with multiple tabs then i need to create those list items
        # dynamically and keep track witch is the current one
        self.list_item.itemSelectionChanged.connect(self._item_selected)

    def _load_channel(self):
        self.tree_view_channels.clear()
        self.channel_list_metadata = [
            (id, title) for id, title in self.feed.channel_id_and_title
        ]
        for _, title in self.channel_list_metadata:
            self._add_channel(title)

        if len(self.channel_list_metadata) != 0:
            first_channel_id = self.channel_list_metadata[0][0]
            self._load_feed(first_channel_id)

            if len(self.list_item_metadata) != 0:
                self._set_content(self.list_item_metadata[0]["content"])

    def _load_feed(self, channel_id):
        # TODO: pass which tab, so it now were should load
        # when we add multiple tabs support
        self.list_item.clear()
        self.list_item_metadata = [
            item for _, item in self.feed.get_feed(channel_id).items()
        ]
        for item in self.list_item_metadata:
            self._add_list_item(item["title"], not item["read"])

    def _on_new_item_added(self, item):
        # NOTE: not wise to call _load_feed yet since
        # this method will be called when adding a new
        # channel, and there fore each new element added
        # by that window will call this method
        # I need to se a way of disabling selectively
        # the notifications (crate a api for that later)
        # TODO: create a custom window to list all new feeds
        # just like RSSOwl does intead of disabling the notifications
        if self._show_notifications:
            self.tray.show_message("New item", item["title"])

    def _set_component_font(self, comp, weight, italic):
        font = comp.font()
        font.setItalic(italic)
        font.setWeight(weight)
        comp.setData(QtCore.Qt.FontRole, font)

    # TODO: refactor this class and remove this and its counterpart
    def _mark_list_item_unread(self, item):
        self._set_component_font(item, QtGui.QFont.Bold, False)

    def _mark_list_item_read(self, item):
        self._set_component_font(item, QtGui.QFont.Normal, True)

    def _set_item_status(self, item, metaitem, is_read):
        """Update the read mark in the engine and in the UI"""
        self.feed.mark_feed_item_as(metaitem["channel"], metaitem["id"], is_read)

        if is_read:
            self._mark_list_item_read(item)
        else:
            self._mark_list_item_unread(item)

    def _add_list_item(self, text, read=False):
        # FIXME: since i removed the logic that appends
        # items to the list_item_metadata then this can't
        # be used to add new items that can be brought by
        # refresh/update. Add other func to that or modify
        # this one
        item = QtWidgets.QListWidgetItem(text)

        if read:
            self._mark_list_item_unread(item)
        else:
            self._mark_list_item_read(item)

        self.list_item.addItem(item)

    def hideEvent(self, e):
        self._prev_rect = self.geometry()
        super().hideEvent(e)
        self.tray.show()
        self.hide()

    def show(self):
        super().show()
        self.tray.hide()
        self.setWindowState(QtCore.Qt.WindowMaximized)

        if self._prev_rect is not None:
            self.move(self._prev_rect.x(), self._prev_rect.x())

    # TODO: not forget to create a remove() that removes from the list and listwidget
    # (maybe we call just hide it instead?)
    # FIXME: this is called when 'ctrl + a' is typed, find a way to avoid that
    def _item_selected(self):
        qt_item = self.list_item.currentItem()
        title = qt_item.text()

        it = filter(lambda it: it["title"] == title, self.list_item_metadata)
        item = list(it)[0]
        item["read"] = not item["read"]

        self._set_content(item["content"])
        # FIXME: clicking is not responsive since the listwidgetitem style
        # does not consistently changes all times, whitch make it confusing
        self._set_item_status(qt_item, item, item["read"])

    def _new_clicked(self):
        self._show_notifications = False
        self.new_feed_dialog.show()

    def _save_clicked(self):
        self.feed.close()

    def _mark_read_clicked(self):
        items = self.list_item.selectedItems()
        for item in items:
            # not the ideal way but i can't get the indexes of all selected items
            it = filter(lambda it: it["title"] == item.text(), self.list_item_metadata)
            metaitem = list(it)[0]
            self._set_item_status(item, metaitem, True)

    def _mark_all_read_clicked(self):
        size = self.list_item.count()
        for i in range(size):
            item = self.list_item.item(i)
            metaitem = self.list_item_metadata[i]
            self._set_item_status(item, metaitem, True)

    def _refresh_clicked(self):
        # TODO: check the better way of
        # deciding how to handle refreshing
        # the current item, current channel and
        # everything
        self._show_notifications = True
        self._load_channel()
        # text = fetch_rss('https://mundopodcast.com.br/feed/')
        # parse_rss(text, 'https://mundopodcast.com.br/feed/', url)

    def _look_for_updates(self):
        urls = self.feed.channel_links
        for url in urls:
            parse_rss(self.feed, fetch_rss(url), url)

    def _add_channel(self, text):
        # TODO: this snippet will be used to set up folders
        top_level_item = QtWidgets.QTreeWidgetItem(self.tree_view_channels)
        self.tree_view_channels.addTopLevelItem(top_level_item)
        top_level_item.setText(0, text)

        # and this the elements itself
        # item = QtWidgets.QTreeWidgetItem(top_level_item)
        # item.setText(0, "subitem")

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    def _tree_item_selected(self, it, col):
        title = it.text(col)
        iterator = filter(lambda _tuple: _tuple[1] == title, self.channel_list_metadata)
        items = list(iterator)
        if len(items) != 0:
            id = items[0][0]
            # do the stuff with it...
            self._load_feed(id)

    def _set_content(self, text):
        self.text_edit_content.setText(text)
