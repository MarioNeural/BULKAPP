import tkinter as tk
from tkinter import messagebox
import re


def one_line_arrays(json_string):
    # Esta función reemplazará arrays multilinea con su versión en una línea
    def replace_array(match):
        # Tomamos el contenido del array y lo separamos por comas
        items = match.group(1).split(',')
        # Eliminamos espacios en blanco y nos quedamos con los elementos que no estén vacíos
        cleaned_items = [item.strip() for item in items if item.strip()]
        return '[' + ', '.join(cleaned_items) + ']'

    return re.sub(r'\[\s*((?:"[^"]+",?\s*)+)\]', replace_array, json_string)