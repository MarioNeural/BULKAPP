import pandas as pd
import os
import webbrowser
import numpy as np
import sys
from io import StringIO
import boto3
from dotenv import load_dotenv
import tkinter as tk
from tkinter import messagebox
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from styles.styles import DARK_GREEN, LIGHT_GREEN, TEXT_BLACK, TEXT_WHITE, RED, BLUE, GRAY, ORANGE

ancho_btn = 20

advertiser_number_map = {
    'Educo': 143,
    'Sr. Gorsky': 36,
    'Son Jaumell': 261,
    'Pestana': 309,
    'AM Resorts': 151,
    'Best Hotels': 275,
    'Ocean Hotels': 34,
    'Sandos': 123,
    'Petit Celler': 142,
    'Insotel': 281,
    'Iberia Express': 209,
    'MiBodega': 362,
    'Estival Group': 381,
    'Canariasviaja': 321,
    'Pepephone': 36,
    'AECC': 349,
    'Liga-T': 332,
    'OK Mobility': 371,
    'Oasis Hotel': 351,
    'Excelsia': 142,
    'Viva Hotels': 261,
    'Wonders': 289,
    'Médicos del Mundo': 225,
    'Gilmar': 339,
    'Ametller Origen': 215,
    'Solvia': 109,
    'Palmaia': 123,
    'Vicente Ferrer': 210,
    'EU Business School': 283,
    'Civitatis': 245,
    'Savoy Signature': 341,
    'Manos Unidas': 139,
    'Medplaya': 393,
    'Oasis Wild Life': 394,
    'Zafiro Hoteles': 148,
    'Inseryal': 401,
    'IESE': 402,
    'Hoteles Poseidón': 395,
    'Megacentro': 362,
    'H10': 34,
    'Campus Training': 414,
    'Culmia': 358,
    'Flexicar': 410,
    'Aproperties': 408,
    'ING Direct': 36,
    'Vercine': 36,
    'Vodafone': 36,
    'Aldeas Infantiles': 422,
    # Agrega más anunciantes según sea necesario
}

standard_sizes = ["300x600", "160x600", "300x250", "320x100", "728x90", "970x250"]

def load_data():
    input_data = sys.stdin.read()
    df = pd.read_csv(StringIO(input_data), sep='\t')
    df.columns = [col.lower() for col in df.columns]
    df = df[df['trackingcode'].notna() & (df['trackingcode'] != '')]
    df = df.applymap(lambda x: '' if pd.isna(x) else str(x))  
    return df


load_dotenv()

def load_taxonomy(advertiser):
    bucket_name = 'neural-commons'
    
    if advertiser not in advertiser_number_map:
        raise ValueError(f"Advertiser '{advertiser}' not found in the mapping dictionary")
    
    object_key = f'taxonomy/staging/{advertiser_number_map[advertiser]}.csv'

    s3 = boto3.client('s3',
                      aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                      aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                      region_name=os.getenv("AWS_REGION"))

    obj = s3.get_object(Bucket=bucket_name, Key=object_key)
    
    return pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')), sep=';')

def find_id_or_name(column, value, mapping_dicts, missing_elements, default=''):
    """Busca el ID en el diccionario de mapeo, si no lo encuentra devuelve el nombre o el valor predeterminado."""
    if pd.isna(value) or value == '':
        return default

    name = str(value).lower()
    id_col = ''

    if column == 'strategy':
        id_col = mapping_dicts.get('strategy_name', {}).get(name, default)
    else:
        id_col = mapping_dicts.get(column, {}).get(name, '')
        if not id_col:
            id_col = mapping_dicts.get(column + '_name', {}).get(name, default)
        if not id_col:  # Si no se encuentra el ID, devolver el nombre sin agregar a missing_elements
            return name  # Devolver el nombre de la campaña o lineitem para que se guarde en la columna correspondiente

    if not id_col or id_col == default:
        if column not in ['campaign', 'lineitem']:
            missing_elements.add((column, name))
        return name

    id_col = str(id_col)
    return str(int(float(id_col))) if id_col.replace('.', '', 1).isdigit() else id_col


def get_manual_inputs(missing_elements):
    inputs = {}

    def on_ok():
        for element in missing_elements:
            col, name = element
            inputs[element] = input_vars[element].get()
        root.quit()
        root.destroy()

    def copy_to_clipboard(value):
        root.clipboard_clear()
        root.clipboard_append(value)
        root.update() 

    root = tk.Tk()
    root.title("IDs faltantes")
    root.configure(bg=DARK_GREEN)
    root.attributes('-topmost', True)

    window_width = 400
    max_window_height = 400
    content_height = 200 + 90 * len(missing_elements) 
    window_height = min(content_height, max_window_height)
    pos_x = root.winfo_screenwidth() // 4 - window_width // 2
    pos_y = root.winfo_screenheight() // 2 - window_height // 2

    root.geometry(f"{window_width + 40}x{window_height}+{pos_x}+{pos_y}") 

    container = tk.Frame(root, bg=DARK_GREEN)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg=DARK_GREEN)
    canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)

    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview, width=40)  
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    scrollable_frame = tk.Frame(canvas, bg=DARK_GREEN)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    label = tk.Label(scrollable_frame, text="Faltan los siguientes ids:", bg=DARK_GREEN, fg=TEXT_BLACK, wraplength=window_width - 60)
    label.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

    input_vars = {}
    row = 1
    for col, name in missing_elements:
        frame = tk.Frame(scrollable_frame, bg=DARK_GREEN)
        frame.grid(row=row, column=0, padx=10, pady=5, sticky='ew')

        label = tk.Label(frame, text=f"{col.capitalize()}: '{name}'", bg=DARK_GREEN, fg=TEXT_BLACK, wraplength=window_width - 160) 
        label.pack(side="left", fill="x", expand=True)

        copy_button = tk.Button(frame, text="Copiar", command=lambda value=name: copy_to_clipboard(value), bg=ORANGE, fg=TEXT_WHITE, width=ancho_btn)
        copy_button.pack(side="left", padx=5)

        input_var = tk.StringVar()
        input_entry = tk.Entry(scrollable_frame, textvariable=input_var, bg="white", fg=TEXT_BLACK)
        input_entry.grid(row=row + 1, column=0, padx=10, pady=10, sticky='ew')

        input_vars[(col, name)] = input_var
        row += 2

    ok_button = tk.Button(scrollable_frame, text="Aceptar", command=on_ok, bg=BLUE, fg=TEXT_WHITE, width=ancho_btn)
    ok_button.grid(row=row, column=0, padx=10, pady=10, sticky='ew')

    root.mainloop()

    return inputs

def check_sizes(df):
    invalid_sizes = df[~df['size'].isin(standard_sizes)]['size'].unique()
    if len(invalid_sizes) > 0:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True) 
        messagebox.showwarning("Advertencia", f"Hay tamaños no incluidos en los estándares: {', '.join(invalid_sizes)}")
        root.destroy()

def validate_trackingcode_name(trackingcode_name):
    # Definir los caracteres no permitidos en una URL
    invalid_characters = re.compile(r'[ ñÑáéíóúÁÉÍÓÚ%&#¿?$¡!/çÇ<>€.,:;"Üü{}=@|ºª]')
    # invalid_characters = re.compile(r'[ñÑçÇ]')
    
    if invalid_characters.search(trackingcode_name):
        root = tk.Tk()
        root.withdraw() 
        root.attributes('-topmost', True) 
        messagebox.showwarning("Advertencia", f"El trackingcode '{trackingcode_name}' contiene caracteres no permitidos para una URL.")
        sys.exit(1)
        root.destroy()
        raise ValueError(f"El trackingcode '{trackingcode_name}' contiene caracteres no permitidos para una URL.")

def main():
    data_df = load_data()
    
    data_df.columns = [col.lower() for col in data_df.columns]

    if 'advertiser' not in data_df.columns:
        raise ValueError("The data must contain an 'advertiser' column.")
    
    if 'size' in data_df.columns:
        check_sizes(data_df)
    
    first_advertiser = data_df['advertiser'].iloc[0]

    if first_advertiser.lower() in [ad.lower() for ad in advertiser_number_map]:
        taxonomy_df = load_taxonomy(first_advertiser)
        taxonomy_df.columns = taxonomy_df.columns.str.lower()
    else:
        raise ValueError(f"Advertiser '{first_advertiser}' not found in the mapping dictionary.")

    mapping_dicts = {}
    for i in range(0, len(taxonomy_df.columns), 2):
        name_col = taxonomy_df.columns[i]
        id_col = taxonomy_df.columns[i+1]
        mapping_dicts[name_col] = dict(zip(taxonomy_df[name_col].astype(str).str.lower(), taxonomy_df[id_col]))

    crear_tcs_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'CrearTcs.csv')
    
    if os.path.exists(crear_tcs_file_path):
        os.remove(crear_tcs_file_path)
    
    new_columns = ["trackingcode_name", "awareness_type", "publisher", "publisher_id", "campaign", "campaign_id", "model", "model_id", "placement_id", "lineitem_id", "new_lineitem_name", "channel", "channel_id", "strategy", "strategy_id", "retargeting", "sem_type", "bulk_prospecting"]
    crear_tcs_df = pd.DataFrame(columns=new_columns)

    def clean_lineitem_name(lineitem):
        if lineitem.endswith('_XXXXX'):
            return lineitem[:-6]
        return lineitem

    missing_elements = set()
    new_rows = []
    for index, row in data_df.iterrows():
        if not row.get('trackingcode'):
            continue

        trackingcode_name = str(row.get('trackingcode', '')).strip()

        # Llamamos a la función para validar el trackingcode_name
        validate_trackingcode_name(trackingcode_name)

        lineitem_cleaned = clean_lineitem_name(str(row.get('lineitem', '')).strip())
        
        new_row = {col: '' for col in crear_tcs_df.columns}

        new_row['trackingcode_name'] = trackingcode_name
        new_row['publisher_id'] = find_id_or_name('publisher', str(row.get('publisher', '')).strip(), mapping_dicts, missing_elements, str(row.get('publisher', '')).strip())
        
        if 'campaign name' in data_df.columns:
            campaign_value = str(row.get('campaign name', '')).strip()
        else:
            campaign_value = str(row.get('campaign', '')).strip()
        
        campaign_id_or_name = find_id_or_name('campaign', campaign_value, mapping_dicts, missing_elements, campaign_value)
        
        # Aquí corregimos para que si no se encuentra el ID, el nombre se quede en `campaign` y `campaign_id` se mantenga vacío
        if not campaign_id_or_name.isdigit():  # No se encontró un ID válido
            new_row['campaign'] = campaign_id_or_name
            new_row['campaign_id'] = ''
        else:  # Si se encuentra el ID, se almacena en `campaign_id`
            new_row['campaign'] = ''
            new_row['campaign_id'] = campaign_id_or_name

        lineitem_id = find_id_or_name('lineitem', lineitem_cleaned, mapping_dicts, missing_elements, lineitem_cleaned)
        if lineitem_id == lineitem_cleaned or not lineitem_id.isdigit():
            new_row['new_lineitem_name'] = lineitem_cleaned
            new_row['lineitem_id'] = ''
        else:
            new_row['lineitem_id'] = lineitem_id
        
        new_row['channel_id'] = find_id_or_name('channel', str(row.get('channel', '')).strip(), mapping_dicts, missing_elements, str(row.get('channel', '')).strip())
        new_row['model_id'] = find_id_or_name('model', str(row.get('model', '')).strip(), mapping_dicts, missing_elements, str(row.get('model', '')).strip())
        new_row['placement_id'] = find_id_or_name('placement id', str(row.get('placement id', '')).strip(), mapping_dicts, missing_elements, str(row.get('placement id', '')).strip())

        awareness_type = str(row.get('awareness type', '')).strip().lower()
        if awareness_type == "TRUE":
            new_row['awareness_type'] = True
        if awareness_type == "true":
            new_row['awareness_type'] = True
        elif awareness_type == "verdadero":
            new_row['awareness_type'] = True
        elif awareness_type == "VERDADERO":
            new_row['awareness_type'] = True
        else:
            new_row['awareness_type'] = ""

        strategy = str(row.get('subcampaign', row.get('strategy', ''))).strip().lower()
        new_row['strategy_id'] = find_id_or_name('strategy', strategy, mapping_dicts, missing_elements)

        new_rows.append(new_row)

    new_crear_tcs_df = pd.DataFrame(new_rows, columns=crear_tcs_df.columns)
    new_crear_tcs_df = new_crear_tcs_df.applymap(lambda x: '' if pd.isna(x) or str(x).strip().lower() == 'nan' else str(x))


    if missing_elements:
        manual_inputs = get_manual_inputs(missing_elements)
        for (col, name), manual_id in manual_inputs.items():
            new_crear_tcs_df.loc[new_crear_tcs_df[f"{col}_id"] == name, f"{col}_id"] = str(manual_id)


    new_crear_tcs_df = new_crear_tcs_df.applymap(lambda x: '' if pd.isna(x) or str(x).strip().lower() == 'nan' else str(x))

    new_crear_tcs_df.to_csv(crear_tcs_file_path, index=False, sep=';')

    data_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    webbrowser.open(data_folder_path)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        messagebox.showerror("Error", f"Ha ocurrido un error: {e}")
        sys.exit(1)
