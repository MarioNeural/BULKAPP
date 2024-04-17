import tkinter as tk
import os
from tkinter import ttk

class ProgressBarHandler:
    def __init__(self, app, progress_bar):
        self.app = app
        self.progress_bar = progress_bar
        self.script_running = False

    def get_file_size(self):
        filepath = 'app/INPUT_JSON/input.json' 
        if os.path.isfile(filepath):
            return os.path.getsize(filepath)
        else:
            return 0

    def update_progress_bar(self):
        if not self.script_running:
            return 

        file_size = self.get_file_size()
        if file_size == 0:
            return

        interval = max(file_size / 50, 20) 

        if self.progress_bar['value'] < 99:
            new_value = self.progress_bar['value'] + 1
            self.progress_bar['value'] = new_value
            self.app.after(int(interval), self.update_progress_bar)
        else:
            self.stop_progress_bar()

    def start_progress_bar(self):
        self.script_running = True
        self.progress_bar['value'] = 0
        self.update_progress_bar()

    def stop_progress_bar(self):
        self.script_running = False
        self.progress_bar['value'] = 100
