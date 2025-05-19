from PySide6.QtWidgets import QTabWidget, QLabel, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QStyle
from PySide6.QtCore import Qt, Slot, Signal 
from PySide6.QtGui import QFont
from src.db import Analyse
import sys 

# Class for the header row with bold text 
class HeaderRow(QWidget):
    def __init__(self, stretch: list, spacing, *args):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setLayout = self.layout
        for idx, item in enumerate(args): # Constructor takes in tuple 
            font = QFont()
            font.setBold(True)
            font.setPointSize(11)
            label = QLabel(item)
            label.setFont(font)
            self.layout.addWidget(label, stretch[idx])
        self.layout.addSpacing(30) # Adds a spacing at the last column due to the discard button 
        self.layout.setContentsMargins(2,2,2,2)
        self.layout.insertSpacing(1, spacing) # Insert spacing after the first column (the id column) to better align

# Class for each row item, with text size of 10 and discard button 
class RowEntry(QWidget):
    deleted_row = Signal() # Signal sent to the overall pomodoro entries widget to update list if any item is deleted 

    def __init__(self, *args):
        # TODO: Add delete button 
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setLayout = self.layout
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
        self.layout.setSpacing(20)

        for item in args:
            if item:
                if len(item) > 35:
                    self.item_label = QLabel(item[:30] + "...")
                else:
                    self.item_label = QLabel(item)
            else:
                self.item_label = QLabel("")
            self.item_label.setToolTip(item)
            self.item_label.setFont(font)
            self.layout.addWidget(self.item_label, 2)

        self.layout.setStretch(0, 1)

        self.delete_button = QPushButton("")
        self.delete_button.setIcon(self.delete_button.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton))
        self.delete_button.setMaximumWidth(20)
        self.layout.addWidget(self.delete_button)
        self.layout.setContentsMargins(5,5,5,5)
        self.setStyleSheet("RowEntry { border-bottom: 1px solid black }") # Adds a solid black line to the bottom of the row 
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.delete_button.released.connect(self.delete_row)

    @Slot()
    def delete_row(self):
        # Call db function to delete row in pomodoro table where endtime = self.endtime and emit signal to remove the row 
        num = self.layout.count()
        if num == 4:
            # if 3 item in the row, delete from pomodoro timer 
            Analyse.delete_pomodoro_rows(self.layout.itemAt(0).widget().text())
        elif num == 5:
            # if 4 item in the row, delete from the main task or sub task table
            sub_task = self.layout.itemAt(1).widget().text()
            endtime = self.layout.itemAt(0).widget().text()
            
            if sub_task:
                # if sub task is not blank, delete sub task
                Analyse.delete_completed_sub_task(sub_task, endtime)

            else:
                # delete main task and all its sub task 
                maintask = self.layout.itemAt(2).widget().text()
                section = self.layout.itemAt(3).widget().text()
                Analyse.delete_completed_main_task_plus_sub_tasks(maintask, section, endtime)
            
        self.deleted_row.emit()
        
# Class for the entire list of entries with the headers         
class CompletedPomodoro(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout = self.layout
        self.layout.setSpacing(0) # Set spacing to 0 so there is no spacing between each row item
        self.update_items()

    @Slot()
    def update_items(self):
        # Delete the widgets from layout
        while self.layout.count() != 0:
            widget = self.layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        # Update the layout 
        completed_pomo = Analyse.get_pomodoro_rows()
        self.layout.addWidget(HeaderRow([1, 2, 2], 6, "Time Completed", "Duration (mins)", "Timer Type"))
        for endtime, duration_mins, timertype in completed_pomo:
            rowItem = RowEntry(str(endtime), str(duration_mins), timertype)
            self.layout.addWidget(rowItem)
            rowItem.deleted_row.connect(self.update_items)
        self.layout.addStretch() # Add stretch at the end so there is no stretch on each row item
    
            
# Class to create a scroll area for the pomodoro entries 
class CompletedPomodoroScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.completed_pomo = CompletedPomodoro()
        self.setWidget(self.completed_pomo)
        self.setWidgetResizable(True)

class CompletedTasks(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout = self.layout
        self.layout.setSpacing(0) # Set spacing to 0 so there is no spacing between each row item
        self.update_items()

    @Slot()
    def update_items(self):
        # Delete the widgets from layout
        while self.layout.count() != 0:
            widget = self.layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        # Update the layout 
        completed_tasks = Analyse.get_all_completed_tasks()
        self.layout.addWidget(HeaderRow([1, 2, 2, 2], 57, "Time Completed", "Sub Task", "Main Task", "Section"))
        for endtime, sub_task, main_task, section in completed_tasks:
            rowItem = RowEntry(str(endtime), sub_task, main_task, section)
            self.layout.addWidget(rowItem)
            rowItem.deleted_row.connect(self.update_items)
        self.layout.addStretch() # Add stretch at the end so there is no stretch on each row item

# Class to create a scroll area for the completed tasks entries 
class CompletedTasksScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.completed_tasks = CompletedTasks()
        self.setWidget(self.completed_tasks)
        self.setWidgetResizable(True)

# Class for the entire completed tab that includes both pomodoro section and to do list section
class CompletedTab(QTabWidget):
    def __init__(self):
        super().__init__()
        self.completed_pomo = CompletedPomodoroScrollArea()
        self.completed_tasks = CompletedTasksScrollArea()
        self.addTab(self.completed_pomo, "Pomodoro")
        self.addTab(self.completed_tasks, "Tasks")

# Class for the entire analyse tab
class AnalyseTab(QTabWidget):
    w, h = 1000, 700
    def __init__(self):
        super().__init__()
        self.resize(self.w, self.h)
        self.completed_widget = CompletedTab()
        self.addTab(self.completed_widget, "Completed")
        self.addTab(QLabel("Pomodoro Widget"), "Pomodoro")
        self.addTab(QLabel("Todolist Widget"), "To do list")
        self.setTabPosition(QTabWidget.TabPosition.West)