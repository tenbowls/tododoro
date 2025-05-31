from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel, QListWidget, QSizePolicy, QScrollArea, QAbstractScrollArea, QListWidgetItem, \
QAbstractItemView, QGridLayout, QPushButton, QInputDialog, QMessageBox
from PySide6.QtCore import Qt, Slot, Signal, QTimer
from PySide6.QtGui import QBrush, QFont, QColor, QAction 

if __name__ == "__main__":
    import overhead as oh 
else:
    import src.overhead as oh 

logger = oh.get_logger("tdl section")
logger.debug("Logger started")

# Main Task Item (the first item) in the QListWidget, hence text is bold with highlighted background
class MainTaskItem(QListWidgetItem):
    def __init__(self, main_task):
        super().__init__(main_task)
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.setFont(font)
        self.setBackground(QBrush(QColor("#FFFCA1")))

# Sub Task Item in the QListWidget, setting the text is be slightly bigger than default
class SubTaskItem(QListWidgetItem):
    def __init__(self, sub_task):
        super().__init__(sub_task)
        font = QFont()
        font.setPointSize(12)
        self.setFont(font)

# Widget for the five buttons 
class Buttons(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.unselect_button = QPushButton("Unselect")
        self.rename_button = QPushButton("Rename")
        self.delete_button = QPushButton("Delete")
        self.complete_button = QPushButton("Complete")
        self.focus_button = QPushButton("Focus")
        self.layout.addWidget(self.complete_button)
        self.layout.addWidget(self.delete_button)
        self.layout.addWidget(self.rename_button)
        self.layout.addWidget(self.unselect_button)
        self.layout.addWidget(self.focus_button)

        #Styling for the buttons
        self.complete_button.setStyleSheet("background-color: #72FCBC") # Complete colour green
        self.delete_button.setStyleSheet("background-color: #FC9595") # Delete colour red 
        self.focus_button.setStyleSheet("background-color: #CFFFFF") # Focus colour blue 

# QListWidget for each main task with many sub tasks
class MainTaskList(QListWidget):
    # Custom signal that is emitted when any item is clicked
    clicked = Signal(QListWidget, QListWidgetItem)

    def __init__(self, main_task_txt):
        # Takes in a main_task_txt name and adds that as the first item
        super().__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Only one item can be selected in the qlistwidget at the same time 
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.main_task_item = MainTaskItem(main_task_txt)
        self.addItem(self.main_task_item)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.itemClicked.connect(self.item_clicked)

    # Emit a custom signal when items are clicked
    def item_clicked(self, item):
        self.clicked.emit(self, item)
        logger.debug(f"Detected click on '{self.item(0).text()}' widget on item '{item.text()}'")

    # Ignore all mouse clicks except for left button clicks 
    def mousePressEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            super(MainTaskList, self).mousePressEvent(event)
        else:
            return
        
    def get_num_sub_tasks(self):
        '''Return the list of sub tasks name in the main task list widget'''
        sub_tasks = []
        for i in range(1, self.count()):
            sub_tasks.append(self.item(i).text())
        return sub_tasks

# Class for all the main task widgets
class AllMainTaskList(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout = self.layout
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Dictionary to store all the QListWidget objects for tracking and accessing each QListWidget
        self.main_task_dicts = {}

    def get_num_tasks(self)->int:
        '''Return the number of open tasks (including the main tasks) in a section'''
        num = 0
        for main_tasks in self.main_task_dicts.values():
            num += main_tasks.count()
        return num
    
    @Slot()
    def unselect_all_items(self) -> None:
        '''Unselect all items in the section'''
        for main_task_widget in self.main_task_dicts.values():
            for item in main_task_widget.selectedItems():
                item.setSelected(False)

    def get_main_tasks(self) -> list:
        '''Returns a list of all the main task in the section'''
        main_tasks = []
        for main_task_widget in self.main_task_dicts.values():
            main_tasks.append(main_task_widget.item(0).text())
        return main_tasks


# Class to create a scrollable area for all the QListWidgets in each section        
class TodolistScroll(QScrollArea):
    def __init__(self):
        super().__init__()
        self.all_main_tasks = AllMainTaskList()
        self.setWidget(self.all_main_tasks)
        self.setWidgetResizable(True)

# Class to create the main Todolist Section 
class TodolistSection(QWidget):
    # Custom signals received by the todolist_main widgets for adding items to the database
    add_main_task_to_db = Signal(str)
    delete_main_task_in_db = Signal(str)
    complete_main_task_in_db = Signal(str)
    rename_main_task_in_db = Signal(str, str)

    rename_sub_task_in_db = Signal(str, str, str)
    add_sub_task_to_db = Signal(str, str)
    delete_sub_task_in_db = Signal(str, str)
    complete_sub_task_in_db = Signal(str, str)

    set_main_task_as_pending = Signal(str)
    set_sub_task_as_pending = Signal(str, str)

    update_focus_task = Signal(str)

    def __init__(self):
        # Creating some flags for tracking 
        self.selected = None # To ensure only one item is clicked at the same time 
        self.mode_is_main = True # Check if qlineedit item is a main task or sub task 

        self.selected_widget = None 
        self.selected_task = None

        # Some flags to remember the last action for undo
        self.last_task_is_main = None
        self.last_task_name = None
        self.last_main_task_name = None
        self.last_task_is_complete = None 

        super().__init__()
        self.layout = QGridLayout(self)
        self.setLayout = self.layout  

        # Creating the prompt message and QLineEdit widgets and adding to the layout
        self.task_prompt = QLineEdit(placeholderText="Main task name")
        self.task_prompt.setMaxLength(50)
        self.task_prompt.returnPressed.connect(self.task_added) # Connect the return pressed signal to the task added function 
        self.msg_prompt = QLabel("Insert main task:")
        self.msg_prompt.setFixedHeight(self.task_prompt.sizeHint().height())
        self.enter_button = QPushButton("Insert")
        self.enter_button.released.connect(self.task_added)
        self.layout.addWidget(self.enter_button, 2, 1, 1, 1)
        self.layout.addWidget(self.msg_prompt, 1, 0, 1, 2, Qt.AlignmentFlag.AlignTop)
        self.layout.setVerticalSpacing(0)
        self.layout.addWidget(self.task_prompt, 2, 0, 1, 1, Qt.AlignmentFlag.AlignTop)

        # Creating the scrollable object and adding to the layout 
        self.tasks_scroll = TodolistScroll()
        self.layout.setRowMinimumHeight(2, 5)
        self.layout.addWidget(self.tasks_scroll, 3, 0, 1, 1)

        # Creating status message with undo option 
        self.status_with_undo_msg = QLabel("")
        self.layout.addWidget(self.status_with_undo_msg, 4, 0, 1, 2, Qt.AlignmentFlag.AlignLeft)
        self.status_with_undo_msg.linkActivated.connect(self.undo)
        self.timer5s = QTimer() # Timer to only show the undo option for 5s
        self.timer5s.timeout.connect(self.status_with_undo_msg.clear)

        # Creating the buttons objects and adding to the layout, and connecting the signal to the slots 
        self.buttons = Buttons()
        self.layout.addWidget(self.buttons, 3, 1, 1, 1, Qt.AlignmentFlag.AlignTop)
        self.buttons.rename_button.released.connect(self.rename)
        self.buttons.delete_button.released.connect(self.delete)
        self.buttons.unselect_button.released.connect(self.tasks_scroll.all_main_tasks.unselect_all_items)
        self.buttons.unselect_button.released.connect(self.reset_flags)
        self.buttons.complete_button.released.connect(self.complete)
        self.buttons.focus_button.released.connect(self.focus)

    @Slot()
    def task_added(self):
        task = self.task_prompt.displayText().strip().replace("'", "")
        if task:
            if self.mode_is_main:
                # If main task is added
                if task not in self.tasks_scroll.all_main_tasks.main_task_dicts.keys():
                    # Check that the main task is not duplicated in the section 
                    main_task_list = MainTaskList(task)
                    main_task_list.clicked.connect(self.item_clicked)
                    main_task_list.itemClicked.emit(main_task_list.item(0)) # Emit signal so the newly added main task is selected 
                    main_task_list.item(0).setSelected(True)
                    self.tasks_scroll.all_main_tasks.main_task_dicts[task] = main_task_list
                    self.task_prompt.setText("")
                    self.tasks_scroll.all_main_tasks.layout.addWidget(main_task_list)
                    logger.debug(f"Added main task '{task}' to section")
                    self.add_main_task_to_db.emit(task)
                else: # Show error if main task name already exist 
                    QMessageBox.warning(self, "Duplicate", f"Duplicate main task '{task}' not allowed!")
                    logger.debug(f"Duplicate main task '{task}' is not allowed")
                    self.task_prompt.setText("")
            else:
                # If sub task is added 
                repeat, items, s =  oh.check_task_re(task) # Use regex to check if ^num-num^ format exist for mass adding task 
                existing_sub_tasks = self.selected_widget.get_num_sub_tasks()
                if repeat:
                    for i in range(items[0], items[1] + 1):
                        task = s[0] + str(i) + s[1]
                        if task in existing_sub_tasks: # Don't add the task if a same name already exist 
                            continue 
                        else:
                            self.selected_widget.addItem(SubTaskItem(task))
                            logger.debug(f"Sub task '{task}' added under main task '{self.selected_widget.item(0).text()}'")
                            self.add_sub_task_to_db.emit(task, self.selected_widget.item(0).text())
                    self.task_prompt.setText("")
                    return

                if task in existing_sub_tasks: # Show error if sub task name already exist
                    QMessageBox.warning(self, "Duplicate", f"Duplicate sub task '{task}' not allowed!")
                    return
                
                self.selected_widget.addItem(SubTaskItem(task))
                self.task_prompt.setText("")
                logger.debug(f"Sub task '{task}' added under main task '{self.selected_widget.item(0).text()}'")
                self.add_sub_task_to_db.emit(task, self.selected_widget.item(0).text())

    @Slot()
    def item_clicked(self, main_widget, item):
        # Ensure only one item is clicked at the same time
        self.selected_task = item
        if self.selected:
            if self.selected == item:
                # If the item was already selected, unselect it
                self.selected.setSelected(False)
                self.selected = None
            else:
                # If a different item was selected, unselected that item as only one item can be selected at the same time
                self.selected.setSelected(False)
                self.selected = item
        else:
            self.selected = item

        self.selected_widget = main_widget
        self.selected_task = item

        if main_widget.item(0) == item:
            # If the main task is selected, change the prompt to ask for sub task details
            self.set_mode_sub()

        else:
            # If sub task is selected, disable the prompt
            self.disable_prompt()

        if self.selected == None:
            # If no tasks are selected, change the prompt to ask for main task details
            self.set_mode_main()
            self.selected_widget = None
            self.selected_task = None

    @Slot()
    def focus(self):
        # If the focus button is clicked, update the text in the focus section
        if self.selected_task:
            self.update_focus_task.emit(self.selected_task.text())


    @Slot()
    def rename(self):
        if self.selected_task:
            max_len = 50 if self.mode_is_main else 60
            # Prompt user to enter the new task name
            new_name, accepted = QInputDialog.getText(self, "Rename", f"Enter new name for '{self.selected_task.text()}'", text=f"{self.selected_task.text()}")
            if accepted:
                new_name = new_name.strip()
                if new_name: # Continue only if not empty string 
                    new_name = new_name.replace("'", "")
                    if len(new_name) > max_len: # Error if the name is too long 
                        QMessageBox.information(self, "Character limit exceeded", f"New name exceeded character limit of {max_len}")
                        return
                    
                    logger.debug(f"Updating task name '{self.selected_task.text()}' to '{new_name}'")
                    if self.selected_task == self.selected_widget.item(0): # If main task is renamed 
                        self.tasks_scroll.all_main_tasks.main_task_dicts[new_name] = self.tasks_scroll.all_main_tasks.main_task_dicts[self.selected_task.text()]
                        del self.tasks_scroll.all_main_tasks.main_task_dicts[self.selected_task.text()]
                        self.rename_main_task_in_db.emit(self.selected_task.text(), new_name)
                        
                    else: # If sub task is renamed 
                        self.rename_sub_task_in_db.emit(self.selected_task.text(), new_name, self.selected_widget.item(0).text())
                    self.selected_task.setText(new_name)

    @Slot()
    def delete(self):
        if self.selected_task:
            # Checks if the selected task is the main task
            if self.selected_widget.item(0) == self.selected_task:
                # Ask the user for confirmation then remove widget and delete from dictionary
                ans = QMessageBox.warning(self, "Confirm delete?", f"Are you sure to you to delete '{self.selected_task.text()}'"
                                           f"main task with {self.selected_widget.count()-1} sub tasks?", 
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if ans == QMessageBox.StandardButton.Yes:
                    logger.debug(f"Deleting main task '{self.selected_task.text()}'")
                    # Emit signal to delete each subtasks
                    item_count = self.selected_widget.count()
                    if item_count > 1:
                        for i in range(1, item_count):
                            self.delete_sub_task_in_db.emit(self.selected_widget.item(i).text(), self.selected_task.text())

                    # Deleting the main task 
                    self.delete_main_task_in_db.emit(self.selected_task.text())
                    self.tasks_scroll.all_main_tasks.layout.removeWidget(self.selected_widget)
                    del self.tasks_scroll.all_main_tasks.main_task_dicts[self.selected_widget.item(0).text()]
                    self.selected_widget.deleteLater()
                    self.selected_widget = None
                    self.reset_flags()
            else:
                # If sub task is selected, delete item without prompt 
                self.start_timer() # Start timer to show the undo option 
                self.get_status(False, self.selected_task.text(), self.selected_widget.item(0).text(), False) # Show the status message with undo button 
                logger.debug(f"Deleting sub task '{self.selected_task.text()}'")
                self.delete_sub_task_in_db.emit(self.selected_task.text(), self.selected_widget.item(0).text())
                self.selected_widget.takeItem(self.selected_widget.row(self.selected_task))
                selected = self.selected_widget.selectedItems()
                for items in selected:
                    items.setSelected(False) # Unselect all the items 
                self.reset_flags()

    @Slot()
    def complete(self):
        if self.selected_task:
            # Check if selected task is the main task
            if self.selected_task == self.selected_widget.item(0):
                # Check if subtasks exist, do not allow to be marked as complete if subtasks exist
                task_count = self.selected_widget.count()
                if task_count > 1:
                    QMessageBox.warning(self, "Sub tasks not completed", f"{task_count - 1} sub task(s) still exist in"
                                         f" '{self.selected_task.text()}'. \nNot allowed to mark as complete.")
                    return
                self.start_timer() # Start timer for the undo message to show 
                self.get_status(True, self.selected_task.text(), self.selected_task.text(), True) # Show status with undo button 
                self.complete_main_task_in_db.emit(self.selected_task.text())
                self.tasks_scroll.all_main_tasks.layout.removeWidget(self.selected_widget)
                del self.tasks_scroll.all_main_tasks.main_task_dicts[self.selected_widget.item(0).text()]
                self.selected_widget.deleteLater()
                self.selected_widget = None
            else: # If selected task is sub task 
                self.start_timer()
                self.get_status(False, self.selected_task.text(), self.selected_widget.item(0).text(), True)
                self.complete_sub_task_in_db.emit(self.selected_task.text(), self.selected_widget.item(0).text())
                self.selected_widget.takeItem(self.selected_widget.row(self.selected_task))
                selected = self.selected_widget.selectedItems()
                for items in selected:
                    items.setSelected(False) # Unselect all the items 
            self.reset_flags()
    
    @Slot()
    def undo(self, _):
        # Slot to capture the undo click on the status message to undo the action
        if self.last_task_is_complete:
            # Last action was set as complete, so have to set as incomplete:
            if self.last_task_is_main:
                # Last action was setting main task as complete, undoing action: adding back item into UI and updating database
                logger.debug(f"User undid action of completing main task {self.last_task_name}")
                main_task_list = MainTaskList(self.last_task_name)
                main_task_list.clicked.connect(self.item_clicked)
                self.tasks_scroll.all_main_tasks.main_task_dicts[self.last_task_name] = main_task_list
                self.tasks_scroll.all_main_tasks.layout.addWidget(main_task_list)

                # Emit signal to change main task status from complete to pending and remove end time 
                self.set_main_task_as_pending.emit(self.last_task_name)
            else:
                # Last action was setting sub task as complete, add sub task back under main task and update database 
                logger.debug(f"User undid action of completing sub task {self.last_task_name}")
                self.tasks_scroll.all_main_tasks.main_task_dicts[self.last_main_task_name].addItem(SubTaskItem(self.last_task_name))

                # Emit signal to change sub task status from complete to pending and remove end time
                self.set_sub_task_as_pending.emit(self.last_task_name, self.last_main_task_name)
        else:
            # Last action was delete the task, only sub task have undo option, main task deletion will not be able to undo as there is already a message prompt
            # Add sub task back under the main task and add it into the database 
            logger.debug(f"User undid action of deleting task {self.last_task_name}")
            self.tasks_scroll.all_main_tasks.main_task_dicts[self.last_main_task_name].addItem(SubTaskItem(self.last_task_name))
            self.add_sub_task_to_db.emit(self.last_task_name, self.last_main_task_name)
            
        self.status_with_undo_msg.clear()

    def start_timer(self):
        self.timer5s.start(8000)

    def get_status(self, is_main_task: bool, task_name: str, main_task_name: str, is_complete: bool) -> None:
        '''Updates the status message with the undo button and update the flags in case undo option is clicked'''
        task_type = "main" if is_main_task else "sub"
        task_action = "Completed" if is_complete else "Deleted"
        self.status_with_undo_msg.setText(f"{task_action} {task_type} task '{task_name}' <a href='a'><b>[Undo]</b></a>")
        self.last_task_is_complete = is_complete
        self.last_task_is_main = is_main_task
        self.last_task_name = task_name
        self.last_main_task_name = main_task_name

    def add_main_task_to_tab(self, task: str):
        # Add main task to the section and emit signal 
        main_task_list = MainTaskList(task)
        main_task_list.clicked.connect(self.item_clicked)
        self.tasks_scroll.all_main_tasks.main_task_dicts[task] = main_task_list
        self.tasks_scroll.all_main_tasks.layout.addWidget(main_task_list)

    def set_mode_main(self):
        # Set the prompt to ask for main task
        self.msg_prompt.setText("Insert main task:")
        self.task_prompt.setEnabled(True)
        self.task_prompt.setPlaceholderText("Main task name")
        self.task_prompt.setMaxLength(50)
        self.mode_is_main = True

    def set_mode_sub(self):
        # Set the prompt to ask for sub task
        self.msg_prompt.setText("Insert sub task:")
        self.task_prompt.setEnabled(True)
        self.task_prompt.setPlaceholderText("Sub task name")
        self.task_prompt.setMaxLength(60)
        self.mode_is_main = False

    def disable_prompt(self):
        # Disable the prompt when a sub task is clicked 
        self.msg_prompt.setText("")
        self.task_prompt.setPlaceholderText("")
        self.task_prompt.setEnabled(False)
        self.mode_is_main = None

    @Slot()
    def reset_flags(self):
        # Reset all the flags back to initial state
        self.selected = None
        self.mode_is_main = True
        self.selected_widget = None
        self.selected_task = None
        self.set_mode_main()

if __name__ == "__main__":
    app = QApplication([])
    listwidget = TodolistSection()
    listwidget.show()
    app.exec()