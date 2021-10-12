from PyQt5.QtWidgets import QMenu, QSystemTrayIcon, QAction
from PyQt5.QtGui import QIcon

class SystemTray():
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.icon = QIcon("plus.png")
		self._tray = QSystemTrayIcon()
		self._tray.setIcon(self.icon)
		self._tray.setToolTip('Syndicate')
		self._tray.activated.connect(self._fire_open)

		menu = QMenu()
		self.open_action = menu.addAction('open')
		self.exit_action = menu.addAction('exit')
		self._tray.setContextMenu(menu)
	
	def _fire_open(self, e):
		"""On system tray icon double click"""
		if QSystemTrayIcon.DoubleClick == e:
			self.open_action.activate(QAction.Trigger)
	
	def show_message(self, title, message):
		was_visible = self._tray.isVisible
		self._tray.show()
		self._tray.showMessage(title, message, self.icon)
		if (was_visible):
			self._tray.hide()

	def show(self):
		self._tray.show()

	def hide(self):
		self._tray.hide()
