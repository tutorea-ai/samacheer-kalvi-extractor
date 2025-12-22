# Samacheer Kalvi Extractor & Slicer

A centralized Python automation tool designed to streamline the retrieval and **granular extraction** of Samacheer Kalvi (Tamil Nadu State Board) educational assets. This utility serves as the core content engine for the Tutorea AI educational platform.

## 📖 Project Overview
This tool decouples file storage from application logic using a centralized JSON catalog. It maps standardized filenames to Google Drive IDs and employs a **Modular Indexing System** to slice specific Units, Prose, Poems, or Grammar sections from massive textbook PDFs automatically.

## 🚀 Key Features

### 1. Smart Asset Management
* **Centralized Catalog:** All file mappings are maintained in `book_catalog.json`, allowing instant asset updates without code redeployment.
* **Intelligent Routing:** Automatically handles business logic for file retrieval:
    * Auto-detects terms for lower classes (6-7) vs. full-year books for higher classes (8-12).
    * Intelligent filtering to skip 'Medium' selection for language subjects.

### 2. Granular PDF Slicing (New in v3.0)
* **Precision Extraction:** Capable of downloading a full textbook, cutting out a specific lesson (e.g., "Prose: Sea Turtles"), and saving it as a standalone PDF.
* **Dual-Layer Mapping:** Stores both the **PDF Page Range** (for the software slicer) and the **Print Page Range** (for physical book reference).
* **Dynamic Menus:** The CLI automatically builds interactive menus based on the available JSON data for the selected Class and Subject.

### 3. Modular Architecture
* **Scalable Indexing:** Uses a folder-based structure (`src/indexes/languages/english/class-6.json`) to keep data isolated and manageable.
* **Performance:** Loads only the specific index required for the requested subject, ensuring high speed even as the dataset grows.

## 📂 Repository Structure

```text
samacheer-kalvi-extractor/
├── src/
│   ├── book_downloader.py       # Core script (Downloader + Slicer Logic)
│   ├── book_catalog.json        # "Source of Truth" for Drive IDs
│   └── indexes/                 # Modular Slicing Data
│       ├── languages/
│       │   ├── english/         # Complete English Dataset (Class 6-12)
│       │   └── tamil/           # (Reserved for future)
│       └── subjects/            # (Reserved for Science/Maths)
└── requirements.txt             # Project dependencies

## 🛠️ Installation & Usage

### 1. Prerequisites
Ensure you have **Python 3.x** and **pip** installed on your system.

### 2. Setup (Linux/Mac)
It is recommended to run this project inside a virtual environment to manage dependencies cleanly.

```bash
# Clone the repository
git clone [https://github.com/tutorea-ai/samacheer-kalvi-extractor.git](https://github.com/tutorea-ai/samacheer-kalvi-extractor.git)
cd samacheer-kalvi-extractor

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

## Running the Extractor
Once the environment is active and dependencies are installed:

cd src
python3 book_downloader.py