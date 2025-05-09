import sys, winsound 
from PySide6.QtCore import QTime, QTimer, Slot, Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QCheckBox, QWidget, QGridLayout, QTabWidget, QLCDNumber, QPushButton, QHBoxLayout, QSizePolicy, \
QLineEdit, QMessageBox 
from PySide6.QtGui import QIcon
import src.overhead as oh 
from enum import Enum

# For displaying error messages with the critical icon
class MsgBox(QMessageBox):
    def __init__(self, msg):
        super().__init__()
        self.setText(msg)
        self.setIcon(QMessageBox.Icon.Critical)

# Handle error in case json config file cannot be read
try:
    timer_config = oh.read_config()['timer']
except Exception as e:
    app = QApplication([])
    error_msg = MsgBox(str(e))
    error_msg.exec()
    sys.exit(1)

logger = oh.get_logger("Tododoro GUI", "w")
logger.debug("Logger started")

# For storing the 4 different timers from the config file to be used by the program
class TimerMode(Enum):
    FOCUS_SHORT = timer_config["focus-short"]
    FOCUS_LONG = timer_config["focus-extended"]
    BREAK_SHORT = timer_config["break-short"]
    BREAK_LONG = timer_config["break-extended"]

# Colours for the stylesheet of the buttons and timer objects
class ObjectsColour(Enum):
    FOCUS = "#CFFFFF"
    BREAK = "#E6FFE6"
    START = "#52FF52"
    STOP = "#FF9652"
    STOP_DISABLED = "#FFE9DB"
    PAUSE = "#FFE90C"

# Timer object 
class Timer(QLCDNumber):
    def __init__(self, mins, sec=0, bgcolor="#FFFFFF"):
        super().__init__()
        # LCD Number Text Object
        self.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.setDigitCount(5)
        self.setStyleSheet(f"""
                           color: #000000;
                           background-color: {bgcolor};
                           border: None
                           """)

        # Timer Object, initialized but not started
        self.timer = QTimer(self)
        self.timer.setInterval((mins * 60 + sec) * 1000)
        self.display(QTime(0, mins, sec).toString("mm:ss"))

        # Delay timer to update the timer, initialized but not started
        self.delay = QTimer(self)
        self.delay.timeout.connect(self.update_time)

    @Slot()
    def update_time(self):
        # This function is called from the delay timer to constantly update the time
        time_display = QTime(*convert_from_ms(self.timer.remainingTime()))
        self.display(time_display.toString("mm:ss"))

    def change_time(self, mins, sec=0):
        # To change the time of the timer, called when the extended time button is toggled, should be called when timer is inactive 
        self.timer.setInterval(convert_to_ms(mins, sec))
        self.display(QTime(0, mins, sec).toString("mm:ss"))

    def start_timer(self):
        # Timer is started when the user presses the start button 
        self.timer.start()
        self.update_time()
        self.delay.start(500)

    def pause_timer(self):
        # Timer is paused when the user presses the pause button 
        self.delay.stop()
        remaining_time = self.timer.remainingTime()
        self.timer.stop()
        self.timer.setInterval(remaining_time)

    def reset_timer(self, mins, sec=0):
        # Timer is reset to the original time 
        self.timer.stop()
        self.delay.stop()
        self.timer.setInterval((mins * 60 + sec) * 1000)
        self.display(QTime(0, mins, sec).toString("mm:ss"))

def convert_to_ms(mins: int, sec=0, h=0) -> int:
    '''Convert mins, sec, and h to millisecond'''
    return mins * 60 * 1000 + sec * 1000 + h * 60 * 60 * 1000

def convert_from_ms(ms: int) -> tuple:
    '''Convert millisecond to hr, mins, sec'''
    hr = ms // (1000 * 60 * 60)
    mins = mins = (ms - hr * (1000 * 60 * 60)) // (1000 * 60)
    sec = (ms - hr * (1000 * 60 * 60) - mins * (1000 * 60))  // 1000
    return hr, mins, sec 

class Tododoro(QWidget):
    def __init__(self):
        super().__init__()

        # Values to add to db when timer successfully complete 
        self.initial = True
        self.timer_mode = TimerMode.FOCUS_LONG
        self.timer_starting_time = None 
        self.timer_ending_time = None
        self.timer_task = None

        logger.debug("Creating objects for GUI")
        
        # Create two timers 
        self.timer_focus = Timer(TimerMode.FOCUS_LONG.value, bgcolor=ObjectsColour.FOCUS.value)
        self.timer_break = Timer(TimerMode.BREAK_LONG.value, bgcolor=ObjectsColour.BREAK.value)

        # Create check box for extended time and set it to be checked by default
        self.timer_type = QCheckBox("Extended time")
        self.timer_type.setChecked(True)
        self.timer_type.checkStateChanged.connect(self.timer_type_changed)

        # Create two buttons start and stop 
        self.start_pause = QPushButton("Start")
        self.start_pause.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.start_pause.setStyleSheet(f"background-color: {ObjectsColour.START.value}")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(f"background-color: {ObjectsColour.STOP_DISABLED.value}")
        # self.timer_type.setStyleSheet("""background-color: #AAAAAA;""")

        # Create tab widget 
        self.tabbar = QTabWidget()
        self.tabbar.addTab(self.timer_focus, "Focus")
        self.tabbar.addTab(self.timer_break, "Break")
        self.tabbar.setTabPosition(QTabWidget.TabPosition.West)
        # self.tabbar.setStyleSheet(f"""
        #                           QTabBar {{
        #                               background-color: {black}
        #                           }}""")

        # Create Horizontal Box Layout for the two buttons 
        self.buttons = QHBoxLayout()
        self.buttons.addWidget(self.start_pause)
        self.buttons.addWidget(self.stop_button)

        # Connecting signals from the buttons and completion of timers to slots
        self.start_pause.clicked.connect(self.start_or_pause_timer)
        self.timer_focus.timer.timeout.connect(self.timer_completed)
        self.timer_break.timer.timeout.connect(self.timer_completed)
        self.stop_button.clicked.connect(self.timer_stopped)

        w, h = 500, 200
        self.resize(w, h)

        # Creating the grid layout and adding items and setting spacing
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
        self.layout.setRowStretch(0, 3)
        self.layout.setRowStretch(1, 4)
        self.layout.setRowStretch(3, 1)
        self.layout.setRowStretch(4, 4)
        self.layout.addWidget(self.tabbar, 1, 1)
        self.layout.addWidget(self.timer_type, 2, 1, alignment=Qt.AlignmentFlag.AlignHCenter)

    @Slot()
    def timer_type_changed(self):
        # Change the timer timing when the type is changed
        if self.timer_type.checkState() == Qt.CheckState.Unchecked:
            self.timer_focus.change_time(TimerMode.FOCUS_SHORT.value)
            self.timer_break.change_time(TimerMode.BREAK_SHORT.value)

        else:
            self.timer_focus.change_time(TimerMode.FOCUS_LONG.value)
            self.timer_break.change_time(TimerMode.BREAK_LONG.value)
        
    def pause_timer(self, timer: QTimer):
        timer.pause_timer()
        self.start_pause.setText("Resume")
        self.start_pause.setStyleSheet(f"background-color: {ObjectsColour.START.value}")

    def start_timer(self, timer: QTimer):
        timer.start_timer()
        self.start_pause.setText("Pause")
        self.start_pause.setStyleSheet(f"background-color: {ObjectsColour.PAUSE.value}")

    @Slot()
    def start_or_pause_timer(self):
        # When start or pause button is pressed, start or pause the timer 
        if self.tabbar.currentIndex() == 0:
            # At Focus Tab
            if self.timer_focus.timer.isActive():
                self.pause_timer(self.timer_focus)

            else:
                self.tabbar.setTabEnabled(1, False)
                self.start_timer(self.timer_focus)
                

        else:
            # At Break Tab
            if self.timer_break.timer.isActive():
                self.pause_timer(self.timer_break)
            else:
                self.tabbar.setTabEnabled(0, False)
                self.start_timer(self.timer_break)

        if self.initial:
            logger.debug("Timer started")
            self.timer_starting_time = oh.get_datetime_now()

            # Enable the stop button once timer is started and disable the timer type check box 
            self.stop_button.setEnabled(True)
            self.timer_type.setEnabled(False)
            self.stop_button.setStyleSheet(f"background-color: {ObjectsColour.STOP.value}")

            # Get the timer type so the duration can be added to the db once timer is completed 
            if self.timer_type.checkState() == Qt.CheckState.Unchecked and self.tabbar.currentIndex() == 0:
                self.timer_mode = TimerMode.FOCUS_SHORT

            elif self.timer_type.checkState() == Qt.CheckState.Checked and self.tabbar.currentIndex() == 0:
                self.timer_mode = TimerMode.FOCUS_LONG

            elif self.timer_type.checkState() == Qt.CheckState.Unchecked and self.tabbar.currentIndex() == 1:
                self.timer_mode = TimerMode.BREAK_SHORT

            elif self.timer_type.checkState() == Qt.CheckState.Checked and self.tabbar.currentIndex() == 1:
                self.timer_mode = TimerMode.BREAK_LONG

    @Slot()
    def timer_stopped(self):
        # Once timer is stopped, time lapsed will be added to the database 
        logger.debug("Timer stopped")
        self.timer_ending_time = oh.get_datetime_now()
        if self.timer_mode.name[:5].lower() == "break":
            self.add_to_db((self.timer_mode.value * 60) - (self.timer_break.timer.remainingTime() / 1000))
        else:
            self.add_to_db((self.timer_mode.value * 60) - (self.timer_focus.timer.remainingTime() / 1000))
        self.reset()

    def reset(self):
        # Reset the timer and buttons back to the initial state once timer is completed or stopped 
        logger.debug("Resetting timer")
        self.timer_type.setEnabled(True)
        self.tabbar.setTabEnabled(0, True)
        self.tabbar.setTabEnabled(1, True)
        self.start_pause.setText("Start")
        self.initial = True
        self.timer_starting_time = None 
        self.timer_ending_time = None
        self.stop_button.setEnabled(False) 
        self.start_pause.setStyleSheet(f"background-color: {ObjectsColour.START.value}")
        self.stop_button.setStyleSheet(f"background-color: {ObjectsColour.STOP_DISABLED.value}")

        if self.timer_type.checkState() == Qt.CheckState.Unchecked:
            self.timer_focus.reset_timer(TimerMode.FOCUS_SHORT.value)
            self.timer_break.reset_timer(TimerMode.BREAK_SHORT.value)
                                    
        else:
            self.timer_focus.reset_timer(TimerMode.FOCUS_LONG.value)
            self.timer_break.reset_timer(TimerMode.BREAK_LONG.value)

    @Slot()
    def timer_completed(self):
        # Once timer has completed, trigger a beep sound and add entry to the database
        winsound.Beep(500, 800)
        logger.debug("Timer successfully completed")
        self.timer_ending_time = oh.get_datetime_now()
        
        # Add to database 
        self.add_to_db(self.timer_mode.value * 60)
        self.reset()

    def add_to_db(self, duration: int):
        # Call function from db to add entry to database, displays error if encountered 
        try:
            db.add_timer_row(self.timer_starting_time, self.timer_ending_time, duration, str(self.timer_mode.name)[:5].lower(), self.timer_task)
        except Exception as e:
            logger.error(f"Adding timer details to database failed: {e}")
            error_msg = MsgBox(str(e))
            self.reset()
            error_msg.exec()
            return 


class Tododoro_Win(QMainWindow):
    def __init__(self):
        super().__init__()
        tddr = Tododoro()
        self.setCentralWidget(tddr)
        # self.setWindowIcon(QIcon("timer2.ico"))
        self.setWindowTitle("Tododoro")
        # self.setStyleSheet("background-color: #EEEEEE")

if __name__ == "__main__":
    app = QApplication([])

    try:
        import src.db as db
    except Exception as e:
        error_msg = MsgBox(str(e))
        error_msg.exec()

    _, _, x, y = app.primaryScreen().geometry().getRect()
    item = Tododoro_Win()
    item.show()
    app.exec()
    db.end_connection()
    sys.exit(0)