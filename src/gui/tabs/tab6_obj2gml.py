from PyQt5.QtWidgets import (
  QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFileDialog, QTextEdit, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt

import time
from datetime import datetime
import os
import tqdm
import sys
from tqdm import tqdm
from pathlib import Path

from src.core.obj2gml import Obj2GMLManager
from PyQt5.QtCore import QThread, pyqtSignal

class WorkerThread(QThread):
    progress = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, input_dir):
        super().__init__()
        self.input_dir = input_dir
        self.manager = Obj2GMLManager()

    def run(self):
        # We need to bridge the core callback to the signal
        # The RunObj2GML class in obj2gml_workflow supports a callback.
        # But Obj2GMLManager wraps it.
        # Let's verify Obj2GMLManager. It instantiates RunObj2GML.
        # I should have updated Obj2GMLManager to accept a callback!
        # For now, I'll bypass Manager wrapper if needed or update Manager.
        # Let's instantiate the lower level class directly if Manager is too simple?
        # Or better: Update Manager in next step. For now, use this structure.
        
        # Wait, I didn't update Manager to pass callback.
        # I will modify this file to use the Workflow class directly (since it has callback support now)
        # OR update the Manager. 
        # Using Workflow directly here is cleaner for GUI progress updates.
        
        from src.core.obj2gml_workflow import RunObj2GML
        
        def callback(msg):
            self.progress.emit(msg)
            
        converter = RunObj2GML(self.input_dir, progress_callback=callback)
        try:
             # RunObj2GML.run() is synchronous? Yes I removed QThread inheritance.
             converter.run() # This is the method I preserved/renamed? No I kept it as `run`.
             self.finished_signal.emit(True)
        except Exception as e:
             self.progress.emit(str(e))
             self.finished_signal.emit(False)

class Obj2GML(QWidget):
    def __init__(self):
        super().__init__()
        # UI components
        layout = QVBoxLayout()

        # ===== Input Building Footprint =====
        layout.addWidget(self._bold_label("Input the files directory"))

        self.input_dir = QLineEdit()
        self.btn_browse_dir = QPushButton("Browse")
        row1 = QHBoxLayout()
        row1.addWidget(self.input_dir)
        row1.addWidget(self.btn_browse_dir)
        layout.addLayout(row1)

        # ===== Process Button =====
        self.btn_process = QPushButton("Process")
        self.btn_process.setStyleSheet("font-weight: bold; font-size: 20px; padding: 10px;")
        self.btn_process.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Make button fill the width
        # Add button to a horizontal layout to make it stretch
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_process)
        button_layout.setStretch(0, 1)

        layout.addLayout(button_layout)
        # ===== Log Console =====
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        layout.addWidget(self.log_console)

        self.setLayout(layout)

        # Connect
        self.btn_browse_dir.clicked.connect(self.browse_dir)
        self.btn_process.clicked.connect(self.process)
    
    def process(self):
        if not self.input_dir.text():
            QMessageBox.warning(self, "Missing Input", "Please select the files directory!")
            return
        
        self.log_console.append("🚀 Starting process...")
        self.worker = WorkerThread(self.input_dir.text())
        self.worker.progress.connect(lambda msg: self.log_console.append(msg))
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()
        
    def on_finished(self, success):
        if success:
            QMessageBox.information(self, "Success", "Processing Completed!")
        else:
            QMessageBox.warning(self, "Failed", "Processing Failed!")

    def browse_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.input_dir.setText(folder)
            self.log_console.append(f"📁 Point Cloud selected: {folder}")
    
    def _bold_label(self, text):
        label = QLabel(f"<b>{text}</b>")
        return label

    def log_with_timestamp(self, message):
        """Print message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")