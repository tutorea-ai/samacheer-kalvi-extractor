# Samacheer Kalvi Extractor

A centralized Python automation tool designed to streamline the retrieval of **Samacheer Kalvi (Tamil Nadu State Board)** educational assets from cloud storage. This utility serves as the extraction engine for the Tutorea AI educational platform.

## 📖 Project Overview
This tool decouples file storage from application logic using a centralized JSON catalog (`book_catalog.json`). It maps standardized, readable filenames (e.g., `class-10-term0-english.pdf`) to immutable Google Drive IDs, enabling the development team to fetch specific textbook assets programmatically without manual intervention.

## 🚀 Key Features
* **Centralized Asset Management:** All file mappings are maintained in a remote JSON catalog on GitHub, allowing instant asset updates without code redeployment.
* **Smart Query Engine:** Automatically handles business logic for file retrieval:
    * Auto-detects terms for lower classes (6-7) vs. full-year books for higher classes (8-12).
    * Intelligent filtering to skip 'Medium' selection for language subjects.
* **Secure Retrieval:** Bypasses standard download hurdles to fetch authorized content directly from company-managed Google Drive storage.

## 📂 Repository Structure
* `src/book_downloader.py` - The core extraction script containing the business logic.
* `src/book_catalog.json` - The "Source of Truth" database mapping filenames to Drive IDs.
* `requirements.txt` - Project dependencies.

---

## 🛠️ Installation & Usage

### 1. Setup
Clone the repository and install the required dependencies:

```bash
git clone [https://github.com/tutorea-ai/samacheer-kalvi-extractor.git](https://github.com/tutorea-ai/samacheer-kalvi-extractor.git)
cd samacheer-kalvi-extractor
pip install -r requirements.txt

