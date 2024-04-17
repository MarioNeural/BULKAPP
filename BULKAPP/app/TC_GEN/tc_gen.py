import pandas as pd
import os
import webbrowser
import numpy as np
import sys
from io import StringIO

def load_data():
    input_data = sys.stdin.read()  # Lee toda la entrada estándar como una sola cadena
    df = pd.read_csv(StringIO(input_data), sep='\t')
    # Asegúrate de que la línea anterior imprime las columnas correctamente. Si hay un problema con el delimitador, las columnas no se separarán correctamente.

    # Seleccionar solo las columnas relevantes, si es necesario
    relevant_columns = ['Channel', 'Subcampaign', 'Lineitem', 'Publisher', 'Model', 'Campaign', 'Awareness Type', 'Trackingcode']
    df = df[relevant_columns] if all(col in df.columns for col in relevant_columns) else df
    return df

def load_taxonomy():
    # Construir la ruta absoluta del archivo
    current_dir = os.path.dirname(os.path.abspath(__file__))
    taxonomy_file_path = os.path.join(current_dir, 'taxonomy.csv')
    return pd.read_csv(taxonomy_file_path, sep=';')

def find_id_or_name(column, value, mapping_dicts, default=''):
    """Busca el ID en el diccionario de mapeo, si no lo encuentra devuelve el nombre."""
    if pd.isna(value) or value == '':
        return default

    name = str(value).lower()
    id_col = ''

    if column == 'strategy':
        # Buscar en 'strategy_name', no en 'subcampaign_name'
        id_col = mapping_dicts.get('strategy_name', {}).get(name, default)
    elif column == 'campaign':
        # Tratamiento especial para 'campaign'
        id_col = mapping_dicts.get(column + '_name', {}).get(name, '')
        if not id_col:
            id_col = mapping_dicts.get(column + '_name', {}).get('always on', default)
    else:
        # Manejo general para otros campos
        id_col = mapping_dicts.get(column + '_name', {}).get(name, default)

    # Convertir a entero y luego a cadena si es numérico, para eliminar '.0'
    if str(id_col).replace('.', '', 1).isdigit():
        return str(int(float(id_col)))
    else:
        return id_col if id_col else name

def main():
    data_df = load_data()
    taxonomy_df = load_taxonomy()

    # Normalizar nombres de columnas a minúsculas para manejar mayúsculas/minúsculas
    data_df.columns = data_df.columns.str.lower()
    taxonomy_df.columns = taxonomy_df.columns.str.lower()

    # Crear diccionarios para mapear nombres a IDs
    mapping_dicts = {}
    for i in range(0, len(taxonomy_df.columns), 2):
        name_col = taxonomy_df.columns[i]
        id_col = taxonomy_df.columns[i+1]
        mapping_dicts[name_col] = dict(zip(taxonomy_df[name_col].astype(str).str.lower(), taxonomy_df[id_col]))

    # Cargar CrearTcs.csv usando una ruta absoluta
    crear_tcs_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'CrearTcs.csv')
    crear_tcs_df = pd.read_csv(crear_tcs_file_path, sep=';')

    def clean_lineitem_name(lineitem):
        if lineitem.endswith('_XXXXX'):
            return lineitem[:-6]  # Elimina los últimos 6 caracteres "_XXXXX"
        return lineitem

    # Procesar cada fila de los datos de entrada
    new_rows = []
    for index, row in data_df.iterrows():
        lineitem_cleaned = clean_lineitem_name(str(row.get('lineitem', '')).strip())
        
        new_row = {col: '' for col in crear_tcs_df.columns}

        # Extrae los valores estándar y los limpia de espacios adicionales
        new_row['trackingcode_name'] = str(row.get('trackingcode', '')).strip()
        new_row['publisher_id'] = find_id_or_name('publisher', str(row.get('publisher', '')).strip(), mapping_dicts, str(row.get('publisher', '')).strip())
        new_row['campaign_id'] = find_id_or_name('campaign', str(row.get('campaign', '')).strip(), mapping_dicts, str(row.get('campaign', '')).strip())
        new_row['lineitem_id'] = find_id_or_name('lineitem', lineitem_cleaned, mapping_dicts, lineitem_cleaned)
        new_row['channel_id'] = find_id_or_name('channel', str(row.get('channel', '')).strip(), mapping_dicts, str(row.get('channel', '')).strip())
        new_row['model_id'] = find_id_or_name('model', str(row.get('model', '')).strip(), mapping_dicts, str(row.get('model', '')).strip())
        new_row['placement_id'] = find_id_or_name('placement id', str(row.get('placement id', '')).strip(), mapping_dicts, str(row.get('placement id', '')).strip())

        # Verifica el valor de 'Awareness Type'
        awareness_type = str(row.get('awareness type', '')).strip().lower()
        if awareness_type == "verdadero":
            new_row['awareness_type'] = True
        else:
            new_row['awareness_type'] = ""

        strategy = str(row.get('subcampaign', row.get('strategy', ''))).strip().lower()
        new_row['strategy_id'] = find_id_or_name('strategy', strategy, mapping_dicts)

        new_rows.append(new_row)

    # Crea el DataFrame con las nuevas filas
    new_crear_tcs_df = pd.DataFrame(new_rows, columns=crear_tcs_df.columns)

    # Añadir columna para new_lineitem_name si aún no existe
    if 'new_lineitem_name' not in new_crear_tcs_df.columns:
        new_crear_tcs_df['new_lineitem_name'] = np.nan

    # Función para revisar y mover datos de lineitem_id a new_lineitem_name si contiene letras
    def move_if_contains_letters(item):
        if any(c.isalpha() for c in item):
            return item, np.nan 
        else:
            return np.nan, item 

    # Aplicar la función y asignar los resultados apropiados
    new_crear_tcs_df['new_lineitem_name'], new_crear_tcs_df['lineitem_id'] = zip(*new_crear_tcs_df['lineitem_id'].apply(move_if_contains_letters))

    # Reemplazar cadenas vacías con np.nan
    new_crear_tcs_df.replace('', np.nan, inplace=True)

    # Eliminar filas donde todas las columnas relevantes están vacías o contienen NaN
    columns_to_check = ['trackingcode_name', 'lineitem_id']
    new_crear_tcs_df.dropna(how='any', subset=columns_to_check, inplace=True)

    # Guardar los resultados en el archivo CrearTcs.csv
    new_crear_tcs_df.to_csv(crear_tcs_file_path, index=False, sep=';')

    # Abrir la carpeta 'data' en el explorador de archivos
    data_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    webbrowser.open(data_folder_path)

if __name__ == "__main__":
    main()