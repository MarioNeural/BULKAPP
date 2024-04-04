import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import subprocess
import time
import json
import re
import shutil
import threading

# FUNCIONES
from functions.process_json import process_json
from functions.one_line_arrays import one_line_arrays

from functions.timer_functions import TimerUpdater
from functions.progress_bar_functions import ProgressBarHandler

from functions.open import open_test_html, open_folder, open_json_with_vscode


# ESTILOS
from styles.styles import DARK_GREEN, LIGHT_GREEN, TEXT_BLACK, TEXT_WHITE, RED, BLUE

FOLDER_PATH = os.path.join("app")


def extract_data_from_rows(data):
    lines = data.split("\n")
    
    if len(lines) < 2:
        return []

    headers = lines[0].split("\t")
    for col in ["Size", "Trackingcode Id", "Trackingcode", "URL", "URL Final"]:
        if col not in headers:
            messagebox.showerror("Error", f"Falta la columna '{col}' en los datos.")
            return []

    size_index = headers.index("Size")
    tc_index = headers.index("Trackingcode Id")
    name_index = headers.index("Trackingcode")
    landing_index = headers.index("URL")
    link_index = headers.index("URL Final")
    
    temp_dict = {}

    for line in lines[1:]:
        if line:
            values = line.split("\t")
            current_size = values[size_index]
            current_tc = values[tc_index]
            current_name = "_".join(values[name_index].split("_")[:-1]).strip()

            if not current_name:
                continue

            current_landing = values[landing_index]
            current_link = re.sub(r'&tc_alt.*$', '', values[link_index])

            if current_name in temp_dict:
                temp_dict[current_name]['sizes'].append(current_size)
                temp_dict[current_name]['tcs'].append(current_tc)
            else:
                temp_dict[current_name] = {
                    'sizes': [current_size],
                    'tcs': [current_tc],
                    'line': line,
                    'landing': current_landing,
                    'link': current_link
                }

    all_results = [
    generate_object(value['sizes'], value['tcs'], value['line'], key, value['landing'], value['link'], name_index)
    for key, value in temp_dict.items()
]
    return all_results


def generate_object(sizes, tcs, line, key, landing, link, name_index):
    values = line.split("\t")

    url_match = re.search(r'(?<!"|\')https?://[^\s<>"\']+(?<!["\'])', line)
    if url_match:
        landing = url_match.group(0)

    utm_content_pattern = r'(&utm_content=([a-zA-Z_]*?)\d*x\d*)'
    match = re.search(utm_content_pattern, link)
    if match:
        prefix = match.group(2)
        link = re.sub(utm_content_pattern, '', link)
        add_utm_size = f"utm_content={prefix}"
    else:
        add_utm_size = None

    aws_path_1 = ""
    aws_path_2 = ""
    link = re.sub(r'&tc_alt.*$', '', link)
    viewability = ""
    if include_viewability.get():
        script_match = re.search(r'<script.*?src="([^"]+)', line)
        if script_match:
            viewability_url = script_match.group(1)
            viewability = re.sub(r'\d{6}.*$', '', viewability_url)

    if link_type.get() == "iframe":
        result_obj = {
            "type": "iframe",
            "sizes": sizes,
            "tcs": tcs,
            "name": "_".join(values[name_index].split("_")[:-1]).strip(),
            "landing": landing,
            "aws_path_1": aws_path_1,
            "aws_path_2": aws_path_2,
            "link": link 
        }
    else:
        result_obj = {
            "type": "link",
            "sizes": sizes,
            "tcs": tcs,
            "name": "_".join(values[name_index].split("_")[:-1]).strip(),
            "landing": landing,
            "aws_path_1": aws_path_1,
            "aws_path_2": aws_path_2,
            "url": link 
        }



    if include_viewability.get():
        result_obj["viewability"] = viewability

    if add_utm_size:
        result_obj["add_utm_size"] = add_utm_size

    return result_obj


def save_json(json_data):
    try:
        json_output = json.dumps(json_data, indent=4)
        
        json_output = one_line_arrays(json_output)

        output_folder = os.path.join('app', 'INPUT_JSON')
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        file_path = os.path.join(output_folder, 'input.json')

        with open(file_path, 'w') as f:
            f.write(json_output)

    except Exception as e:
        messagebox.showerror("Error", f"Error al guardar los datos: {e}")
    finally:
        input_window.destroy()


def show_object_window(json_data, index=0):
    def process_current_object():
        aws_path_1_entry_value = aws_path_1_entry.get()
        aws_path_2_entry_value = aws_path_2_entry.get()
        if not aws_path_1_entry_value:
            messagebox.showwarning("Atención", "Debes introducir un valor para aws_path_1")
            return

        aws_path_1_entry_value = aws_path_1_entry_value.replace("s3://adgravity/", "")

        json_data[index]['aws_path_1'] = aws_path_1_entry_value
        json_data[index]['aws_path_2'] = aws_path_2_entry_value
        object_window.destroy()
        if index + 1 < len(json_data):
            show_object_window(json_data, index+1)
        else:
            save_json(json_data)

    object_window = tk.Toplevel(app, bg=DARK_GREEN)
    object_window.geometry("1000x400")
    object_window.title(f"Objeto {index+1} de {len(json_data)}")

    obj_text = tk.Text(object_window, height=13, width=120, bg=LIGHT_GREEN, fg=TEXT_BLACK)
    obj_text.pack(pady=10)
    formatted_json = one_line_arrays(json.dumps(json_data[index], indent=4))
    obj_text.insert(tk.END, formatted_json)

    lbl_instruction = tk.Label(object_window, text="Introduce ruta de aws, ej: s3://adgravity/mundo_pacifico/2023/10/halloween/", bg=DARK_GREEN, fg=TEXT_BLACK)
    lbl_instruction.pack(pady=5)

    aws_path_1_entry = tk.Entry(object_window, width=60, bg=DARK_GREEN, fg=TEXT_BLACK)
    aws_path_1_entry.pack(pady=10)

    aws_path_2_lbl = tk.Label(object_window, text="AWS Path 2:", bg=LIGHT_GREEN, fg=TEXT_BLACK)
    aws_path_2_lbl.pack(pady=5)
    
    aws_path_2_entry = tk.Entry(object_window, width=60, bg=DARK_GREEN, fg=TEXT_BLACK)
    if link_type.get() == "iframe":
        aws_path_2_entry.insert(0, "/index.html")
    aws_path_2_entry.pack(pady=10)

    btn_next = tk.Button(object_window, text="Siguiente", command=process_current_object, bg=LIGHT_GREEN, fg=TEXT_BLACK)
    btn_next.pack(pady=5)


def process_data(input_data):
    try:
        data = input_data.get("1.0", tk.END)
        json_data = extract_data_from_rows(data)
        show_object_window(json_data)
    except Exception as e:
        messagebox.showerror("Error", f"Error al procesar los datos: {e}")
    finally:
        input_window.destroy()

def show_input_window():
    global input_window, link_type
    input_window = tk.Toplevel(app, bg=DARK_GREEN)
    input_window.title("Introducir datos")

    link_type = tk.StringVar(value="iframe")
    chk_link_type_iframe = tk.Radiobutton(input_window, text="Iframe", variable=link_type, value="iframe", bg=DARK_GREEN, fg=TEXT_BLACK)
    chk_link_type_link = tk.Radiobutton(input_window, text="Link", variable=link_type, value="link", bg=DARK_GREEN, fg=TEXT_BLACK)
    
    chk_link_type_iframe.pack(pady=5)
    chk_link_type_link.pack(pady=5)

    lbl_instruction = tk.Label(input_window, text="Introduce los datos:", bg=DARK_GREEN, fg=TEXT_BLACK)
    lbl_instruction.pack(pady=10)

    chk_viewability = tk.Checkbutton(input_window, text="Incluir viewability", variable=include_viewability, bg=DARK_GREEN, fg=TEXT_BLACK)
    chk_viewability.pack(pady=5)

    input_data = tk.Text(input_window, height=6, width=80, bg=LIGHT_GREEN, fg=TEXT_BLACK)
    input_data.pack(pady=10)

    btn_process = tk.Button(input_window, text="Procesar", command=lambda: process_data(input_data), bg=LIGHT_GREEN, fg=TEXT_BLACK)
    btn_process.pack(pady=5)


def ejecutar_script(script_name):
    global last_execution_time
    try:
        script_path = os.path.join("app", script_name)
        result = subprocess.run(["python", script_path], capture_output=True, text=True)
        output_text.insert(tk.END, result.stdout)
        output_text.see(tk.END)
        timer_updater.set_last_execution_time(time.time())
    except Exception as e:
        messagebox.showerror("Error", f"Error al ejecutar {script_name}: {e}")

csv_generated = False
iframe_detected = False  

script_running = False  # Variable para rastrear el estado de ejecución del script
script_completed = False  # Nueva variable global

def ejecutar_img_aws_bulk_thread():
    global csv_generated, iframe_detected, last_execution_time, script_running

    try:
        script_path = os.path.join("app", "__IMG_aws_Bulk_v08.pyw")
        process = subprocess.Popen(["pythonw", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True)

        # Lee stdout
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_text.insert(tk.END, line)
            output_text.see(tk.END)

        # Lee stderr
        while True:
            error_line = process.stderr.readline()
            if not error_line:
                break
            # Aquí puedes decidir cómo mostrar los mensajes de error, por ejemplo, insertándolos en output_text
            output_text.insert(tk.END, error_line)
            output_text.see(tk.END)

        process.stdout.close()
        process.stderr.close()

        timer_updater.set_last_execution_time(time.time())

    except Exception as e:
        messagebox.showerror("Error", f"Error al ejecutar el script: {e}")
    finally:
        script_running = False
        progress_bar['value'] = 100  # Establecer la barra de progreso al 100% al finalizar el script

        app.after(1000, lambda: progress_bar.grid_forget())
        app.after(1000, lambda: progress_bar.grid_forget())

        # Comprobación adicional para habilitar el botón de generación de CSV
        if not script_running:
            csv_generated = True  # Asumiendo que la ejecución fue exitosa
            generar_csv_btn.config(state=tk.NORMAL)

def confirmacion_ejecucion():
    def on_si():
        popup.destroy()
        iniciar_ejecucion_bulk()

    def on_no():
        popup.destroy()

    popup = tk.Toplevel(app)
    popup.title("Confirmación")
    popup.configure(bg=DARK_GREEN)

    window_width = 300
    window_height = 100
    pos_x = app.winfo_x() + (app.winfo_width() // 2) - (window_width // 2)
    pos_y = app.winfo_y() + (app.winfo_height() // 6) - (window_height // 6)

    popup.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    label = tk.Label(popup, text="¿Desea ejecutar el Bulk ahora?", bg=DARK_GREEN, fg=TEXT_BLACK)
    label.pack(pady=10)

    boton_si = tk.Button(popup, text="Sí", command=on_si, bg=BLUE, fg=TEXT_WHITE, font=("Helvetica", 12, "bold"), height=1, width=6)
    boton_si.pack(side=tk.LEFT, padx=(50, 10), pady=10)

    boton_no = tk.Button(popup, text="No", command=on_no, bg=RED, fg=TEXT_WHITE, font=("Helvetica", 12, "bold"), height=1, width=6)
    boton_no.pack(side=tk.RIGHT, padx=(10, 50), pady=10)

def iniciar_ejecucion_bulk():
    global script_running
    script_running = True
    progress_bar_handler.start_progress_bar()
    progress_bar.grid(row=3, column=0, columnspan=4, pady=10)
    progress_bar['mode'] = 'determinate'
    progress_bar['value'] = 0

    thread = threading.Thread(target=ejecutar_img_aws_bulk_thread)
    thread.start()

def ejecutar_img_aws_bulk():
    confirmacion_ejecucion()  # Mostrar la ventana de confirmación



def generar_archivo_csv(src_csv_filename):
    try:
        src_csv_path = os.path.join("app", src_csv_filename)

        compartir_folder_path = os.path.join("app", "COMPARTIR")
        os.makedirs(compartir_folder_path, exist_ok=True)

        # Determina el nombre del archivo destino basado en el archivo fuente.
        if src_csv_filename == "360_ENC_file.csv":
            dest_csv_filename = "360_file.csv"
        else:
            dest_csv_filename = "360_ENC_file.csv"

        dest_csv_path = os.path.join(compartir_folder_path, dest_csv_filename)
        if os.path.exists(dest_csv_path):
            os.remove(dest_csv_path)

        # Copia el archivo al destino.
        dest_csv_path = os.path.join(compartir_folder_path, src_csv_filename)
        shutil.copyfile(src_csv_path, dest_csv_path)

        # Abre la carpeta donde se encuentra el archivo.
        os.startfile(compartir_folder_path)

    except Exception as e:
        print(f"Error al generar y copiar los archivos CSV: {e}")

def generar_csv():
    global csv_generated
    if csv_generated:
        output_text_content = output_text.get("1.0", tk.END)

        last_iframe_index = output_text_content.rfind('<iframe')
        last_a_index = output_text_content.rfind('<a')

        if last_iframe_index > last_a_index:
            src_csv_filename = "360_ENC_file.csv"
            success_msg = "Se va a generar el archivo 360_ENC_file.csv para creatividades tipo <iframe>."
        elif last_a_index > last_iframe_index:
            src_csv_filename = "360_file.csv"
            success_msg = "Se va a generar el archivo 360_file.csv para creatividades tipo <a>."
        else:
            messagebox.showerror("Error", "No se pudo determinar el tipo de archivo CSV a generar.")
            return

        def on_si():
            generar_archivo_csv(src_csv_filename)
            csv_popup.destroy()

        def on_no():
            csv_popup.destroy()

        csv_popup = tk.Toplevel(app)
        csv_popup.title("Generar CSV")
        csv_popup.configure(bg=DARK_GREEN)

        window_width = 450
        window_height = 150
        pos_x = app.winfo_x() + (app.winfo_width() // 2) - (window_width // 2)
        pos_y = app.winfo_y() + (app.winfo_height() // 6) - (window_height // 6)

        csv_popup.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

        label = tk.Label(csv_popup, text=success_msg + "\n¿Desea generar el archivo y abrir la carpeta ahora?", bg=DARK_GREEN, fg=TEXT_BLACK)
        label.pack(pady=10)

        boton_si = tk.Button(csv_popup, text="Sí", command=on_si, bg=BLUE, fg=TEXT_WHITE, font=("Helvetica", 12, "bold"), height=1, width=10)
        boton_si.pack(side=tk.LEFT, padx=(50, 10), pady=10)

        boton_no = tk.Button(csv_popup, text="No", command=on_no, bg=RED, fg=TEXT_WHITE, font=("Helvetica", 12, "bold"), height=1, width=10)
        boton_no.pack(side=tk.RIGHT, padx=(10, 50), pady=10)



app = tk.Tk()
app.title("Bulk App - Neural.one")
app.configure(bg=DARK_GREEN)

include_viewability = tk.BooleanVar(value=True)

frame = tk.Frame(app, bg=DARK_GREEN)
frame.pack(padx=10, pady=10)

progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="indeterminate", length=200)
progress_bar_handler = ProgressBarHandler(app, progress_bar)

output_text = tk.Text(frame, wrap=tk.WORD, bg=LIGHT_GREEN, fg=TEXT_BLACK)
output_text.grid(row=4, column=0, columnspan=4, pady=10)

btn_img_aws_bulk = tk.Button(frame, text="Ejecutar BULK", command=ejecutar_img_aws_bulk, 
                             bg=LIGHT_GREEN, fg=TEXT_BLACK, 
                             font=("Helvetica", 12, "bold"), 
                             width=20, height=2)
btn_img_aws_bulk.grid(row=0, column=0, padx=10)


btn_show_input = tk.Button(frame, text="Introducir datos", command=show_input_window, bg=LIGHT_GREEN, fg=TEXT_BLACK)
btn_show_input.grid(row=0, column=3, columnspan=4, padx=10)

time_label = tk.Label(frame, text="", bg=DARK_GREEN, fg=TEXT_BLACK)
time_label.grid(row=1, column=0)

open_folder_btn = tk.Button(frame, text="Carpeta de archivos", command=open_folder, bg=LIGHT_GREEN, fg=TEXT_BLACK)
open_folder_btn.grid(row=2, column=3, columnspan=4, pady=10)

open_html_btn = tk.Button(frame, text="test.html", command=open_test_html, bg=LIGHT_GREEN, fg=TEXT_BLACK)
open_html_btn.grid(row=0, column=0, columnspan=4, pady=10)

open_json_btn = tk.Button(frame, text="Abrir JSON", command=open_json_with_vscode, bg=LIGHT_GREEN, fg=TEXT_BLACK)
open_json_btn.grid(row=1, column=3, columnspan=4, pady=10)

generar_csv_btn = tk.Button(frame, text="Generar CSV 360", command=generar_csv, bg=LIGHT_GREEN, fg=TEXT_BLACK)
generar_csv_btn.grid(row=0, column=2, padx=10)
generar_csv_btn.config(state=tk.DISABLED) 

btn_process_json = tk.Button(frame, text="JSON Civitatis", command=process_json, 
                             bg=LIGHT_GREEN, fg=TEXT_BLACK)
btn_process_json.grid(row=3, column=3, columnspan=4, pady=10)

timer_updater = TimerUpdater(app, time_label)

timer_updater.update_timer()

app.mainloop()
