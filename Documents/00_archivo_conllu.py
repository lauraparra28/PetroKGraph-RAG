# El objetivo de este archivo es imprimir en un csv el sentence_id y texto que se encuentra en el conllu

CONLLU_PATH = "petroner-uri-2023-07-11.conllu"

import csv

def conllu_a_csv(archivo_entrada, archivo_salida):
    datos_extraidos = []
    id_actual = None
    texto_actual = None

    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                
                # Extraer el ID de la sentencia
                if linea.startswith('# sent_id ='):
                    id_actual = linea.split('=', 1)[1].strip()
                
                # Extraer el texto de la sentencia
                elif linea.startswith('# text ='):
                    texto_actual = linea.split('=', 1)[1].strip()
                
                # Cuando se han encontrado ambos campos, se guardan en la lista
                if id_actual and texto_actual:
                    datos_extraidos.append({
                        'sentence_id': id_actual,
                        'text': texto_actual
                    })
                    # Reiniciar variables para la siguiente oración
                    id_actual = None
                    texto_actual = None

        # Guardar la información en un archivo CSV
        with open(archivo_salida, 'w', newline='', encoding='utf-8') as csvfile:
            campos = ['sentence_id', 'text']
            escritor = csv.DictWriter(csvfile, fieldnames=campos)
            
            escritor.writeheader()
            for fila in datos_extraidos:
                escritor.writerow(fila)
        
        print(f"Proceso completado. Se han extraído {len(datos_extraidos)} oraciones.")
        print(f"Archivo guardado como: {archivo_salida}")

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {archivo_entrada}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

# Uso del script
conllu_a_csv(CONLLU_PATH, 'resultado_conllu_petroner.csv')