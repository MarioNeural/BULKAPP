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
# from functions.timer_functions import TimerUpdater
from functions.progress_bar_functions import ProgressBarHandler
from functions.open import open_test_html, open_folder, open_json_with_vscode

# ESTILOS
from styles.styles import DARK_GREEN, LIGHT_GREEN, TEXT_BLACK, TEXT_WHITE, RED, BLUE, GRAY, ORANGE
ancho_btn = 24

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

            if process_individual.get():
                obj = generate_object([current_size], [current_tc], line, current_name, current_landing, current_link, name_index, headers)
                temp_dict[f"{current_name}_{current_size}"] = obj
            else:
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

    if process_individual.get():
        all_results = [value for key, value in temp_dict.items()]
    else:
        all_results = [
            generate_object(value['sizes'], value['tcs'], value['line'], key, value['landing'], value['link'], name_index, headers)
            for key, value in temp_dict.items()
        ]
    return all_results

def generate_object(sizes, tcs, line, key, landing, link, name_index, headers):
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
        
        utm_content_full = match.group(1)[1:]
        x_index = utm_content_full.find('x')
        if x_index != -1:
            part_before_x = utm_content_full[:x_index - 3] + utm_content_full[x_index + 1:x_index + 4]
            part_after_x = utm_content_full[x_index + 4:]
            utm_content_parts = f"{utm_content_full[:x_index - 3]}{utm_content_full[x_index + 4:]}"
        else:
            utm_content_parts = None
    else:
        add_utm_size = None
        utm_content_parts = None

    aws_path_1 = ""
    aws_path_2 = ""
    link = re.sub(r'&tc_alt.*$', '', link)
    viewability = ""
    impression_tag = ""
    
    include_viewability_flag = include_viewability.get()
    include_impression_flag = include_impression.get()

    if include_viewability_flag:
        script_match = re.search(r'<script.*?src="([^"]+)', line)
        if script_match:
            viewability_url = script_match.group(1)
            viewability = re.sub(r'\d{6}.*$', '', viewability_url)
    
    if include_impression_flag and "Impression" in headers:
        impression_index = headers.index("Impression")
        if impression_index < len(values):
            impression_tag = values[impression_index].replace('"', "'")
    
    if link_type.get() == "iframe":
        result_obj = {
            "type": "iframe",
            "sizes": sizes,
            "name": key,
            "landing": landing,
            "aws_path_1": aws_path_1,
            "aws_path_2": aws_path_2,
            "link": link
        }
    else:
        result_obj = {
            "type": "link",
            "sizes": sizes,
            "name": key,
            "landing": landing,
            "aws_path_1": aws_path_1,
            "aws_path_2": aws_path_2,
            "url": link
        }

    if include_viewability_flag:
        result_obj["viewability"] = viewability
    else:
        # Si no se incluye la viewability, no incluimos los TCs
        tcs = []

    result_obj["tcs"] = tcs
    
    if include_impression_flag:
        result_obj["impression_tag"] = impression_tag

    if add_utm_size:
        result_obj["add_utm_size"] = add_utm_size
    
    if utm_content_parts:
        result_obj["utm_content"] = utm_content_parts

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
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
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
last_custom_value = "" 

def show_object_window(json_data, index=0):
    global object_frame, last_aws_path_2_selection, last_custom_value

    if 'object_frame' not in globals():
        object_frame = tk.Frame(app, bg=DARK_GREEN)
        object_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky='nsew')

    for widget in object_frame.winfo_children():
        widget.destroy()

    obj_text = tk.Text(object_frame, height=7, width=70, bg=LIGHT_GREEN, fg=TEXT_BLACK)
    obj_text.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

    formatted_json = one_line_arrays(json.dumps(json_data[index], indent=4))
    obj_text.insert(tk.END, formatted_json)

    lbl_instruction = tk.Label(object_frame, text="Introduce ruta de AWS, ej: s3://adgravity/mundo_pacifico/2023/10/halloween/", bg=DARK_GREEN, fg=TEXT_BLACK)
    lbl_instruction.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

    options_iframe = ["Custom", ".html", "/index.html"]
    options_link = ["Custom",".png", ".jpg", ".gif"]

    aws_path_2_combobox = ttk.Combobox(object_frame, state="readonly")
    aws_path_2_combobox.grid(row=3, column=0, columnspan=3, padx=10, pady=5)
    
    if link_type.get() == "iframe":
        aws_path_2_combobox['values'] = options_iframe
    else:
        aws_path_2_combobox['values'] = options_link

    aws_path_2_combobox.set("Custom" if last_aws_path_2_selection == "" else last_aws_path_2_selection)

    custom_entry = tk.Entry(object_frame, width=20, bg=LIGHT_GREEN, fg=TEXT_BLACK)
    custom_entry.grid(row=4, column=0, columnspan=3, padx=10, pady=5)
    custom_entry.grid_remove()
    custom_entry.insert(tk.END, last_custom_value)

    def show_custom_entry():
        if aws_path_2_combobox.get() == "Custom":
            custom_entry.grid()
        else:
            custom_entry.grid_remove()

    show_custom_entry()

    aws_path_2_combobox.bind("<<ComboboxSelected>>", lambda event: show_custom_entry())

    aws_path_1_entry_value = tk.Entry(object_frame, width=60, bg=LIGHT_GREEN, fg=TEXT_BLACK)
    aws_path_1_entry_value.grid(row=5, column=1, columnspan=1, padx=10, pady=5)

    btn_next = tk.Button(object_frame, text="Continuar", command=lambda: process_current_object(json_data, index, aws_path_1_entry_value, aws_path_2_combobox, custom_entry), bg=BLUE, fg=TEXT_WHITE)
    btn_next.grid(row=5, column=2, columnspan=2, padx=10, pady=5)

    lbl_instruction = tk.Label(object_frame, text="Auto AWS", bg=DARK_GREEN, fg=TEXT_BLACK)
    lbl_instruction.grid(row=6, column=0, columnspan=1)

    aws_auto_entry = tk.Entry(object_frame, width=60, bg=LIGHT_GREEN, fg=TEXT_BLACK)
    aws_auto_entry.grid(row=6, column=1, columnspan=1, padx=10, pady=5)

    btn_apply_all = tk.Button(object_frame, text="Aplicar a todos", command=lambda: apply_to_all(json_data, aws_path_1_entry_value, aws_path_2_combobox, custom_entry, aws_auto_entry), bg=ORANGE, fg=TEXT_WHITE)
    btn_apply_all.grid(row=6, column=2, columnspan=2, padx=10, pady=5)

    toggle_frame(object_frame)



def execute_auto_aws(aws_path):
    parts = aws_path.split('/', 3)
    if len(parts) < 4:
        messagebox.showerror("Error", "La ruta de AWS debe ser completa, incluyendo bucket y path.")
        return

    base_url = f"s3://{parts[2]}"
    path = parts[3]

    script_path = os.path.join("app", "AWS_AUTO", "aws_auto.py")
    
    try:
        result = subprocess.run(["python", script_path, base_url, path], capture_output=True, text=True)
        if result.returncode == 0:
            show_temp_message("Éxito", "El script se ha ejecutado correctamente", duration=2000)
        else:
            messagebox.showerror("Error", f"Error al ejecutar el script: {result.stderr}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def apply_to_all(json_data, aws_path_1_entry, aws_path_2_combobox, custom_entry, aws_auto_entry):
    aws_path_1_entry_value = aws_path_1_entry.get()
    aws_path_2_combobox_value = aws_path_2_combobox.get()
    custom_entry_value = custom_entry.get()
    aws_auto_value = aws_auto_entry.get()

    progress_bar_handler.start()
    app.update()

    def run_apply():
        try:
            for obj in json_data:
                obj['aws_path_1'] = aws_path_1_entry_value.replace("s3://adgravity/", "")

                if aws_path_2_combobox_value == "Custom":
                    obj['aws_path_2'] = custom_entry_value
                else:
                    obj['aws_path_2'] = aws_path_2_combobox_value

            save_json(json_data)

            if aws_auto_value:
                execute_auto_aws(aws_auto_value)

        except Exception as e:
            messagebox.showerror("Error", f"Error al aplicar a todos: {e}")
        finally:
            progress_bar_handler.stop()
            toggle_frame(output_text)

    threading.Thread(target=run_apply).start()


def process_current_object(json_data, index, aws_path_1_entry, aws_path_2_combobox, custom_entry):
    global last_aws_path_2_selection, last_custom_value

    aws_path_1_entry_value = aws_path_1_entry.get()
    aws_path_2_combobox_value = aws_path_2_combobox.get()
    custom_entry_value = custom_entry.get()

    json_data[index]['aws_path_1'] = aws_path_1_entry_value

    json_data[index]['aws_path_1'] = aws_path_1_entry_value.replace("s3://adgravity/", "")

    if aws_path_2_combobox_value == "Custom":
        json_data[index]['aws_path_2'] = custom_entry_value
        last_custom_value = custom_entry_value 
    else:
        json_data[index]['aws_path_2'] = aws_path_2_combobox_value

    last_aws_path_2_selection = aws_path_2_combobox_value 

    next_index = index + 1
    if next_index < len(json_data):
        if json_data[next_index].get('type') == "iframe" and aws_path_2_combobox_value == "Custom":
            json_data[next_index]['aws_path_2'] = custom_entry_value
        show_object_window(json_data, next_index)  
    else:
        save_json(json_data) 
        show_temp_message("Completo", "Todos los objetos procesados.", duration=2000)
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

process_individual = tk.BooleanVar(value=False)

def show_input_window():
    global input_frame, link_type, include_viewability, include_impression, process_individual
    if 'input_frame' not in globals() or not input_frame.winfo_children():
        input_frame = tk.Frame(app, bg=DARK_GREEN)

        link_type = tk.StringVar(value="")
        include_viewability = tk.BooleanVar(value=True)
        include_impression = tk.BooleanVar(value=False)
        process_individual = tk.BooleanVar(value=False)

        def select_link_type(type):
            link_type.set(type)
            if link_type.get() == "iframe":
                btn_iframe.config(bg=GRAY, relief="sunken")
                btn_link.config(bg=LIGHT_GREEN, relief="raised")
            else:
                btn_iframe.config(bg=LIGHT_GREEN, relief="raised")
                btn_link.config(bg=GRAY, relief="sunken")

        btn_iframe = tk.Button(input_frame, text="Iframe", command=lambda: select_link_type("iframe"), relief="raised", bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
        btn_link = tk.Button(input_frame, text="Link", command=lambda: select_link_type("link"), relief="sunken", bg=GRAY, fg=TEXT_BLACK, width=ancho_btn)

        btn_iframe.grid(row=0, column=0, padx=10, pady=10)
        btn_link.grid(row=0, column=1, padx=10, pady=10)

        lbl_instruction = tk.Label(input_frame, text="Introduce los datos:", bg=DARK_GREEN, fg=TEXT_BLACK)
        lbl_instruction.grid(row=1, column=0, columnspan=2, pady=10)

        chk_viewability = tk.Checkbutton(input_frame, text="Incluir viewability", variable=include_viewability, onvalue=True, offvalue=False, bg=DARK_GREEN, fg=TEXT_BLACK)
        chk_viewability.grid(row=2, column=0, columnspan=1, pady=10)

        chk_impression = tk.Checkbutton(input_frame, text="Incluir impression", variable=include_impression, onvalue=True, offvalue=False, bg=DARK_GREEN, fg=TEXT_BLACK)
        chk_impression.grid(row=2, column=0, columnspan=2, pady=10)

        chk_process_individual = tk.Checkbutton(input_frame, text="Procesar individualmente", variable=process_individual, onvalue=True, offvalue=False, bg=DARK_GREEN, fg=TEXT_BLACK)
        chk_process_individual.grid(row=2, column=1, columnspan=2, pady=10)

        input_data = tk.Text(input_frame, height=8, width=70, bg=LIGHT_GREEN, fg=TEXT_BLACK)
        input_data.grid(row=5, column=0, columnspan=2, pady=15, padx=10)

        btn_process = tk.Button(input_frame, text="Continuar", command=lambda: process_data(input_data), bg=BLUE, fg=TEXT_WHITE)
        btn_process.grid(row=6, column=0, columnspan=2, pady=10)

        btn_clear = tk.Button(input_frame, text="Limpiar campo de texto", command=lambda: clear_text_field(input_data), bg=RED, fg=TEXT_WHITE)
        btn_clear.grid(row=7, column=0, columnspan=2, pady=10)

    toggle_frame(input_frame)

def ejecutar_script(script_name):
    global last_execution_time
    try:
        script_path = os.path.join("app", script_name)
        result = subprocess.run(["python", script_path], capture_output=True, text=True)
        output_text.insert(tk.END, result.stdout)
        output_text.see(tk.END)
    except Exception as e:
        messagebox.showerror("Error", f"Error al ejecutar {script_name}: {e}")

csv_generated = False
iframe_detected = False  

script_running = False 
script_completed = False 

def ejecutar_bulk_thread(script_path):
    """Ejecuta un script en un hilo y actualiza la barra de progreso."""
    global script_running, csv_generated

    def run_script():
        try:
            toggle_frame(output_text)
            progress_bar_handler.start()  # Inicia la barra de progreso
            process = subprocess.Popen(
                ["pythonw", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True,
            )

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

        except Exception as e:
            messagebox.showerror("Error", f"Error al ejecutar el script: {e}")
        finally:
            generar_csv_btn.config(state=tk.NORMAL)
            open_test_html()
            progress_bar_handler.stop()  # Detiene la barra de progreso

    # Ejecutar el script en un hilo para no bloquear la UI
    script_running = True
    threading.Thread(target=run_script).start()

def mostrar_opciones_bulk():
    toggle_frame(output_text)
    popup = tk.Toplevel(app)
    popup.title("Selecciona el tipo de Bulk")
    popup.configure(bg=DARK_GREEN)

    # Configurar tamaño y posición
    window_width = 300
    window_height = 300
    pos_x = app.winfo_x() + (app.winfo_width() // 2) - (window_width // 2)
    pos_y = app.winfo_y() + (app.winfo_height() // 2) - (window_height // 2)
    popup.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    # Definir scripts asociados a cada botón
    botones = [
        ("BULK 08", os.path.join("app", "__IMG_aws_Bulk_v08.pyw")),
        ("H10", os.path.join("app", "__IMG_aws_Bulk_v04-h10.pyw")),
        ("Ocean Hotels", os.path.join("app", "__IMG_aws_Bulk_v04-h10.pyw")),
        ("Okmobility", os.path.join("app", "__IMG_aws_Bulk_v04-okmobility.pyw")),
    ]

    def ejecutar_bulk(script_path):
        popup.destroy()  # Cierra la ventana emergente
        ejecutar_bulk_thread(script_path)  # Llama a la función que ejecuta el script

    # Crear botones para cada tipo de Bulk
    for texto, script in botones:
        btn = tk.Button(
            popup,
            text=texto,
            command=lambda s=script: ejecutar_bulk(s),
            bg=LIGHT_GREEN,
            fg=TEXT_BLACK,
            width=ancho_btn,
        )
        btn.pack(pady=(20, 5))

    # Botón para cancelar
    btn_cancelar = tk.Button(
        popup,
        text="Cancelar",
        command=popup.destroy,
        bg=RED,
        fg=TEXT_WHITE,
        width=ancho_btn,
    )
    btn_cancelar.pack(pady=(25, 5))


def generar_archivo_csv(src_csv_filename):
    try:
        # Construir la ruta del archivo fuente
        src_csv_path = os.path.join("app", src_csv_filename)

        # Verificar si el archivo fuente existe
        if not os.path.exists(src_csv_path):
            raise FileNotFoundError(f"El archivo {src_csv_path} no existe. Por favor, verifica que se haya generado correctamente.")

        # Construir la ruta de la carpeta de destino
        compartir_folder_path = os.path.join("app", "COMPARTIR")
        os.makedirs(compartir_folder_path, exist_ok=True)

        # Limpiar la carpeta COMPARTIR antes de copiar el nuevo archivo
        for filename in os.listdir(compartir_folder_path):
            file_path = os.path.join(compartir_folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Construir la ruta del archivo destino
        dest_csv_path = os.path.join(compartir_folder_path, src_csv_filename)

        # Copiar el archivo fuente al destino
        shutil.copyfile(src_csv_path, dest_csv_path)

        # Abrir la carpeta de destino para mostrar el archivo copiado
        os.startfile(compartir_folder_path)

    except FileNotFoundError as e:
        messagebox.showerror("Archivo no encontrado", str(e))
    except Exception as e:
        messagebox.showerror("Error", f"Error al generar y copiar los archivos CSV: {e}")


def generar_csv(plataforma):
    global csv_generated
    csv_generated = True
    if not csv_generated:
        messagebox.showerror("Error", "No se ha generado el contenido necesario para crear un CSV.")
        return

    # Diccionario con los nombres de archivos por plataforma
    plataformas_archivos = {
        "DV360": ("360_ENC_file.csv", "360_file.csv"),
        "Quantcast": ("QCT_ESC_file.xlsx", "QCT_file.csv"),
        "Zeta": ("RKT_file.xlsx", "RKT_file.xlsx"),
        "StackAdapt": ("STACK_ENC_file.xlsx", "STACK_file.xlsx"),
        "TTD": ("TTD_ESC_file.xlsx", "TTD_file.xlsx"),
        "Zemanta": ("ZEM_ENC_file.xlsx", "ZEM_file.xlsx"),
        "AdForm": ("ADF_file.xlsx", "ADF_file.xlsx"),
    }

    # Obtener el contenido del campo de texto para analizar
    output_text_content = output_text.get("1.0", tk.END)

    # Seleccionar los archivos según la plataforma
    if plataforma not in plataformas_archivos:
        messagebox.showerror("Error", f"La plataforma '{plataforma}' no está configurada.")
        return

    # Determinar si es un archivo de iframe o link
    if "<iframe" in output_text_content:
        src_csv_filename = plataformas_archivos[plataforma][0]
    elif "<a" in output_text_content:
        src_csv_filename = plataformas_archivos[plataforma][1]
    else:
        messagebox.showerror("Error", "No se detectó el tipo de contenido adecuado (iframe o link).")
        return

    # Intentar generar el archivo
    generar_archivo_csv(src_csv_filename)

def mostrar_opciones_archivo():
    # Crear una ventana emergente para las opciones
    popup = tk.Toplevel(app)
    popup.title("Selecciona")
    popup.configure(bg=DARK_GREEN)

    # Configurar tamaño y posición de la ventana emergente
    window_width = 300
    window_height = 300
    pos_x = app.winfo_x() + (app.winfo_width() // 2) - (window_width // 2)
    pos_y = app.winfo_y() + (app.winfo_height() // 2) - (window_height // 2)
    popup.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    # Lista de plataformas disponibles
    plataformas = ["DV360", "Quantcast", "Zeta", "StackAdapt", "TTD", "Zemanta", "AdForm"]

    # Crear botones para cada plataforma
    for plataforma in plataformas:
        btn = tk.Button(
            popup,
            text=plataforma,
            command=lambda p=plataforma: [popup.destroy(), generar_csv(p)],
            bg=LIGHT_GREEN,
            fg=TEXT_BLACK,
            width=ancho_btn
        )
        btn.pack(pady=(10, 5))  


def execute_main_script(data):
    def run_script():
        try:
            script_path = os.path.join(FOLDER_PATH, "TC_GEN", "tc_gen.py")
            process = subprocess.Popen(["python", script_path], stdin=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=data)
            
            if process.returncode != 0:
                raise Exception(stderr.strip() if stderr else 'Script failed without an error message.')
            else:
                show_temp_message("Éxito", "El script se ejecutó correctamente")  # Mostrar mensaje temporal
        except Exception as e:
            messagebox.showerror("Error", f"Error al ejecutar el script: {e}")
        finally:
            progress_bar_handler.stop()  # Detiene la animación
            toggle_frame(output_text)

    # Inicia la animación y ejecuta el script en un hilo
    progress_bar_handler.start()
    app.update()  # Asegura que la animación aparezca inmediatamente
    threading.Thread(target=run_script).start()


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

def show_aws_popup():
    popup = tk.Toplevel(app)
    popup.title("AWS Folder Path")
    popup.configure(bg=DARK_GREEN)
    popup.transient(app) 

    window_width = 300
    window_height = 100
    pos_x = app.winfo_x() + (app.winfo_width() // 2) - (window_width // 2)
    pos_y = app.winfo_y() + (app.winfo_height() // 2) - (window_height // 2)
    popup.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    lbl_instruction = tk.Label(popup, text="Introduce la ubicación de la carpeta en AWS:", bg=DARK_GREEN, fg=TEXT_BLACK)
    lbl_instruction.pack(padx=10, pady=5)

    aws_path_entry = tk.Entry(popup, width=40, bg=LIGHT_GREEN, fg="black")
    aws_path_entry.pack(padx=10, pady=5)

    btn_continue = tk.Button(popup, text="Continuar", command=lambda: execute_script(aws_path_entry.get(), popup), bg=BLUE, fg=TEXT_WHITE)
    btn_continue.pack(padx=10, pady=10)

def execute_script(aws_path, popup):
    def run_script():
        try:
            parts = aws_path.split('/', 3) 
            if len(parts) < 4:
                messagebox.showerror("Error", "La ruta de AWS debe ser completa, incluyendo bucket y path.")
                return

            base_url = f"s3://{parts[2]}"
            path = parts[3]

            script_path = os.path.join("app", "AWS_AUTO", "aws_auto.py")
            result = subprocess.run(["python", script_path, base_url, path], capture_output=True, text=True)
            
            if result.returncode == 0:
                show_temp_message("Éxito", "Script ejecutado correctamente")  # Mostrar mensaje temporal
            else:
                messagebox.showerror("Error", f"Error al ejecutar el script: {result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            progress_bar_handler.stop()  # Detiene la animación
            popup.destroy()

    # Inicia la animación y ejecuta el script en un hilo
    progress_bar_handler.start()
    app.update()  # Asegura que la animación aparezca inmediatamente
    threading.Thread(target=run_script).start()



def show_temp_message(title, message, duration=2000):
    popup = tk.Toplevel(app)
    popup.title(title)
    popup.configure(bg=DARK_GREEN)

    # Configurar el tamaño y posición
    window_width = 300
    window_height = 100
    pos_x = app.winfo_x() + (app.winfo_width() // 2) - (window_width // 2)
    pos_y = app.winfo_y() + (app.winfo_height() // 2) - (window_height // 2)
    popup.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    # Contenido del mensaje
    label = tk.Label(popup, text=message, bg=DARK_GREEN, fg=TEXT_BLACK)
    label.pack(pady=20)

    # Cierra automáticamente después de `duration` milisegundos
    popup.after(duration, popup.destroy)



btn_show_input = tk.Button(frame, text="Introduce datos", command=show_input_window, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
btn_show_input.grid(row=0, column=2, columnspan=4, padx=10)

btn_show_auto_aws = tk.Button(frame, text="Auto AWS", command=lambda: show_aws_popup(), bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
btn_show_auto_aws.grid(row=1, column=2, columnspan=4, padx=10, pady=10)

input_frame = tk.Frame(app, bg=DARK_GREEN)
create_tcs_frame = tk.Frame(app, bg=DARK_GREEN)
object_frame = tk.Frame(app, bg=DARK_GREEN) 

progress_canvas = tk.Canvas(frame, width=150, height=20, bg='white')
progress_canvas.grid(row=3, column=0, columnspan=7, pady=10)

progress_bar_handler = ProgressBarHandler(app, progress_canvas)

output_text = tk.Text(frame, wrap=tk.WORD, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=70)
output_text.grid(row=4, column=0, columnspan=4, pady=5, padx=10)

btn_img_aws_bulk = tk.Button(frame, text="Ejecutar BULK", command=mostrar_opciones_bulk, bg=BLUE, fg=TEXT_WHITE, width=ancho_btn)
btn_img_aws_bulk.grid(row=0, column=0, rowspan=2, pady=(0, 10), sticky='ns')

btn_create_tcs = tk.Button(frame, text="Crear TCs", command=show_create_tcs_window, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
btn_create_tcs.grid(row=0, column=1, padx=10)

# time_label = tk.Label(frame, text="", bg=DARK_GREEN, fg=TEXT_BLACK, width=ancho_btn)
# time_label.grid(row=1, column=0)

open_folder_btn = tk.Button(frame, text="Carpeta de archivos", command=open_folder, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
open_folder_btn.grid(row=1, column=1)

open_html_btn = tk.Button(frame, text="test.html", command=open_test_html, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
open_html_btn.grid(row=3, column=0)

open_json_btn = tk.Button(frame, text="Abrir JSON", command=open_json_with_vscode, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
open_json_btn.grid(row=2, column=2, columnspan=4)

generar_csv_btn = tk.Button(frame, text="Generar Archivo", command=mostrar_opciones_archivo, bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
generar_csv_btn.grid(row=2, column=0, padx=10)
generar_csv_btn.config(state=tk.DISABLED) 

btn_process_json = tk.Button(frame, text="JSON Civitatis", command=process_json, 
                             bg=LIGHT_GREEN, fg=TEXT_BLACK, width=ancho_btn)
btn_process_json.grid(row=3, column=2, columnspan=4, pady=10)

# timer_updater = TimerUpdater(app, time_label)

# timer_updater.update_timer()

app.mainloop()
