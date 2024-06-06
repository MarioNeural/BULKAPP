import pandas as pd
import os
import webbrowser
import numpy as np
import sys
from io import StringIO
import boto3
from dotenv import load_dotenv

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
    'Palmaia': 109,
    # Agrega más anunciantes según sea necesario
}

def load_data():
    input_data = sys.stdin.read()
    df = pd.read_csv(StringIO(input_data), sep='\t')
    df.columns = [col.lower() for col in df.columns] 
    df = df[df['trackingcode'].notna() & (df['trackingcode'] != '')] 
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

def find_id_or_name(column, value, mapping_dicts, default=''):
    """Busca el ID en el diccionario de mapeo, si no lo encuentra devuelve el nombre."""
    if pd.isna(value) or value == '':
        return default

    name = str(value).lower()
    id_col = ''

    if column == 'strategy':
        id_col = mapping_dicts.get('strategy_name', {}).get(name, default)
    elif column == 'campaign':
        id_col = mapping_dicts.get(column + '_name', {}).get(name, '')
        if not id_col:
            id_col = mapping_dicts.get(column + '_name', {}).get('always on', default)
    else:
        id_col = mapping_dicts.get(column + '_name', {}).get(name, default)

    if str(id_col).replace('.', '', 1).isdigit():
        return str(int(float(id_col)))
    else:
        return id_col if id_col else name

def main():
    data_df = load_data()
    
    data_df.columns = [col.lower() for col in data_df.columns]

    if 'advertiser' not in data_df.columns:
        raise ValueError("The data must contain an 'advertiser' column.")
    
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
    
    # Delete existing file if it exists
    if os.path.exists(crear_tcs_file_path):
        os.remove(crear_tcs_file_path)
    
    # Define the columns for the new DataFrame
    new_columns = ["trackingcode_name", "awareness_type", "publisher", "publisher_id", "campaign", "campaign_id", "model", "model_id", "placement_id", "lineitem_id", "new_lineitem_name", "channel", "channel_id", "strategy", "strategy_id", "retargeting", "sem_type", "bulk_prospecting"]
    crear_tcs_df = pd.DataFrame(columns=new_columns)

    def clean_lineitem_name(lineitem):
        if lineitem.endswith('_XXXXX'):
            return lineitem[:-6]
        return lineitem

    new_rows = []
    for index, row in data_df.iterrows():
        lineitem_cleaned = clean_lineitem_name(str(row.get('lineitem', '')).strip())
        
        new_row = {col: '' for col in crear_tcs_df.columns}

        new_row['trackingcode_name'] = str(row.get('trackingcode', '')).strip()
        new_row['publisher_id'] = find_id_or_name('publisher', str(row.get('publisher', '')).strip(), mapping_dicts, str(row.get('publisher', '')).strip())
        new_row['campaign_id'] = find_id_or_name('campaign', str(row.get('campaign', '')).strip(), mapping_dicts, str(row.get('campaign', '')).strip())
        new_row['lineitem_id'] = find_id_or_name('lineitem', lineitem_cleaned, mapping_dicts, lineitem_cleaned)
        new_row['channel_id'] = find_id_or_name('channel', str(row.get('channel', '')).strip(), mapping_dicts, str(row.get('channel', '')).strip())
        new_row['model_id'] = find_id_or_name('model', str(row.get('model', '')).strip(), mapping_dicts, str(row.get('model', '')).strip())
        new_row['placement_id'] = find_id_or_name('placement id', str(row.get('placement id', '')).strip(), mapping_dicts, str(row.get('placement id', '')).strip())

        awareness_type = str(row.get('awareness type', '')).strip().lower()
        if awareness_type == "verdadero":
            new_row['awareness_type'] = True
        else:
            new_row['awareness_type'] = ""

        strategy = str(row.get('subcampaign', row.get('strategy', ''))).strip().lower()
        new_row['strategy_id'] = find_id_or_name('strategy', strategy, mapping_dicts)

        new_rows.append(new_row)

    new_crear_tcs_df = pd.DataFrame(new_rows, columns=crear_tcs_df.columns)

    if 'new_lineitem_name' not in new_crear_tcs_df.columns:
        new_crear_tcs_df['new_lineitem_name'] = np.nan

    def move_if_contains_letters(item):
        if any(c.isalpha() for c in item):
            return item, np.nan 
        else:
            return np.nan, item 

    new_crear_tcs_df['new_lineitem_name'], new_crear_tcs_df['lineitem_id'] = zip(*new_crear_tcs_df['lineitem_id'].apply(move_if_contains_letters))

    new_crear_tcs_df.replace('', np.nan, inplace=True)

    # Write the new data to the CSV file
    new_crear_tcs_df.to_csv(crear_tcs_file_path, index=False, sep=';')

    data_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    webbrowser.open(data_folder_path)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
