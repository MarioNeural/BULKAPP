import time

class TimerUpdater:
    def __init__(self, app, time_label):
        self.app = app
        self.time_label = time_label
        self.last_execution_time = None

    def update_timer(self):
        if self.last_execution_time is not None:
            elapsed_time = time.time() - self.last_execution_time
            if elapsed_time < 60:
                self.time_label.config(text=f"Han pasado {int(elapsed_time)} segundos desde el último BULK")
            else:
                minutes = int(elapsed_time / 60)
                self.time_label.config(text=f"Han pasado {minutes} minutos desde el último BULK")
        self.app.after(1000, self.update_timer)

    def set_last_execution_time(self, time_value):
        self.last_execution_time = time_value