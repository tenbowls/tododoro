from PySide6.QtWidgets import QApplication, QTabWidget, QLabel, QTabBar, QMessageBox, QInputDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Slot, Qt, Signal 
import sys 

import src.overhead as oh 
import src.todolist_section as tdl
from src.db import SectionTools, MainTaskTools, SubTaskTools
from src.todolist_section import SubTaskItem

# Get logger and start logging 
logger = oh.get_logger("todolist")
logger.debug("Logger started")

# Decorator to display error message when function fails 
def error_handler(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Function execution of {func.__name__} failed: {e}")
            err = oh.ErrorBox(str(e))
            err.exec()
    return inner 

class Todolist(QTabWidget):
    update_focus_task_section = Signal(str)
    update_completed_task = Signal()

    def __init__(self):
        super().__init__()

        # Keep track of the tab names to ensure no duplicates 
        # Get the section name from the database 
        self.tab_sections = SectionTools.get_section_name()

        # Connecting tab bar signals and enabling tabs closable 
        self.tabBarClicked.connect(self.tab_bar_clicked)
        self.tabBarDoubleClicked.connect(self.rename_tab)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.delete_tab)
        self.setTabPosition(QTabWidget.TabPosition.West)

        # Creating an empty tab with "+", when "+" tab bar is clicked, create a new tab
        empty_tab = QLabel("")
        empty_tab.setStyleSheet("background-color: #CCCCCC")
        self.addTab(empty_tab, "+")

        # Hide the close button of the "+" tab so it cannot be clicked
        self.tabBar().tabButton(self.count()-1, QTabBar.ButtonPosition.RightSide).resize(0, 0)

        # Initialize all the tab sections based on the database information
        for i, section in enumerate(self.tab_sections):
            self.add_tab_section(i, section)
        
        # Selecting the first tab when the app is first opened 
        if self.tab_sections:
            self.setCurrentIndex(0)

            # Add main tasks to each section based on database entries 
            main_tasks = MainTaskTools.get_main_tasks()
            for tab in self.tab_sections:
                for maintask, section in main_tasks:
                    if section == tab:
                        self.widget(self.tab_sections.index(tab)).add_main_task_to_tab(maintask)
                        main_task_id = MainTaskTools.get_main_task_id(maintask, section)

                        # Add sub tasks to each main task based on database entries 
                        sub_tasks = SubTaskTools.get_sub_tasks(main_task_id)
                        for sub_task in sub_tasks:
                            self.widget(self.tab_sections.index(tab)).tasks_scroll.all_main_tasks.main_task_dicts[maintask].addItem(SubTaskItem(sub_task))

    # Slot for when tab_bar is clicked
    @error_handler
    @Slot()
    def tab_bar_clicked(self, i):
        num_tabs = self.count()

        # If tab_bar of "+" is pressed (which is the last tab), create a new tab, else do nothing
        if i == num_tabs - 1:
            idx = 0 if num_tabs == 1 else num_tabs - 1 # Index for where the new tab is added 
            ans, ok = QInputDialog.getText(self, "New Section Name", "Enter section name:") # Prompts the user for tab name 
            if ok:
                if ans.strip() == '': # Don't allow empty strings as tab names
                    QMessageBox.warning(self, "Empty name", "Empty name is not allowed.")
                elif ans not in self.tab_sections:
                    logger.debug(f"Adding new tab '{ans}' at index {idx}")
                    self.add_tab_section(idx, ans)
                    self.tab_sections.append(ans)
                    SectionTools.add_section_name(ans)
                else: # Don't allow duplicate of tab section
                    QMessageBox.warning(self, "Duplicate", f"Duplicate section of '{ans}' not allowed!")

    def add_tab_section(self, i, name):
        # Creates a new tab
        tdlSection = tdl.TodolistSection()

        # Adding all the signals from the TodolistSection widget to the existing todolist_main slot
        tdlSection.add_main_task_to_db.connect(self.add_main_task_to_db)
        tdlSection.rename_main_task_in_db.connect(self.rename_main_task_in_db)
        tdlSection.delete_main_task_in_db.connect(self.delete_main_task_in_db)
        tdlSection.complete_main_task_in_db.connect(self.complete_main_task_in_db)
        tdlSection.add_sub_task_to_db.connect(self.add_sub_task_to_db)
        tdlSection.rename_sub_task_in_db.connect(self.rename_sub_task_in_db)
        tdlSection.delete_sub_task_in_db.connect(self.delete_sub_task_in_db)
        tdlSection.complete_sub_task_in_db.connect(self.complete_sub_task_in_db)
        tdlSection.set_main_task_as_pending.connect(self.set_main_task_as_pending)
        tdlSection.set_sub_task_as_pending.connect(self.set_sub_task_as_pending)
        tdlSection.update_focus_task.connect(self.update_focus_task)

        self.insertTab(i, tdlSection, name.replace("'", ""))

    # Slots for when information in database has to be changed
    @error_handler 
    @Slot()
    def add_main_task_to_db(self, task):
        MainTaskTools.add_main_tasks(task, self.tabText(self.currentIndex()))

    @error_handler
    @Slot()
    def rename_main_task_in_db(self, oldnametask, newnametask):
        MainTaskTools.rename_main_tasks(oldnametask, newnametask, self.tabText(self.currentIndex()))

    @error_handler
    @Slot()
    def delete_main_task_in_db(self, task):
        MainTaskTools.delete_main_tasks(task, self.tabText(self.currentIndex()))

    @error_handler
    @Slot()
    def complete_main_task_in_db(self, task):
        MainTaskTools.complete_main_tasks(task, self.tabText(self.currentIndex()))
        self.update_completed_task.emit()

    @error_handler
    @Slot()
    def add_sub_task_to_db(self, subtask, maintask):
        SubTaskTools.add_sub_tasks(subtask, maintask, self.tabText(self.currentIndex()))

    @error_handler
    @Slot()
    def rename_sub_task_in_db(self, oldnametask, newnametask, main_task):
        SubTaskTools.rename_sub_tasks(oldnametask, newnametask, main_task, self.tabText(self.currentIndex()))

    @error_handler
    @Slot()
    def delete_sub_task_in_db(self, subtask, maintask):
        SubTaskTools.delete_sub_tasks(subtask, maintask, self.tabText(self.currentIndex()))

    @error_handler
    @Slot()
    def complete_sub_task_in_db(self, subtask, maintask):
        SubTaskTools.complete_sub_tasks(subtask, maintask, self.tabText(self.currentIndex()))
        self.update_completed_task.emit()

    @error_handler
    @Slot()
    def set_main_task_as_pending(self, task):
        MainTaskTools.set_main_task_as_pending(task, self.tabText(self.currentIndex()))

    @error_handler  
    @Slot()
    def set_sub_task_as_pending(self, subtask, maintask):
        SubTaskTools.set_sub_task_as_pending(subtask, maintask, self.tabText(self.currentIndex()))

    # Slot for when delete button is clicked on the section
    @error_handler  
    @Slot()      
    def delete_tab(self, i):
        num = self.widget(i).tasks_scroll.all_main_tasks.get_num_tasks() # Gets the number of all tasks in the section

        # Prompts the user to confirm to delete the section with x number of open tasks
        ans = QMessageBox.warning(self, "Confirm?", f"Do you want to delete section '{self.tabText(i)}' with {num} open tasks?", 
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if ans == QMessageBox.StandardButton.Yes:
            logger.debug(f"Deleting '{self.tabText(i)}' from index {i}")
            if self.currentIndex() == i:
                self.setCurrentIndex(max(0, i - 1)) # Go to the tab to the left of the deleted tab if the deleted tab is the selected tab

            for main_task in self.widget(i).tasks_scroll.all_main_tasks.get_main_tasks():

                # Delete sub tasks when tab is deleted
                num_sub_tasks = self.widget(i).tasks_scroll.all_main_tasks.main_task_dicts[main_task].count()
                while num_sub_tasks > 1:
                    item = self.widget(i).tasks_scroll.all_main_tasks.main_task_dicts[main_task].takeItem(1)
                    SubTaskTools.delete_sub_tasks(item.text(), main_task, self.tabText(i))
                    num_sub_tasks = self.widget(i).tasks_scroll.all_main_tasks.main_task_dicts[main_task].count()

                # Delete main tasks when tab is deleted
                MainTaskTools.delete_main_tasks(main_task, self.tabText(i))

            SectionTools.delete_section_name(self.tabText(i))
            self.tab_sections.remove(self.tabText(i))
            self.removeTab(i)

    # Slot for when tab is double clicked
    @error_handler
    @Slot()
    def rename_tab(self, i):
        # Do nothing if the "+" tab is double clicked
        if i == self.count() - 1:
            return
        
        # Prompts the user to enter a name
        ans = QInputDialog.getText(self, "Rename", f"Enter new name for {self.tabText(i)}", text=f"{self.tabText(i)}")
        
        if ans[1]:
            if ans[0] in self.tab_sections: # If tab name already exist, show error
                QMessageBox.warning(self, "Duplicate", f"Duplicate name '{ans[0]}' not allowed!")
                return
            
            elif ans[0].strip() == "": # Show error if empty name 
                QMessageBox.warning(self, "Empty name", "Empty name is not allowed.")
                return

            SectionTools.change_section_name(self.tabText(i), ans[0]) # Update database 
            self.tab_sections.remove(self.tabText(i))
            self.setTabText(i, ans[0])
            self.tab_sections.append(ans[0])
            logger.debug(f"Tab at index {i} renamed from '{self.tabText(i)}' to '{ans[0]}'")

    @Slot()
    def update_focus_task(self, focus_task):
        self.update_focus_task_section.emit(focus_task)

class FocusSection(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setLayout = self.layout
        self.focus_task = QLabel("FOCUS: ")
        self.focus_task.setStyleSheet("background-color: #CFFFFF; font-family: 'Arial', 'sans-serif'; font-size: 14px; font-weight: bold;") 
        self.clear_task = QPushButton("Clear")
        self.layout.addWidget(self.focus_task, Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(self.clear_task)
        self.layout.setContentsMargins(0,0,0,0)
        self.clear_task.released.connect(self.clear_focus_task)

    @Slot()
    def update_focus_task(self, focus_task):
        self.focus_task.setText(f"FOCUS: {focus_task}")

    @Slot()
    def clear_focus_task(self):
        self.focus_task.setText("FOCUS: ")

class TodolistwFocus(QWidget):
    w, h = 800, 700
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout = self.layout
        self.focus_section = FocusSection()
        self.todolist = Todolist()
        self.layout.addWidget(self.focus_section)
        self.layout.addWidget(self.todolist)
        self.todolist.update_focus_task_section.connect(self.focus_section.update_focus_task)
        
if __name__ == "__main__":
    app = QApplication([])
    widget = TodolistwFocus()
    widget.show()
    app.exec()
    sys.exit(0)