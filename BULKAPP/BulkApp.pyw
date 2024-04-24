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
ancho_btn = 20

FOLDER_PATH = os.path.join("app")

app = tk.Tk()
app.title("Bulk App - Neural.one")
app.configure(bg=DARK_GREEN)
app.rowconfigure(0, weight=1)
app.columnconfigure(0, weight=1)

link_type = tk.StringVar()
script_running = False
script_completed = False
include_viewability = tk.BooleanVar(value=True)

frame = tk.Frame(app, bg=DARK_GREEN)
frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

def extract_data_from_rows(data):
    lines = data.split("\n")
    
    if len(lines) < 2:
        return []

    headers = lines[0].split("\t")
    for col in ["Size", "Trackingcode Id", "Trackingcode", "URL", "URL Final"]:
        if col not in headers:
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


def toggle_frame(frame_to_show):
    all_components = [input_frame, create_tcs_frame, object_frame, output_text]
    for component in all_components:
        if component is not None:
            component.grid_forget() 

    frame_to_show.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky='nsew') 
    if frame_to_show == output_text:
        output_text.grid(row=4, column=0, columnspan=4, pady=10, sticky='ew') 
        output_text.delete('1.0', tk.END)

last_aws_path_2_selection = ""
last_custom_value = ""  # Variable global para almacenar el último valor ingresado en el campo de texto personalizado

def show_object_window(json_data, index=0):
    global object_frame, last_aws_path_2_selection, last_custom_value
    if 'object_frame' not in globals():
        object_frame = tk.Frame(app, bg=DARK_GREEN)
        object_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky='nsew')

    for widget in object_frame.winfo_children():
        widget.destroy()

    obj_text = tk.Text(object_frame, height=13, width=70, bg=LIGHT_GREEN, fg=TEXT_BLACK)
    obj_text.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

    formatted_json = one_line_arrays(json.dumps(json_data[index], indent=4))
    obj_text.insert(tk.END, formatted_json)

    lbl_instruction = tk.Label(object_frame, text="Introduce ruta de AWS, ej: s3://adgravity/mundo_pacifico/2023/10/halloween/", bg=DARK_GREEN, fg=TEXT_BLACK)
    lbl_instruction.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

    aws_path_1_entry_value = tk.Entry(object_frame, width=60, bg=LIGHT_GREEN, fg=TEXT_BLACK)
    aws_path_1_entry_value.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

    options_iframe = [".html", "/index.html"]  # Cambiado el orden para que "Custom" sea la primera opción
    options_link = [".png", ".jpg", ".gif"]
    options = options_iframe + options_link

    aws_path_2_combobox = ttk.Combobox(object_frame, values=options, state="readonly")
    aws_path_2_combobox.grid(row=3, column=1, padx=10, pady=5)
    aws_path_2_combobox.set("Custom" if last_aws_path_2_selection == "" else last_aws_path_2_selection)

    custom_entry = tk.Entry(object_frame, width=30, bg=LIGHT_GREEN, fg=TEXT_BLACK)
    custom_entry.grid(row=3, column=2, padx=10, pady=5)
    custom_entry.grid_remove()
    custom_entry.insert(tk.END, last_custom_value)

    def show_custom_entry():
        if aws_path_2_combobox.get() == "Custom":
            custom_entry.grid()
        else:
            custom_entry.grid_remove()

    show_custom_entry()  # Mostrar el campo de texto personalizado desde el principio

    aws_path_2_combobox.bind("<<ComboboxSelected>>", lambda event: show_custom_entry())

    btn_next = tk.Button(object_frame, text="Continuar", command=lambda: process_current_object(json_data, index, aws_path_1_entry_value, aws_path_2_combobox, custom_entry), bg=LIGHT_GREEN, fg=TEXT_BLACK)
    btn_next.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

    toggle_frame(object_frame)


def process_current_object(json_data, index, aws_path_1_entry, aws_path_2_combobox, custom_entry):
    global last_aws_path_2_selection, last_custom_value

    aws_path_1_entry_value = aws_path_1_entry.get()
    aws_path_2_combobox_value = aws_path_2_combobox.get()
    custom_entry_value = custom_entry.get()

    # Actualizar el valor de 'aws_path_1' y 'aws_path_2' según lo que se haya ingresado en los campos correspondientes
    json_data[index]['aws_path_1'] = aws_path_1_entry_value

    # Añadir esta línea para ajustar 'aws_path_1'
    json_data[index]['aws_path_1'] = aws_path_1_entry_value.replace("s3://adgravity/", "")

    if aws_path_2_combobox_value == "Custom":
        json_data[index]['aws_path_2'] = custom_entry_value
        last_custom_value = custom_entry_value  # Almacenar el valor ingresado en el campo de texto personalizado
    else:
        json_data[index]['aws_path_2'] = aws_path_2_combobox_value

    last_aws_path_2_selection = aws_path_2_combobox_value 

    next_index = index + 1
    if next_index < len(json_data):
        # Asegúrate de pasar el texto personalizado al siguiente objeto si existe
        if json_data[next_index].get('type') == "iframe" and aws_path_2_combobox_value == "Custom":
            json_data[next_index]['aws_path_2'] = custom_entry_value
        show_object_window(json_data, next_index)  
    else:
        save_json(json_data) 
        messagebox.showinfo("Completo", "Todos los objetos procesados.")
        toggle_frame(output_text)




def process_data(input_data):
    try:
        data = input_data.get("1.0", tk.END)
        json_data = extract_data_from_rows(data)
        if json_data:  
            show_object_window(json_data)
        else:
            messagebox.showinfo("Info", "No data processed. Check input format.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al procesar los datos: {e}")
        print("Error occurred:", e) 

def clear_text_field(text_field):
    text_field.delete("1.0", tk.END)

def show_input_window():
    global input_frame, link_type, include_viewability
    if 'input_frame' not in globals() or not input_frame.winfo_children():
        input_frame = tk.Frame(app, bg=DARK_GREEN)

        link_type = tk.StringVar(value="") 
        include_viewability = tk.BooleanVar(value=True)

        def select_link_type(type):
            link_type.set(type)
            btn_iframe.config(relief="sunken" if link_type.get() == "iframe" else "raised")
            btn_link.config(relief="sunken" if link_type.get() == "link" else "raised")

        btn_iframe = tk.Button(input_frame, text="Iframe", command=lambda: select_link_type("iframe"), relief="raised", bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
        btn_link = tk.Button(input_frame, text="Link", command=lambda: select_link_type("link"), relief="raised", bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)

        btn_iframe.grid(row=0, column=0, padx=10, pady=10)
        btn_link.grid(row=0, column=1, padx=10, pady=10)

        lbl_instruction = tk.Label(input_frame, text="Introduce los datos:", bg=DARK_GREEN, fg=TEXT_BLACK)
        lbl_instruction.grid(row=1, column=0, columnspan=2, pady=10)

        chk_viewability = tk.Checkbutton(input_frame, text="Incluir viewability", variable=include_viewability, onvalue=True, offvalue=False, bg=DARK_GREEN, fg=TEXT_BLACK)
        chk_viewability.grid(row=2, column=0, columnspan=2, pady=10)

        input_data = tk.Text(input_frame, height=8, width=70, bg=LIGHT_GREEN, fg=TEXT_BLACK)
        input_data.grid(row=3, column=0, columnspan=2, pady=10, padx=10)

        btn_process = tk.Button(input_frame, text="Continuar", command=lambda: process_data(input_data), bg=BLUE, fg=TEXT_WHITE)
        btn_process.grid(row=4, column=0, columnspan=2, pady=10)

        btn_clear = tk.Button(input_frame, text="Limpiar campo de texto", command=lambda: clear_text_field(input_data), bg=RED, fg=TEXT_WHITE)
        btn_clear.grid(row=5, column=0, columnspan=2, pady=10)

    toggle_frame(input_frame)




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

script_running = False 
script_completed = False 

def ejecutar_img_aws_bulk_thread():
    global csv_generated, iframe_detected, last_execution_time, script_running

    try:
        script_path = os.path.join("app", "__IMG_aws_Bulk_v08.pyw")
        process = subprocess.Popen(["pythonw", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True)

        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_text.insert(tk.END, line)
            output_text.see(tk.END)

        while True:
            error_line = process.stderr.readline()
            if not error_line:
                break
            output_text.insert(tk.END, error_line)
            output_text.see(tk.END)

        process.stdout.close()
        process.stderr.close()

        timer_updater.set_last_execution_time(time.time())

    except Exception as e:
        messagebox.showerror("Error", f"Error al ejecutar el script: {e}")
    finally:
        script_running = False
        progress_bar['value'] = 100 

        app.after(1000, lambda: progress_bar.grid_forget())
        app.after(1000, lambda: progress_bar.grid_forget())

        if not script_running:
            csv_generated = True 
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

    window_width = 220
    window_height = 100
    pos_x = app.winfo_x() + (app.winfo_width() // 2) - (window_width // 2)
    pos_y = app.winfo_y() + (app.winfo_height() // 6) - (window_height // 6)

    popup.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    label = tk.Label(popup, text="¿Desea ejecutar el Bulk ahora?", bg=DARK_GREEN, fg=TEXT_BLACK)
    label.grid(row=0, column=0, columnspan=2, padx=30, pady=10, sticky='ew') 

    boton_si = tk.Button(popup, text="Sí", command=on_si, bg=BLUE, fg=TEXT_WHITE, font=("Helvetica", 12, "bold"), height=1, width=6)
    boton_si.grid(row=1, column=0, padx=10, pady=10, sticky='e') 

    boton_no = tk.Button(popup, text="No", command=on_no, bg=RED, fg=TEXT_WHITE, font=("Helvetica", 12, "bold"), height=1, width=6)
    boton_no.grid(row=1, column=1, padx=10, pady=10, sticky='w') 

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
    confirmacion_ejecucion() 



def generar_archivo_csv(src_csv_filename):
    try:
        src_csv_path = os.path.join("app", src_csv_filename)

        compartir_folder_path = os.path.join("app", "COMPARTIR")
        os.makedirs(compartir_folder_path, exist_ok=True)

        if src_csv_filename == "360_ENC_file.csv":
            dest_csv_filename = "360_file.csv"
        else:
            dest_csv_filename = "360_ENC_file.csv"

        dest_csv_path = os.path.join(compartir_folder_path, dest_csv_filename)
        if os.path.exists(dest_csv_path):
            os.remove(dest_csv_path)

        dest_csv_path = os.path.join(compartir_folder_path, src_csv_filename)
        shutil.copyfile(src_csv_path, dest_csv_path)

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

        window_width = 460
        window_height = 150
        pos_x = app.winfo_x() + (app.winfo_width() // 2) - (window_width // 2)
        pos_y = app.winfo_y() + (app.winfo_height() // 6) - (window_height // 6)

        csv_popup.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

        label = tk.Label(csv_popup, text=success_msg + "\n¿Desea generar el archivo y abrir la carpeta ahora?", bg=DARK_GREEN, fg=TEXT_BLACK)
        label.grid(row=0, column=0, columnspan=2, padx=30, pady=10, sticky='ew') 

        boton_si = tk.Button(csv_popup, text="Sí", command=on_si, bg=BLUE, fg=TEXT_WHITE, font=("Helvetica", 12, "bold"), height=1, width=10)
        boton_si.grid(row=1, column=0, padx=10, pady=10, sticky='e') 

        boton_no = tk.Button(csv_popup, text="No", command=on_no, bg=RED, fg=TEXT_WHITE, font=("Helvetica", 12, "bold"), height=1, width=10)
        boton_no.grid(row=1, column=1, padx=10, pady=10, sticky='w') 


def execute_main_script(data):
    try:
        script_path = os.path.join(FOLDER_PATH, "TC_GEN", "tc_gen.py")
        process = subprocess.Popen(["python", script_path], stdin=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=data)
        
        if process.returncode != 0:
            raise Exception(stderr.strip() if stderr else 'Script failed without an error message.')
        else:
            messagebox.showinfo("Éxito", "El script se ejecutó correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al ejecutar el script: {e}")
    finally:
        toggle_frame(output_text)


def show_create_tcs_window():
    global create_tcs_frame 
    output_text.grid_forget() 
    if 'create_tcs_frame' not in globals() or not create_tcs_frame.winfo_children(): 
        create_tcs_frame = tk.Frame(app, bg=DARK_GREEN)
        lbl_instruction = tk.Label(create_tcs_frame, text="Introduce los datos para Crear TCs:", bg=DARK_GREEN, fg=TEXT_BLACK)
        lbl_instruction.grid(row=0, column=0, pady=10)

        input_data = tk.Text(create_tcs_frame, height=14, width=70, bg=LIGHT_GREEN, fg=TEXT_BLACK)
        input_data.grid(row=1, column=0, pady=10, padx=10)

        btn_continue = tk.Button(create_tcs_frame, text="Continuar", command=lambda: execute_main_script(input_data.get("1.0", tk.END)), bg=BLUE, fg=TEXT_WHITE)
        btn_continue.grid(row=2, column=0, pady=10)

        btn_clear = tk.Button(create_tcs_frame, text="Limpiar campo de texto", command=lambda: clear_text_field(input_data), bg=RED, fg=TEXT_WHITE)
        btn_clear.grid(row=3, column=0, pady=10)
        
    toggle_frame(create_tcs_frame) 


btn_show_input = tk.Button(frame, text="Introduce datos", command=show_input_window, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
btn_show_input.grid(row=0, column=3, columnspan=4, padx=10)

input_frame = tk.Frame(app, bg=DARK_GREEN)
create_tcs_frame = tk.Frame(app, bg=DARK_GREEN)
object_frame = tk.Frame(app, bg=DARK_GREEN) 

progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="indeterminate", length=150)
progress_bar_handler = ProgressBarHandler(app, progress_bar)

output_text = tk.Text(frame, wrap=tk.WORD, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=70)
output_text.grid(row=4, column=0, columnspan=4, pady=5, padx=10)

btn_img_aws_bulk = tk.Button(frame, text="Ejecutar BULK", command=ejecutar_img_aws_bulk, bg=BLUE, fg=TEXT_WHITE, width=ancho_btn)
btn_img_aws_bulk.grid(row=0, column=0, padx=50)


btn_create_tcs = tk.Button(frame, text="Crear TCs", command=show_create_tcs_window, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
btn_create_tcs.grid(row=0, column=2, padx=10)


time_label = tk.Label(frame, text="", bg=DARK_GREEN, fg=TEXT_BLACK, width=ancho_btn)
time_label.grid(row=1, column=0)

open_folder_btn = tk.Button(frame, text="Carpeta de archivos", command=open_folder, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
open_folder_btn.grid(row=2, column=3, columnspan=4, pady=10)

open_html_btn = tk.Button(frame, text="test.html", command=open_test_html, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
open_html_btn.grid(row=3, column=0, pady=10)

open_json_btn = tk.Button(frame, text="Abrir JSON", command=open_json_with_vscode, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
open_json_btn.grid(row=1, column=3, columnspan=4, pady=10)

generar_csv_btn = tk.Button(frame, text="Generar CSV DV360", command=generar_csv, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
generar_csv_btn.grid(row=2, column=0, padx=10)
generar_csv_btn.config(state=tk.DISABLED) 

btn_process_json = tk.Button(frame, text="JSON Civitatis", command=process_json, 
                             bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
btn_process_json.grid(row=3, column=3, columnspan=4, pady=10)

timer_updater = TimerUpdater(app, time_label)

timer_updater.update_timer()

app.mainloop()
