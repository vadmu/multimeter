from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QLineEdit, QPlainTextEdit, \
    QPushButton, QVBoxLayout, QComboBox, QSpacerItem, QSizePolicy
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject
import logging
from io import StringIO


def make_html_compatible(text_str):
    """
    replacing > and < symbols with unicode arrows
    """
    return text_str.strip().replace(">", "\u2B9E").replace("<", "\u2B9C")


class CommunicationWidget(QWidget):
    SIG_RAW_CMD_SEND = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_text_input = QLineEdit()
        self.user_text_input.setPlaceholderText("Command to send. Examples: *IDN?, *CLS, READ? CONF:VOLT, CONF:RES")
        self.user_text_input.returnPressed.connect(self.send_cmd)
        self.btn_send = QPushButton("Send")
        self.btn_send.setObjectName("Operation")
        self.btn_send.clicked.connect(self.send_cmd)
        self.message_layout = QHBoxLayout()
        self.message_layout.addWidget(self.user_text_input)
        self.message_layout.addWidget(self.btn_send)

        self.response_view = QPlainTextEdit()
        self.response_view.setReadOnly(True)
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.response_view)
        self.main_layout.addLayout(self.message_layout)
        self.setLayout(self.main_layout)
        self.return_press_enabled = True

    @pyqtSlot()
    def send_cmd(self):
        if self.return_press_enabled:
            msg = self.user_text_input.text()
            # html = "<font color=\"CornflowerBlue\">" + make_html_compatible(msg) + "</font>"
            html = "<font color=\"LightSkyBlue\">" + \
                   make_html_compatible(">>> " + msg) + \
                   "</font>"
            self.response_view.appendHtml(html)
            self.SIG_RAW_CMD_SEND.emit(msg.strip())

    @pyqtSlot(str)
    def on_reply_received(self, msg):
        html = "<font color=\"Orange\">" + make_html_compatible("<<< " + msg) + "</font>"
        self.response_view.appendHtml(html)


class SimpleLogObject(QObject):
    SIG_MSG = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LogBuffer(StringIO):
    def __init__(self, *args, **kwargs):
        StringIO.__init__(self, *args, **kwargs)
        self.qlog = SimpleLogObject()

    def write(self, message):
        if message:
            self.qlog.SIG_MSG.emit(message)
        StringIO.write(self, message)


class LoggerWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_buffer = LogBuffer()
        self.log_formatter = logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)-20s [%(process)-5d:%(thread)-5d] %(message)s")
        self.log_handler = logging.StreamHandler(self.log_buffer)
        self.log_handler.setFormatter(self.log_formatter)
        self.log_buffer.qlog.SIG_MSG.connect(self.on_logger_message)
        self.logger = logging.getLogger()
        self.logger.addHandler(self.log_handler)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("Operation")
        self.clear_button.clicked.connect(self.log_view.clear)
        self.lvl_selector = QComboBox()
        self.lvl_selector.currentTextChanged.connect(self.set_logger_level)
        self.lvl_selector.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(QLabel("Logger level:"))
        self.buttons_layout.addWidget(self.lvl_selector)
        self.buttons_layout.addSpacerItem(QSpacerItem(50, 25, QSizePolicy.MinimumExpanding, QSizePolicy.Maximum))
        self.buttons_layout.addWidget(self.clear_button)
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.log_view)
        self.main_layout.addLayout(self.buttons_layout)
        self.setLayout(self.main_layout)

    @pyqtSlot(str)
    def set_logger_level(self, lvl="DEBUG"):
        self.logger.setLevel(lvl)

    @pyqtSlot(str)
    def on_logger_message(self, msg):
        msg = make_html_compatible(msg)
        level = msg.split(" ")[2]
        if level == "ERROR":
            msg = "<font color=\"DeepPink\">" + msg + "</font>"
            self.log_view.appendHtml(msg)
        elif level == "WARNING":
            msg = "<font color=\"Yellow\">" + msg + "</font>"
            self.log_view.appendHtml(msg)
        elif level == "DEBUG":
            msg = "<font color=\"Lime\">" + msg + "</font>"
            self.log_view.appendHtml(msg)
        elif level == "INFO":
            msg = "<font color=\"Aqua\">" + msg + "</font>"
            self.log_view.appendHtml(msg)
        else:
            msg = "<font color=\"White\">" + msg + "</font>"
            self.log_view.appendHtml(msg)

