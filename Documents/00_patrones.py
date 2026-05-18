import csv
import re

CONLLU_PATH = "petroner-uri-2023-07-11.conllu"

# -----------------------------------------
# PATRONES
# -----------------------------------------

PATRONES_INICIO = [
    r'^RESUMO\b',
    r'^ABSTRACT\b',
    r'^INTRODU[ÇC][ÃA]O\b',
    r'^INTRODUCTION\b'
]

PATRONES_FIN = [
    r'^AGRADECIMENTOS\b',
    r'^REFER[ÊE]NCIAS',
    r'^REFER[ÊE]NCIAS BIBLIOGR'
]

regex_inicio = [
    re.compile(p, re.IGNORECASE)
    for p in PATRONES_INICIO
]

regex_fin = [
    re.compile(p, re.IGNORECASE)
    for p in PATRONES_FIN
]

# -----------------------------------------
# FUNCIONES
# -----------------------------------------

def es_inicio(texto):
    return any(r.search(texto) for r in regex_inicio)


def es_fin(texto):
    return any(r.search(texto) for r in regex_fin)


# -----------------------------------------
# EXTRACCIÓN
# -----------------------------------------

def extraer_articulos(conllu_path, salida_csv):

    articulos = []

    text_actual = None
    sent_id_actual = None

    articulo_actual = None

    ultimo_sent_id = None
    ultimo_texto = None

    contador = 1

    with open(conllu_path, 'r', encoding='utf-8') as f:

        for linea in f:

            linea = linea.strip()

            # -------------------------------------
            # EXTRAER TEXTO
            # -------------------------------------

            if linea.startswith('# text ='):
                text_actual = linea.split('=', 1)[1].strip()

            # -------------------------------------
            # EXTRAER SENT_ID
            # -------------------------------------

            elif linea.startswith('# sent_id ='):

                sent_id_actual = linea.split('=', 1)[1].strip()

                # -------------------------------------
                # DETECTAR INICIO
                # -------------------------------------

                if text_actual and es_inicio(text_actual):

                    # Si ya había un artículo abierto,
                    # cerrarlo usando la oración anterior

                    if articulo_actual is not None:

                        articulo_actual['id_fin'] = ultimo_sent_id
                        articulo_actual['texto_fin'] = ultimo_texto

                        articulos.append(articulo_actual)

                    # Crear nuevo artículo

                    articulo_actual = {
                        'articulo': contador,
                        'id_inicio': sent_id_actual,
                        'texto_inicio': text_actual,
                        'id_fin': None,
                        'texto_fin': None
                    }

                    contador += 1

                # -------------------------------------
                # DETECTAR FIN EXPLÍCITO
                # -------------------------------------

                elif articulo_actual is not None and text_actual and es_fin(text_actual):

                    articulo_actual['id_fin'] = sent_id_actual
                    articulo_actual['texto_fin'] = text_actual

                    articulos.append(articulo_actual)

                    articulo_actual = None

                # Guardar último elemento válido

                ultimo_sent_id = sent_id_actual
                ultimo_texto = text_actual

    # -----------------------------------------
    # CERRAR ÚLTIMO ARTÍCULO
    # -----------------------------------------

    if articulo_actual is not None:

        articulo_actual['id_fin'] = ultimo_sent_id
        articulo_actual['texto_fin'] = ultimo_texto

        articulos.append(articulo_actual)

    # -----------------------------------------
    # GUARDAR CSV
    # -----------------------------------------

    with open(salida_csv, 'w', newline='', encoding='utf-8') as csvfile:

        campos = [
            'articulo',
            'id_inicio',
            'texto_inicio',
            'id_fin',
            'texto_fin'
        ]

        writer = csv.DictWriter(csvfile, fieldnames=campos)

        writer.writeheader()

        for fila in articulos:
            writer.writerow(fila)

    print(f"Artículos encontrados: {len(articulos)}")
    print(f"CSV generado: {salida_csv}")


# -----------------------------------------
# EJECUTAR
# -----------------------------------------

extraer_articulos(
    CONLLU_PATH,
    'articulos_conllu.csv'
)