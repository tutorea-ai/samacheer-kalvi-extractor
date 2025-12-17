import requests

# ======================================================
# 1. CONFIGURATION & DATA
# ======================================================
CATALOG_URL = "https://raw.githubusercontent.com/Dravid005/samacheer-kalvi-pdf-downloader/main/src/book_catalog.json"

SUB_11_12 = ["Tamil", "English", "Maths", "Physics", "Chemistry", "Biology", "Computer Science", "Commerce", "Accountancy"]
SUB_6_10  = ["Tamil", "English", "Maths", "Science", "Social Science"]

# ======================================================
# 2. CORE FUNCTIONS
# ======================================================
def get_book_catalog():
    print("⏳ Connecting to the Library Catalog...")
    try:
        response = requests.get(CATALOG_URL)
        return response.json() if response.status_code == 200 else {}
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return {}

def download_file(file_id, filename):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    print(f"\n⬇️  Downloading: {filename}")
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status() 
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
                
                # --- FIX IS HERE: Check size BEFORE closing the file ---
                if f.tell() < 2000: 
                    print("⚠️ Warning: File too small. Check ID.")
                else:
                    print(f"✅ Success! Saved as: {filename}")
                    
    except Exception as e:
        print(f"❌ Download failed: {e}")

def generate_filename(std, term, subject, medium):
    # Standardize inputs
    std, subject, medium = std.lower().strip(), subject.lower().strip(), medium.lower().strip()
    
    # Logic: Term is '0' for classes 8-12
    term = term if std in ["6", "7"] else "0"
    
    # Logic: If language, no medium suffix. Else, add medium.
    suffix = "" if subject in ["english", "tamil"] else f"-{medium}-medium"
    
    return f"class-{std}-term{term}-{subject}{suffix}.pdf"

# ======================================================
# 3. MAIN INTERFACE
# ======================================================
def main():
    print("\n🐙 SAMACHEER SMART DOWNLOADER 2.0 🐙")
    
    catalog = get_book_catalog()
    if not catalog: return print("❌ Error: Could not load catalog.")

    # --- INPUTS ---
    std = input("\n👉 Enter Class (6-12): ").strip()
    
    term = "0"
    if std in ["6", "7"]:
        term = input("\nSelect Term (1-3): ").strip()

    subjects = SUB_11_12 if std in ["11", "12"] else SUB_6_10
    
    print(f"\nSelect Subject for Class {std}:")
    for i, sub in enumerate(subjects, 1):
        print(f"   {i}. {sub}")
        
    try:
        sub_idx = int(input(f"👉 Enter number (1-{len(subjects)}): ")) - 1
        subject = subjects[sub_idx]
    except (ValueError, IndexError):
        subject = "English"
        print("❌ Invalid choice. Defaulting to English.")

    medium = "english"
    if subject.lower() not in ["tamil", "english"]:
        choice = input("\nSelect Medium (1. English / 2. Tamil): ").strip()
        medium = "tamil" if choice == "2" else "english"
    else:
        print(f"ℹ️  Skipping medium for {subject}.")

    # --- PROCESS ---
    filename = generate_filename(std, term, subject, medium)
    print(f"\n🔎 Looking for: {filename}")

    if filename in catalog:
        print(f"🆔 Found ID: {catalog[filename]}")
        download_file(catalog[filename], filename)
    else:
        print("❌ Book not found in catalog.")

if __name__ == "__main__":
    main()