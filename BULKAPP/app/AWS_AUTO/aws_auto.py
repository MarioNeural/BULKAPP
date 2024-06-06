import boto3
import re
import os
import json
import sys
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

def encontrar_directorios(base_url, path, target_phrase):

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    
    bucket = base_url.split('/')[2]
    full_prefix = '/'.join(base_url.split('/')[3:]) + (path if path.endswith('/') else path + '/')

    target_keys = set(re.split('-|_', target_phrase.lower()))
    print("Palabras clave derivadas de target_phrase:", target_keys)

    def buscar_profundo(current_prefix, keys):
        if not keys:
            return current_prefix.rstrip('/')
        new_keys = keys.copy()
        try:
            response = s3.list_objects_v2(Bucket=bucket, Prefix=current_prefix, Delimiter='/')
            if 'CommonPrefixes' in response:
                for common_prefix in response['CommonPrefixes']:
                    dir_name = common_prefix['Prefix'].rstrip('/').split('/')[-1].lower()
                    # Comprobación exacta en lugar de coincidencia de substring
                    if dir_name in new_keys:
                        print(f"Coincidencia exacta encontrada: {dir_name} para la clave {dir_name}")
                        new_keys.remove(dir_name)
                        result = buscar_profundo(common_prefix['Prefix'], new_keys)
                        if result:
                            return result
        except ClientError as e:
            print(f"Error al acceder a S3: {e.response['Error']['Message']}")
            return None
        return current_prefix.rstrip('/')

    final_path = buscar_profundo(full_prefix, target_keys)
    if final_path:
        # Si el prefijo del base_url es "s3://adgravity/", eliminarlo completamente
        if base_url.startswith("s3://adgravity/"):
            final_path = final_path.replace("s3://adgravity/", "")
        return f"{final_path}/"
    else:
        print("No se encontraron directorios relevantes.")
        return None

def actualizar_json(base_url, path):
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(script_dir, 'INPUT_JSON', 'input.json')

    with open(input_path, 'r') as file:
        data = json.load(file)

    for item in data:
        name = item['name']
        aws_path_1 = encontrar_directorios(base_url, path, name)
        if aws_path_1:
            item['aws_path_1'] = aws_path_1
        else:
            print(f"No se encontró path para: {name}")

    with open(input_path, 'w') as file:
        json.dump(data, file, indent=4)

    print("JSON actualizado correctamente.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python aws_auto.py <base_url> <path>")
        sys.exit(1)
    base_url = sys.argv[1]
    path = sys.argv[2]
    actualizar_json(base_url, path)