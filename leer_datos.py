import json


def leer_datos_json(fichero_json):
    try:
        with open(fichero_json, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("El archivo JSON no se encuentra. Asegúrate de tener los datos guardados.")
        return []
