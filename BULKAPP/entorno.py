from dotenv import load_dotenv
import os

load_dotenv()

access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
database_url = os.getenv("AWS_REGION")

print("Acces Key:", access_key)
