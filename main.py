
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import numpy as np
import pyqtgraph as pg
from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QApplication, QMainWindow
import os
from os import path
import sys
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


FORM_CLASS, _ = loadUiType(path.join(path.dirname(__file__), "task1_design.ui"))


# Signal Object
class Signal:
    def __init__(self, file_name, file_path, data, color, graph, show):
        self.name = file_name
        self.path = file_path
        self.data = data
        self.color = color
        self.graph = graph
        self.show = show

    def __str__(self):
        return (f"Name: {self.name}, Path: {self.path}, Data: {self.data}, Color: {self.color}, Graph: {self.graph}, "
                f"Show: {self.show}")


class MainApp(QMainWindow, FORM_CLASS):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        QMainWindow.__init__(self)

        self.setupUi(self)
        self.button = self.findChild(QPushButton, "pushButton")
        self.setWindowTitle("Multi-Channel Signal Viewer")
        self.graphicsView1.getViewBox().setLimits(xMin=0)
        self.graphicsView2.getViewBox().setLimits(xMin=0)
        self.MAX1 = 1
        self.Max2 = 1
        self.MIN1 = 1
        self.MIN2 = 2



        # Initialize the graphs
        self.plotdata1 = []
        self.plotdata2 = []
        self.x1 = np.linspace(0, 10000, 10000)
        self.x2 = np.linspace(0, 10000, 10000)
        self.idx_1 = 0
        self.idx_2 = 0
        self.WINDOW_SZ = 250

        # Define Colors

        red = QColor("red")
        blue = QColor("blue")
        white = QColor("white")
        purple = QColor("purple")
        yellow = QColor("yellow")
        green = QColor("green")

        # Color Map
        self.color_map = {
            'red': red,
            'blue': blue,
            'white': white,
            'green': green,
            'yellow': yellow,
            'purple': purple,
        }

        # Color Stacks
        self.color_stack1 = [red, blue, purple, yellow, green, white]
        self.color_stack2 = [red, blue, purple, yellow, green, white]

        # Create a timer object
        self.timer1 = pg.QtCore.QTimer()
        self.timer2 = pg.QtCore.QTimer()

        # Pause & Play Buttons
        self.PlayButton1.clicked.connect(lambda: self.toggle_pause(1))
        self.PlayButton2.clicked.connect(lambda: self.toggle_pause(2))
        self.PlayButton1.setShortcut(QKeySequence('Ctrl+p'))

        # Rewind Buttons
        self.rewindButton1.clicked.connect(lambda: self.rewind(1))
        self.rewindButton2.clicked.connect(lambda: self.rewind(2))
        self.rewindButton1.setShortcut(QKeySequence('Ctrl+z'))

        # Set time intervals
        self.time_interval1 = 100
        self.time_interval2 = 100
        self.timer1.setInterval(self.time_interval1)  # set the timer to fire every "time_interval" ms
        self.timer2.setInterval(self.time_interval2)  # set the timer to fire every "time_interval" ms
        self.timer1.timeout.connect(lambda: self.update_fun(1))
        self.timer2.timeout.connect(lambda: self.update_fun(2))

        # Speed Buttons
        self.speedUp1.clicked.connect(self.Up1)
        self.speedUp2.clicked.connect(self.Up2)
        self.speedDown1.clicked.connect(self.Down1)
        self.speedDown2.clicked.connect(self.Down2)
        self.int_time_interval2 = self.time_interval2

        # Importing a Signal Button
        self.uploadButton.clicked.connect(self.upload)
        self.uploadButton.setShortcut(QKeySequence('Ctrl+i'))

        # Sync CheckBox
        self.syncCheckBox.stateChanged.connect(self.sync_fun)

        # Hide/Show
        self.showBox1.stateChanged.connect(lambda: self.show_fun(1))
        self.showBox2.stateChanged.connect(lambda: self.show_fun(2))

        # Changing Signal Properties
        self.comboBox1.currentTextChanged.connect(lambda: self.signal_prop(1))
        self.comboBox2.currentTextChanged.connect(lambda: self.signal_prop(2))
        self.editButton1.clicked.connect(lambda: self.signal_edit(1))
        self.editButton2.clicked.connect(lambda: self.signal_edit(2))

        # Control
        if self.plotdata1:
            max_length = max(len(data) for data in self.plotdata1)
            self.horizontalScrollBar.setRange(0, max(250, max_length))
        else:

            self.horizontalScrollBar.setRange(0, 250)
        if self.plotdata2:
            max_length = max(len(data) for data in self.plotdata2)
            self.horizontalScrollBar_2.setRange(0, max(250, max_length))
        else:
            self.horizontalScrollBar_2.setRange(0, 250)

        # Adding Limits for scrolling in the x-axis
        self.horizontalScrollBar.valueChanged.connect(lambda: self.scroll_graph(self.horizontalScrollBar.value(), 1))
        self.horizontalScrollBar_2.valueChanged.connect(lambda: self.scroll_graph(self.horizontalScrollBar_2.value(), 2))

        # ZOOM GRAPH 1
        self.ZoomInButton1.clicked.connect(lambda: self.zoomIn(1))
        self.ZoomInButton1.setShortcut(QKeySequence('Ctrl++'))
        self.ZoomOutButton1.clicked.connect(lambda: self.zoomOut(1))
        self.ZoomOutButton1.setShortcut(QKeySequence('Ctrl+-'))

        # ZOOM GRAPH 2
        self.ZoomInButton2.clicked.connect(lambda: self.zoomIn(2))
        self.ZoomOutButton2.clicked.connect(lambda: self.zoomOut(2))

        # EXPORT
        self.snap1.clicked.connect(lambda: self.capture(1))
        self.snap2.clicked.connect(lambda: self.capture(2))
        self.screenshots1 = []
        self.screenshots2 = []

        self.exportButton.clicked.connect(self.export_to_pdf)
        self.exportButton.setShortcut(QKeySequence('Ctrl+e'))

        # PANNING
        self.graphicsView1.getViewBox().setMouseEnabled(x=False, y=True)
        self.graphicsView2.getViewBox().setMouseEnabled(x=False, y=True)
        self.graphicsView1.getViewBox().setLimits(yMin=0)
        self.graphicsView1.getViewBox().setLimits(yMax=1)
        self.graphicsView2.getViewBox().setLimits(yMin=0)
        self.graphicsView2.getViewBox().setLimits(yMax=1)

        self.current_zoom1 = 1.0
        self.current_zoom2 = 1.0
        self.max_zoom_factor = 2.0
        self.min_zoom_factor = 1.0

    # Class Functions
    def sync_fun(self):

        if self.syncCheckBox.isChecked():

            if (not self.timer1.isActive()) and (self.timer2.isActive()):
                self.timer2.start()
                self.timer1.start()

            self.graphicsView1.enableAutoRange()
            self.graphicsView2.enableAutoRange()

            self.time_interval2 = self.time_interval1

            if self.timer1.isActive():
                self.timer1.stop()
                self.timer1.setInterval(int(self.time_interval1))
                self.timer1.start()

            if self.timer2.isActive():
                self.timer2.stop()
                self.timer2.setInterval(int(self.time_interval2))
                self.timer2.start()
        else:
            self.time_interval2 = self.int_time_interval2

            if self.timer2.isActive():
                self.timer2.stop()
                self.timer2.setInterval(int(self.time_interval2))
                self.timer2.start()

    def reset(self, graph):
        if graph == 1:
            self.frame_2.setEnabled(False)
            self.lineEdit1.setText('')
            self.colorBox1.setCurrentIndex(-1)
            self.graphicsView1.clear()
        else:
            self.frame_3.setEnabled(False)
            self.lineEdit2.setText('')
            self.colorBox2.setCurrentIndex(-1)
            self.graphicsView2.clear()

    def toggle_signal(self, graph):

        if graph == 1:
            if self.toggle1_1.isChecked():
                return
            else:

                for signal in self.plotdata1:

                    if signal.name == self.comboBox1.currentText():
                        signal.graph = 2

                        # Remove and Add to Arrays
                        self.plotdata2.append(signal)
                        self.plotdata1.remove(signal)
                        if len(self.plotdata1) == 0:
                            self.reset(1)

                        self.enable_settings(2)

                        # Remove Signal Prop
                        self.comboBox1.removeItem(self.comboBox1.currentIndex())
                        self.comboBox2.addItem(signal.name)
        else:
            if self.toggle2_2.isChecked():
                return
            else:

                for signal in self.plotdata2:
                    if signal.name == self.comboBox2.currentText():
                        signal.graph = 1

                        # Remove and Add to Arrays
                        self.plotdata1.append(signal)
                        self.plotdata2.remove(signal)
                        if len(self.plotdata2) == 0:
                            self.reset(2)

                        self.enable_settings(1)

                        # Remove Signal Prop
                        self.comboBox2.removeItem(self.comboBox2.currentIndex())
                        self.comboBox1.addItem(signal.name)

    def get_color_name(self, signal):
        for key, val in self.color_map.items():
            if val == signal.color:
                color_name = key
                return color_name

    # Enables the Widgets & start the Timers
    def enable_settings(self, graph):
        if graph == 1:
            self.timer1.start(self.time_interval1)
            self.signal_prop(1)
            self.frame_2.setEnabled(True)
            self.comboBox1.setEnabled(True)
        else:
            self.timer2.start(self.time_interval2)
            self.signal_prop(2)
            self.frame_3.setEnabled(True)
            self.comboBox2.setEnabled(True)

    def upload(self):

        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        filters = "CSV and DAT Files (*.csv *.dat)"
        file_path, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileNames()", "", filters, options=options)

        if file_path:
            file_name = os.path.basename(file_path)
            data = np.fromfile(file_path, dtype=np.int16)

            show = True
            if self.radioButton1.isChecked():
                graph = 1
                color = self.color_stack1.pop()
                self.ImportLabel.setText(f'{file_name}')

                signal = Signal(file_name, file_path, data, color, graph, show)
                if self.plotdata1:
                    for sign in self.plotdata1:
                        if sign.name != file_name:
                            self.plotdata1.append(signal)
                            self.comboBox1.addItem(f"{file_name}")
                else:
                    self.plotdata1.append(signal)
                    self.comboBox1.addItem(f"{file_name}")
                self.enable_settings(1)

            elif self.radioButton2.isChecked():
                graph = 2
                color = self.color_stack2.pop()
                self.ImportLabel.setText(f'{file_name}')

                signal = Signal(file_name, file_path, data, color, graph, show)

                if self.plotdata2:
                    for sig in self.plotdata2:
                        if sig.name != file_name:
                            self.plotdata2.append(signal)
                            self.comboBox2.addItem(f"{file_name}")
                else:
                    self.plotdata2.append(signal)
                    self.comboBox2.addItem(f"{file_name}")
                self.enable_settings(2)

            else:
                graph = 3

                color = self.color_stack1.pop()
                color2 = self.color_stack2.pop()
                self.ImportLabel.setText(f'{file_name}')

                signal1 = Signal(file_name, file_path, data, color, graph, show)
                signal2 = Signal(file_name, file_path, data, color2, graph, show)

                if self.plotdata1:
                    for sig in self.plotdata1:
                        if sig.name != file_name:
                            self.plotdata1.append(signal1)
                            self.comboBox1.addItem(f"{file_name}")
                else:
                    self.plotdata1.append(signal1)
                    self.comboBox1.addItem(f"{file_name}")

                if self.plotdata2:
                    for sig in self.plotdata2:
                        if sig.name != file_name:
                            self.plotdata2.append(signal2)

                            self.comboBox2.addItem(f"{file_name}")
                else:
                    self.plotdata2.append(signal2)

                    self.comboBox2.addItem(f"{file_name}")

                self.enable_settings(1)
                self.enable_settings(2)

    def update_fun(self, graph):
        if graph == 1:
            x_min = self.idx_1
            x_max = min(len(self.x1), self.idx_1 + self.WINDOW_SZ)
            self.graphicsView1.setXRange(x_min, x_max)

            for signal in self.plotdata1:
                data = signal.data[x_min:x_max]
                mx = max(data)
                mn = min(data)
                if mx > self.MAX1:
                    self.MAX1 = mx
                elif mn < self.MIN1:
                    self.MIN1 = mn
                plot_item = self.graphicsView1.plot(pen=signal.color)
                plot_item.setData(self.x1[x_min:x_max], data)

                self.graphicsView1.getViewBox().setLimits(yMin=self.MIN1, yMax=self.MAX1)

                if signal.show:  # Check the visibility state
                    plot_item.setVisible(True)
                else:
                    plot_item.setVisible(False)

            self.idx_1 += 1
            if self.idx_1 >= len(self.x1):
                self.idx_1 = 0

        else:
            x_min = self.idx_2
            x_max = min(len(self.x2), self.idx_2 + self.WINDOW_SZ)
            self.graphicsView2.setXRange(x_min, x_max)

            for signal in self.plotdata2:
                data = signal.data[x_min:x_max]
                mx = max(data)
                mn = min(data)
                if mx > self.Max2:
                    self.Max2 = mx
                elif mn < self.MIN2:
                    self.MIN2 = mn
                plot_item = self.graphicsView2.plot(pen=signal.color)
                plot_item.setData(self.x2[x_min:x_max], data)

                self.graphicsView2.getViewBox().setLimits(yMin=self.MIN2, yMax=self.Max2)
                if signal.show:  # Check the visibility state
                    plot_item.setVisible(True)
                else:
                    plot_item.setVisible(False)

            self.idx_2 += 1
            if self.idx_2 >= len(self.x2):
                self.idx_2 = 0

    def show_fun(self, graph):
        if graph == 1:
            for signal in self.plotdata1:
                if signal.name == self.comboBox1.currentText():
                    if self.showBox1.isChecked():
                        signal.show = True
                    else:
                        signal.show = False
        else:
            for signal in self.plotdata2:
                if signal.name == self.comboBox2.currentText():
                    if self.showBox2.isChecked():
                        signal.show = True
                    else:
                        signal.show = False

    def signal_prop(self, graph):
        if graph == 1:
            for signal in self.plotdata1:
                if signal.name == self.comboBox1.currentText():
                    # Adjust LineEdit
                    self.lineEdit1.setText(f"{signal.name}")

                    # Adjust Show/Hide CheckBox
                    if signal.show:
                        self.showBox1.setChecked(True)
                    else:
                        self.showBox1.setChecked(False)

                    # Adjust Color comboBox
                    color = self.get_color_name(signal)
                    self.colorBox1.setCurrentText(color)
        else:
            for signal in self.plotdata2:
                if signal.name == self.comboBox2.currentText():
                    # Adjust LineEdit
                    self.lineEdit2.setText(f"{signal.name}")

                    # Adjust Show/Hide CheckBox
                    if signal.show:
                        self.showBox2.setChecked(True)
                    else:
                        self.showBox2.setChecked(False)

                    # Adjust Color comboBox
                    color = self.get_color_name(signal)
                    self.colorBox2.setCurrentText(color)

    def signal_edit(self, graph):

        if graph == 1:
            for signal in self.plotdata1:
                if signal.name == self.comboBox1.currentText():

                    # EDIT COLOR
                    color = self.colorBox1.currentText()
                    signal.color = self.color_map[color]

                    # EDIT NAME
                    signal.name = self.lineEdit1.text()
                    index = self.comboBox1.currentIndex()
                    self.comboBox1.setItemText(index, signal.name)

                    # EDIT GRAPH
                    self.toggle_signal(1)
                    self.toggle1_1.setChecked(True)

        else:
            for signal in self.plotdata2:
                if signal.name == self.comboBox2.currentText():
                    # EDIT COLOR
                    color = self.colorBox2.currentText()
                    signal.color = self.color_map[color]

                    # EDIT NAME
                    signal.name = self.lineEdit2.text()
                    index = self.comboBox2.currentIndex()
                    self.comboBox2.setItemText(index, signal.name)

                    # EDIT COLOR
                    signal.color = self.color_map[color]

                    # EDIT GRAPH
                    self.toggle_signal(2)
                    self.toggle2_2.setChecked(True)

    def toggle_pause(self, graph):
        if graph == 1:
            if self.timer1.isActive():
                self.timer1.stop()
            else:
                self.timer1.start()

            if self.syncCheckBox.isChecked():
                if self.timer1.isActive():
                    self.timer2.start()

                else:
                    self.timer2.stop()
        else:
            if self.timer2.isActive():
                self.timer2.stop()
            else:
                self.timer2.start()

            if self.syncCheckBox.isChecked():
                if self.timer2.isActive():
                    self.timer1.start()

                else:
                    self.timer1.stop()

    def rewind(self, graph):
        if graph == 1:
            self.graphicsView1.clear()
            self.idx_1 = 0
            if self.syncCheckBox.isChecked():
                self.graphicsView2.clear()
                self.idx_2 = 0
        else:
            self.graphicsView2.clear()
            self.idx_2 = 0
            if self.syncCheckBox.isChecked():
                self.graphicsView1.clear()
                self.idx_1 = 0

    def Up1(self):
        if self.time_interval1 > 1:
            self.time_interval1 /= 10
            if self.timer1.isActive():
                self.timer1.setInterval(int(self.time_interval1))

            if self.syncCheckBox.isChecked():
                self.sync_fun()

        else:
            return

    def Up2(self):
        if self.time_interval2 > 1:
            self.time_interval2 /= 10
            self.int_time_interval2 = self.time_interval2
            if self.timer2.isActive():
                self.timer2.setInterval(int(self.time_interval2))

            if self.syncCheckBox.isChecked():
                self.sync_fun()
        else:
            return

    def Down1(self):
        if self.time_interval1 < 10000:
            self.time_interval1 *= 10
            if self.timer1.isActive():
                self.timer1.stop()
                self.timer1.setInterval(int(self.time_interval1))
                self.timer1.start()

            if self.syncCheckBox.isChecked():
                self.sync_fun()

        else:
            return

    def Down2(self):
        if self.time_interval1 < 10000:
            self.time_interval1 *= 10
            self.int_time_interval2 = self.time_interval2
            if self.timer2.isActive():
                self.timer2.setInterval(int(self.time_interval2))

            if self.syncCheckBox.isChecked():
                self.sync_fun()
        else:
            return

    def scroll_graph(self, position, graph):
        if graph == 1:
            x_min = max(0, position - self.WINDOW_SZ // 4)
            x_max = min(len(self.x1), x_min + self.WINDOW_SZ)
            self.graphicsView1.setXRange(x_min, x_max)
        else:
            x2_min = max(0, position - self.WINDOW_SZ // 4)
            x2_max = min(len(self.x2), x2_min + self.WINDOW_SZ)
            self.graphicsView2.setXRange(x2_min, x2_max)

    def zoomIn(self, graph):

        if graph == 1:
            zoom_factor = 0.8
            if self.current_zoom1 < self.max_zoom_factor:
                self.graphicsView1.getViewBox().scaleBy((zoom_factor, zoom_factor))
                self.current_zoom1 += 0.25

            if self.syncCheckBox.isChecked():
                self.graphicsView1.getViewBox().scaleBy((zoom_factor, zoom_factor))
        else:
            zoom_factor = 0.8
            if self.current_zoom2 < self.max_zoom_factor:
                self.graphicsView2.getViewBox().scaleBy((zoom_factor, zoom_factor))
                self.current_zoom2 += 0.25

            if self.syncCheckBox.isChecked():
                self.graphicsView2.getViewBox().scaleBy((zoom_factor, zoom_factor))

    def zoomOut(self, graph):
        if graph == 1:
            zoom_factor = 1.2
            if self.current_zoom1 > self.min_zoom_factor:
                self.graphicsView1.getViewBox().scaleBy((zoom_factor, zoom_factor))
                self.current_zoom1 -= 0.25
            if self.syncCheckBox.isChecked():
                self.graphicsView2.getViewBox().scaleBy((zoom_factor, zoom_factor))
        else:
            zoom_factor = 1.2
            if self.current_zoom2 > self.min_zoom_factor:
                self.graphicsView2.getViewBox().scaleBy((zoom_factor, zoom_factor))
                self.current_zoom2 -= 0.25
            if self.syncCheckBox.isChecked():
                self.graphicsView1.getViewBox().scaleBy((zoom_factor, zoom_factor))

    def calculate_statistics(self, graph):

        if graph == 1:

            statistics = []
            mean = []
            std_dev = []
            minimum = []
            maximum = []
            statistics.append(["Signal Number:", "Mean", "Std_dev", "Minimum", "Maximum"])
            for signal in self.plotdata1:
                mean.append(np.mean(signal.data))
                std_dev.append(np.std(signal.data))
                minimum.append(np.min(signal.data))
                maximum.append(np.max(signal.data))

            for j in range(len(self.plotdata1)):
                statistics.append([j+1, round(mean[j]), round(std_dev[j]), round(minimum[j]), round(maximum[j])])
            stats = Table(statistics)

            return stats
        else:
            statistics2 = []
            mean2 = []
            std_dev2 = []
            minimum2 = []
            maximum2 = []
            statistics2.append(["Signal Number:", "Mean", "Std_dev", "Minimum", "Maximum"])

            for signal in self.plotdata2:
                mean2.append(np.mean(signal.data))
                std_dev2.append(np.std(signal.data))
                minimum2.append(np.min(signal.data))
                maximum2.append(np.max(signal.data))

            for j in range(len(self.plotdata2)):
                statistics2.append([j + 1, round(mean2[j]), round(std_dev2[j]), round(minimum2[j]), round(maximum2[j])])
            stats2 = Table(statistics2)

            return stats2

    def capture(self, graph):
        if graph == 1:
            frame_to_capture1 = self.graphicsView1
            screenshot = frame_to_capture1.grab()
            self.screenshots1.append(screenshot)
        else:
            frame_to_capture2 = self.graphicsView2
            screenshot = frame_to_capture2.grab()
            self.screenshots2.append(screenshot)

    def export_to_pdf(self, output_pdf_path):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")

        if file_path:
            report = canvas.Canvas(file_path, pagesize=letter)
            report.setFont("Helvetica", 12)
            if self.screenshots1:
                # Draw some text on the PDF
                report.drawString(100, 750, "Graph 1")
                aspectRatio = 3

                # Initialize variables for positioning and page management
                max_height = 700  # Maximum vertical height for content on a page
                current_y = 700  # Initial y-coordinate

                # Add the first screenshot to the initial page
                screenshot_path = "screenshot0.png"
                self.screenshots1[0].save(screenshot_path, "PNG")
                report.drawImage(screenshot_path, 100, current_y - 100, width=400, height=133)
                current_y -= 110

                # Iterate through the remaining screenshots
                for idx in range(1, len(self.screenshots1)):
                    screenshot = self.screenshots1[idx]
                    screenshot_path = f"screenshot{idx}.png"
                    screenshot.save(screenshot_path, "PNG")
                    # screenshot_width, screenshot_height = screenshot.width(), screenshot.height()
                    screenshot_width, screenshot_height = 400, 133

                    # Check if adding the screenshot would exceed the page height
                    if current_y - screenshot_height < 50:
                        report.showPage()
                        current_y = 750  # Reset to the top of the new page

                        # Draw the screenshot on the current page
                    report.drawImage(screenshot_path, 100, current_y - screenshot_height, width=screenshot_width,
                                     height=screenshot_height)
                    current_y -= screenshot_height + 10

                table = self.calculate_statistics(1)
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header row background color
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align all cells
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Header bottom padding
                    ('BACKGROUND', (0, 1), (-1, -1), colors.ghostwhite),  # Data row background color
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)  # Table grid color and width
                ])
                table.setStyle(style)
                table_height1 = table.wrapOn(report, 0, 0)[1]
                if current_y - table_height1 < 20:
                    report.showPage()
                    table_y = 750
                table.drawOn(report, 150, current_y - table_height1)

            if self.screenshots2:
                if self.screenshots1:
                    report.showPage()
                    current_y = 700

                # Draw some text on the PDF
                report.drawString(100, 750, "Graph 2")
                aspectRatio = 3

                # Initialize variables for positioning and page management
                max_height = 700  # Maximum vertical height for content on a page
                # current_y = 700  # Initial y-coordinate

                # Add the first screenshot to the initial page
                screenshot_path = "screenshot2_0.png"
                self.screenshots2[0].save(screenshot_path, "PNG")
                report.drawImage(screenshot_path, 100, current_y - 100, width=400, height=133)
                current_y -= 110

                # Iterate through the remaining screenshots
                for idx in range(1, len(self.screenshots2)):
                    screenshot = self.screenshots2[idx]
                    screenshot_path = f"screenshot2_{idx}.png"
                    screenshot.save(screenshot_path, "PNG")
                    # screenshot_width, screenshot_height = screenshot.width(), screenshot.height()
                    screenshot_width, screenshot_height = 400, 133

                    # Check if adding the screenshot would exceed the page height
                    if current_y - screenshot_height < 50:
                        report.showPage()
                        current_y = 750  # Reset to the top of the new page

                        # Draw the screenshot on the current page
                    report.drawImage(screenshot_path, 100, current_y - screenshot_height, width=screenshot_width,
                                     height=screenshot_height)
                    current_y -= screenshot_height + 10

                table = self.calculate_statistics(2)
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header row background color
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align all cells
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Header bottom padding
                    ('BACKGROUND', (0, 1), (-1, -1), colors.ghostwhite),  # Data row background color
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)  # Table grid color and width
                ])
                table.setStyle(style)
                table_height = table.wrapOn(report, 0, 0)[1]
                if current_y - table_height < 20:
                    report.showPage()
                    table_y = 750
                table.drawOn(report, 150, current_y - table_height)

            report.save()
            self.screenshots2.clear()
            self.screenshots1.clear()

def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
