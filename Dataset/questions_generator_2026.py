
import os
import json
import rdflib
from rdflib import Namespace, URIRef
import networkx as nx
import random

parent_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(parent_dir, 'data')
os.makedirs(data_dir, exist_ok=True)

g = rdflib.Graph()
g.parse(os.path.join(parent_dir, 'ontology', 'OntoGeoLogicaInstanciasRelacoes_merged.owl'), format='xml')
G = nx.Graph()
print("✅ Successfully loaded PetroKGraph.")

for subj, pred, obj in g:
    G.add_edge(str(subj), str(obj), label=str(pred))

nodes_number = G.number_of_nodes()
axis_number = G.number_of_edges()
average_degree = axis_number*2/nodes_number
density = nx.density(G)
print(f'This graph has {nodes_number} nodes, {axis_number} axis')
print(f'Density:{density:.5f} and {average_degree:.3f} average degree')

namespace_base = Namespace("http://www.semanticweb.org/bg40/ontologies/2022/5/untitled-ontology-2#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
rdf= Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")


def gen_info(graph):

    fields = {}
    basins = {}
    wells = {}
    formations = {}

    for s, p, o in graph:

        if isinstance(s, URIRef) and "CAMP_CD_CAMPO" in s:
            campo_id = s.split("#")[1]
            if campo_id not in fields:
                fields[campo_id] = {"types": [], "located_in": [], "labels": [], "related": []}
            if "type" in p:
                fields[campo_id]["types"].append(o)
            elif "located_in" in p:
                fields[campo_id]["located_in"].append(o)
            elif "label" in p:
                fields[campo_id]["labels"].append(str(o))
            else:
                fields[campo_id]["related"].append((p, o))

        if isinstance(s, URIRef) and "BASE_CD_BACIA" in s:
            bacia_id = s.split("#")[1]
            if bacia_id not in basins:
                basins[bacia_id] = {"types": [], "labels": []}
            if "type" in p:
                basins[bacia_id]["types"].append(o)
            elif "label" in p:
                basins[bacia_id]["labels"].append(str(o))
                
        if isinstance(s, URIRef) and "POCO_CD_POCO" in s:
            poco_id = s.split("#")[1]
            if poco_id not in wells:
                wells[poco_id] = {"types": [], "located_in": [], "labels": [], "crosses": []}
            if "type" in p:
                wells[poco_id]["types"].append(o)
            elif "located_in" in p:
                wells[poco_id]["located_in"].append(o)
            elif "crosses" in p:
                wells[poco_id]["crosses"].append(str(o))
            elif "label" in p:
                wells[poco_id]["labels"].append(str(o))

        if isinstance(s, URIRef) and "formacao" in s:
            unidade_lito_id = s.split("#")[1]
            if unidade_lito_id not in formations:
                formations[unidade_lito_id] = {"types": [], "located_in": [], "has_age": [], "part_of": [],"carrier_of": [], "constituted_by": [], "crosses": [],  "labels": []}
            if "type" in p:
                formations[unidade_lito_id]["types"].append(o)
            elif "located_in" in p:
                formations[unidade_lito_id]["located_in"].append(str(o))  
            elif "constituted_by" in p:
                formations[unidade_lito_id]["constituted_by"].append(o) 
            elif "has_age" in p:
                formations[unidade_lito_id]["has_age"].append(str(o))  
            elif "part_of" in p:
                formations[unidade_lito_id]["part_of"].append(o)   
            elif "carrier_of" in p:
                formations[unidade_lito_id]["carrier_of"].append(o) 
            elif "crosses" in p:
                formations[unidade_lito_id]["crosses"].append(str(o))
            elif "label" in p:
                formations[unidade_lito_id]["labels"].append(str(o))
            
        if isinstance(s, URIRef) and "grupo" in s:
            unidade_lito_id = s.split("#")[1]
            if unidade_lito_id not in formations:
                formations[unidade_lito_id] = {"types": [], "located_in": [], "has_age": [], "part_of": [],"carrier_of": [], "constituted_by": [], "crosses": [],  "labels": []}
            if "type" in p:
                formations[unidade_lito_id]["types"].append(o)
            elif "located_in" in p:
                formations[unidade_lito_id]["located_in"].append(str(o))  
            elif "constituted_by" in p:
                formations[unidade_lito_id]["constituted_by"].append(o) 
            elif "has_age" in p:
                formations[unidade_lito_id]["has_age"].append(str(o))  
            elif "part_of" in p:
                formations[unidade_lito_id]["part_of"].append(o)  
            elif "carrier_of" in p:
                formations[unidade_lito_id]["carrier_of"].append(o)  
            elif "crosses" in p:
                formations[unidade_lito_id]["crosses"].append(str(o))
            elif "label" in p:
                formations[unidade_lito_id]["labels"].append(str(o))
            
        if isinstance(s, URIRef) and "membro" in s:
            unidade_lito_id = s.split("#")[1]
            if unidade_lito_id not in formations:
                formations[unidade_lito_id] = {"types": [], "located_in": [], "has_age": [], "part_of": [],"carrier_of": [], "constituted_by": [], "crosses": [],  "labels": [] }
            if "type" in p:
                formations[unidade_lito_id]["types"].append(o)
            elif "located_in" in p:
                formations[unidade_lito_id]["located_in"].append(str(o))  
            elif "constituted_by" in p:
                formations[unidade_lito_id]["constituted_by"].append(o) 
            elif "has_age" in p:
                formations[unidade_lito_id]["has_age"].append(str(o))  
            elif "part_of" in p:
                formations[unidade_lito_id]["part_of"].append(o)   
            elif "carrier_of" in p:
                formations[unidade_lito_id]["carrier_of"].append(o) 
            elif "crosses" in p:
                formations[unidade_lito_id]["crosses"].append(str(o))
            elif "label" in p:
                formations[unidade_lito_id]["labels"].append(str(o))

            
    return fields, basins, wells, formations


def get_primary_label(labels_list, fallback="Desconhecido"):
    if labels_list:
        return labels_list[0]
    return fallback

def format_with_synonyms(synonyms_list):
    if not synonyms_list:
        return "Desconhecido"
    principal = synonyms_list[0]
    extras = synonyms_list[1:]
    if extras:
        return f"{principal} ({', '.join(extras)})"
    else:
        return principal

def gen_questions(fields, basins, wells, formations, graph, random_sample=False):
    questions = []
    multihop_questions = []
    id_counter = 0 

    # ===============================================================
    # 2) FIELDS
    # ===============================================================

    for field_uri, info in fields.items():
        field_names = info["labels"]
        if field_names:
            main_name = field_names[0]  # usa el primer label como principal
            other_names = field_names[1:]  # los demás quedan como sinónimos
            id_counter += 1
            if other_names:
                answer_text = [[name] for name in other_names]
                context_text = f"O campo {main_name} também é conhecido pelos seguintes nomes: {format_with_synonyms(other_names)}."
            else:
                answer_text = [["Não há outros nomes."]]
                context_text = f"O campo {main_name} não possui outros nomes conhecidos além de {main_name}."

            questions.append({
                    "id": id_counter,
                    "level": 0,
                    "question": f"Quais outros nomes possíveis para o campo {main_name}?",
                    "answer": answer_text,
                    "context": context_text
            })



        located_uris = info["located_in"]
        if located_uris:
            subanswers = []
            context_parts = []

            field_name_principal = get_primary_label(info["labels"], fallback=field_uri)

            for loc_uri in located_uris:
                loc_str = str(loc_uri)
                loc_id = loc_str.split("#")[1] if "#" in loc_str else loc_str

                if loc_id in basins and basins[loc_id]["labels"]:
                    synonyms = basins[loc_id]["labels"]
                else:
                    label_found = graph.value(URIRef(loc_uri), rdfs.label)
                    synonyms = [str(label_found)] if label_found else [loc_id]

                subanswers.append(synonyms)
                context_parts.append(format_with_synonyms(synonyms))

            if subanswers:
                context_text = ", ".join(context_parts)
                id_counter += 1
                questions.append({
                    "id": id_counter,
                    "level": 1,
                    "question": f"Em que bacia está localizado o campo {field_name_principal}?",
                    "answer": subanswers,
                    "context": f"O campo {field_name_principal} está localizado na(s) bacia(s): {context_text}."
                })


    count_campos = {}     
    campos_por_bacia = {}  

    for campo_id, info in fields.items():
        if info["located_in"]:
            bacia_uri_full = info["located_in"][0]
            bacia_uri_id = bacia_uri_full.split("#")[-1]

            bacia_label_found = graph.value(URIRef(bacia_uri_full), rdfs.label)
            bacia_label = bacia_label_found.title() if bacia_label_found else bacia_uri_id
            
            campo_nome = info["labels"][0].title() if info["labels"] else campo_id

            if bacia_label not in count_campos:
                count_campos[bacia_label] = {
                    "count": 0,
                    "uri": bacia_uri_id
                }
            count_campos[bacia_label]["count"] += 1

            if bacia_label not in campos_por_bacia:
                campos_por_bacia[bacia_label] = {
                    "uri": bacia_uri_id,
                    "campos": []
                }
            campos_por_bacia[bacia_label]["campos"].append(campo_nome)

    for bacia_label, data in count_campos.items():
        bacia_uri_id = data["uri"]
        count = data["count"]

        id_counter += 1
        questions.append({
            "id": id_counter,
            "level": 2, # Nivel verificado 1-HOP
            "question": f"Quantos campos estão localizados na bacia {bacia_label} de URI {bacia_uri_id}?",
            "answer": [[str(count)]],
            "context": f"Existem {count} campos localizados na bacia {bacia_label}."
        })

    for bacia_label, data in campos_por_bacia.items():
        bacia_uri_id = data["uri"]
        campos_list = data["campos"] 
        campos_joined = ", ".join(campos_list)

        id_counter += 1
        questions.append({
            "id": id_counter,
            "level": 2, # Nivel verificado 1-HOP
            "question": f"Quais são os campos localizados na bacia {bacia_label} de URI {bacia_uri_id}?",
            "answer": campos_list,
            "context": (
                f"Na bacia {bacia_label} de URI {bacia_uri_id} existem {len(campos_list)} "
                f"campos: {campos_joined}."
            )
        })

    # ===============================================================
    # 3) WELLS
    # ===============================================================

    for well_uri, info in wells.items():
        well_names = info["labels"]
        if well_names:
            main_name = well_names[0]  # usa o primeiro label como principal
            other_names = well_names[1:]  # os demais ficam como sinônimos

            id_counter += 1
            if other_names:
                answer_text = [[name] for name in other_names]
                context_text = f"Além de {main_name}, o poço {well_uri} também é conhecido como {format_with_synonyms(other_names)}."
            else:
                answer_text = [["Não há outros nomes."]]
                context_text = f"O poço {main_name} não possui outros nomes conhecidos além de {main_name}."

            questions.append({
                    "id": id_counter,
                    "level": 0,
                    "question": f"Quais outros nomes possíveis para o poço {main_name}?",
                    "answer": answer_text,
                    "context": context_text
            })
                
        # --- Bacias do poço (CORREGIDO) ---
        loc_uris = info["located_in"]
        if loc_uris:
            basins_subanswers = []
            basins_context_parts = []

            well_name_principal = get_primary_label(info["labels"], fallback=well_uri)

            for loc_uri in loc_uris:
                loc_str = str(loc_uri)
                loc_id = loc_str.split("#")[1] if "#" in loc_str else loc_str

                # Solo bacias
                if loc_id in basins and basins[loc_id]["labels"]:
                    synonyms = basins[loc_id]["labels"]
                    # (opcional) ordena y deduplica sinónimos de cada bacia
                    synonyms = sorted(dict.fromkeys(synonyms), key=str.lower)
                    basins_subanswers.append(synonyms)
                    basins_context_parts.append(format_with_synonyms(synonyms))

            if basins_subanswers:
                # (opcional) ordenar/eliminar duplicados a nivel bacia
                # normaliza por la primera etiqueta
                unique_by_main = {}
                for syns in basins_subanswers:
                    main = syns[0]
                    unique_by_main[main] = syns
                basins_subanswers = list(unique_by_main.values())
                basins_context_parts = [format_with_synonyms(s) for s in basins_subanswers]

                context_text = ", ".join(basins_context_parts)
                id_counter += 1
                questions.append({
                    "id": id_counter,
                    "level": 1,
                    "question": f"Em que bacia está localizado o poço {well_name_principal}?",
                    "answer": basins_subanswers,
                    "context": f"O poço {well_name_principal} está localizado na(s) bacia(s): {context_text}."
                })


        # --- Campos do poço (CORREGIDO) ---
        loc_uris = info["located_in"]
        if loc_uris:

            fields_subanswers = []
            fields_context_parts = []

            well_name_principal = get_primary_label(info["labels"], fallback=well_uri)

            for loc_uri in loc_uris:
                loc_str = str(loc_uri)
                loc_id = loc_str.split("#")[1] if "#" in loc_str else loc_str
                
                #Solo campos
                if loc_id in fields and fields[loc_id]["labels"]:

                    synonyms = fields[loc_id]["labels"]
                    synonyms = sorted(dict.fromkeys(synonyms), key=str.lower)
                    fields_subanswers.append(synonyms)
                    fields_context_parts.append(format_with_synonyms(synonyms))

            if fields_subanswers:
                context_text = ", ".join(fields_context_parts)
                id_counter += 1
                questions.append({
                    "id": id_counter,
                    "level": 2, # Nivel verificado 1-HOP
                    "question": f"Em que campo está localizado o poço {well_name_principal}?",
                    "answer": fields_subanswers,
                    "context": f"O poço {well_name_principal} está localizado no(s) campo(s): {context_text}."
                })

        # --- Formations crossed by the well ---
        if info["crosses"]:
            subanswers = []
            context_parts = []

            well_name_principal = get_primary_label(info["labels"], fallback=well_uri)

            for cross_uri_str in info["crosses"]:
                cross_id = cross_uri_str.split("#")[1] if "#" in cross_uri_str else cross_uri_str

                if cross_id in formations and formations[cross_id]["labels"]:
                    synonyms = formations[cross_id]["labels"]
                else:
                    label_found = graph.value(URIRef(cross_uri_str), rdfs.label)
                    synonyms = [str(label_found)] if label_found else [cross_id]

                subanswers.append(synonyms)
                context_parts.append(format_with_synonyms(synonyms))

            if subanswers:
                context_text = ", ".join(context_parts)
                id_counter += 1
                questions.append({
                    "id": id_counter,
                    "level": 2, # Nivel verificado 1-HOP
                    "question": f"Que unidades litoestratigráficas o poço {well_name_principal} atravessa?",
                    "answer": subanswers,
                    "context": f"O poço {well_name_principal} atravessa: {context_text}."
                })

    # ===============================================================
    # 4) FORMATIONS
    # ===============================================================
    for formation_uri, info in formations.items():
        formation_names = info["labels"]
        formation_name_principal = get_primary_label(formation_names, fallback=formation_uri)

        if info["carrier_of"]:
            subanswers = []
            context_parts = []
            for carrier_uri in info["carrier_of"]:
                carrier_str = str(carrier_uri)
                carrier_id = carrier_str.split("#")[1] if "#" in carrier_str else carrier_str

                label_found = graph.value(URIRef(carrier_uri), rdfs.label)
                synonyms = [str(label_found)] if label_found else [carrier_id]

                subanswers.append(synonyms)
                context_parts.append(format_with_synonyms(synonyms))

            if subanswers:
                context_text = ", ".join(context_parts)
                id_counter += 1
                questions.append({
                    "id": id_counter,
                    "level": 2, # Nivel verificado 1-HOP
                    "question": f"Que estruturas geológicas são apresentadas por {formation_name_principal}?",
                    "answer": subanswers,
                    "context": (
                        f"{formation_name_principal} apresenta as seguintes estruturas geológicas: "
                        + context_text + "."
                    )
                })

    # ===============================================================
    # 5) SPARQL: "Quantos poços no CAMPO X?" / "Quais poços no CAMPO X?"
    # ===============================================================
    query_wells_in_field = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <http://www.semanticweb.org/bg40/ontologies/2022/5/untitled-ontology-2#>

        SELECT ?field ?well (COUNT(?well) as ?pozos)
               (GROUP_CONCAT(?wellName; separator=", ") as ?wellNames)
        WHERE {
            ?well rdf:type ont:well .
            ?field rdf:type ont:field .
            ?well ont:located_in ?field .
            {
                SELECT ?well (SAMPLE(?name) AS ?wellName)
                WHERE {
                    ?well rdfs:label ?name .
                }
                GROUP BY ?well
            }
        }
        GROUP BY ?field
    """
    results = graph.query(query_wells_in_field)
    for row in results:
        field_uri = row.field
        wellNames = str(row.wellNames).split(", ") if row.wellNames else []

        field_labels = list(graph.objects(field_uri, rdfs.label))
        field_labels_str = [str(x) for x in field_labels] if field_labels else []
        field_label_principal = get_primary_label(field_labels_str, fallback=str(field_uri))


        subanswers = []
        context_parts = []
        for w_name in wellNames:
            subanswers.append([w_name])
            context_parts.append(w_name)

        if subanswers:
            context_text = ", ".join(context_parts)
            id_counter += 1
            questions.append({
                "id": id_counter,
                "level": 2,  # Nivel verificado 1-HOP
                "question": f"Quais são os poços localizados no campo {field_label_principal}?",
                "answer": subanswers,
                "context": (
                    f"No campo {field_label_principal} estão localizados os poços: {context_text}."
                )
            })

    # ===============================================================
    # 7) Contar campos/poços por bacia
    # ===============================================================

    pozos_por_bacia = {}

    for well_uri, well_info in wells.items():

        well_name_principal = get_primary_label(well_info["labels"], fallback=str(well_uri))
        
        if well_info["located_in"]:

            bacia_ref = well_info["located_in"][0]
            bacia_id = bacia_ref.split("#")[1] if "#" in bacia_ref else bacia_ref
            
            if bacia_id.startswith("BASE_CD_BACIA"):

                label_value = graph.value(
                    URIRef(f"http://www.semanticweb.org/bg40/ontologies/2022/5/untitled-ontology-2#{bacia_id}"), 
                    rdfs.label
                )
                if label_value:
                    bacia_label = str(label_value).title()
                else:
                    bacia_label = bacia_id

                if bacia_label not in pozos_por_bacia:
                    pozos_por_bacia[bacia_label] = []
                pozos_por_bacia[bacia_label].append(well_name_principal)


    for bacia_label_principal, wells_list in pozos_por_bacia.items():

        wells_list = list(set(wells_list))
        count_pozos = len(wells_list)


        id_counter += 1
        questions.append({
            "id": id_counter,         
            "level": 2,  # Nivel verificado 1-HOP
            "question": f"Quantos poços estão localizados na bacia {bacia_label_principal}?",
            "answer": [[str(count_pozos)]],
            "context": f"Existem {count_pozos} poços localizados na bacia {bacia_label_principal}."
        })


    # ===============================================================
    # 8) PREGUNTAS MULTI-HOP
    # ===============================================================


    fluids_query = """
        SELECT ?fluid ?label
        WHERE {
            ?fluid rdfs:subClassOf* <http://www.semanticweb.org/bg40/ontologies/2022/5/untitled-ontology-2#o&g_earth_fluid> .
            ?fluid rdfs:label ?label .
        }
    """

    results_fluids = graph.query(fluids_query)

    list_fluids = list(set([str(row.label) for row in results_fluids]))


    fluids_dict = {}

    for row in results_fluids:
        fluid_uri_str = str(row.fluid)
        fluid_label_str = str(row.label)
        if fluid_uri_str not in fluids_dict:
            fluids_dict[fluid_uri_str] = set()
        fluids_dict[fluid_uri_str].add(fluid_label_str)

    for f_uri in fluids_dict:
        fluids_dict[f_uri] = sorted(list(fluids_dict[f_uri]))


    query_multihop_lithology = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX ont: <http://www.semanticweb.org/bg40/ontologies/2022/5/untitled-ontology-2#>

        SELECT ?well ?lithology_label 
            (GROUP_CONCAT(DISTINCT STRAFTER(STR(?lithostratigraphic_unit), "#"); separator=", ") AS ?units)
        WHERE {
            ?well rdf:type ont:well .
            ?lithostratigraphic_unit rdf:type ont:lithostratigraphic_unit .
            ?lithostratigraphic_unit ont:constituted_by ?lithology .
            ?well ont:crosses ?lithostratigraphic_unit .
            ?lithology rdfs:label ?lithology_label .
        }
        GROUP BY ?well ?lithology_label
    """
    results_multiB = graph.query(query_multihop_lithology)

    for row in results_multiB:
        well_uri = row.well
        lithology_label = str(row.lithology_label)
        units_str = row.units.toPython() if row.units else ""

        well_label = graph.value(well_uri, rdfs.label)
        well_id = well_uri.split("#")[1] if "#" in well_uri else str(well_uri)
        well_label_str = str(well_label) if well_label else well_id
        well_name_principal = get_primary_label([well_label_str], fallback=well_uri)

        if units_str:
            splitted_units = units_str.split(", ")
            unit_labels = []

            for local_id in splitted_units:
                full_uri = URIRef(f"http://www.semanticweb.org/bg40/ontologies/2022/5/untitled-ontology-2#{local_id}")
                label_found = graph.value(full_uri, rdfs.label)
                
                unit_labels.append(str(label_found) if label_found else local_id)

            if unit_labels:
                subanswers = [unit_labels]
                units_text = ", ".join(unit_labels)

                multihop_questions.append({
                    "level": 3, # Nivel verificado MULTI-HOP
                    "question": (
                        f"Que unidades litoestratigráficas o poço {well_name_principal} atravessa "
                        f"que são constituídas por rochas do tipo {lithology_label}?"
                    ),
                    "answer": subanswers,
                    "context": (
                        f"O poço {well_name_principal} atravessa as seguintes unidades litoestratigráficas "
                        f"compostas por rochas do tipo {lithology_label}: {units_text}."
                    )
                })

    if random_sample:
        random.seed(2025)
        multihop_questions = random.sample(multihop_questions, min(343, len(multihop_questions)))

    for q in multihop_questions:
        id_counter += 1
        q["id"] = id_counter
        questions.append(q)
    

    materials_to_formations = {}
    for fluid_class_uri_str in fluids_dict.keys():
        materials_to_formations[fluid_class_uri_str] = set()

    for form_uri, form_info in formations.items():
        formation_labels = form_info.get("labels", [])

        if "constituted_by" in form_info:
            for mat_uri in form_info["constituted_by"]:

                for tipo_uri in graph.objects(URIRef(mat_uri), rdf.type):
                    tipo_uri_str = str(tipo_uri)

                   
                    if tipo_uri_str in fluids_dict:
                        if formation_labels:
                            materials_to_formations[tipo_uri_str].add(formation_labels[0])
                        else:
                           
                            materials_to_formations[tipo_uri_str].add(form_uri.split("#")[-1])


    for fluid_uri_str, formation_labels_set in materials_to_formations.items():

        fluid_synonyms = fluids_dict[fluid_uri_str]
        fluid_name_formatted = format_with_synonyms(fluid_synonyms)

        if formation_labels_set:
            subanswers = []
            context_parts = []

            for formation_label in formation_labels_set:
                found = False
                for furi, finfo in formations.items():
                    if formation_label in finfo.get("labels", []):
                        synonyms = finfo["labels"]
                        subanswers.append(synonyms)
                        context_parts.append(format_with_synonyms(synonyms))
                        found = True
                        break
                if not found:
                    subanswers.append([formation_label])
                    context_parts.append(formation_label)

            if subanswers:
                context_text = ", ".join(context_parts)
                id_counter += 1
                questions.append({
                    "id": id_counter,
                    "level": 2, # Nivel verificado 1-HOP
                    "question": (
                        f"Que unidades litoestratigráficas são constituídas "
                        f"por fluido {fluid_name_formatted}?"
                    ),
                    "answer": subanswers,
                    "context": (
                        f"As unidades litoestratigráficas constituídas por {fluid_name_formatted} "
                        f"são: {context_text}."
                    )
                })


    fluids_to_formations = {
        mat_name: formations_list
        for mat_name, formations_list in materials_to_formations.items()
        if mat_name in list_fluids
    }



    for fluid_uri_str, formation_labels_set in materials_to_formations.items():

        fluid_synonyms = fluids_dict.get(fluid_uri_str, [])
        fluid_name_formatted = format_with_synonyms(fluid_synonyms)

        if formation_labels_set:
            combined_ages = set()
            combined_formations_context = []

            for form_label in formation_labels_set:
                found = False
                for form_uri, form_info in formations.items():
                    if "labels" in form_info and form_label in form_info["labels"]:

                        if "has_age" in form_info:
                            for age_uri in form_info["has_age"]:
                                age_label = graph.value(URIRef(age_uri), rdfs.label)
                                if age_label:
                                    combined_ages.add(str(age_label))
                        

                        if form_info["labels"]:
                            combined_formations_context.append(format_with_synonyms(form_info["labels"]))
                        else:
                            combined_formations_context.append(form_label)
                        
                        found = True
                        break
                if not found:
                    combined_formations_context.append(form_label)

            if combined_ages:
                all_ages = ", ".join(sorted(combined_ages))
                formations_str = ", ".join(combined_formations_context)

                id_counter += 1
                questions.append({
                    "id": id_counter,
                    "level": 3, # Nivel verificado MULTI-HOP
                    "question": (
                        f"Qual a idade geológica das unidades litoestratigráficas "
                        f"constituídas por {fluid_name_formatted}?"
                    ),
                    "answer": [[age] for age in sorted(combined_ages)],
                    "context": (
                        f"A idade geológica das formações {formations_str} constituídas por {fluid_name_formatted} "
                        f"é {all_ages}."
                    )
                })

    for fluid_uri_str, formation_labels_set in materials_to_formations.items():
        fluid_synonyms = fluids_dict.get(fluid_uri_str, [])
        fluid_name_formatted = format_with_synonyms(fluid_synonyms)

        # 1. Quantos poços atravessam
        wells_set = set()
        for well_uri, well_info in wells.items():
            if "crosses" in well_info and well_info["crosses"]:
                for cross_uri in well_info["crosses"]:
                    cross_id = cross_uri.split("#")[-1]
                    if cross_id in formations:
                        for mat_uri in formations[cross_id].get("constituted_by", []):
                            for tipo_uri in graph.objects(URIRef(mat_uri), rdf.type):
                                if str(tipo_uri) == fluid_uri_str:
                                    wells_set.add(str(well_uri))

        if wells_set:
            id_counter += 1
            questions.append({
                "id": id_counter,
                "level": 3, # Nivel verificado MULTI-HOP
                "question": f"Quantos poços atravessam unidades litoestratigráficas constituídas por {fluid_name_formatted}?",
                "answer": [[str(len(wells_set))]],
                "context": f"Existem {len(wells_set)} poços que atravessam unidades litoestratigráficas constituídas por {fluid_name_formatted}."
            })

        # 2. Em quais bacias
        bacias_set = set()
        for form_uri, form_info in formations.items():
            if set(form_info.get("labels", [])) & formation_labels_set:
                for loc_uri in form_info.get("located_in", []):
                    loc_id = loc_uri.split("#")[-1]
                    if loc_id in basins:
                        bacia_label = get_primary_label(basins[loc_id]["labels"], fallback=loc_id)
                        bacias_set.add(bacia_label)

        if bacias_set:
            subanswers = []
            context_parts = []
            for bacia_label in bacias_set:
                found = False
                for basin_uri, basin_info in basins.items():
                    if bacia_label in basin_info.get("labels", []):
                        synonyms = basin_info["labels"]
                        subanswers.append(synonyms)
                        context_parts.append(format_with_synonyms(synonyms))
                        found = True
                        break
                if not found:
                    subanswers.append([bacia_label])
                    context_parts.append(bacia_label)

            context_text = ", ".join(context_parts)
            id_counter += 1
            questions.append({
                "id": id_counter,
                "level": 3, # Nivel verificado MULTI-HOP
                "question": f"Em quais bacias estão as unidades litoestratigráficas constituídas por {fluid_name_formatted}?",
                "answer": subanswers,
                "context": f"As unidades litoestratigráficas constituídas por {fluid_name_formatted} estão localizadas na(s) bacia(s): {context_text}."
            })

        # 3. Em quais campos
        fields_set = set()
        for well_uri, well_info in wells.items():
            if "crosses" in well_info and well_info["crosses"]:
                for cross_uri in well_info["crosses"]:
                    cross_id = cross_uri.split("#")[-1]
                    if cross_id in formations:
                        for mat_uri in formations[cross_id].get("constituted_by", []):
                            for tipo_uri in graph.objects(URIRef(mat_uri), rdf.type):
                                if str(tipo_uri) == fluid_uri_str:
                                    for loc_uri2 in well_info.get("located_in", []):
                                        loc_id2 = loc_uri2.split("#")[-1]
                                        if loc_id2 in fields:
                                            labels = fields[loc_id2].get("labels", [])
                                            fields_set.add(labels[0] if labels else loc_id2)

        if fields_set:
            subanswers = []
            context_parts = []
            for field_label in fields_set:
                found = False
                for field_uri, field_info in fields.items():
                    if field_label in field_info.get("labels", []):
                        synonyms = field_info["labels"]
                        subanswers.append(synonyms)
                        context_parts.append(format_with_synonyms(synonyms))
                        found = True
                        break
                if not found:
                    subanswers.append([field_label])
                    context_parts.append(field_label)

            context_text = ", ".join(context_parts)
            id_counter += 1
            questions.append({
                "id": id_counter,
                "level": 3, # Nivel verificado MULTI-HOP
                "question": f"Em quais campos estão as unidades litoestratigráficas constituídas por {fluid_name_formatted}?",
                "answer": subanswers,
                "context": f"As unidades litoestratigráficas constituídas por {fluid_name_formatted} estão nos seguintes campos: {context_text}."
            })

        # 4. Quais estruturas geológicas
        struct_set = set()
        for form_uri, form_info in formations.items():
            if set(form_info.get("labels", [])) & formation_labels_set:
                for struct_uri in form_info.get("carrier_of", []):
                    label = graph.value(URIRef(struct_uri), rdfs.label)
                    if label:
                        struct_set.add(str(label))

        if struct_set:
            context_text = ", ".join(struct_set)
            id_counter += 1
            questions.append({
                "id": id_counter,
                "level": 3, # Nivel verificado MULTI-HOP
                "question": f"Quais estruturas geológicas ocorrem nas unidades litoestratigráficas constituídas por {fluid_name_formatted}?",
                "answer": [[s] for s in struct_set],
                "context": f"As unidades litoestratigráficas constituídas por {fluid_name_formatted} apresentam as seguintes estruturas geológicas: {context_text}."
            })



    structure_to_formations_map = {}
    for form_uri, form_info in formations.items():
        if "carrier_of" in form_info and form_info["carrier_of"]:
            for struct_uri in form_info["carrier_of"]:

                struct_id_parts = struct_uri.split("#")[-1].split('_')
                struct_id = '_'.join(struct_id_parts[:7])  

                if struct_id not in structure_to_formations_map:
                    structure_to_formations_map[struct_id] = set()
                structure_to_formations_map[struct_id].add(form_uri)


    structure_to_fields_map = {}
    for struct_id, form_set in structure_to_formations_map.items():
        structure_to_fields_map[struct_id] = set()

    for well_uri, well_info in wells.items():
        if well_info.get("crosses"):
            crosses_ids = {c.split("#")[-1] for c in well_info["crosses"]}


            for struct_id, form_set in structure_to_formations_map.items():
                if form_set.intersection(crosses_ids):
                    if "located_in" in well_info:
                        for loc_uri in well_info["located_in"]:
                            loc_id = loc_uri.split("#")[-1]
                            if loc_id in fields:

                                f_labels = fields[loc_id].get("labels", [])
                                field_name = f_labels[0] if f_labels else loc_id

                                if structure_to_fields_map[struct_id] is None:
                                    structure_to_fields_map[struct_id] = set()
                                structure_to_fields_map[struct_id].add(field_name)

    for struct_id, field_set in structure_to_fields_map.items():
        if field_set:
            struct_label = graph.value(
                URIRef(f"http://www.semanticweb.org/bg40/ontologies/2022/5/untitled-ontology-2#{struct_id}"),
                rdfs.label
            )
            struct_label_str = str(struct_label) if struct_label else struct_id

            fields_list = sorted(list(field_set))
            fields_text = ", ".join(fields_list)

            id_counter += 1
            questions.append({
                "id": id_counter,
                "level": 3, # Nivel verificado MULTI-HOP
                "question": (
                    f"Em quais campos estão as unidades litoestratigráficas que apresentam a estrutura geológica {struct_label_str}?"
                ),
                "answer": [fields_list],
                "context": (
                    f"As unidades litoestratigráficas que apresentam a estrutura geológica {struct_label_str} "
                    f"estão nos seguintes campos: {fields_text}."
                )
            })


    # ===============================================================
    # 9) O QUÉ É UMA ROCHA?
    # ===============================================================


    query_describe_rock = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX ont: <http://www.semanticweb.org/bg40/ontologies/2022/5/untitled-ontology-2#>

    SELECT ?rock ?label_pt ?definition_pt
    WHERE {
        ?rock rdfs:subClassOf ont:rock .
        ?rock rdfs:label ?label_pt .
        ?rock skos:definition ?definition_pt .

        FILTER (lang(?label_pt) = "pt")
        FILTER (lang(?definition_pt) = "pt")
    }
    """

    results = graph.query(query_describe_rock)
    results_list = list(results)

    rock_data = {}

    for row in results_list:
        rock_uri = str(row.rock)
        rock_label = str(row.label_pt)
        rock_definition = str(row.definition_pt)

        if rock_uri not in rock_data:
            rock_data[rock_uri] = (rock_label, rock_definition)

    for rock_uri, (rock_label, rock_definition) in rock_data.items():

        id_counter += 1
        questions.append({
            "id": id_counter,
            "level": 4, #definition verified
            "question": f"O que é um(a) {rock_label}?",
            "answer": [[rock_definition]],
            "context": rock_definition
        })



    # ===============================================================
    # 10) PREGUNTAS – Quantos poços da [BACIA] atravessam unidades litoestratigráficas que são constituídas por rochas do tipo [LITOLOGIA]?
    # ===============================================================

    lithologies_to_formations = {} 
    for form_uri, form_info in formations.items():
        form_id = form_uri  

        for mat_uri in form_info.get("constituted_by", []):
            mat_label = graph.value(URIRef(mat_uri), rdfs.label)
            mat_label_str = str(mat_label) if mat_label else mat_uri.split("#")[-1]

            if mat_label_str not in lithologies_to_formations:
                lithologies_to_formations[mat_label_str] = set()
            lithologies_to_formations[mat_label_str].add(form_id)

    basin_to_wells = {} 

    for basin_uri, basin_info in basins.items():
        basin_id = basin_uri.split("#")[-1]
        basin_to_wells[basin_id] = set()

    for well_uri, well_info in wells.items():
        for loc_uri in well_info.get("located_in", []):
            loc_id = loc_uri.split("#")[-1]
            if loc_id in basin_to_wells:
                basin_to_wells[loc_id].add(well_uri)

    for basin_uri, basin_info in basins.items():
        basin_id = basin_uri.split("#")[-1]
        basin_label = get_primary_label(basin_info["labels"], fallback=basin_id)

        wells_in_basin = basin_to_wells[basin_id] 

        for litologia, formacao_ids in lithologies_to_formations.items():

            wells_count = 0
            wells_that_cross = []  

            for w_uri in wells_in_basin:
                w_info = wells[w_uri]
                crosses = w_info.get("crosses", []) 

                found_match = False
                for f_uri in crosses:
                    f_id = f_uri.split("#")[-1]
                    if f_id in formacao_ids:
                        found_match = True
                        break
                if found_match:
                    wells_count += 1
                    wells_that_cross.append(w_uri)

            if wells_count > 0:
                id_counter += 1
                questions.append({
                    "id": id_counter,
                    "level": 3, # Nivel verificado MULTI-HOP
                    "question": (
                        f"Quantos poços da bacia {basin_label} atravessam unidades litoestratigráficas "
                        f"que são constituídas por rochas do tipo {litologia}?"
                    ),
                    "answer": [[str(wells_count)]],
                    "context": (
                        f"Na bacia {basin_label}, {wells_count} poços atravessam unidades litoestratigráficas "
                        f"com rochas do tipo {litologia}."
                    )
                })


    # ===============================================================
    # 11) Descreva a [UNIDADE CRONOESTRATIGRÁFICA]
    # ===============================================================

    query_describe_chronounit = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX ont: <http://www.semanticweb.org/bg40/ontologies/2022/5/untitled-ontology-2#>

    SELECT DISTINCT ?unit ?label_pt ?definition_pt
    WHERE {
        ?unit rdf:type ont:geological_time_interval .
        ?unit rdfs:label ?label_pt .
        FILTER(lang(?label_pt) = "pt") .
        ?unit skos:definition ?definition_pt .
        FILTER(lang(?definition_pt) = "pt") .
    }
    """
    results = graph.query(query_describe_chronounit) 
    results_list = list(results)

    unit_to_data = {}

    for row in results_list:
        unit = str(row[0])
        label_pt = str(row[1])
        definition_pt = str(row[2])

        if unit not in unit_to_data:
            unit_to_data[unit] = (label_pt, definition_pt)

    for unit, (label_pt, definition_pt) in unit_to_data.items():

        id_counter += 1
        questions.append({
            "id": id_counter,
            "level": 4, # definition verified
            "question": f"Descreva a unidade cronoestratigráfica {label_pt}.",
            "answer": [[definition_pt]],
            "context": definition_pt
        })

    return questions

def filter_level_zero(questions):
    """Devuelve solo las preguntas con level=0."""
    return [q for q in questions if q.get("level") == 0]

def filter_one_hop(questions, levels=(1, 2)):
    """Devuelve solo las preguntas cuyo level esté en los niveles indicados."""
    return [q for q in questions if q.get("level") in levels]

def filter_multi_hop(questions):
    """Devuelve solo las preguntas con level=3."""
    return [q for q in questions if q.get("level") == 3]

def filter_definition(questions):
    """Devuelve solo las preguntas con level=4."""
    return [q for q in questions if q.get("level") == 4]



fields, basins, wells, formations = gen_info(g)
print("✅ Successfully loaded all graph components.")
print(f"✅ Generated info for {len(fields)} fields, {len(basins)} basins, {len(wells)} wells, {len(formations)} formations.")
questions_balanced = gen_questions(fields, basins, wells, formations, g, random_sample=True)
questions_unbalanced = gen_questions(fields, basins, wells, formations, g, random_sample=False)

with open("PetroKGraph_text_dataset_balanced_complete.json", "w", encoding='utf-8') as f:
    json.dump(questions_balanced, f, ensure_ascii=False, indent=4)
print(f"✅ Saved {len(questions_balanced)} balanced questions to PetroKGraph_text_dataset_balanced_complete.json")

with open("PetroKGraph_text_dataset_unbalanced_complete.json", "w", encoding='utf-8') as f:
    json.dump(questions_unbalanced, f, ensure_ascii=False, indent=4)
print(f"✅ Saved {len(questions_unbalanced)} unbalanced questions to PetroKGraph_text_dataset_unbalanced_complete.json")

# 🔹 Filtramos solo las de level=0
questions_balanced_level0 = filter_level_zero(questions_balanced)
questions_balanced_one_hop = filter_one_hop(questions_balanced)
questions_balanced_multi_hop = filter_multi_hop(questions_balanced)
questions_balanced_definition = filter_definition(questions_balanced)

output_path = os.path.join(data_dir, "PetroKGraph_dataset_aggregation.json")
with open(output_path, "w", encoding='utf-8') as f:
    json.dump(questions_balanced_level0, f, ensure_ascii=False, indent=4)
print(f"✅ Saved {len(questions_balanced_level0)} aggregation questions.")

output_path_1hop = os.path.join(data_dir, "PetroKGraph_dataset_1hop.json")
with open(output_path_1hop, "w", encoding='utf-8') as f:
    json.dump(questions_balanced_one_hop, f, ensure_ascii=False, indent=4)
print(f"✅ Saved {len(questions_balanced_one_hop)} one-hop questions.")

output_path_multi_hop = os.path.join(data_dir, "PetroKGraph_dataset_multi_hop.json")
with open(output_path_multi_hop, "w", encoding='utf-8') as f:
    json.dump(questions_balanced_multi_hop, f, ensure_ascii=False, indent=4)
print(f"✅ Saved {len(questions_balanced_multi_hop)} multi-hop questions.")

output_path_definition = os.path.join(data_dir, "PetroKGraph_dataset_definition.json")
with open(output_path_definition, "w", encoding='utf-8') as f:
    json.dump(questions_balanced_definition, f, ensure_ascii=False, indent=4)
print(f"✅ Saved {len(questions_balanced_definition)} definition questions.")