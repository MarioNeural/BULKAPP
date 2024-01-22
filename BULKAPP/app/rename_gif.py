import os
import re
import zipfile

def descomprimir_archivo(archivo_zip, directorio_destino):
    with zipfile.ZipFile(archivo_zip, 'r') as archivo:
        archivo.extractall(directorio_destino)
    print("Archivos Gif descomprimidos con éxito.")
    
    # Obtener la ruta absoluta del archivo ZIP
ruta_archivo_zip = os.path.expanduser('/Users/usuario/Downloads/ar/300x600/')

# Directorio destino para extraer los archivos

def rename_files(root_folder):
    for folder_path, _, file_names in os.walk(root_folder):
        for file_name in file_names:
            if file_name.lower().endswith('.gif'):
                file_path = os.path.join(folder_path, file_name)
                resolution = extract_resolution(file_name)
                new_file_name = f"{resolution}.gif"
                new_file_path = os.path.join(folder_path, new_file_name)
                os.rename(file_path, new_file_path)

def extract_resolution(file_name):
    pattern = r'(\d{2,4})[xX](\d{2,4})'
    match = re.search(pattern, file_name)
    if match:
        resolution = match.group(0)
        return resolution
    else:
        return file_name
    
directorio_destino = '/Users/usuario/Downloads/renombrado'  # Ruta al directorio donde se extraerán los archivos

descomprimir_archivo(ruta_archivo_zip, directorio_destino)



# Especifica la ruta del directorio raíz
root_folder = directorio_destino

# Llama a la función para renombrar los archivos GIF
rename_files(root_folder)
