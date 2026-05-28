import os
import sys
import json

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def read_file(ruta_archivo):
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        contenido = archivo.read()
    return contenido

def load_prompts():
    prompts = {}
    prompts_dir = os.path.join(parent_dir, 'prompts')
    for filename in os.listdir(prompts_dir):
        if filename.endswith('.txt'):
            with open(os.path.join(prompts_dir, filename), 'r', encoding='utf-8') as file:
                prompts[filename] = file.read()
    return prompts

def load_dataset():
    datasets = {}
    dataset_dir = os.path.join(parent_dir, 'data')
    for filename in os.listdir(dataset_dir):
        if filename.endswith('.json'):
            with open(os.path.join(dataset_dir, filename), 'r', encoding='utf-8') as file:
                datasets[filename] = json.load(file)
    return datasets