import boto3
import re
import os
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

    # Dividir la frase en palabras clave por '-' y '_'
    target_keys = set(re.split('-|_', target_phrase.lower()))
    print("Palabras clave derivadas de target_phrase:", target_keys)

    # Función recursiva para buscar en profundidad
    def buscar_profundo(current_prefix, keys):
        if not keys:
            return current_prefix.rstrip('/')

        new_keys = keys.copy()
        try:
            response = s3.list_objects_v2(Bucket=bucket, Prefix=current_prefix, Delimiter='/')
            if 'CommonPrefixes' in response:
                for common_prefix in response['CommonPrefixes']:
                    dir_name = common_prefix['Prefix'].rstrip('/').split('/')[-1].lower()
                    # Buscar cualquier clave que coincida con el nombre del directorio
                    for key in keys:
                        if key in dir_name:
                            print(f"Coincidencia encontrada: {dir_name} para la clave {key}")
                            new_keys.remove(key)
                            # Continuar la búsqueda en el nuevo directorio con las claves restantes
                            result = buscar_profundo(common_prefix['Prefix'], new_keys)
                            if result:
                                return result
                            break
        except ClientError as e:
            print(f"Error al acceder a S3: {e.response['Error']['Message']}")
            return None

        return current_prefix.rstrip('/')

    # Comienza la búsqueda desde el prefijo base
    final_path = buscar_profundo(full_prefix, target_keys)
    if final_path:
        return f"s3://{bucket}/{final_path}/"  # Asegura que la URL final tenga un '/' al final
    else:
        print("No se encontraron directorios relevantes.")
        return None

# Uso de la función
base_url = 's3://adgravity'
path = 'AM_RESORTS/2024/04/waw/premium_prs/'
target_phrase = 'amresorts-eu_v1mp_AO-ZOETRY_dis_prs-1_WAW_ABRIL_ADSTORY'
resultado = encontrar_directorios(base_url, path, target_phrase)
if resultado:
    print("URL final encontrada:", resultado)
else:
    print("No se encontró la URL solicitada.")
