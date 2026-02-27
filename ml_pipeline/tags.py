import spacy
nlp = spacy.load("en_core_web_sm")

def extract_tags(text):
    doc = nlp(text)
    tags = list(set([ent.text for ent in doc.ents]))
    return tags
