import re
import pandas as pd
from conllu import parse_incr

EXCEL_PATH = "PetroNER - Treino-Teste.xlsx"
CONLLU_PATH = "petroner-uri-2023-07-11.conllu"


def load_article_ranges(excel_path):
    raw = pd.read_excel(excel_path, sheet_name=0, header=2)

    df = raw.iloc[:10, [0, 1, 2, 3, 4, 5, 13]].copy()
    df.columns = [
        "conllu_code",
        "volume_file",
        "article_file",
        "sent_start",
        "sent_end",
        "num_sentences",
        "dataset_split",
    ]

    df = df.dropna(subset=["conllu_code", "sent_start", "sent_end", "dataset_split"])
    df["sent_start"] = df["sent_start"].astype(int)
    df["sent_end"] = df["sent_end"].astype(int)

    return df


def split_sent_id(sent_id):
    match = re.match(r"(.+)-(\d+)$", sent_id)
    if not match:
        return None, None

    return match.group(1), int(match.group(2))


def build_range_index(article_ranges):
    index = {}

    for _, row in article_ranges.iterrows():
        index.setdefault(row["conllu_code"], []).append(row.to_dict())

    return index


def find_article_for_sentence(sent_id, range_index):
    conllu_code, sent_number = split_sent_id(sent_id)

    if conllu_code is None:
        return None

    for article in range_index.get(conllu_code, []):
        if article["sent_start"] <= sent_number <= article["sent_end"]:
            return article

    return None

def get_misc_value(token, key):
    misc = token.get("misc") or {}
    return misc.get(key)


def get_local_id_from_grafo(grafo):
    if not grafo:
        return None

    return grafo.replace("#", "").strip()


def extract_mentions(tokenlist):
    mentions = []
    current = None

    for token in tokenlist:
        tag = token.get("deps")

        if not tag or tag in ["O", "_"]:
            if current:
                mentions.append(current)
                current = None
            continue

        if "=" not in tag:
            continue

        prefix, label = tag.split("=", 1)
        form = token.get("form")
        grafo = get_misc_value(token, "grafo")
        start_char = get_misc_value(token, "start_char")
        end_char = get_misc_value(token, "end_char")

        if prefix == "B":
            if current:
                mentions.append(current)

            current = {
                "label": label,
                "tokens": [form],
                "grafo": grafo,
                "local_id": get_local_id_from_grafo(grafo),
                "start_char": start_char,
                "end_char": end_char,
            }

        elif prefix == "I" and current and current["label"] == label:
            current["tokens"].append(form)

            if grafo and not current["grafo"]:
                current["grafo"] = grafo
                current["local_id"] = get_local_id_from_grafo(grafo)

            if end_char:
                current["end_char"] = end_char

        else:
            if current:
                mentions.append(current)

            current = {
                "label": label,
                "tokens": [form],
                "grafo": grafo,
                "local_id": get_local_id_from_grafo(grafo),
                "start_char": start_char,
                "end_char": end_char,
            }

    if current:
        mentions.append(current)

    for m in mentions:
        m["text"] = " ".join(m["tokens"])

    return mentions

def parse_conllu_sentences(conllu_path, range_index):
    sentences = []
    mentions = []

    with open(conllu_path, "r", encoding="utf-8") as f:
        for tokenlist in parse_incr(f):
            sent_id = tokenlist.metadata["sent_id"]
            text = tokenlist.metadata["text"]
            # print para procurar sent_star & sent_end antes de finalizar reference ali finaliza sentence_id depois o texto

            article = find_article_for_sentence(sent_id, range_index)

            if article is None:
                continue

            conllu_code, sent_number = split_sent_id(sent_id)

            document_id = (
                f"{article['conllu_code']}::"
                f"{article['sent_start']}-{article['sent_end']}"
            )

            sentences.append({
                "id": sent_id,
                "text": text,
                "sentence_number": sent_number,
                "document_id": document_id,
                "volume_file": article["volume_file"],
                "article_file": article["article_file"],
                "dataset_split": article["dataset_split"],
            })

            for i, mention in enumerate(extract_mentions(tokenlist)):
                mentions.append({
                    "id": f"{sent_id}::m{i}",
                    "sentence_id": sent_id,
                    "document_id": document_id,
                    "text": mention["text"],
                    "ner_label": mention["label"],
                    "grafo": mention["grafo"],
                    "local_id": mention["local_id"],
                    "start_char": mention["start_char"],
                    "end_char": mention["end_char"],
                })

    return sentences, mentions

### Cargar a Neo4j ###
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "diripar8$"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def batch(rows, size=1000):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def load_sentences(sentences):
    query = """
    UNWIND $rows AS row

    MERGE (d:Document {id: row.document_id})
    SET d.volume_file = row.volume_file,
        d.article_file = row.article_file,
        d.dataset_split = row.dataset_split

    MERGE (s:Sentence {id: row.id})
    SET s.text = row.text,
        s.sentence_number = row.sentence_number,
        s.dataset_split = row.dataset_split

    MERGE (d)-[:HAS_SENTENCE]->(s)
    """

    with driver.session() as session:
        for rows in batch(sentences):
            session.run(query, rows=rows)


def load_mentions(mentions):
    query = """
    UNWIND $rows AS row

    MATCH (s:Sentence {id: row.sentence_id})

    MERGE (m:EntityMention {id: row.id})
    SET m.text = row.text,
        m.ner_label = row.ner_label,
        m.grafo = row.grafo,
        m.local_id = row.local_id,
        m.start_char = row.start_char,
        m.end_char = row.end_char

    MERGE (s)-[:HAS_MENTION]->(m)
    """

    with driver.session() as session:
        for rows in batch(mentions):
            session.run(query, rows=rows)


def link_mentions_to_kg(mentions):
    rows_with_kg = [m for m in mentions if m["local_id"]]

    query = """
    UNWIND $rows AS row

    MATCH (m:EntityMention {id: row.id})
    MATCH (e:KGEntity {local_id: row.local_id})

    MERGE (m)-[:REFERS_TO]->(e)
    """

    with driver.session() as session:
        for rows in batch(rows_with_kg):
            session.run(query, rows=rows)
            
article_ranges = load_article_ranges(EXCEL_PATH)
range_index = build_range_index(article_ranges)

sentences, mentions = parse_conllu_sentences(CONLLU_PATH, range_index)

load_sentences(sentences)

load_mentions(mentions)
print(f"Loaded {len(sentences)} sentences and {len(mentions)} mentions into Neo4j.")


link_mentions_to_kg(mentions)
print("Linked mentions to KG entities where possible.")
print("Done.")