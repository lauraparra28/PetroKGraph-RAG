"""
Evaluación de respuestas (EM, F1, Group-F1, BLEU, ROUGE-L) con
RAGAS opcional (faithfulness, context_recall, context_precision, answer_relevancy).

Uso:
  # Con RAGAS (por defecto)
  python evaluate_with_gold_cypher.py --ragas --tag 1hop

  # Sin RAGAS
  python evaluate_with_gold_cypher.py --no-ragas --tag aggregation
"""
import os, re, unicodedata, json
from collections import Counter
from datetime import datetime
from tqdm import tqdm
from sklearn.metrics import f1_score
import sacrebleu
from neo4j import GraphDatabase
from main_neo4j import chain
from utils import base_utils as bu
import argparse
from typing import Any, Dict, List  

# =========================
# Configuración y utilidades
# =========================

neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "diripar8$"))

def parse_args():
    p = argparse.ArgumentParser(description="Evaluación de RAG con RAGAS opcional.")
    p.add_argument("--ragas", dest="ragas", action="store_true", help="Habilita métricas RAGAS.")
    p.add_argument("--no-ragas", dest="ragas", action="store_false", help="Deshabilita métricas RAGAS.")
    p.add_argument("--results-dir", type=str, default="results", help="Directorio de salida.")
    p.add_argument("--tag", type=str, default="definition", help="Etiqueta para prefijo de archivos.")
    return p.parse_args()

def now_tag():
    return datetime.now().strftime("%d_%m_%Y")

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    
# =========================
# Normalización y métricas
# =========================

def normalize(text: str) -> str:
    if text is None: return ""
    if isinstance(text, list): text = " ".join(map(str, text))
    text = text.replace("\n", " ").replace("\t", " ").replace("\xa0", " ")
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize_norm(s: str) -> List[str]:
    return normalize(s).split()

def flatten_answers(ans):
    if isinstance(ans, list) and ans and isinstance(ans[0], list):
        return [normalize(a) for sub in ans for a in sub]
    elif isinstance(ans, list):
        return [normalize(a) for a in ans]
    else:
        return [normalize(ans)]

def normalize_nested_list(nested_list):
    return [[normalize(item) for item in sublist] for sublist in nested_list]

def flatten_and_normalize(records):
    """
    Convierte resultados de Neo4j en un set de strings normalizados,
    ignorando claves (alias) y orden.
    """
    values = []
    for r in records:
        for v in dict(r).values():
            if isinstance(v, list):
                values.extend(v)
            else:
                values.append(v)
    # normaliza y deja como set
    return set(normalize(str(x)) for x in values if x is not None)

# =============================================
# Métrica Execution Accuracy (EA)
# =============================================

def execution_accuracy(pred_cypher: str, gold_cypher: str, driver: GraphDatabase.driver) -> bool:
    """
    Evalúa si la query generada (pred_cypher) es semánticamente correcta comparando
    sus resultados con la query dorada (gold_cypher).

    Retorna True si ambos resultados son idénticos, False en caso contrario.
    """
    try:
        with neo4j_driver.session() as session:
            # Ejecutar gold
            gold_results = list(session.run(gold_cypher))
            # Ejecutar predicción
            pred_results = list(session.run(pred_cypher))

            # Normalizar resultados para comparar (orden y tipos)
            gold_set = flatten_and_normalize(gold_results)
            pred_set = flatten_and_normalize(pred_results)
            print("Gold Results:", gold_set)
            print("Pred Results:", pred_set)

        # Comparación exacta
        if gold_set == pred_set:
            print("✅ Execution Accuracy: Las queries producen resultados idénticos.")
        return gold_set == pred_set

    except Exception as e:
        # Si hay error de sintaxis o ejecución en la query generada
        print("❌ Error al ejecutar la query generada")
        return False

# =========================
# Context helpers
# =========================

def to_ctx_strings(ctx) -> List[str]:
    if ctx is None: return []
    if isinstance(ctx, str): return [ctx]
    if isinstance(ctx, list):
        out = []
        for item in ctx:
            out.extend(to_ctx_strings(item))
        out = [s for s in (x.strip() for x in out) if s]
        return list(dict.fromkeys(out))
    if isinstance(ctx, dict):
        parts = []
        for v in ctx.values():
            if isinstance(v, str): parts.append(v)
            elif isinstance(v, list) and all(isinstance(x, str) for x in v):
                parts.extend(v)
        return ["; ".join(p for p in parts if p)] if parts else [json.dumps(ctx, ensure_ascii=False)]
    return [str(ctx)]

def to_ctx_strings_pretty(ctx) -> List[str]:
    if isinstance(ctx, list) and ctx and isinstance(ctx[0], dict) and "f.rdfs_label" in ctx[0]:
        labels = []
        for d in ctx:
            labels.extend(d.get("f.rdfs_label", []) or [])
        labels = sorted(set(x for x in labels if isinstance(x, str) and x.strip()))
        return ["; ".join(labels)] if labels else []
    return to_ctx_strings(ctx)

# =========================
# RAGAS Metrics
# =========================

def run_ragas_metrics(question: str, contexts: List[str], pred: str, golds_flat: List[str]) -> Dict[str, float]:
    """
    Importa RAGAS dinámicamente para evitar dependencia si está desactivado.
    Devuelve dict con métricas RAGAS.
    """
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, context_recall, context_precision, answer_relevancy

    ground_truth_str = ", ".join(golds_flat)
    ragas_data = Dataset.from_dict({
        "question": [question],
        "contexts": [contexts],
        "answer": [pred],
        "ground_truth": [ground_truth_str],
    })
    res = evaluate(
        ragas_data,
        metrics=[faithfulness, context_recall, context_precision, answer_relevancy]
    )
    row = res.to_pandas().iloc[0].to_dict()
    return {
        "faithfulness": float(row["faithfulness"]),
        "context_recall": float(row["context_recall"]),
        "context_precision": float(row["context_precision"]),
        "answer_relevancy": float(row["answer_relevancy"]),
    }

# =========================
# Main
# =========================

def main():
    args = parse_args()
    ensure_dir(args.results_dir)

    fecha = now_tag()
    output_file = os.path.join(args.results_dir, f"Gold_cypher_{args.tag}_evaluation_results_{fecha}.jsonl")
    final_metrics_file = os.path.join(args.results_dir, f"Gold_cypher_{args.tag}_final_metrics_{fecha}.json")
    print("📁 Archivos preparados:", output_file, "|", final_metrics_file)
    print(f"⚙️  RAGAS habilitado: {args.ragas}")

    # Dataset
    dataset = bu.load_dataset()[f"PetroKGraph_dataset_gold_cypher_{args.tag}_400.json"]
    print("✅ Dataset cargado")

    # Acumuladores
    n = len(dataset)
    EA_count = 0
    # Acumuladores RAGAS (sólo si habilitado)
    ragas_acc = {"faithfulness": [], "context_recall": [], "context_precision": [], "answer_relevancy": []} if args.ragas else None

    # Limpia JSONL
    open(output_file, "w", encoding="utf-8").close()

    for ex in tqdm(dataset):
        qid = ex["id"]
        question = ex["question"]
        golds_flat = sorted(set(flatten_answers(ex["answer"])))

        # Llama a tu cadena
        out = chain.invoke({"query": question})
        
        contexts_raw = out["intermediate_steps"][1]["context"]
        contexts = to_ctx_strings_pretty(contexts_raw)

        # Pred normalizada
        pred = normalize(out["result"])

        correct = 0
        total = 0

        # Métricas de texto
        gold__Cypher = ex["gold_cypher"]
        pred_cypher = out["intermediate_steps"][0]["query"]
            
        if execution_accuracy(pred_cypher, gold__Cypher, neo4j_driver):
            correct += 1
            EA_count += 1
        total += 1




        # RAGAS opcional
        ragas_dict = None
        if args.ragas:
            ragas_dict = run_ragas_metrics(question, contexts, pred, golds_flat)
            # acumula
            for k in ragas_acc:
                ragas_acc[k].append(ragas_dict[k])

        # Escribe línea JSONL
        result_line = {
            "id": qid,
            "question": question,
            "gold": golds_flat,
            "pred": pred,
            "execution_accuracy": correct,
            
        }
        if ragas_dict is not None:
            result_line["ragas"] = ragas_dict

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(result_line, indent=4, ensure_ascii=False) + "\n")

    # Agrega resultados finales
    
    EA_score = EA_count / n if n else 0.0    
    execution_acc = correct / n if n else 0.0
    # F1, BLEU, ROUGE-L no aplican aquí (solo EA)
    print("\n * * * MÉTRICAS FINALES (Cypher) * * *")
    print(f"Execution Accuracy: {EA_score:.2%}")

    final_metrics = {
        "total_examples": n,
        "Execution Accuracy": EA_score,
        
    }

    if args.ragas and ragas_acc is not None and n:
        faithfulness_avg      = sum(ragas_acc["faithfulness"])/n
        context_recall_avg    = sum(ragas_acc["context_recall"])/n
        context_precision_avg = sum(ragas_acc["context_precision"])/n
        answer_relevancy_avg  = sum(ragas_acc["answer_relevancy"])/n

        print("\n * * * MÉTRICAS FINALES (RAGAS) * * *")
        print(f"Faithfulness:      {faithfulness_avg:.3%}")
        print(f"Answer Relevancy:  {answer_relevancy_avg:.3%}")
        print(f"Context Recall:    {context_recall_avg:.3%}")
        print(f"Context Precision: {context_precision_avg:.3%}")

        final_metrics.update({
            "RAGAS Faithfulness": faithfulness_avg,
            "RAGAS Answer Relevancy": answer_relevancy_avg,
            "RAGAS Context Recall": context_recall_avg,
            "RAGAS Context Precision": context_precision_avg,
        })
    else:
        print("\n(RAGAS deshabilitado: se omiten métricas RAGAS)")

    with open(final_metrics_file, "w", encoding="utf-8") as f:
        json.dump(final_metrics, f, indent=4, ensure_ascii=False)
    

    print("\n📁 Resultados guardados en:")
    print("  - JSONL por ejemplo:", output_file)
    print("  - Resumen final:     ", final_metrics_file)

if __name__ == "__main__":
    main()