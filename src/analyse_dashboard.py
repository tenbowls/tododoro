from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QSizePolicy
from PySide6.QtCore import Qt, Slot

import logging
from src.overhead import get_logger
from src.overhead import ErrorBox

# Creating logger object to suppress logging messages from matplotlib
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import MaxNLocator

from src.db import AnalyseTodolist

matplotlib.use("QtAgg")
plt.style.use("seaborn-v0_8-darkgrid")

logger = get_logger("analyse (d)")
logger.debug("Logger started")

def error_handler(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Function execution of {func.__name__} failed: {e}")
            err = ErrorBox(str(e))
            err.exec()
    return inner 


class CompletedTasks(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout = self.layout 

        # Creating a drop down list to choose the last x days to display 
        self.drop_down_tasks = QComboBox()
        self.drop_down_tasks.addItem("Last 7 days")
        self.drop_down_tasks.addItem("Last 30 days")
        self.drop_down_tasks.addItem("Last 365 days")
        self.drop_down_tasks.setCurrentIndex(0)
        self.drop_down_tasks.currentIndexChanged.connect(self.update_num_task) # Update the task when the drop down list option is changed 
        self.drop_down_tasks.setToolTip("Show number of tasks completed in the last x days")
        self.drop_down_tasks.setFixedWidth(100)
        self.layout.addWidget(self.drop_down_tasks, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.insertSpacing(1, 10)

        # dictionary to store the text for the various time frame chosen 
        self.duration_dict = {7: "in the last 7 days", 30: "in the last 30 days", 365: "in the last 365 days"}

        # labels to display, default to show last 7 days 
        self.all_completed_tasks = QLabel("All Completed Tasks", alignment=Qt.AlignmentFlag.AlignCenter)
        self.completed_tasks = QLabel(f"Completed Tasks\n{self.duration_dict[7]}", alignment=Qt.AlignmentFlag.AlignCenter)
        self.num_all_completed_tasks = QLabel(str(AnalyseTodolist.get_num_all_completed_tasks()), alignment=Qt.AlignmentFlag.AlignCenter) 
        self.num_completed_tasks = QLabel(str(AnalyseTodolist.get_num_completed_tasks(7)), alignment=Qt.AlignmentFlag.AlignCenter) 

        # Styling to the text and numbers
        text_style = "color: #545E75; font-weight: bold; font-size: 25px; font-family: arial, roboto, sans-serif" 
        num_style = "color: #304D6D; font-weight: bold; font-size: 40px; font-family: arial, roboto, sans-serif"

        self.all_completed_tasks.setStyleSheet(text_style)
        self.completed_tasks.setStyleSheet(text_style)
        self.num_all_completed_tasks.setStyleSheet(num_style)
        self.num_completed_tasks.setStyleSheet(num_style)

        self.layout.addWidget(self.completed_tasks)
        self.layout.addWidget(self.num_completed_tasks)
        self.layout.insertSpacing(4, 25) 
        self.layout.addWidget(self.all_completed_tasks)
        self.layout.addWidget(self.num_all_completed_tasks)
        self.layout.insertSpacing(7, 25) 
        
        self.layout.addStretch()

    @error_handler
    @Slot()
    def update_num_task(self, new_idx=1):
        logger.debug("Updating number of completed tasks")
        choices = [7, 30, 365]
        new_idx = self.drop_down_tasks.currentIndex()
        self.num_completed_tasks.setText(str(AnalyseTodolist.get_num_completed_tasks(choices[new_idx])))
        self.num_all_completed_tasks.setText(str(AnalyseTodolist.get_num_all_completed_tasks()))
        self.completed_tasks.setText(f"Completed Tasks\n{self.duration_dict[choices[new_idx]]}")

class MatplotLibGraph(FigureCanvasQTAgg):
    def __init__(self, width=2, height=2, dpi=100):
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        plt.subplots_adjust(top=0.98, bottom=0.25)
        super().__init__(fig)

class TodolistPlots(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout = self.layout 

        # Drop down list for selecting plot duration 
        self.drop_down_choices = QComboBox()
        self.drop_down_choices.addItem("Daily")
        self.drop_down_choices.addItem("Weekly")
        self.drop_down_choices.addItem("Monthly")
        self.drop_down_choices.addItem("Yearly")
        self.drop_down_choices.setCurrentIndex(0)
        self.drop_down_choices.setToolTip("Plots the last 20 data points\nChanges the x-axis to plot by daily/weekly/monthly/yearly")
        self.drop_down_choices.setFixedWidth(100)
        self.layout.addWidget(self.drop_down_choices, alignment=Qt.AlignmentFlag.AlignCenter)
        self.drop_down_choices.currentIndexChanged.connect(self.update_plot)

        # Matplotlib graph for top 20 (default is daily)
        self.graph = MatplotLibGraph()
        self.update_plot(0)
        toolbar = NavigationToolbar(self.graph, self)
        self.layout.addWidget(toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.graph)
        self.layout.setStretch(0, 0)
        self.layout.setStretch(1, 0)
        self.layout.setStretch(2, 1)

    @error_handler
    @Slot()
    def update_plot(self, idx=0):
        logger.debug("Updating to do list plot")
        option_chosen = ['day', 'week', 'month', 'year']
        idx = self.drop_down_choices.currentIndex()
        date_array, num_array = AnalyseTodolist.get_num_completed_task_by_time(option_chosen[idx])
        self.graph.axes.cla()
        self.graph.axes.plot(date_array, num_array, '-o')
        self.graph.axes.set_xlabel(option_chosen[idx].title())
        self.graph.axes.set_ylabel("Number of tasks completed")
        self.graph.axes.set_ylim(max(0, min(num_array)-1), max(num_array)+2)
        self.graph.axes.set_xticks(self.graph.axes.get_xticks())
        self.graph.axes.set_xticklabels(date_array, rotation=45, ha='right', rotation_mode='anchor')
        ax = self.graph.figure.gca()
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        for x, y in zip(date_array, num_array):
            self.graph.axes.annotate(f"{y}", (x, y), textcoords='data', fontsize=12)
        self.graph.draw()

class CompletedTimers(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout = self.layout 

        # Drop down list to choose the last x days to display 
        self.drop_down_tasks = QComboBox()
        self.drop_down_tasks.addItem("Last 7 days")
        self.drop_down_tasks.addItem("Last 30 days")
        self.drop_down_tasks.addItem("Last 365 days")
        self.drop_down_tasks.setCurrentIndex(0)
        self.drop_down_tasks.currentIndexChanged.connect(self.update_num_timers)
        self.drop_down_tasks.setToolTip("Show total duration of timers completed in the last x days")
        self.drop_down_tasks.setFixedWidth(100)
        self.layout.addWidget(self.drop_down_tasks, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.insertSpacing(1, 10)

        # dictionary to store the text for the various time frame chosen 
        self.duration_dict = {7: "in the last 7 days", 30: "in the last 30 days", 365: "in the last 365 days"}

        # labels to display, default to show last 7 days 
        self.total_focus_time = AnalyseTodolist.get_sum_timers(7, 'focus')
        self.all_focus_time = AnalyseTodolist.get_sum_all_timers('focus')
        self.label_focus_time = QLabel(f"Total focus time \n{self.duration_dict[7]}", alignment=Qt.AlignmentFlag.AlignCenter)
        self.label_all_focus_time = QLabel("Total focus time \nfrom the beginning", alignment=Qt.AlignmentFlag.AlignCenter)
        self.num_total_focus_time = QLabel(str(self.convert_to_hr_mins(self.total_focus_time)), alignment=Qt.AlignmentFlag.AlignCenter) 
        self.num_all_focus_time = QLabel(str(self.convert_to_hr_mins(self.all_focus_time)), alignment=Qt.AlignmentFlag.AlignCenter) 

        # Styling to the text and numbers
        text_style = "color: #545E75; font-weight: bold; font-size: 25px; font-family: arial, roboto, sans-serif" 
        num_style = "color: #304D6D; font-weight: bold; font-size: 40px; font-family: arial, roboto, sans-serif"

        self.label_focus_time.setStyleSheet(text_style)
        self.label_all_focus_time.setStyleSheet(text_style)

        self.num_total_focus_time.setStyleSheet(num_style)
        self.num_all_focus_time.setStyleSheet(num_style)

        self.layout.addWidget(self.label_focus_time)
        self.layout.addWidget(self.num_total_focus_time)
        self.layout.insertSpacing(4, 25) 
        self.layout.addWidget(self.label_all_focus_time)
        self.layout.addWidget(self.num_all_focus_time)
        self.layout.insertSpacing(7, 25) 
        
        self.layout.addStretch()

    @error_handler
    @Slot()
    def update_num_timers(self, new_idx=0): # new_idx parameter does not matter as function will search for self.drop_down_tasks.currentIndex()
        logger.debug("Updating sum of timers")
        choices = [7, 30, 365]
        new_idx = self.drop_down_tasks.currentIndex()

        self.total_focus_time = AnalyseTodolist.get_sum_timers(choices[new_idx], 'focus')
        self.num_total_focus_time.setText(self.convert_to_hr_mins(self.total_focus_time))
        self.label_focus_time.setText(f"Total focus time \n{self.duration_dict[choices[new_idx]]}")

        self.all_focus_time = AnalyseTodolist.get_sum_all_timers('focus')
        self.num_all_focus_time.setText(self.convert_to_hr_mins(self.all_focus_time))

    def convert_to_hr_mins(self, seconds: int):
        hrs = seconds // 3600 
        mins = (seconds - hrs * 3600) // 60
        return f"{hrs} h {mins} mins" if hrs else f"{mins} mins"

class PomodoroPlots(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout = self.layout 

        # Drop down list for selecting plot duration 
        self.drop_down_choices = QComboBox()
        self.drop_down_choices.addItem("Daily")
        self.drop_down_choices.addItem("Weekly")
        self.drop_down_choices.addItem("Monthly")
        self.drop_down_choices.addItem("Yearly")
        self.drop_down_choices.setCurrentIndex(0)
        self.drop_down_choices.setToolTip("Plots the last 20 data points\nChanges the x-axis to plot by daily/weekly/monthly/yearly")
        self.drop_down_choices.setFixedWidth(100)
        self.layout.addWidget(self.drop_down_choices, alignment=Qt.AlignmentFlag.AlignCenter)
        self.drop_down_choices.currentIndexChanged.connect(self.update_plot)

        # Matplotlib graph for top 20 (default is weekly)
        self.graph = MatplotLibGraph()
        self.update_plot(0)
        toolbar = NavigationToolbar(self.graph, self)
        self.layout.addWidget(toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.graph)
        self.layout.setStretch(0, 0)
        self.layout.setStretch(1, 0)
        self.layout.setStretch(2, 1)

    @error_handler
    @Slot()
    def update_plot(self, idx=0):
        logger.debug("Updating pomodoro plot")
        option_chosen = ['day', 'week', 'month', 'year']
        idx = self.drop_down_choices.currentIndex()
        date_array, num_array = AnalyseTodolist.get_sum_focus_timers_by_time(option_chosen[idx])
        self.graph.axes.cla()
        self.graph.axes.plot(date_array, num_array, '-o')
        self.graph.axes.set_xlabel(option_chosen[idx].title())
        self.graph.axes.set_ylabel("Sum of focus timer completed")
        self.graph.axes.set_ylim(max(0, min(num_array)-1), max(num_array)+2)
        self.graph.axes.set_xticks(self.graph.axes.get_xticks())
        self.graph.axes.set_xticklabels(date_array, rotation=45, ha='right', rotation_mode='anchor')
        ax = self.graph.figure.gca()
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        for x, y in zip(date_array, num_array):
            if y: # don't display any labels if 0 mins 
                self.graph.axes.annotate(f"{CompletedTimers.convert_to_hr_mins(None, y*60)}", (x, y), textcoords='data', fontsize=12)
        self.graph.draw()

class AnalysePomodoroWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setLayout = self.layout 

        self.completed_timers = CompletedTimers()
        self.graph = PomodoroPlots()

        self.layout.addWidget(self.completed_timers, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.graph)
        self.layout.setStretch(0, 0)
        self.layout.setStretch(1, 1)
        self.setContentsMargins(50, 0, 0, 0)

class AnalyseTodolistWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setLayout = self.layout 

        self.completed_tasks = CompletedTasks()
        self.graph = TodolistPlots()

        self.layout.addWidget(self.completed_tasks, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.graph)
        self.layout.setStretch(0, 0)
        self.layout.setStretch(1, 1)
        self.setContentsMargins(50, 0, 0, 0)