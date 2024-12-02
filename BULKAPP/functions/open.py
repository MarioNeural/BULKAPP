import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import webbrowser
import pandas as pd
import re
from urllib.parse import urlparse, urlunparse
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


FOLDER_PATH = os.path.join("app")
CSV_FILE_NAMES = ['360_file.csv']

verified_urls = {}
errors = []
report = []

def open_folder():
    try:
        os.startfile(FOLDER_PATH)
    except Exception as e:
        messagebox.showerror("Error", f"Error al abrir la carpeta: {e}")

def open_json_with_vscode():
    json_file_path = os.path.abspath(os.path.join('app', 'INPUT_JSON', 'input.json'))
    try:
        vscode_path = r"C:\Users\Mario Neural\AppData\Local\Programs\Microsoft VS Code\Code.exe"
        subprocess.run([vscode_path, json_file_path], check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")

def check_http_status(url):
    try:
        response = requests.get(url, timeout=10)  # Añadir un timeout
        return response.status_code == 200  # Retornar True si la respuesta es 200 OK
    except requests.exceptions.Timeout:
        print(f"Timeout al intentar acceder a {url}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error al intentar acceder a {url}: {e}")
        return False


def get_base_url(url):
    # Filtramos la URL eliminando los parámetros que empiezan con 'utm_'
    parsed_url = urlparse(url)
    query_params = [param for param in parsed_url.query.split('&') if not param.startswith('utm_')]
    base_query = '&'.join(query_params)
    base_url = urlunparse(parsed_url._replace(query=base_query))
    return base_url

def extract_link_url(tag, csv_file_name):
    if csv_file_name == '360_file.csv':
        match = re.search(r'<a\s+href="\$\{CLICK_URL\}([^"]+)"', tag)
        if match:
            extracted_url = match.group(1)
            print(f"URL extraída para: {extracted_url}")
            return extracted_url
        else:
            print("No se pudo extraer la URL")
    else:
        link_url_match = re.search(r'src="[^"]*?&link=([^"&]+)', tag)
        if link_url_match:
            extracted_url = link_url_match.group(1)
            print(f"URL extraída: {extracted_url}")
            return extracted_url
        else:
            print("No se pudo extraer la URL de la impresión")
    return None

def perform_checks(tag, index, csv_file_name):
    check_report = {
        'fila': index + 1,
        'url': '',
        'tc_alt': False,
        'bucket_checked': False,
        'bucket_status': '',
        'pixel_checked': False,
        'pixel_status': '',
        'universal_checked': False,
        'universal_status': ''
    }
    
    print(f"Contenido del tag en la fila {index + 1}: {tag}")
    
    link_url = extract_link_url(tag, csv_file_name)
    if link_url:
        check_report['url'] = link_url
    
    check_tc_alt = 'tc_alt' in tag  
    check_report['tc_alt'] = check_tc_alt
    
    # Extraemos la URL del bucket si está presente
    bucket_url_match = re.search(r'<script[^>]+src=["\'](https?://[^"\']*bucket[^"\']*|//[^"\']*bucket[^"\']*)["\']', tag)
    if bucket_url_match:
        bucket_url = bucket_url_match.group(1)
        if bucket_url.startswith("//"):
            bucket_url = f"https:{bucket_url}" 
        print(f"Bucket URL extraída: {bucket_url}")
        check_report['bucket_checked'] = True
    else:
        bucket_url = None
        print(f"Fila {index + 1}: No se pudo extraer la URL del bucket.")
    
    # Extraemos la URL del pixel si está presente
    pixel_url_match = re.search(r'<img\s+src=["\']([^"\']+)["\']', tag)
    script_pixel_match = re.search(r'<script[^>]+src=["\']([^"\']+)["\'][^>]*attributionsrc[^>]*>', tag, re.IGNORECASE)

    if pixel_url_match:
        pixel_url = pixel_url_match.group(1)
        print(f"Pixel URL extraída: {pixel_url}")
        check_report['pixel_checked'] = True
    elif script_pixel_match:
        pixel_url = script_pixel_match.group(1)
        print(f"Pixel Script URL extraída: {pixel_url}")
        check_report['pixel_checked'] = True
    else:
        pixel_url = None
        print(f"Fila {index + 1}: No se encontró un pixel de imagen o script para verificar.")

    if not bucket_url and not pixel_url:
        errors.append(f"Fila {index + 1}: No se encontró URL del bucket ni pixel de imagen o script para verificar.")
        report.append(check_report)
        return False
    
    status_ok = True

    # Verificamos el estado del bucket URL
    if bucket_url:
        status_ok = check_http_status(bucket_url)
        check_report['bucket_status'] = '200 OK' if status_ok else 'Error'
        print(f"HTTP status del bucket URL: {check_report['bucket_status']}")
        if not status_ok:
            errors.append(f"Fila {index + 1}: El bucket URL {bucket_url} no responde con estado 200.")
    
    # Verificamos el estado del pixel URL
    if pixel_url:
        pixel_status_ok = check_http_status(pixel_url)
        check_report['pixel_status'] = '200 OK' if pixel_status_ok else 'Error'
        print(f"HTTP status del pixel URL: {check_report['pixel_status']}")
        if not pixel_status_ok:
            errors.append(f"Fila {index + 1}: El pixel URL {pixel_url} no responde con estado 200.")
        status_ok = status_ok and pixel_status_ok

    report.append(check_report)
    return status_ok


def find_csv_file():
    for file_name in CSV_FILE_NAMES:
        csv_path = os.path.join(FOLDER_PATH, file_name)
        if os.path.exists(csv_path):
            return csv_path, file_name
    return None, None

def analyze_csv():
    global verified_urls, errors, report
    verified_urls = {}
    errors = []
    report = []
    
    try:
        csv_file_path, csv_file_name = find_csv_file()
        if csv_file_path is None:
            messagebox.showerror("Error", "No se encontró ningún archivo CSV válido en la carpeta.")
            return

        df = pd.read_csv(csv_file_path)
        
        if 'Third-party tag' not in df.columns:
            messagebox.showerror("Error", "No se encontró la columna 'Third-party tag' en el archivo CSV.")
            return
        
        for index, tag in df['Third-party tag'].items():
            perform_checks(tag, index, csv_file_name)
        
        if errors:
            output_text = '\n'.join(errors)
            print(output_text)
            messagebox.showerror("Errores Encontrados", output_text)
        else:
            messagebox.showinfo("Check Completo", "Las impresiones en las creatividades han sido verificadas")
        
        print("\n--- Reporte de Comprobaciones ---")
        any_errors = False
        for entry in report:
            if entry['universal_status'] == 'Error' or entry['bucket_status'] == 'Error' or entry['pixel_status'] == 'Error':
                print(f"Fila {entry['fila']}: URL revisada: {entry['url']}")
                if entry['tc_alt']:
                    if entry['universal_checked']:
                        print(f" - Contenedor universal y n_one: {entry['universal_status']}")
                    if entry['bucket_checked']:
                        print(f" - Bucket URL: {entry['bucket_status']}")
                if entry['pixel_checked']:
                    print(f" - Pixel de imagen: {entry['pixel_status']}")
                print()
                any_errors = True
        
        if not any_errors:
            print("Todas las filas verificadas están OK.")

    except FileNotFoundError:
        messagebox.showerror("Error", "No se encontró el archivo CSV en la carpeta.")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al analizar el CSV: {e}")


def open_test_html():
    analyze_csv()
    file_path = os.path.abspath(os.path.join(FOLDER_PATH, 'HTML', 'test.html'))
    
    if not os.path.exists(file_path):
        print("El archivo test.html no existe en la ruta proporcionada.")
        messagebox.showerror("Error", "El archivo test.html no se encuentra.")
        return

    formatted_path = file_path.replace("\\", "/") if os.name == 'nt' else file_path

    url = f'file:///{formatted_path}'

    webbrowser.open(url)
