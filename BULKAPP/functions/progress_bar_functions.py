import tkinter as tk

class ProgressBarHandler:
    def __init__(self, app, canvas, square_size=30):
        self.app = app
        self.canvas = canvas
        self.square_size = square_size
        self.position = 0
        self.square = self.canvas.create_rectangle(0, 0, square_size, canvas.winfo_height(), fill="green")
        self.running = False
        self.canvas.grid_remove()  # Oculta el canvas inicialmente

    def start(self):
        self.running = True
        self.canvas.grid()  # Muestra el canvas
        self.move_square()

    def stop(self):
        self.running = False
        self.canvas.grid_remove()  # Oculta el canvas cuando se detiene

    def move_square(self):
        if not self.running:
            return
        
        # Mueve el cuadrado de izquierda a derecha y lo reinicia cuando sale del canvas
        self.position += 5
        if self.position > self.canvas.winfo_width():
            self.position = -self.square_size  # Reinicia la posición al salir del canvas

        # Actualiza la posición del cuadrado
        self.canvas.coords(self.square, self.position, 0, self.position + self.square_size, self.canvas.winfo_height())
        
        # Llama a esta función de nuevo después de un breve retraso para crear el efecto de animación
        self.app.after(30, self.move_square)
