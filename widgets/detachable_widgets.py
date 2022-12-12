from PyQt5.QtWidgets import QApplication, QTabWidget, QLabel
from PyQt5.QtCore import pyqtSlot, QEvent, QMetaObject, Qt, Q_ARG


class DetachableTabWidget(QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tabBarDoubleClicked.connect(self.detach_tab)
        # self.setMovable(True)
        self.widgets_by_id = {}
        self.texts_by_id = {}
        self.indexes_by_id = {}

    @pyqtSlot(int)
    def tabInserted(self, index: int):
        widget = self.widget(index)
        idw = id(widget)
        if idw not in self.widgets_by_id:
            # populate dicts once on widget creation
            self.widgets_by_id[idw] = widget
            self.texts_by_id[idw] = self.tabText(index)
            self.indexes_by_id[idw] = index

    @pyqtSlot(object)
    def delayed_insert(self, idw):
        target_index = 0
        for index in range(self.count()):
            # find the first widget with a higher default_index and use its index for insertion
            _idw = id(self.widget(index))
            if self.indexes_by_id[_idw] > self.indexes_by_id[idw]:
                break
            else:
                target_index += 1
        self.insertTab(target_index, self.widgets_by_id[idw], self.texts_by_id[idw])

    @pyqtSlot(QEvent, object)
    def custom_close_event(self, event, idw=None):
        widget = self.widgets_by_id[idw]
        widget.resize(100, 100)
        widget.setParent(self)

        # it looks like insertTab() doesn't work properly with a direct call
        # and the event loop has to finish closeEvent before insertTab() call
        QMetaObject.invokeMethod(self, 'delayed_insert', Qt.QueuedConnection, Q_ARG(object, idw))

    @pyqtSlot(int)
    def detach_tab(self, index):
        idw = id(self.widget(index))
        icon = self.tabIcon(index)
        text = self.tabText(index)
        if icon.isNull():
            icon = self.window().windowIcon()
        widget = self.widgets_by_id[idw]
        widget.setParent(None)
        widget.closeEvent = lambda event: self.custom_close_event(event, idw)
        widget.setWindowIcon(icon)
        widget.setWindowTitle(text)
        widget.setStyleSheet(self.window().styleSheet())
        widget.show()


if __name__ == '__main__':
    app = QApplication([])
    from PyQt5.QtWidgets import QGroupBox, QVBoxLayout

    tab1 = QLabel('Test Widget 1')
    tab2 = QLabel('Test Widget 2')
    tab3 = QLabel('Test Widget 3')
    tab4 = QGroupBox("dgdfg")
    layout = QVBoxLayout()
    layout.addWidget(QLabel("TEST"))
    layout.addWidget(QLabel("TEST"))
    layout.addWidget(QLabel("TEST"))
    layout.addWidget(QLabel("TEST"))
    layout.addWidget(QLabel("TEST"))
    layout.addWidget(QLabel("TEST"))
    tab4.setLayout(layout)

    tw = DetachableTabWidget()
    tw.setStyleSheet("""
        QLabel{
        font-size:14px;
        border: 1px solid red;
        padding: 0px;
        margin: 0px;
    }""")
    tw.addTab(tab1, 'Tab1')
    tw.addTab(tab2, 'Tab2')
    tw.addTab(tab3, 'Tab3')
    tw.addTab(tab4, 'Tab4')
    tw.setGeometry(300, 300, 300, 300)
    tw.show()

    app.exec_()
