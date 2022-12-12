from PyQt5.QtWidgets import QApplication, QMenu, QAction, QActionGroup, \
    QGridLayout, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSpinBox, QListWidget, QComboBox, \
    QDoubleSpinBox
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
import pyqtgraph as pg
from time import time


class Trend1D(pg.GraphicsLayoutWidget):
    """
        1D Plot widget with time axis at the bottom
    """

    def __init__(self, title="", labels=None, show_fps=True, use_dateaxis=True):
        pg.GraphicsLayoutWidget.__init__(self)
        self.data_dict = {}
        if use_dateaxis:
            self.pw = self.addPlot(labels=labels,
                                   axisItems={'bottom': pg.DateAxisItem(
                                       orientation='bottom')},
                                   row=1, col=0, colspan=2)
        else:
            self.pw = self.addPlot(labels=labels, row=1, col=0, colspan=2)
        if title:
            self.title = pg.LabelItem(justify='left')
            self.title.setText("<span style='font-size: 8pt; font-weight:bold;" + \
                               "font-family: Consolas;" + \
                               f"color:white'> {title}")
            self.addItem(self.title, row=0, col=0)
        if show_fps:
            self.fps_label = pg.LabelItem(justify='right')
            self.fps_label.setText("0 fps")
            self.addItem(self.fps_label, row=0, col=1)
        self.n_updates = 0
        self.last_update_time = 0
        self.legend = pg.LegendItem()
        self.legend.setParentItem(self.pw)
        self.legend.anchor(itemPos=(1, 0), parentPos=(1, 0))
        self.restore_leg_pos_action = QAction("Restore legend position")
        self.restore_leg_pos_action.triggered.connect(self.restore_legend_position)
        self.pw.vb.menu.addAction(self.restore_leg_pos_action)
        self.max_points = 5000

    @pyqtSlot(dict)
    def add_curve_data(self, curve_data_dict):
        for c_name, new_data_xy in curve_data_dict.items():
            if c_name not in self.data_dict:
                continue
            if type(new_data_xy[0]) == int or type(new_data_xy[0]) == float:
                self.data_dict[c_name]["x"].append(new_data_xy[0])
                self.data_dict[c_name]["y"].append(new_data_xy[1])
            elif type(new_data_xy[0]) == list:
                self.data_dict[c_name]["x"] += new_data_xy[0]
                self.data_dict[c_name]["y"] += new_data_xy[1]
            else:
                print("Unsupported format:", type(new_data_xy[0]))
                return
            if len(self.data_dict[c_name]["x"]) != len(self.data_dict[c_name]["y"]):
                print("length of x:",
                      len(self.data_dict[c_name]["x"]),
                      "is different from length of y:",
                      len(self.data_dict[c_name]["y"]))
                return
            x_len = len(self.data_dict[c_name]["x"])
            # max_len = self.data_dict[c_name]["max_len"]
            if x_len > self.max_points:
                self.data_dict[c_name]["x"] = self.data_dict[c_name]["x"][-self.max_points:]
                self.data_dict[c_name]["y"] = self.data_dict[c_name]["y"][-self.max_points:]
            if self.data_dict[c_name]["enabled"]:
                self.data_dict[c_name]["curve"].setData(
                    self.data_dict[c_name]["x"],
                    self.data_dict[c_name]["y"])

    def update_ups(self, ts):
        self.n_updates += 1
        if ts - self.last_update_time >= 1:  # 1s
            self.fps_label.setText(f"{self.n_updates / (ts - self.last_update_time) : .2f} fps")
            self.last_update_time = ts
            self.n_updates = 0

    @pyqtSlot(str)
    def clear_curve_data(self, c_name):
        if c_name in self.data_dict:
            self.data_dict[c_name]["x"] = []
            self.data_dict[c_name]["y"] = []
            # self.data_dict[c_name]["max_len"] = MAX_POINTS
            if self.data_dict[c_name]["enabled"]:
                self.data_dict[c_name]["curve"].setData([], [])

    @pyqtSlot()
    def clear_all_curves(self):
        for c_name in self.data_dict:
            self.clear_curve_data(c_name)

    @pyqtSlot(str, bool)
    def enable_curve(self, c_name, enable=True):
        if c_name in self.data_dict:
            if enable:
                self.data_dict[c_name]["enabled"] = True
                self.data_dict[c_name]["curve"].setData(
                    self.data_dict[c_name]["x"],
                    self.data_dict[c_name]["y"])
                self.data_dict[c_name]["curve"].setPen(self.data_dict[c_name]["color"])
                self.legend.setLabelTextColor(self.data_dict[c_name]["color"])
                self.legend.addItem(self.data_dict[c_name]["curve"], c_name)
            else:
                self.data_dict[c_name]["enabled"] = False
                self.data_dict[c_name]["curve"].setData([], [])
                self.legend.removeItem(c_name)

    def disable_curve(self, c_name):
        self.enable_curve(c_name, False)

    def add_curve(self, c_name, color, enabled=True):
        if c_name not in self.data_dict:
            self.data_dict[c_name] = {
                "x": [],
                "y": [],
                "enabled": enabled,
                "color": color,
                "curve": self.pw.plot([], pen=color)
            }
            if enabled:
                self.legend.setLabelTextColor(color)
                self.legend.addItem(self.data_dict[c_name]["curve"], c_name)

    def remove_curve(self, c_name):
        if c_name in self.data_dict:
            self.clear_curve_data(c_name)
            self.legend.removeItem(c_name)
            del self.data_dict[c_name]

    @pyqtSlot()
    def restore_legend_position(self):
        self.legend.anchor(itemPos=(1, 0), parentPos=(1, 0))


class GraphWidget(QWidget):
    def __init__(self, title="", labels=None):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.bottom_layout = QHBoxLayout()
        self.plot = Trend1D(title=title, labels=labels)
        self.clear_button = QPushButton("Clear curves")
        self.clear_button.setObjectName("Operation")
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.clear_button)
        self.layout.addWidget(self.plot)
        self.layout.addLayout(self.bottom_layout)
        self.setMinimumSize(400, 300)
        self.clear_button.clicked.connect(self.plot.clear_all_curves)

    @pyqtSlot(str, str, bool)
    def add_or_remove_curve(self, c_name, color, enabled):
        if c_name not in self.plot.data_dict:
            self.plot.add_curve(c_name, color, enabled)
        else:
            self.plot.data_dict[c_name]["color"] = color
            self.plot.enable_curve(c_name, enabled)


if __name__ == "__main__":
    app = QApplication([])
    import random
    # window = GraphWidget(title='Trend', curves={"Current(mA)": "#ff7", "Voltage(V)": "#f0f"})
    window = GraphWidget(title='Trend')
    window.plot.add_curve("Current(mA)", "#ff7")
    window.plot.add_curve("Voltage(V)", "#f0f", False)
    window.plot.add_curve_data({
        "Current(mA)":
            [
                list(range(5000)),
                [random.random() + 1 for i in range(5000)],
            ],
        "Voltage(V)":
            [
                list(range(500, 5500)),
                [random.random() for i in range(500, 5500)],
            ],
    })
    window.plot.add_curve_data({
        "Current(mA)":
            [
                list(range(7000, 8000)),
                [random.random() - 1 for i in range(7000, 8000)],
            ],
        "Voltage(V)":
            [
                list(range(7000, 9000)),
                [random.random() + 2 for i in range(7000, 9000)],
            ],
    })
    window.plot.enable_curve("Voltage(V)")
    window.plot.disable_curve("Voltage(V)")
    window.plot.enable_curve("Voltage(V)")

    window.setWindowTitle("Trend")
    window.setGeometry(100, 100, 800, 600)
    window.show()
    window.raise_()
    app.exec_()
