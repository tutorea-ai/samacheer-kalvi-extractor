# 🐙 Samacheer Kalvi PDF Extractor API

RESTful API for generating PDFs and TXT files from Tamil Nadu State Board (Samacheer Kalvi) textbooks.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env if needed
```

### 3. Run Server
```bash
python run.py
```

Server starts at: **http://localhost:8000**  
API Docs: **http://localhost:8000/docs**

---

## 📖 API Usage

### Generate Full Book PDF
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "class_num": 12,
    "subject": "english",
    "mode": "full_book",
    "output_format": "pdf"
  }'
```

### Generate Specific Lesson TXT
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "class_num": 12,
    "subject": "english",
    "mode": "lesson",
    "unit": 6,
    "lesson_choice": 2,
    "output_format": "txt"
  }'
```

### Download File
```bash
curl -O http://localhost:8000/api/download/Class12-Unit6-Poem.pdf
```

---

## 🛠️ Development

### Project Structure