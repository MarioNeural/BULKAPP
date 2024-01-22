import os
import zipfile
from collections import deque

def descomprimir_zip(zip_file_path, output_dir):
    stack = deque()
    stack.append((zip_file_path, output_dir))

    while stack:
        zip_file_path, current_output_dir = stack.pop()
        with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
            zip_file.extractall(current_output_dir)
            for member in zip_file.namelist():
                member_path = os.path.join(current_output_dir, member)
                if member.lower().endswith('.zip'):
                    stack.append((member_path, current_output_dir))

if __name__ == "__main__":
    # Ruta del archivo zip inicial
    zip_file_path = '/Users/usuario/Downloads/Display-En-20230906T095532Z-001.zip'
    # Carpeta de destino donde se descomprimirán los archivos
    output_dir = '/Users/usuario/Downloads/descomprimido'
    
    descomprimir_zip(zip_file_path, output_dir)
    print("¡Descompresión completada!")



def descomprimir_zip(zip_file_path, output_dir):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
        # Crear carpeta de destino si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Extraer archivos zip internos en carpetas separadas
        for member in zip_file.namelist():
            if member.lower().endswith('.zip'):
                folder_name = os.path.splitext(member)[0]  # Nombre de la carpeta
                folder_path = os.path.join(output_dir, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                
                # Extraer el archivo zip interno
                with zipfile.ZipFile(os.path.join(output_dir, member), 'r') as internal_zip:
                    internal_zip.extractall(folder_path)

if __name__ == "__main__":
    # Ruta del archivo zip inicial
    zip_file_path = '/Users/usuario/Downloads/Display-En-20230906T095532Z-001.zip'
    # Carpeta de destino donde se descomprimirán los archivos
    output_dir = '/Users/usuario/Downloads/descomprimido'
    
    # Crear la carpeta de destino si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    descomprimir_zip(zip_file_path, output_dir)
    print("¡Descompresión completada!")
