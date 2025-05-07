import sys
from PySide6.QtCore import QTime, QTimer, Slot, Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QCheckBox, QWidget, QGridLayout, QTabWidget, QLCDNumber, QPushButton, QHBoxLayout, QSizePolicy, \
QLineEdit 
import src.todoro as tdr 

def convert_to_ms(mins: int, sec=0, h=0) -> int:
    return mins * 60 * 1000 + sec * 1000 + h * 60 * 60 * 1000

def convert_from_ms(ms: int) -> tuple:
    hr = ms // (1000 * 60 * 60)
    mins = mins = (ms - hr * (1000 * 60 * 60)) // (1000 * 60)
    sec = (ms - hr * (1000 * 60 * 60) - mins * (1000 * 60))  // 1000
    return hr, mins, sec 

class timer(QLCDNumber):
    def __init__(self, mins, sec=0):
        super().__init__()
        self.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.setDigitCount(5)
        self.setStyleSheet("""
                           color: #000000;
                           background-color: #00F0F0;
                           """)

        self.timer = QTimer(self)
        self.timer.setInterval((mins * 60 + sec) * 1000)
        self.display(QTime(0, mins, sec).toString("mm:ss"))
        self.delay = QTimer(self)

    @Slot()
    def update_time(self):
        time_display = QTime(*convert_from_ms(self.timer.remainingTime()))
        self.display(time_display.toString("mm:ss"))

    def change_time(self, mins, sec=0):
        self.timer.setInterval(convert_to_ms(mins, sec))
        self.display(QTime(0, mins, sec).toString("mm:ss"))

    def start_timer(self):
        self.timer.start()
        self.update_time()
        self.delay.timeout.connect(self.update_time)
        self.delay.start(500)

    def pause_timer(self):
        self.delay.stop()
        remaining_time = self.timer.remainingTime()
        self.timer.stop()
        self.timer.setInterval(remaining_time)

    def reset_timer(self, mins, sec=0):
        self.timer.stop()
        self.delay.stop()
        self.timer.setInterval((mins * 60 + sec) * 1000)
        self.display(QTime(0, mins, sec).toString("mm:ss"))

        
class TODORO(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Todoro")
        
        self.timer_focus = timer(tdr.focus_time['l'])
        self.timer_break = timer(tdr.break_time['l'])

        self.timer_type = QCheckBox("Extended time")
        self.timer_type.setChecked(True)
        self.timer_type.checkStateChanged.connect(self.timer_type_changed)

        self.start_pause = QPushButton("Start/Pause")
        self.start_pause.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # self.timer_type.setStyleSheet("""background-color: #AAAAAA;""")

        self.tabbar = QTabWidget()
        self.tabbar.addTab(self.timer_focus, "Focus")
        self.tabbar.addTab(self.timer_break, "Break")

        self.buttons = QHBoxLayout()
        self.buttons.addWidget(self.start_pause)
        self.buttons.addWidget(self.stop_button)

        self.start_pause.clicked.connect(self.start_or_pause_timer)
        self.timer_focus.timer.timeout.connect(self.reset)
        self.timer_break.timer.timeout.connect(self.reset)

        self.stop_button.clicked.connect(self.reset)

        w, h = 500, 200
        self.resize(w, h)

        self.layout = QGridLayout(self)
        self.layout.addLayout(self.buttons, 3, 1)
        self.layout.setRowMinimumHeight(0, 0.05*h)
        self.layout.setRowMinimumHeight(1, 0.7*h)
        self.layout.setRowMinimumHeight(2, 0)
        self.layout.setRowMinimumHeight(3, 0.05*h)
        self.layout.setRowMinimumHeight(4, 0.245*h)
        self.layout.setColumnMinimumWidth(0, 0.1*w)
        self.layout.setColumnMinimumWidth(1, 0.8*w)
        self.layout.setColumnMinimumWidth(2, 0.1*w)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 2)
        self.layout.setColumnStretch(2, 1)
        self.layout.setRowStretch(1, 4)
        self.layout.setRowStretch(3, 1)
        self.layout.setRowStretch(4, 2)

        self.layout.addWidget(self.tabbar, 1, 1)
        self.layout.addWidget(self.timer_type, 2, 1, alignment=Qt.AlignmentFlag.AlignHCenter)

    @Slot()
    def timer_type_changed(self):
        if self.timer_type.checkState() == Qt.CheckState.Unchecked:
            self.timer_focus.change_time(tdr.focus_time['s'])
            self.timer_break.change_time(tdr.break_time['s'])

        else:
            self.timer_focus.change_time(tdr.focus_time['l'])
            self.timer_break.change_time(tdr.break_time['l'])

    @Slot()
    def start_or_pause_timer(self):
        if self.tabbar.currentIndex() == 0:
            # At Focus Tab
            if self.timer_focus.timer.isActive():
                self.timer_focus.pause_timer()
            else:
                self.timer_focus.start_timer()
                self.tabbar.setTabEnabled(1, False)

        else:
            # At Break Tab
            if self.timer_focus.timer.isActive():
                pass
            else:
                self.timer_break.start_timer()
                self.tabbar.setTabEnabled(0, False)
        
        self.timer_type.setEnabled(False)

    @Slot()
    def reset(self):
        self.timer_type.setEnabled(True)
        self.tabbar.setTabEnabled(0, True)
        self.tabbar.setTabEnabled(1, True)
        if self.timer_type.checkState() == Qt.CheckState.Unchecked:
            self.timer_focus.reset_timer(tdr.focus_time['s'])
            self.timer_break.reset_timer(tdr.break_time['s'])

        else:
            self.timer_focus.reset_timer(tdr.focus_time['l'])
            self.timer_break.reset_timer(tdr.break_time['l'])


class TODORO_WIN(QMainWindow):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        tdr = TODORO()
        self.layout.addLayout(tdr.layout, 0, 1)

if __name__ == "__main__":
    app = QApplication([])
    _, _, x, y = app.primaryScreen().geometry().getRect()
    item = TODORO()
    item.show()
    sys.exit(app.exec())