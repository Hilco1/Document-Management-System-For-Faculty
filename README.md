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
## 📊 Dataset Description

The dataset consists of publicly available academic and administrative documents from the Faculty of Electrical Engineering (ETF).

### **Document Types**

- Syllabus  
- Decision  
- Schedule  
- Ranking / Results  
- Regulation  
- Announcement  

### **Synthetic Data**

Due to limited labeled data, synthetic text augmentation was used to:

- Improve class balance  
- Increase robustness of tag extraction  

Synthetic data is used strictly for model robustness and evaluation purposes.

---

## ⚙️ Technologies Used

- Flask  
- SQLAlchemy  
- Sentence-Transformers  
- HuggingFace Transformers (T5)  
- spaCy  
- KeyBERT  
- PyMuPDF  
- pdfplumber  
- Tesseract OCR  

---

## 🖥 Installation
Clone repository
```bash
git clone https://github.com/Hilco1/Document-Management-System-For-Faculty.git
cd Document-Management-System-For-Faculty 
```
Create Virtual Environment
```bash
python -m venv venv
```
Activate virtual environment:

Windows:
```bash
venv\Scripts\activate
```
Mac / Linux:
```bash
source venv/bin/activate
```



Install dependencies
```bash
pip install -r requirements.txt
```

Install spaCy model
```bash
python -m spacy download en_core_web_sm
```
Install Tesseract OCR. Make sure Tesseract OCR is installed on your system.
After installation, update the Tesseract path inside the project if necessary:
```bash
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe
```

Run application
```bash
python app.py
```
 
The application will start locally and can be accessed in your browser.
---
## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
