import os
import io
import re
import fitz
import pdfplumber
import pytesseract
from PIL import Image

from keybert import KeyBERT
from transformers import T5ForConditionalGeneration, T5Tokenizer
from sentence_transformers import SentenceTransformer
import spacy


# ============================================================
# CONFIG
# ============================================================

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

nlp = spacy.load("en_core_web_sm")
kw_model = KeyBERT()
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

t5_model = T5ForConditionalGeneration.from_pretrained("t5-base")
t5_tokenizer = T5Tokenizer.from_pretrained("t5-base")


# ============================================================
# OCR + PDF EXTRACT
# ============================================================

def ocr_extract(path):
    text = ""
    OCR_LANGS = "bos+hrv+srp_latn+eng"

    if path.lower().endswith(".pdf"):
        # A) Digital extract
        try:
            with fitz.open(path) as pdf:
                for page in pdf:
                    t = page.get_text()
                    if t and t.strip():
                        text += t + "\n"
            if text.strip():
                return text
        except:
            pass

        # B) Table extract
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            row = [cell if cell else "" for cell in row]
                            text += " | ".join(row) + "\n"
            if text.strip():
                return text
        except:
            pass

        # C) OCR fallback
        try:
            with fitz.open(path) as pdf:
                for page in pdf:
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    text += pytesseract.image_to_string(img, lang=OCR_LANGS)
            return text
        except:
            pass

    # Image OCR
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img, lang=OCR_LANGS)
    except:
        text = ""

    return text


# ============================================================
# SUMMARIZATION (T5)
# ============================================================

def summarize_text(text, max_len=200):
    cleaned = re.sub(r"\s+", " ", text.replace("\n", " "))

    input_text = (
        "Summarize the following university academic or administrative document "
        "in 3-5 clear professional sentences. Focus on institution, purpose, and key topics: "
        + cleaned[:3000]
    )

    tokens = t5_tokenizer.encode(
        input_text,
        return_tensors="pt",
        max_length=512,
        truncation=True
    )

    summary_ids = t5_model.generate(
        tokens,
        max_length=max_len,
        min_length=60,
        length_penalty=2.0,
        no_repeat_ngram_size=3,
        early_stopping=True
    )

    summary = t5_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary.strip()


# ============================================================
# TAG EXTRACTION
# ============================================================

LEMMA_MAP = {
    "student": "Student", "studentima": "Student", "studenti": "Student",
    "profesor": "Profesor", "profesori": "Profesor",
    "asistent": "Asistent", "asistenti": "Asistent",
    "predavač": "Predavač", "predavac": "Predavač",
    "sarajevo": "Sarajevo", "sarajevu": "Sarajevo",
    "fakultet": "Fakultet", "fakulteta": "Fakultet",
    "univerzitet": "Univerzitet", "univerziteta": "Univerzitet",
    "raspored": "Raspored", "rasporedu": "Raspored",
    "prijava": "Prijava", "prijave": "Prijava",
    "ispit": "Ispit", "ispiti": "Ispit",
    "rok": "Rok", "rokovi": "Rok",
    "termin": "Termin", "termini": "Termin",
    "kurs": "Predmet", "predmet": "Predmet", "predmeti": "Predmet",

    "faculty": "Fakultet",
    "university": "Univerzitet",
    "schedule": "Raspored",
    "exam": "Ispit",
}

STOPWORDS_CUSTOM = {
    "koji", "koje", "koja", "su", "je", "na", "u",
    "za", "od", "the", "and", "are", "is"
}

FACULTY_KEYWORDS = [
    "elektrotehnika", "telekomunikacije", "automatika",
    "računarstvo", "elektronika", "nastava", "predmet",
    "fakultet", "univerzitet", "sarajevo",
    "program", "curriculum", "raspored", "ispiti", "rokovi"
]


def extract_tags(text, max_tags=12):
    raw = []
    doc = nlp(text)

    # A) NER
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE"] and len(ent.text.split()) <= 4:
            raw.append(ent.text)

    # B) KeyBERT
    try:
        keywords = kw_model.extract_keywords(
            text,
            top_n=max_tags,
            use_mmr=True,
            diversity=0.6
        )
        for kw, score in keywords:
            if score > 0.4:
                raw.append(kw)
    except:
        pass

    # C) Domain keywords
    lower_text = text.lower()
    for w in FACULTY_KEYWORDS:
        if w in lower_text:
            raw.append(w)

    # D) Cleanup
    clean = []

    for t in raw:
        t = t.strip().lower()

        if re.search(r"\d{4,6}", t):
            continue

        if t.isdigit() and 1940 <= int(t) <= 2035:
            clean.append(t)
            continue

        if len(t) < 4:
            continue

        if len(t.split()) > 3:
            continue

        if t in STOPWORDS_CUSTOM:
            continue

        if t in LEMMA_MAP:
            clean.append(LEMMA_MAP[t])
        else:
            clean.append(t.capitalize())

    # Deduplicate (preserve order)
    final = []
    for x in clean:
        if x not in final:
            final.append(x)

    return final[:max_tags]


# ============================================================
# EMBEDDINGS
# ============================================================

def embed_text(text):
    vec = embed_model.encode(text)
    return vec.tolist()


# ============================================================
# IMAGE TAGS
# ============================================================

IMAGE_TAG_WHITELIST = {
    "asistent","profesor","student","raspored","ispit","termin",
    "studij","studija","fakultet","univerzitet","sarajevo",
    "oprema","nabavka","ponuda","laboratorija","kancelarija",
    "projekat","predmet","odsjek","izbor","komisija","bodovi"
}


def extract_image_tags(text, limit=4):
    if not text or len(text.strip()) == 0:
        return ["Dokument", "Slika", "ETF"][:limit]

    words = [w.lower() for w in text.split() if w.isalpha()]
    found = [w.capitalize() for w in words if w in IMAGE_TAG_WHITELIST]

    if not found:
        found = ["Slika", "Dokument", "ETF"]

    return list(dict.fromkeys(found))[:limit]