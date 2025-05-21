from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QSizePolicy
from PySide6.QtCore import Qt, Slot

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
#from matplotlib.figure import Figure 
from matplotlib.ticker import MaxNLocator

from src.db import AnalyseTodolist

matplotlib.use("QtAgg")
plt.style.use("seaborn-v0_8-darkgrid")

class CompletedTasks(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout = self.layout 

        self.drop_down_tasks = QComboBox()
        self.drop_down_tasks.addItem("Last 7 days")
        self.drop_down_tasks.addItem("Last 30 days")
        self.drop_down_tasks.addItem("Last 365 days")
        self.drop_down_tasks.setCurrentIndex(1)
        self.drop_down_tasks.currentIndexChanged.connect(self.update_num_task)
        self.drop_down_tasks.setToolTip("Show number of tasks completed in the last x days")
        self.drop_down_tasks.setFixedWidth(100)
        self.layout.addWidget(self.drop_down_tasks, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.insertSpacing(1, 20)

        # dictionary to store the text for the various time frame chosen 
        self.duration_dict = {7: "in the last 7 days", 30: "in the last 30 days", 365: "in the last 365 days", 'x': "in the last x days", 
                         "custom": "from start_date to end_date"}

        # labels to display, default to show last 30 days 
        self.all_completed_tasks = QLabel("All Completed Tasks", alignment=Qt.AlignmentFlag.AlignCenter)
        self.completed_tasks = QLabel(f"Completed Tasks\n{self.duration_dict[30]}", alignment=Qt.AlignmentFlag.AlignCenter)
        self.num_all_completed_tasks = QLabel(str(AnalyseTodolist.get_num_all_completed_tasks()), alignment=Qt.AlignmentFlag.AlignCenter) 
        self.num_completed_tasks = QLabel(str(AnalyseTodolist.get_num_completed_tasks(30)), alignment=Qt.AlignmentFlag.AlignCenter) 

        # Styling to the text and numbers
        text_style = "color: #545E75; font-weight: bold; font-size: 25px; font-family: arial, roboto, sans-serif" 
        num_style = "color: #304D6D; font-weight: bold; font-size: 40px; font-family: arial, roboto, sans-serif"

        self.all_completed_tasks.setStyleSheet(text_style)
        self.completed_tasks.setStyleSheet(text_style)
        self.num_all_completed_tasks.setStyleSheet(num_style)
        self.num_completed_tasks.setStyleSheet(num_style)

        self.layout.addWidget(self.completed_tasks)
        self.layout.addWidget(self.num_completed_tasks)
        self.layout.insertSpacing(4, 50) 
        self.layout.addWidget(self.all_completed_tasks)
        self.layout.addWidget(self.num_all_completed_tasks)
        
        self.layout.addStretch()

    @Slot()
    def update_num_task(self, new_idx=1):
        choices = [7, 30, 365]
        new_idx = self.drop_down_tasks.currentIndex()
        self.num_completed_tasks.setText(str(AnalyseTodolist.get_num_completed_tasks(choices[new_idx])))
        self.num_all_completed_tasks.setText(str(AnalyseTodolist.get_num_all_completed_tasks()))
        self.completed_tasks.setText(f"Completed Tasks\n{self.duration_dict[choices[new_idx]]}")

class MatplotLibGraph(FigureCanvasQTAgg):
    def __init__(self, width=5, height=5, dpi=100):
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
        self.drop_down_choices.setCurrentIndex(1)
        self.drop_down_choices.setToolTip("Plots the last 20 data points\nChanges the x-axis to plot by daily/weekly/monthly/yearly")
        self.drop_down_choices.setFixedWidth(100)
        self.layout.addWidget(self.drop_down_choices, alignment=Qt.AlignmentFlag.AlignCenter)
        self.drop_down_choices.currentIndexChanged.connect(self.update_plot)

        # Matplotlib graph for top 20 (default is weekly)
        self.graph = MatplotLibGraph()
        self.update_plot(1)
        toolbar = NavigationToolbar(self.graph, self)
        self.layout.addWidget(toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.graph)
        self.layout.setStretch(0, 0)
        self.layout.setStretch(1, 0)
        self.layout.setStretch(2, 1)

        

    @Slot()
    def update_plot(self, idx=1):
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
        #self.graph.axes.tick_params(axis='x', labelrotation=45)
        ax = self.graph.figure.gca()
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        for x, y in zip(date_array, num_array):
            self.graph.axes.annotate(f"{y}", (x, y), textcoords='data', fontsize=12)
        self.graph.draw()

        
        

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