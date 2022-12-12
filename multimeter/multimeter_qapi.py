from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt, QTimer, QMetaObject
import logging
import traceback
from time import time
from random import random
from multimeter.visa_interface import VISAInterface


class MultimeterQObject(QObject):
    """
        Qt wrapper for Multimeter
    """
    SIG_UPDATE_PLOTS = pyqtSignal(float, float)
    SIG_RAW_CMD_REPLY = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("Multimeter")
        try:
            self.interface = VISAInterface(
                address='USB0::0x0957::0x0607::MY47001094::0::INSTR',
                logger_name="Keysight 34410A"
            )
        except ConnectionError:
            self.interface = None
            self.logger.error(
                "Something wrong with the connection. "
                "Please, check if the device is on, "
                "is set to remote control and the address is correct"
            )
        self.polling_timer = QTimer(self)
        self.polling_timer.setTimerType(Qt.PreciseTimer)
        self.polling_timer.timeout.connect(self.get_value)
        self.polling_period_ms = 1000

    @pyqtSlot(bool, int)
    def enable_polling(self, enable=False, period=1000):
        self.polling_period_ms = period
        if enable:
            self.start_polling_timer()
        else:
            self.stop_polling_timer()

    @pyqtSlot()
    def start_polling_timer(self):
        if self.polling_timer.isActive():
            self.polling_timer.stop()
        self.polling_timer.start(self.polling_period_ms)

    @pyqtSlot()
    def stop_polling_timer(self):
        if self.polling_timer.isActive():
            self.polling_timer.stop()

    @pyqtSlot()
    def get_value(self):
        """Read real values from the device."""
        if self.interface is not None:
            ts = time()
            value = float(self.interface.talk("READ?"))
            self.SIG_UPDATE_PLOTS.emit(ts, value)
        # ts = time()
        # value = random()
        # self.SIG_UPDATE_PLOTS.emit(ts, value)
        

    @pyqtSlot(str)
    def send_raw_cmd(self, cmd_str):
        if self.interface is not None:
            self.logger.info(f"USER CMD: {cmd_str}")
            try:
                if cmd_str.endswith("?"):
                    reply = self.interface.talk(cmd_str)
                    self.logger.info(f"DEVICE REPLY: {reply}")
                    self.SIG_RAW_CMD_REPLY.emit(str(reply))
                else:
                    self.interface.write(cmd_str)

            except Exception as e:
                error_msg = traceback.print_exc()
                self.logger.error(error_msg)
        else:
            # Normally this code should never be executed, it is here just for debug purposes
            self.logger.warning(f"Command {cmd_str} was ignored. Please, connect to the device first!")
    
    @pyqtSlot()
    def stop(self):
        QMetaObject.invokeMethod(self, 'stop_polling_timer', Qt.QueuedConnection)
        if self.interface is not None:
            self.interface.close()
