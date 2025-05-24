from PySide6.QtWidgets import QTabWidget, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QStyle, QLineEdit
from PySide6.QtCore import Qt, Slot, Signal 
from PySide6.QtGui import QFont
from src.db import Completed 

from src.overhead import get_logger
import src.analyse_dashboard as analyse_tdl
from src.analyse_dashboard import error_handler

logger = get_logger("analyse (c)")

class TaskFilter(QWidget):
    # Class for the filter section in the completed tasks section 
    filter_signal = Signal(str, str, str)
    def __init__(self):
        super().__init__()
        # Reset button with the label "filter" for the first column 
        self.reset_filter = QPushButton("")
        self.reset_filter.setIcon(self.reset_filter.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
        self.reset_filter.setMaximumWidth(20)
        self.reset_filter_layout = QHBoxLayout()
        self.reset_filter_layout.addWidget(self.reset_filter)
        self.reset_filter_layout.addWidget(QLabel("Filter: "), alignment=Qt.AlignmentFlag.AlignRight)
        self.reset_filter.setToolTip("Reset filter")

        self.layout = QHBoxLayout(self)
        self.setLayout = self.layout 
        self.sub_task_filter = QLineEdit()
        self.main_task_filter = QLineEdit()
        self.section_filter = QLineEdit()
        self.enter_button = QPushButton("")
        self.enter_button.setIcon(self.enter_button.style().standardIcon(QStyle.StandardPixmap.SP_CommandLink))
        self.enter_button.setMaximumWidth(20)
        self.enter_button.setToolTip("Apply filter")
        self.layout.addLayout(self.reset_filter_layout)
        self.layout.addWidget(self.sub_task_filter)
        self.layout.addWidget(self.main_task_filter)
        self.layout.addWidget(self.section_filter)
        self.layout.setStretch(0, 1)
        self.layout.setStretch(1, 2)
        self.layout.setStretch(2, 2)
        self.layout.setStretch(3, 2)
        self.layout.addWidget(self.enter_button)
        self.layout.insertSpacing(1, 20)

        # Connect the qlineedit signals and the enter button signals to the custom signal 
        self.sub_task_filter.returnPressed.connect(self.update_list)
        self.main_task_filter.returnPressed.connect(self.update_list)
        self.section_filter.returnPressed.connect(self.update_list)
        self.enter_button.released.connect(self.update_list)

    @Slot()
    def update_list(self):
        # Send signal to update completed task table from filter 
        self.filter_signal.emit(self.sub_task_filter.text(), self.main_task_filter.text(), self.section_filter.text())


# Class for the header row with bold text 
class HeaderRow(QWidget):
    def __init__(self, stretch: list, spacing, *args): # takes in a list for the stretch, spacing after the first item, and any number of arguments 
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
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setLayout = self.layout
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
        self.layout.setSpacing(20)

        for item in args:
            if item:
                if len(item) > 40: # Do not show if the whole name if name is too long 
                    self.item_label = QLabel(item[:37] + "...")
                else:
                    self.item_label = QLabel(item)
            else:
                self.item_label = QLabel("")
            self.item_label.setToolTip(item) # Set the status tip to show the whole name
            self.item_label.setFont(font)
            self.layout.addWidget(self.item_label, 2) # Set the stretch as 2

        self.layout.setStretch(0, 1) # Change the stretch for the first column to 1

        # the delete button to delete the row 
        self.delete_button = QPushButton("")
        self.delete_button.setIcon(self.delete_button.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton))
        self.delete_button.setMaximumWidth(20)
        self.layout.addWidget(self.delete_button)

        self.layout.setContentsMargins(5,5,5,5)
        self.setStyleSheet("RowEntry { border-bottom: 1px solid black }") # Adds a solid black line to the bottom of the row 
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.delete_button.released.connect(self.delete_row)

    @error_handler
    @Slot()
    def delete_row(self):
        # Call db function to delete row in pomodoro table where endtime = self.endtime and emit signal to remove the row 
        num = self.layout.count()
        if num == 4:
            # if 3 item in the row, delete from pomodoro timer 
            logger.debug(f"Deleting pomodoro timer entry: {self.layout.itemAt(0).widget().text()}")
            Completed.delete_pomodoro_rows(self.layout.itemAt(0).widget().text())
        elif num == 5:
            # if 4 item in the row, delete from the main task or sub task table
            sub_task = self.layout.itemAt(1).widget().toolTip()
            endtime = self.layout.itemAt(0).widget().text()
            
            if sub_task:
                # if sub task is not blank, delete sub task
                logger.debug(f"Deleting completed sub task entry {sub_task} with end time of {endtime}")
                Completed.delete_completed_sub_task(sub_task, endtime)

            else:
                # delete main task and all its sub task 
                maintask = self.layout.itemAt(2).widget().toolTip()
                section = self.layout.itemAt(3).widget().toolTip()
                logger.debug(f"Deleting completed main task entry {maintask} with end time of {endtime} from section {section}")
                Completed.delete_completed_main_task(maintask, section, endtime)
            
        self.deleted_row.emit()
        
# Class for the entire list of entries with the headers         
class CompletedPomodoro(QWidget):
    update_pomo_items = Signal()
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout = self.layout
        self.layout.setSpacing(0) # Set spacing to 0 so there is no spacing between each row item
        self.update_items()

    @error_handler
    @Slot()
    def update_items(self):
        # Delete the widgets from layout
        logger.debug("Updating completed pomodoro table")
        self.update_pomo_items.emit()
        while self.layout.count() != 0:
            widget = self.layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        # Update the layout 
        completed_pomo = Completed.get_pomodoro_rows()
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
    update_items_signal = Signal()
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout = self.layout
        self.layout.setSpacing(0) # Set spacing to 0 so there is no spacing between each row item
        self.update_items()

    @error_handler
    @Slot()
    def update_items(self):
        logger.debug("Updating completed task table")
        self.update_items_signal.emit() # Emit signals for the to do list dashboard can be updated in the event that any items are deleted 

        # Delete the widgets from layout
        while self.layout.count() != 0:
            widget = self.layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        # Update the layout 
        self.task_filter = TaskFilter()
        self.task_filter.filter_signal.connect(self.update_items_with_filter)
        self.task_filter.reset_filter.released.connect(self.update_items)
        self.layout.addWidget(self.task_filter)
        completed_tasks = Completed.get_all_completed_tasks()
        self.layout.addWidget(HeaderRow([1, 2, 2, 2], 25, "Time Completed", "Sub Task", "Main Task", "Section"))
        for endtime, sub_task, main_task, section in completed_tasks:
            rowItem = RowEntry(str(endtime), sub_task, main_task, section)
            self.layout.addWidget(rowItem)
            rowItem.deleted_row.connect(self.update_items)
        self.layout.addStretch() # Add stretch at the end so there is no stretch on each row item

    @Slot()
    def update_items_with_filter(self, subtaskfilter=None, maintaskfilter=None, sectionfilter=None):
        logger.debug("Updating completed task table with filter")

        self.update_items_signal.emit()

        filter_widget = self.layout.itemAt(0).widget()

        # When deleted row is emitted, no argument is passed
        # When no argument for the filters is received, automatically check the qlineedit for the text and use the text there as the filter
        subtaskfilter = subtaskfilter if subtaskfilter else filter_widget.sub_task_filter.text()
        maintaskfilter = maintaskfilter if maintaskfilter else filter_widget.main_task_filter.text()
        sectionfilter = sectionfilter if sectionfilter else filter_widget.section_filter.text()
        
        # Delete the widgets from layout
        while self.layout.count() != 0:
            widget = self.layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        self.task_filter = TaskFilter()
        self.task_filter.filter_signal.connect(self.update_items_with_filter)
        self.task_filter.reset_filter.released.connect(self.update_items)
        self.layout.addWidget(self.task_filter)

        # Setting the text on the filters qlineedit to what is was before the update for continuity
        self.task_filter.sub_task_filter.setText(subtaskfilter)
        self.task_filter.main_task_filter.setText(maintaskfilter)
        self.task_filter.section_filter.setText(sectionfilter)

        completed_tasks_filtered = Completed.get_filtered_completed_tasks(subtaskfilter, maintaskfilter, sectionfilter)
        self.layout.addWidget(HeaderRow([1, 2, 2, 2], 25, "Time Completed", "Sub Task", "Main Task", "Section"))
        for endtime, sub_task, main_task, section in completed_tasks_filtered:
            rowItem = RowEntry(str(endtime), sub_task, main_task, section)
            self.layout.addWidget(rowItem)
            rowItem.deleted_row.connect(self.update_items_with_filter)

        self.layout.addStretch()
        

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
    w, h = 1200, 700
    def __init__(self):
        super().__init__()
        self.resize(self.w, self.h)
        self.completed_widget = CompletedTab()
        self.analyse_todolist = analyse_tdl.AnalyseTodolistWidget()
        self.analyse_pomo = analyse_tdl.AnalysePomodoroWidget()
        self.addTab(self.completed_widget, "Completed")
        self.addTab(self.analyse_pomo, "Pomodoro")
        self.addTab(self.analyse_todolist, "To do list")
        self.setTabPosition(QTabWidget.TabPosition.West)