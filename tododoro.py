from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QGridLayout, QLineEdit, QMessageBox, QDialog, QDialogButtonBox, QVBoxLayout, QTabWidget, QWidget
from PySide6.QtGui import QAction 
import src.overhead as oh 
import sys 

app = QApplication([]) # Start the QApplication here so the error message can be shown 

# Getting the logger 
try:
    logger = oh.get_logger("Tododoro", "w")
    logger.debug("Logger started")
except Exception as e:
    error_msg = oh.ErrorBox(f"Failed to create logger: {str(e)}")
    error_msg.exec()
    sys.exit(1)

# Importing the pomodoro module for the pomodoro timer 
try:
    import src.pomodoro as pmdr
except Exception as e:
    error_msg = oh.ErrorBox(f"Failed to import pomodoro.py: {str(e)}")
    error_msg.exec()
    sys.exit(1)

# Importing the db module for database functions 
try:
    import src.db as db
except Exception as e:
    error_msg = oh.ErrorBox(f"Failed to import db.py: {str(e)}")
    error_msg.exec()
    sys.exit(1)

# Importing the main todolist module 
try:
    import src.todolist_main as todolist
except Exception as e:
    error_msg = oh.ErrorBox(f"Failed to import todolist_main.py: {str(e)}")
    error_msg.exec()
    sys.exit(1)

# Importing the main todolist module 
try:
    import src.analyse as analyse
except Exception as e:
    error_msg = oh.ErrorBox(f"Failed to import analyse.py: {str(e)}")
    error_msg.exec()
    sys.exit(1)

# Settings dialog for the settings page in the program 
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        # Creating two buttons for the settings dialog 
        buttons = QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel 
        self.buttonBox = QDialogButtonBox(buttons)

        # Connecting the accepted and rejected signal 
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Creating two labels for the settings dialog 
        txt_timer_settings = QLabel("Timer Settings")
        txt_timer_settings.setStyleSheet("font-weight: bold")
        txt_db_settings = QLabel("Database Settings")
        txt_db_settings.setStyleSheet("font-weight: bold")

        # Using a vertical layout 
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Layout for Timer Settings 
        layout_timer_config = QGridLayout()
        layout_timer_config.addWidget(txt_timer_settings, 0, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        # Creating a qlineedit widget for each timer configuration stored in the dictionary for access to it 
        self.timer_qlineedit_dict = {}
        for i, (k, v) in enumerate(pmdr.timer_config.items(), 1): 
            self.timer_qlineedit_dict[k] = (QLineEdit(str(v)), i)

        # For each qlineedit widget, create a qlabel and add the qlabel and qlineedit to the layout 
        for k, v in self.timer_qlineedit_dict.items(): 
            layout_timer_config.addWidget(QLabel(k), v[1], 0, Qt.AlignmentFlag.AlignRight)
            layout_timer_config.addWidget(v[0], v[1], 1)

        self.layout.addLayout(layout_timer_config)
        self.layout.addWidget(QLabel("")) #Adds an empty row after the timer config

        # Layout for Database Settings 
        layout_db_config = QGridLayout()
        layout_db_config.addWidget(txt_db_settings, 0, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        # Creating a qlineedit widget for each database configuration stored in the dictionary for access to it 
        self.db_qlineedit_dict = {}
        for i, (k, v) in enumerate(pmdr.db_config.items(), 1):
            self.db_qlineedit_dict[k] = (QLineEdit(v), i)

            # Setting the password qlineedit to hide the text 
            if k.lower() == "pw" or k.lower() == "password":
                self.db_qlineedit_dict[k][0].setEchoMode(QLineEdit.EchoMode.Password) 

        # Creating the qlabel and qlineedit widget and adding it to the layout 
        for k, v in self.db_qlineedit_dict.items():
            layout_db_config.addWidget(QLabel(k), v[1], 0, Qt.AlignmentFlag.AlignRight)
            layout_db_config.addWidget(v[0], v[1], 1)

        self.layout.addLayout(layout_db_config)
        self.layout.addWidget(QLabel("")) #Adds an empty row after the db config

        # Adding the buttons for the layout
        layout_button = QGridLayout()
        layout_button.addWidget(self.buttonBox, 0, 0, Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(layout_button)

        self.resize(self.minimumSize())

    def accept(self):
        # Checking timer inputs to make sure they are int
        for k, v in self.timer_qlineedit_dict.items():
            if not v[0].displayText().isdigit():
                error_msg = pmdr.oh.ErrorBox(f"Timer value {v[0].displayText()} in {k} is not an integer")
                error_msg.exec()
                return
            if int(v[0].displayText()) < 1 or int(v[0].displayText()) > 59:
                error_msg = pmdr.oh.ErrorBox(f"Timer value {v[0].displayText()} in {k} is not between 1 and 59")
                error_msg.exec()
                return 

        # Prompt the user to restart the program if database settings have been modified in order to use the latest settings 
        for k, v in self.db_qlineedit_dict.items():
            if pmdr.db_config[k] != v[0].displayText():
                restart_msg = QMessageBox(text="Database settings have be modified. Please restart to use the latest settings!", icon=QMessageBox.Icon.Information)
                restart_msg.exec()
                break

        # If input ok, update JSON file
        for k, v in self.timer_qlineedit_dict.items():
            pmdr.timer_config[k] = int(v[0].displayText())
        for k, v in self.db_qlineedit_dict.items():
            pmdr.db_config[k] = v[0].displayText().strip()
        pmdr.config["timer"] = pmdr.timer_config
        pmdr.config["postgres"] = pmdr.db_config

        try:
            oh.update_config(pmdr.config)
        except Exception as e:
            logger.error(f"Updating config.json from the GUI failed: {e}")
            error_msg = pmdr.oh.ErrorBox(str(e))
            error_msg.exec()

        # End the dialog if ok
        QDialog.accept(self)

class MainTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.pomo = pmdr.Pomodoro() 
        self.tdl = todolist.TodolistwFocus()
        self.analyse = analyse.AnalyseTab()
        self.addTab(self.pomo, "Pomodoro")
        self.addTab(self.tdl, "To do list")
        self.addTab(self.analyse, "Analyse")

        # Connecting the signals from the todolist focus section to the pomodoro focus qlabel 
        self.tdl.todolist.update_focus_task_section.connect(self.pomo.update_focus_task)
        self.tdl.focus_section.clear_task.released.connect(self.pomo.clear_focus_task)

        # Add signal to update pomodoro history table when new timer row is added 
        self.pomo.pomo_added.connect(self.analyse.completed_widget.completed_pomo.completed_pomo.update_items)

        # Add signal to update completed task table when tasks have been marked as completed
        self.tdl.todolist.update_completed_task.connect(self.analyse.completed_widget.completed_tasks.completed_tasks.update_items)

class Tododoro_Win(QMainWindow):
    def __init__(self):
        super().__init__()

        self.maintab = MainTabWidget()
        self.setCentralWidget(self.maintab)
        self.maintab.currentChanged.connect(self.change_window)

        self.setWindowTitle("Tododoro")

        # When program is first opened, resize the window to the ideal size for the pomodoro timer
        self.resize(self.maintab.pomo.w, self.maintab.pomo.h) 
        
        # self.setWindowIcon(QIcon("timer2.ico"))
        # self.setStyleSheet("background-color: #EEEEEE")

        # Creating the menu bar 
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        # Adding the settings dialog to the menu bar 
        settings = QAction("Settings", self)
        settings.setStatusTip("The settings button")
        settings.triggered.connect(self.settings_clicked)
        file_menu.addAction(settings) 

        # self.setStatusBar(QStatusBar(self))

    def change_window(self, idx):
        self.resize(self.maintab.widget(idx).w, self.maintab.widget(idx).h)

    @Slot()
    def settings_clicked(self):
        logger.debug("Settings opened by user")
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec():
            logger.debug("Settings updated by user")
            pmdr.TimerMode.update_timers() # Update the Class that stores the timer if the settings have changed 
            # If none of the timers are active, update the display to the new timer settings 
            if not (self.maintab.pomo.timer_focus.timer.isActive() or self.maintab.pomo.timer_break.timer.isActive()):
                self.maintab.pomo.reset()
                    
        else:
            logger.debug("Settings change cancelled by user")

if __name__ == "__main__":
    # _, _, x, y = app.primaryScreen().geometry().getRect()
    item = Tododoro_Win()
    item.show()

    app.exec()
    db.end_connection()
    sys.exit(0)