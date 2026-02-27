# 📁 Document Management System For Faculty

Document Management System designed for academic institutions.  
The system centralizes faculty documents (syllabi, decisions, schedules, announcements) and enhances them using NLP techniques such as OCR, automatic summarization, tag extraction, and semantic search.

---

## 💢 Problem Statement

Academic institutions often store documents across multiple locations (websites, email threads, archives), making retrieval and auditing inefficient.

This system solves the problem by:

- Centralizing document storage
- Automatically generating summaries
- Extracting intelligent tags
- Enabling semantic search
- Supporting document approval workflows

---

## 🏗 System Architecture

1. Document Upload  
2. OCR & Text Extraction  
3. NLP Processing  
   - Summary generation  
   - Tag extraction  
   - Embedding generation  
4. Database Storage  
5. Semantic Search & Approval Workflow  

---

## 🗂 Project Structure

```bash
Code/
│
├── app.py
├── models.py
├── document_processing.py
├── requirements.txt
├── ml_pipeline/
├── templates/
└── static/

Dataset/
├── raw/
│   ├── pdf/
│   └── images/
├── processed/
└── synthetic/  
```
---
📊 Dataset Description 

The dataset consists of publicly available academic and administrative documents from the Faculty of Electrical Engineering (ETF). 

Document Types 

Syllabus 

Decision  

Schedule 

Ranking/Results 

Regulation 

Announcement 

Synthetic Data 

Due to limited labeled data, synthetic text augmentation was used to: 

Improve class balance 

Increase robustness of tag extraction 

Synthetic data is used strictly for model robustness and evaluation purposes. 

 

⚙️ Technologies Used 

Flask 

SQLAlchemy 

Sentence-Transformers 

HuggingFace Transformers (T5) 

spaCy 

KeyBERT 

PyMuPDF 

pdfplumber 

Tesseract OCR

## 🧠 NLP Processing Pipeline

- Automatic summarization (T5 Transformer)  
- Named Entity Recognition (spaCy)  
- Keyword extraction (KeyBERT)  
- Domain-based tag refinement  
- Embedding generation (SentenceTransformers)  

---


---

## ✅ Workflow Support

- Role-based access  
- Document approval flag  
- Timestamped uploads  

---
