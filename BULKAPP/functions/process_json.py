import tkinter as tk
from tkinter import messagebox
import os
import json
import re

def process_json():
    try:
        # Cargar el contenido de input.json
        with open(os.path.join('app', 'INPUT_JSON', 'input.json'), 'r') as file:
            data = json.load(file)

        new_data = []
        for item in data:
            url_field = "url" if "url" in item else "link"

            for size, tc in zip(item["sizes"], item["tcs"]):
                new_item = item.copy()
                new_item["sizes"] = [size]
                new_item["tcs"] = [tc]
                
                pattern = re.compile(r'(cmpint=adg_[a-zA-Z]{2}_[^_]+_)\d+x\d+')
                match = pattern.search(item[url_field])
                if match:
                    prefix = match.group(1)
                    new_url = pattern.sub(f"{prefix}{size}", item[url_field])
                    new_item[url_field] = new_url
                else:
                    new_item[url_field] = item[url_field]
                

                new_data.append(new_item)

        # Guardar los nuevos datos en civitatis_output.json
        output_path = os.path.join('app', 'INPUT_JSON', 'civitatis_output.json')
        with open(output_path, 'w') as file:
            json.dump(new_data, file, indent=4)

        # Copiar contenido de civitatis_output.json en input.json
        with open(output_path, 'r') as file:
            output_data = json.load(file)
        with open(os.path.join('app', 'INPUT_JSON', 'input.json'), 'w') as file:
            json.dump(output_data, file, indent=4)

        # Eliminar civitatis_output.json
        os.remove(output_path)

        messagebox.showinfo("Éxito", "Archivo JSON procesado y actualizado exitosamente.")

    except Exception as e:
        messagebox.showerror("Error", f"Error al procesar el archivo JSON: {e}")