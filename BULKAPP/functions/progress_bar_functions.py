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
        if self.script_running:
            file_size = self.get_file_size()
        
            if file_size < 1000: 
                interval = 20
            elif file_size < 3000:
                interval = 60
            elif file_size < 6000:
                interval = 120
            elif file_size < 10000:
                interval = 200
            elif file_size < 15000:
                interval = 300
            elif file_size < 20000:
                interval = 400
            else:  
                interval = 500
    
            if self.progress_bar['value'] < 80:
                new_value = self.progress_bar['value'] + 1
                self.progress_bar['value'] = new_value
                self.app.after(interval, self.update_progress_bar)
            elif self.progress_bar['value'] < 99:
                new_value = self.progress_bar['value'] + 1
                self.progress_bar['value'] = new_value
                self.app.after(500, self.update_progress_bar)
            elif self.script_running and self.progress_bar['value'] == 99:
                self.app.after(500, self.update_progress_bar)

    def start_progress_bar(self):
        self.script_running = True
        self.progress_bar['value'] = 0
        self.update_progress_bar()

    # Puedes agregar aquí otros métodos si son necesarios
