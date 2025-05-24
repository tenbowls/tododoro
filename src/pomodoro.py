import sys, winsound 
from PySide6.QtCore import QTime, QTimer, Slot, Qt, Signal
from PySide6.QtWidgets import QApplication, QCheckBox, QWidget, QGridLayout, QTabWidget, QLCDNumber, QPushButton, QHBoxLayout, QSizePolicy, \
QStyle, QLabel, QVBoxLayout
from enum import Enum

import src.overhead as oh 

# Getting the logger object 
logger = oh.get_logger("pomodoro")
logger.debug("Logger started")

# Import the add timer function 
from src.db import add_timer_row

# Read the json config file and handle error in case file cannot be read
try:
    config = oh.read_config()
    timer_config = config['timer']
    db_config = config['postgres']

except Exception as e:
    app = QApplication([])
    error_msg = oh.ErrorBox(str(e))
    error_msg.exec()
    sys.exit(1)

# For storing the 4 different timers from the config file to be used by the program
class TimerModeClass():
    FOCUS_SHORT = timer_config["focus-short"]
    FOCUS_LONG = timer_config["focus-extended"]
    BREAK_SHORT = timer_config["break-short"]
    BREAK_LONG = timer_config["break-extended"]

    # To update the values from the main program if the settings have changed 
    def update_timers(self):
        self.FOCUS_SHORT = timer_config["focus-short"]
        self.FOCUS_LONG = timer_config["focus-extended"]
        self.BREAK_SHORT = timer_config["break-short"]
        self.BREAK_LONG = timer_config["break-extended"]

TimerMode = TimerModeClass() # Create an object so the values can be accessed 

# Colours for the stylesheet of the buttons and timer objects
class ObjectsColour(Enum):
    FOCUS = "#CFFFFF"
    BREAK = "#E6FFE6"
    START = "#52FF52"
    STOP = "#FF9652"
    STOP_DISABLED = "#FFE9DB"
    PAUSE = "#FFE90C"

def convert_to_ms(mins: int, sec=0) -> int:
    '''Convert mins, sec, and h to millisecond'''
    return mins * 60 * 1000 + sec * 1000 

def convert_from_ms(ms: int) -> tuple:
    '''Convert millisecond to hr, mins, sec'''
    mins = mins = (ms - hr * (1000 * 60 * 60)) // (1000 * 60)
    sec = (ms - mins * (1000 * 60))  // 1000
    return mins, sec 

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
        self.timer.setInterval(convert_to_ms(mins, sec)) # Convert to millisecond 
        self.display(QTime(0, mins, sec).toString("mm:ss"))

        # Creating a delay timer to update the timer, initialized but not started
        self.delay = QTimer(self)
        self.delay.timeout.connect(self.update_time)

    @Slot()
    def update_time(self):
        # This function is called from the delay timer to constantly update the time that is displayed
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
        self.timer.setInterval(remaining_time) # Change the timer interval to the remaining time as QTimer cannot be paused, only started and stopped

    def reset_timer(self, mins, sec=0):
        # Timer is reset to the original time 
        self.timer.stop()
        self.delay.stop()
        self.timer.setInterval(convert_to_ms(mins, sec))
        self.display(QTime(0, mins, sec).toString("mm:ss"))

class Pomodoro(QWidget):
    w, h = 500, 350 # Window size used by the main program 
    pomo_added = Signal() # Signal to emit when pomodoro timer entry is added to the database 

    def __init__(self):
        super().__init__()
        self.setMinimumSize(self.w-50, self.h-100)

        self.initial = True # Flag to check if the timer is started from new 

        # Values to add to db when timer successfully complete 
        self.timer_mode = "focus", TimerMode.FOCUS_LONG # Default starting state is in the focus extended mode 
        self.timer_starting_time = None 
        self.timer_ending_time = None 

        logger.debug("Creating objects for GUI")
        
        # Create two timers 
        self.timer_focus = Timer(TimerMode.FOCUS_LONG, bgcolor=ObjectsColour.FOCUS.value)
        self.timer_break = Timer(TimerMode.BREAK_LONG, bgcolor=ObjectsColour.BREAK.value)

        # Create check box for extended time and set it to be checked by default
        self.timer_type = QCheckBox("Extended time")
        self.timer_type.setChecked(True)
        self.timer_type.checkStateChanged.connect(self.timer_type_changed)

        # Create two buttons start and stop 
        self.start_pause = QPushButton("Start")
        self.start_pause.setStyleSheet(f"background-color: {ObjectsColour.START.value}")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(f"background-color: {ObjectsColour.STOP_DISABLED.value}")
        
        # self.timer_type.setStyleSheet("""background-color: #AAAAAA;""")

        # Adding the icons for the buttons 
        self.pause_icon = self.start_pause.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
        self.play_icon = self.start_pause.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.stop_icon = self.stop_button.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)
        self.start_pause.setIcon(self.play_icon)
        self.stop_button.setIcon(self.stop_icon)

        # Create tab widget 
        self.tabbar = QTabWidget()
        self.tabbar.addTab(self.timer_focus, "Focus")
        self.tabbar.addTab(self.timer_break, "Break")
        self.tabbar.setTabPosition(QTabWidget.TabPosition.West)

        # Create Horizontal Box Layout for the two buttons 
        self.buttons = QHBoxLayout()
        self.buttons.addWidget(self.start_pause)
        self.buttons.addWidget(self.stop_button)
        self.tabbar.currentChanged.connect(self.toggle_focus_task) # Connect the signal of tab bar change to toggle the focus task qlabel

        # Connecting signals from the buttons and completion of timers to slots
        self.start_pause.clicked.connect(self.start_or_pause_timer)
        self.timer_focus.timer.timeout.connect(self.timer_completed)
        self.timer_break.timer.timeout.connect(self.timer_completed)
        self.stop_button.clicked.connect(self.timer_stopped)

        # Creating the grid layout and adding items and setting spacing
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabbar)
        self.layout.addWidget(self.timer_type, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.layout.addLayout(self.buttons)

        # Create Qlabel for the focus task
        self.focus_task = QLabel("FOCUS: ")
        self.focus_task.setStyleSheet(f"background-color: {ObjectsColour.FOCUS.value}; font-family: 'Arial', 'sans-serif'; font-size: 14px; font-weight: bold;") 
        self.focus_task.setMargin(3)
        self.layout.addWidget(self.focus_task)
        sizepolicy = self.focus_task.sizePolicy()
        sizepolicy.setRetainSizeWhenHidden(True)
        self.focus_task.setSizePolicy(sizepolicy)

    @Slot()
    def timer_type_changed(self):
        # Change the timer timing when the type (extended or not extended) is changed
        if self.timer_type.checkState() == Qt.CheckState.Unchecked:
            self.timer_focus.change_time(TimerMode.FOCUS_SHORT)
            self.timer_break.change_time(TimerMode.BREAK_SHORT)

        else:
            self.timer_focus.change_time(TimerMode.FOCUS_LONG)
            self.timer_break.change_time(TimerMode.BREAK_LONG)
        
    def pause_timer(self, timer: QTimer):
        '''Pauses the timer and changes the button text and colour'''
        timer.pause_timer()
        self.start_pause.setText("Resume")
        self.start_pause.setStyleSheet(f"background-color: {ObjectsColour.START.value}")
        self.start_pause.setIcon(self.play_icon)

    def start_timer(self, timer: QTimer):
        '''Starts the timer and changes the button text and colour'''
        timer.start_timer()
        self.start_pause.setText("Pause")
        self.start_pause.setStyleSheet(f"background-color: {ObjectsColour.PAUSE.value}")
        self.start_pause.setIcon(self.pause_icon)

    @Slot()
    def start_or_pause_timer(self):
        # When start or pause button is pressed, start or pause the timer 
        if self.tabbar.currentIndex() == 0:
            # At Focus Tab
            if self.timer_focus.timer.isActive(): # Pause the timer if timer is active 
                self.pause_timer(self.timer_focus)

            else:
                self.tabbar.setTabEnabled(1, False) # Start the timer and disable tab changing 
                self.start_timer(self.timer_focus)
                

        else:
            # At Break Tab
            if self.timer_break.timer.isActive(): # Pause the timer if timer is active 
                self.pause_timer(self.timer_break)
            else:
                self.tabbar.setTabEnabled(0, False) # Start the timer and disable tab changing 
                self.start_timer(self.timer_break)

        # Checks if the timer is newly started
        if self.initial:
            logger.debug("Timer started")
            self.timer_starting_time = oh.get_datetime_now()

            # Enable the stop button once timer is started and disable the timer type check box 
            self.stop_button.setEnabled(True)
            self.timer_type.setEnabled(False)
            self.stop_button.setStyleSheet(f"background-color: {ObjectsColour.STOP.value}")

            # Get the timer type so the duration can be added to the db once timer is completed 
            if self.timer_type.checkState() == Qt.CheckState.Unchecked and self.tabbar.currentIndex() == 0:
                self.timer_mode = "focus", TimerMode.FOCUS_SHORT

            elif self.timer_type.checkState() == Qt.CheckState.Checked and self.tabbar.currentIndex() == 0:
                self.timer_mode = "focus", TimerMode.FOCUS_LONG

            elif self.timer_type.checkState() == Qt.CheckState.Unchecked and self.tabbar.currentIndex() == 1:
                self.timer_mode = "break", TimerMode.BREAK_SHORT

            elif self.timer_type.checkState() == Qt.CheckState.Checked and self.tabbar.currentIndex() == 1:
                self.timer_mode = "break", TimerMode.BREAK_LONG

    @Slot()
    def timer_stopped(self):
        # Once timer is stopped, time lapsed (in seconds) will be added to the database 
        logger.debug("Timer stopped")
        self.timer_ending_time = oh.get_datetime_now()
        if self.timer_mode[0] == "break":
            if self.timer_break.timer.isActive():
                self.add_to_db((self.timer_mode[1] * 60) - (self.timer_break.timer.remainingTime() / 1000))
            else:
                self.add_to_db((self.timer_mode[1] * 60) - (self.timer_break.timer.interval() / 1000))
        else:
            if self.timer_focus.timer.isActive():
                self.add_to_db((self.timer_mode[1] * 60) - (self.timer_focus.timer.remainingTime() / 1000))
            else:
                self.add_to_db((self.timer_mode[1] * 60) - (self.timer_focus.timer.interval() / 1000))
        self.reset()

    def reset(self):
        # Reset the timer and buttons back to the initial state once timer is completed or stopped 
        logger.debug("Resetting timer")
        self.timer_type.setEnabled(True)
        self.tabbar.setTabEnabled(0, True)
        self.tabbar.setTabEnabled(1, True)
        self.start_pause.setText("Start")
        self.start_pause.setIcon(self.play_icon)
        self.initial = True
        self.timer_starting_time = None 
        self.timer_ending_time = None
        self.stop_button.setEnabled(False) 
        self.start_pause.setStyleSheet(f"background-color: {ObjectsColour.START.value}")
        self.stop_button.setStyleSheet(f"background-color: {ObjectsColour.STOP_DISABLED.value}")

        # Checks the state of whether the extended option is checked 
        if self.timer_type.checkState() == Qt.CheckState.Unchecked:
            self.timer_focus.reset_timer(TimerMode.FOCUS_SHORT)
            self.timer_break.reset_timer(TimerMode.BREAK_SHORT)
                                    
        else:
            self.timer_focus.reset_timer(TimerMode.FOCUS_LONG)
            self.timer_break.reset_timer(TimerMode.BREAK_LONG)

    @Slot()
    def timer_completed(self):
        # Once timer has completed, trigger a beep sound and add entry to the database
        winsound.Beep(500, 800)
        logger.debug("Timer successfully completed")
        self.timer_ending_time = oh.get_datetime_now()
        
        # Add to database 
        self.add_to_db(self.timer_mode[1] * 60)
        self.reset()

        # Change the tab selected when timer has ended (from focus tab to break tab and vice versa)
        idx = 1 if self.tabbar.currentIndex() == 0 else 0
        self.tabbar.setCurrentIndex(idx)

    def add_to_db(self, duration: int):
        # Call function from db to add entry to database, displays error if encountered 
        try:
            add_timer_row(self.timer_starting_time, self.timer_ending_time, duration, str(self.timer_mode[0]))
            self.pomo_added.emit()
        except Exception as e:
            logger.error(f"Adding timer details to database failed: {e}")
            error_msg = oh.ErrorBox(str(e))
            self.reset()
            error_msg.exec()
            return 

    @Slot() 
    def update_focus_task(self, focus_task):
        # Set the focus task text when focus task is set in the to do list section 
        self.focus_task.setText(f"FOCUS: {focus_task}")

    @Slot()
    def clear_focus_task(self):
        self.focus_task.setText("FOCUS: ")

    @Slot()
    def toggle_focus_task(self, tab):
        # If in the break tab, make the focus task section invisible 
        if self.focus_task.isVisible():
            self.focus_task.setVisible(False)
        else:
            self.focus_task.setVisible(True)
        
