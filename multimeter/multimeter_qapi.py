from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt, QTimer, QMetaObject
import logging
from datetime import datetime
from time import time
from random import random
from multimeter.visa_interface import VISAInterface, INSTRUMENT_ADDRESS
import pandas as pd
from pathlib import Path


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
                address=INSTRUMENT_ADDRESS,
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
        self.is_writing_enabled = True
        self.filename = "output.csv"

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
            if self.is_writing_enabled:
                self.write_data_to_file(ts, value)
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
                self.logger.error(e, exc_info=True)
        else:
            # Normally this code should never be executed, it is here just for debug purposes
            self.logger.warning(f"Command {cmd_str} was ignored. Please, connect to the device first!")
    
    @pyqtSlot()
    def stop(self):
        QMetaObject.invokeMethod(self, 'stop_polling_timer', Qt.QueuedConnection)
        if self.interface is not None:
            self.interface.close()

    @pyqtSlot(str)
    def set_filename(self, filename):
        self.filename = filename
        self.logger.info(f"Output filename: {filename}")

    @pyqtSlot(bool)
    def enable_writing(self, enable):
        self.is_writing_enabled = enable
        self.logger.info(f"Write to file: {enable}")

    def write_data_to_file(self, ts, value):
        try:
            dt_milliseconds = datetime.fromtimestamp(ts).isoformat(sep=' ', timespec='milliseconds')
            file_exists = Path(self.filename).is_file()
            df = pd.DataFrame(
                    columns=["Timestamp", "Datetime", "Readings [V or Ohm]"],
                    data=[[ts, dt_milliseconds, value]]
                )

            # CSV
            if self.filename.endswith(".csv"):
                df.to_csv(
                    self.filename, 
                    mode='a' if file_exists else 'w', 
                    index=False, 
                    header=not file_exists
                )

            # DAT or TXT
            elif self.filename.endswith(".dat") or self.filename.endswith(".txt"):
                df.to_csv(
                    self.filename, 
                    sep='\t',
                    mode='a' if file_exists else 'w', 
                    index=False, 
                    header=not file_exists
                )

            # XLSX
            elif self.filename.endswith(".xlsx"):
                if not file_exists:
                    with pd.ExcelWriter(self.filename, mode='w') as writer:  
                        df.to_excel(
                            writer, 
                            index=False, 
                            header=True,
                            sheet_name="Sheet1"
                        )
                else:
                    # if_sheet_exists is only valid in append mode and only starting from pandas 1.4.0
                    with pd.ExcelWriter(self.filename, mode='a', if_sheet_exists='overlay') as writer:  
                        df.to_excel(
                            writer, 
                            index=False, 
                            header=False,
                            sheet_name="Sheet1",
                            startrow=writer.sheets["Sheet1"].max_row
                        )

            else:
                self.logger.warning("Incorrect filename. Please, use CSV / XLSX / DAT / TXT files for output")
        except Exception as e:
            self.logger.error(e, exc_info=True)

