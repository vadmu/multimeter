from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QCheckBox, QFileDialog, QLineEdit
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt


class OutputWidget(QWidget):
    SIG_ENABLE_WRITING = pyqtSignal(bool)
    SIG_SET_FILENAME = pyqtSignal(str)

    def __init__(self, default_filename = 'output.csv'):
        super().__init__()
        self.filename = default_filename
        self.file_lineedit = QLineEdit()
        self.file_lineedit.setText(self.filename)
        # self.file_lineedit.setReadOnly(True)
        self.file_select_button = QPushButton("Select File")
        self.switch = QCheckBox()
        self.switch.setCheckState(Qt.Checked)
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.switch)
        self.layout.addWidget(QLabel("Save to:"))
        self.layout.addWidget(self.file_lineedit)
        self.layout.addWidget(self.file_select_button)

        self.writing_enabled = True
        self.file_select_button.clicked.connect(self.select_file)
        self.switch.stateChanged.connect(self.on_value_changed)
        self.file_lineedit.textChanged.connect(self.on_text_changed)
        self.SIG_SET_FILENAME.emit(self.filename)

    @pyqtSlot()
    def select_file(self):
        filename = str(
            QFileDialog.getSaveFileName(
                self,
                caption='Select File',
                filter="Data files (*.csv *.xlsx *.dat *.txt)"
            )[0]
        )
        if filename:
            self.filename = filename
            self.file_lineedit.setText(self.filename)
            self.SIG_SET_FILENAME.emit(self.filename)

    @pyqtSlot()
    def on_value_changed(self):
        self.SIG_ENABLE_WRITING.emit(self.switch.isChecked())
    
    @pyqtSlot(str)
    def on_text_changed(self, filename):
        self.filename = str(filename)
        self.SIG_SET_FILENAME.emit(self.filename)
