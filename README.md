# Faculty Document Management System (AI-Powered)

Document Management System designed for academic institutions.  
The system centralizes faculty documents (syllabi, decisions, schedules, announcements) and enhances them using NLP techniques such as OCR, automatic summarization, tag extraction, and semantic search.

---

## 🎯 Problem Statement

Academic institutions often store documents across multiple locations (websites, email threads, archives), making retrieval and auditing inefficient.

This system solves the problem by:

- Centralizing document storage
- Automatically generating summaries
- Extracting intelligent tags
- Enabling semantic search
- Supporting document approval workflows

---

## 📥 Document Ingestion

- Upload PDF or image files  
- Automatic OCR for scanned documents  
- Table-aware PDF extraction  

---

## 🧠 NLP Processing Pipeline

- Automatic summarization (T5 Transformer)  
- Named Entity Recognition (spaCy)  
- Keyword extraction (KeyBERT)  
- Domain-based tag refinement  
- Embedding generation (SentenceTransformers)  

---

## 🔎 Semantic Search

- Embedding-based similarity search  
- Context-aware retrieval instead of keyword-only matching  

---

## ✅ Workflow Support

- Role-based access  
- Document approval flag  
- Timestamped uploads  

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

Documentation/
Results/
Presentations/
