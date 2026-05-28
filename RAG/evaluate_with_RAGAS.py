"""
Evaluación de respuestas (EM, F1, Group-F1, BLEU, ROUGE-L) con
RAGAS opcional (faithfulness, context_recall, context_precision, answer_relevancy).

Uso:
  # Con RAGAS (por defecto)
  python evaluate_with_RAGAS.py --ragas --tag 1hop

  # Sin RAGAS
  python evaluate_ragas.py --no-ragas --tag 1hop
"""
import os, re, unicodedata, json
from collections import Counter
from datetime import datetime
from tqdm import tqdm
from sklearn.metrics import f1_score
import sacrebleu
from main_neo4j import chain
from utils import base_utils as bu
import argparse
from typing import Any, Dict, List  

# =========================
# Configuración y utilidades
# =========================

def parse_args():
    p = argparse.ArgumentParser(description="Evaluación de RAG con RAGAS opcional.")
    p.add_argument("--ragas", dest="ragas", action="store_true", help="Habilita métricas RAGAS.")
    p.add_argument("--no-ragas", dest="ragas", action="store_false", help="Deshabilita métricas RAGAS.")
    p.add_argument("--results-dir", type=str, default="results", help="Directorio de salida.")
    p.add_argument("--tag", type=str, default="aggregation", help="Etiqueta para prefijo de archivos.")
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

# =============================================
# Métricas (EM, F1, Group-F1, BLEU, ROUGE-L)
# =============================================

def token_f1(pred: str, gold: str) -> float:
    ptoks, gtoks = tokenize_norm(pred), tokenize_norm(gold)
    if not ptoks or not gtoks: return 0.0
    pc, gc = Counter(ptoks), Counter(gtoks)
    overlap = sum((pc & gc).values())
    if overlap == 0: return 0.0
    precision = overlap / len(ptoks)
    recall    = overlap / len(gtoks)
    return 2 * precision * recall / (precision + recall)

def best_token_f1(pred: str, golds: List[str]) -> float:
    return max((token_f1(pred, g) for g in golds), default=0.0)

def to_group_format(ans):
    if isinstance(ans, str): return [[normalize(ans)]]
    if isinstance(ans, list) and all(isinstance(x, str) for x in ans):
        return [[x] for x in ans]
    if isinstance(ans, list) and all(isinstance(x, list) for x in ans):
        return ans
    return [[normalize(ans)]]

def group_f1(pred: str, gold_groups: List[List[str]]) -> float:
    ptoks = normalize(pred)
    pred_entities = set(ptoks.split())
    matched = 0
    for group in gold_groups:
        group_norm = [normalize(x) for x in group]
        if any(g in ptoks for g in group_norm):
            matched += 1
    if not pred_entities or not gold_groups: return 0.0
    tp = matched
    total_pred_pos = tp  # suposición extractiva
    total_actual_pos = len(gold_groups)
    precision = tp / total_pred_pos if total_pred_pos > 0 else 0.0
    recall    = tp / total_actual_pos if total_actual_pos > 0 else 0.0
    return (2*precision*recall/(precision+recall)) if (precision+recall) > 0 else 0.0

def lcs_len(a: List[str], b: List[str]) -> int:
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m):
        for j in range(n):
            dp[i+1][j+1] = dp[i][j] + 1 if a[i] == b[j] else max(dp[i][j+1], dp[i+1][j])
    return dp[m][n]

def rouge_l_f1(pred: str, gold: str) -> float:
    pt, gt = tokenize_norm(pred), tokenize_norm(gold)
    if not pt or not gt: return 0.0
    lcs = lcs_len(pt, gt)
    prec, rec = lcs/len(pt), lcs/len(gt)
    return (2*prec*rec/(prec+rec)) if (prec+rec) else 0.0

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
    output_file = os.path.join(args.results_dir, f"{args.tag}_evaluation_results_{fecha}.jsonl")
    final_metrics_file = os.path.join(args.results_dir, f"{args.tag}_final_metrics_{fecha}.json")
    print("📁 Archivos preparados:", output_file, "|", final_metrics_file)
    print(f"⚙️  RAGAS habilitado: {args.ragas}")

    # Dataset
    dataset = bu.load_dataset()[f"MiniKGraph_dataset_{args.tag}.json"]
    print("✅ Dataset cargado")

    # Acumuladores
    n = len(dataset)
    em_count = 0
    f1_scores, group_f1_scores, bleu_scores, rouge_scores = [], [], [], []

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

        # EM
        exact_match = any(normalize(g) in pred for g in golds_flat)
        if exact_match: em_count += 1

        # Token-F1 (mejor contra los golds)
        best_f1 = best_token_f1(pred, golds_flat)
        f1_scores.append(best_f1)

        # Group-F1
        gold_groups = normalize_nested_list(to_group_format(ex["answer"]))
        g_f1 = group_f1(pred, gold_groups)
        group_f1_scores.append(g_f1)

        # BLEU
        bleu = sacrebleu.sentence_bleu(pred, golds_flat)
        bleu_scores.append(bleu.score)

        # ROUGE-L (F1 estilo LCS)
        best_rouge = max((rouge_l_f1(pred, g) for g in golds_flat), default=0.0)
        rouge_scores.append(best_rouge)

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
            "exact_match": exact_match,
            "f1_score": best_f1,
            "group_f1": g_f1,
            "bleu_score": bleu.score,
            "rouge_l": best_rouge,
        }
        if ragas_dict is not None:
            result_line["ragas"] = ragas_dict

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(result_line, indent=4, ensure_ascii=False) + "\n")

    # Agrega resultados finales
    em_score = em_count / n if n else 0.0
    f1_avg = sum(f1_scores)/n if n else 0.0
    g_f1_avg = sum(group_f1_scores)/n if n else 0.0
    bleu_avg = sum(bleu_scores)/n if n else 0.0
    rouge_avg = sum(rouge_scores)/n if n else 0.0

    print("\n * * * MÉTRICAS FINALES (texto) * * *")
    print(f"Answer EM:   {em_score:.2%}")
    print(f"Answer F1:   {f1_avg:.2%}")
    print(f"Group F1:    {g_f1_avg:.2%}")
    print(f"BLEU:        {bleu_avg:.2f}")
    print(f"ROUGE-L:     {rouge_avg:.2%}")

    final_metrics = {
        "total_examples": n,
        "Answer EM": em_score,
        "Answer F1": f1_avg,
        "Answer Group F1": g_f1_avg,
        "Answer BLEU": bleu_avg,
        "Answer ROUGE-L": rouge_avg,
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