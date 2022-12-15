from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, \
    QPushButton, QHBoxLayout, QVBoxLayout, QSpinBox
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QMetaObject, Q_ARG, QEvent

from widgets.pg_widgets import GraphWidget
from widgets.detachable_widgets import DetachableTabWidget
from widgets.debug_widgets import CommunicationWidget, LoggerWidget
from widgets.output_widget import OutputWidget

import sys
import logging
from pathlib import Path

from multimeter.multimeter_qapi import MultimeterQObject


BASE_DIR = Path(__file__).absolute().parent
LOG_PATH = BASE_DIR/"logs"
STYLESHEET_PATH = BASE_DIR/"settings"/"style.css"


def convert(value):
    return value * 2


class MainWindow(QMainWindow):
    """
    The main window
    """

    def __init__(self):
        super().__init__()

        # tab widgets
        self.tab_widget = DetachableTabWidget()
        self.trend_widget = GraphWidget()
        self.trend_widget.plot.add_curve("Reading", "#ff7")
        self.trend_widget.plot.add_curve("Converted", "#cfc")
        self.com_widget = CommunicationWidget()
        self.logger_widget = LoggerWidget()
        self.tab_widget.addTab(self.trend_widget, "Trend")
        self.tab_widget.addTab(self.com_widget, "Communication")
        self.tab_widget.addTab(self.logger_widget, "Logs")

        # output widget
        self.output_widget = OutputWidget(default_filename=str(LOG_PATH/"output.xlsx"))

        # polling layout
        self.start_stop_btn = QPushButton(u"\U0001F7E2 Start")
        self.polling_label = QLabel("Polling period:")
        self.polling_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.polling_timer_box = QSpinBox()
        self.polling_timer_box.setSuffix(" ms")
        self.polling_timer_box.setMinimum(100)
        self.polling_timer_box.setMaximum(60000)
        self.polling_timer_box.setValue(1000)
        self.reading_text_label = QLabel("Last reading:")
        self.reading_text_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.reading_value_label = QLabel("---")
        self.polling_layout = QHBoxLayout()
        self.polling_layout.addWidget(self.polling_label)
        self.polling_layout.addWidget(self.polling_timer_box)
        self.polling_layout.addWidget(self.reading_text_label)
        self.polling_layout.addWidget(self.reading_value_label)
        self.polling_layout.addWidget(self.start_stop_btn)

        # central layout
        self.central_layout = QVBoxLayout()
        self.central_layout.addWidget(self.output_widget)
        self.central_layout.addLayout(self.polling_layout)
        self.central_layout.addWidget(self.tab_widget)
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        # style
        self.setStyleSheet(self.read_style_sheet(STYLESHEET_PATH))

        # device thread
        self.api_thread = QThread()
        self.api_worker = MultimeterQObject()
        self.api_worker.moveToThread(self.api_thread)
   
        # connections
        self.api_worker.SIG_UPDATE_PLOTS.connect(self.on_update_plots_sig)
        self.api_worker.SIG_RAW_CMD_REPLY.connect(self.com_widget.on_reply_received)
        self.com_widget.SIG_RAW_CMD_SEND.connect(self.api_worker.send_raw_cmd)
        self.start_stop_btn.clicked.connect(self.on_start_stop_pressed)
        self.polling_timer_box.valueChanged.connect(self.on_polling_changed)
        self.output_widget.SIG_SET_FILENAME.connect(self.api_worker.set_filename)
        self.output_widget.SIG_ENABLE_WRITING.connect(self.api_worker.enable_writing)
        self.api_thread.started.connect(self.output_widget.post_init)

        # start the thread
        QMetaObject.invokeMethod(self.api_thread, 'start', Qt.QueuedConnection)

        # status
        self.is_polling = False

    @pyqtSlot()
    def on_start_stop_pressed(self):
        self.is_polling = not self.is_polling
        if self.is_polling:
            self.start_stop_btn.setText(u"\U0001F7E5 Stop")
        else:
            self.start_stop_btn.setText(u"\U0001F7E2 Start")
        self.on_polling_changed()

    @pyqtSlot()
    def on_polling_changed(self):
        QMetaObject.invokeMethod(
            self.api_worker, 
            'enable_polling', 
            Qt.QueuedConnection,
            Q_ARG(bool, self.is_polling),
            Q_ARG(int,  self.polling_timer_box.value())
        )

    @pyqtSlot(float, float)
    def on_update_plots_sig(self, timestamp, value):
        self.trend_widget.plot.update_ups(timestamp)
        self.trend_widget.plot.add_curve_data({"Reading": [timestamp, value]})
        self.trend_widget.plot.add_curve_data({"Converted": [timestamp, convert(value)]})
        self.reading_value_label.setText(f"{value:.6g}")

    @staticmethod
    def read_style_sheet(filename):
        css = ""
        with open(str(filename), "r") as file:
            css = str(file.read())
        return css

    @pyqtSlot(QEvent)
    def closeEvent(self, event):
        # stop device thread    
        self.api_worker.stop()
        self.api_worker.disconnect()

        # close detached tabs in tabwidgets
        for w in self.tab_widget.widgets_by_id.values():
            w.deleteLater()


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)6s - %(levelname)5s - %(message)s',
        level=logging.DEBUG
        #level=logging.INFO
    )

    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.setWindowTitle("Mutilmeter control")
    mw.setGeometry(50, 50, 800, 600)
    mw.show()
    sys.exit(app.exec_())