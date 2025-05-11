from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QGridLayout, QLineEdit, QMessageBox, QDialog, QDialogButtonBox, QVBoxLayout
from PySide6.QtGui import QAction 
import src.overhead as oh 
import sys 

logger = oh.get_logger("Tododoro", "w")
logger.debug("Logger started")

import src.pomodoro as pmdr

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        buttons = QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel 
        self.buttonBox = QDialogButtonBox(buttons)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        txt_timer_settings = QLabel("Timer Settings")
        txt_timer_settings.setStyleSheet("font-weight: bold")
        txt_db_settings = QLabel("Database Settings")
        txt_db_settings.setStyleSheet("font-weight: bold")

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Layout for Timer Settings 
        layout_timer_config = QGridLayout()
        layout_timer_config.addWidget(txt_timer_settings, 0, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        self.timer_qlineedit_dict = {}
        for i, (k, v) in enumerate(pmdr.timer_config.items(), 1):
            self.timer_qlineedit_dict[k] = (QLineEdit(str(v)), i)
        for k, v in self.timer_qlineedit_dict.items():
            layout_timer_config.addWidget(QLabel(k), v[1], 0, Qt.AlignmentFlag.AlignRight)
            layout_timer_config.addWidget(v[0], v[1], 1)
        self.layout.addLayout(layout_timer_config)

        self.layout.addWidget(QLabel("")) #Adds an empty row after the timer config

        # Layout for Database Settings 
        layout_db_config = QGridLayout()
        layout_db_config.addWidget(txt_db_settings, 0, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        self.db_qlineedit_dict = {}
        for i, (k, v) in enumerate(pmdr.db_config.items(), 1):
            self.db_qlineedit_dict[k] = (QLineEdit(v), i)
        for k, v in self.db_qlineedit_dict.items():
            layout_db_config.addWidget(QLabel(k), v[1], 0, Qt.AlignmentFlag.AlignRight)
            layout_db_config.addWidget(v[0], v[1], 1)
        self.layout.addLayout(layout_db_config)

        self.layout.addWidget(QLabel("")) #Adds an empty row after the db config

        layout_button = QGridLayout()
        layout_button.addWidget(self.buttonBox, 0, 0, Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(layout_button)

        self.resize(self.minimumSize())

    def accept(self):
        check = True
        # Checking timer inputs to make sure they are int
        for k, v in self.timer_qlineedit_dict.items():
            if not v[0].displayText().isdigit():
                error_msg = pmdr.MsgBox(f"Timer value {v[0].displayText()} in {k} is not an integer")
                error_msg.exec()
                check = False
                return

        for v in self.db_qlineedit_dict.values():
            if v[0].isModified():
                restart_msg = QMessageBox(text="Database settings have be modified. Please restart to use the latest settings!", icon=QMessageBox.Icon.Information)
                restart_msg.exec()
                print("is modified")
                break

        # If input ok, update JSON file
        for k, v in self.timer_qlineedit_dict.items():
            pmdr.timer_config[k] = int(v[0].displayText())
        for k, v in self.db_qlineedit_dict.items():
            pmdr.db_config[k] = v[0].displayText() 
        pmdr.config["timer"] = pmdr.timer_config
        pmdr.config["postgres"] = pmdr.db_config

        try:
            oh.update_config(pmdr.config)
        except Exception as e:
            logger.error(f"Updating config.json from the GUI failed: {e}")
            error_msg = pmdr.MsgBox(str(e))
            error_msg.exec()

        # End the dialog if ok
        QDialog.accept(self)

class Tododoro_Win(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tddr = pmdr.Pomodoro()
        self.setCentralWidget(self.tddr)
        self.setWindowTitle("Tododoro")
        # self.setWindowIcon(QIcon("timer2.ico"))
        # self.setStyleSheet("background-color: #EEEEEE")

        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        settings = QAction("Settings", self)
        settings.setStatusTip("The settings button")
        settings.triggered.connect(self.settings_clicked)

        file_menu.addAction(settings) 

        # self.setStatusBar(QStatusBar(self))

    def settings_clicked(self):
        logger.debug("Settings opened by user")
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec():
            logger.debug("Settings updated by user")
            pmdr.TimerMode.update_timers()
            if not (self.tddr.timer_focus.timer.isActive() or self.tddr.timer_break.timer.isActive()):
                self.tddr.reset()
                    
        else:
            logger.debug("Settings change cancelled by user")

if __name__ == "__main__":
    app = QApplication([])

    try:
        import src.db as db
    except Exception as e:
        logger.error(f"Importing db.py from the GUI failed: {e}")
        error_msg = pmdr.MsgBox(str(e) + "\n\nPlease update the database settings!"
        "\n\nTimer entry will not be added to the database, "
        "more errors will be encountered when timer has completed.")
        error_msg.exec()
        # sys.exit(1)

    _, _, x, y = app.primaryScreen().geometry().getRect()
    item = Tododoro_Win()
    item.show()
    app.setStyle('Fusion')
    app.exec()
    db.end_connection()
    sys.exit(0)