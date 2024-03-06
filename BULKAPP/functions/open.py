import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import webbrowser

FOLDER_PATH = os.path.join("app")


def open_folder():
    try:
        os.startfile(FOLDER_PATH)
    except Exception as e:
        messagebox.showerror("Error", f"Error al abrir la carpeta: {e}")



def open_json_with_vscode():
    json_file_path = os.path.abspath(os.path.join('app', 'INPUT_JSON', 'input.json'))
    try:
        # Ruta al ejecutable de VSCode
        vscode_path = r"C:\Users\usuario\AppData\Local\Programs\Microsoft VS Code\Code.exe"

        # Ejecutar VSCode con el archivo JSON
        subprocess.run([vscode_path, json_file_path], check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")



def open_test_html():
    # Construir la ruta absoluta al archivo
    file_path = os.path.abspath(os.path.join('app', 'HTML', 'test.html'))
    
    # Imprimir la ruta para depuración
    print(f"Ruta absoluta al archivo test.html: {file_path}")

    # Verificar si el archivo existe
    if not os.path.exists(file_path):
        print("El archivo test.html no existe en la ruta proporcionada.")
        messagebox.showerror("Error", "El archivo test.html no se encuentra.")
        return

    # Formatear la ruta del archivo para la URL
    formatted_path = file_path.replace("\\", "/") if os.name == 'nt' else file_path

    # Crear la URL
    url = f'file:///{formatted_path}'

    # Intentar abrir el archivo en el navegador
    webbrowser.open(url)