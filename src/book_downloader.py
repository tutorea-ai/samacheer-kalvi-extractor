import requests
import os
import json
import PyPDF2

# ======================================================
# 1. CONFIGURATION
# ======================================================
CATALOG_URL = "https://raw.githubusercontent.com/tutorea-ai/samacheer-kalvi-extractor/main/src/book_catalog.json"

# Note: We don't define a single INDEX_FILE anymore. 
# We calculate it dynamically based on folder structure.

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

def load_unit_index(std, subject):
    """
    Dynamically loads the JSON index based on folder structure:
    src/indexes/languages/english/class-6.json
    """
    # 1. Determine Category (Language vs. Subject)
    # This logic puts English/Tamil in 'languages' folder, everything else in 'subjects'
    if subject.lower() in ["english", "tamil"]:
        category = "languages"
    else:
        category = "subjects"

    # 2. Build the Path
    # Folder: indexes/languages/english/
    base_path = os.path.join("indexes", category, subject.lower())
    
    # Filename: class-6.json
    filename = f"class-{std}.json"
    
    full_path = os.path.join(base_path, filename)

    # 3. Load
    if os.path.exists(full_path):
        # print(f"📂 Loaded Slicer Data: {full_path}") # Optional debug print
        try:
            with open(full_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Warning: {filename} has invalid JSON syntax.")
            return {}
    else:
        # It's normal if the file doesn't exist (e.g., we haven't made Science yet)
        return {}

def download_file(file_id, filename, hidden=False):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    if not hidden:
        print(f"\n⬇️  Downloading Full Book: {filename}...")
    else:
        print(f"⚙️  Fetching source file for slicing...")

    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status() 
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def slice_pdf(source_pdf, output_pdf, start_page, end_page):
    print(f"✂️  Slicing from Page {start_page} to {end_page}...")
    try:
        with open(source_pdf, 'rb') as infile:
            reader = PyPDF2.PdfReader(infile)
            writer = PyPDF2.PdfWriter()

            if end_page > len(reader.pages):
                print(f"⚠️ Error: Book only has {len(reader.pages)} pages. Check your JSON range.")
                return False

            for i in range(start_page - 1, end_page):
                writer.add_page(reader.pages[i])

            with open(output_pdf, 'wb') as outfile:
                writer.write(outfile)
        
        print(f"✅ Success! Created: {output_pdf}")
        return True
    except Exception as e:
        print(f"❌ Slicing Error: {e}")
        return False

def generate_book_key(std, term, subject, medium):
    std, subject, medium = std.lower().strip(), subject.lower().strip(), medium.lower().strip()
    term = term if std in ["6", "7"] else "0"
    suffix = "" if subject in ["english", "tamil"] else f"-{medium}-medium"
    return f"class-{std}-term{term}-{subject}{suffix}.pdf"

# ======================================================
# 3. SMART MENU LOGIC
# ======================================================
def handle_unit_selection(book_key, unit_data, std, subject):
    # --- STEP 1: SHOW UNITS ---
    print(f"\n📖 Available Units in {subject}:")
    units = list(unit_data.keys()) 
    
    for i, u in enumerate(units, 1):
        print(f"   {i}. {u}")
    
    try:
        u_idx = int(input("👉 Select Unit (Number): ")) - 1
        selected_unit = units[u_idx]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        return None, None, None

    # --- STEP 2: SHOW LESSONS ---
    print(f"\n📝 Lessons in {selected_unit}:")
    lessons_map = unit_data[selected_unit]
    lesson_names = list(lessons_map.keys())
    
    for i, l in enumerate(lesson_names, 1):
        print(f"   {i}. {l}")

    try:
        l_idx = int(input("👉 Select Lesson (Number): ")) - 1
        raw_lesson_name = lesson_names[l_idx]     
        
        # --- GET DATA ---
        lesson_data = lessons_map[raw_lesson_name]
        
        if isinstance(lesson_data, dict):
            page_range = lesson_data['pdf_range']
        else:
            page_range = lesson_data 
            
    except (ValueError, IndexError):
        print("❌ Invalid selection or missing data.")
        return None, None, None

    # --- STEP 3: GENERATE CLEAN FILENAME ---
    clean_unit = selected_unit.replace(" ", "")
    
    if ":" in raw_lesson_name:
        parts = raw_lesson_name.split(":")
        category = parts[0].strip() 
        lesson_name = parts[1].strip().replace(" ", "") 
    else:
        category = "Lesson"
        lesson_name = raw_lesson_name.replace(" ", "")

    sub_short = subject[:3] 
    
    final_name = f"Class-{std}-{sub_short}-{clean_unit}-{category}-{lesson_name}.pdf"
    
    return final_name, page_range[0], page_range[1]

# ======================================================
# 4. MAIN INTERFACE
# ======================================================
def main():
    print("\n🐙 SAMACHEER EXTRACTOR & SLICER (v3.1 - Dynamic) 🐙")
    
    catalog = get_book_catalog()
    if not catalog: return print("❌ Error: Could not load catalog.")

    # --- USER INPUTS ---
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
    except:
        subject = "English"

    medium = "english"
    if subject.lower() not in ["tamil", "english"]:
        choice = input("\nSelect Medium (1. English / 2. Tamil): ").strip()
        medium = "tamil" if choice == "2" else "english"

    # --- LOAD SLICER DATA (NEW LOCATION) ---
    # We load this AFTER knowing the class/subject
    unit_index = load_unit_index(std, subject)

    # --- IDENTIFY BOOK ---
    book_filename = generate_book_key(std, term, subject, medium)
    
    if book_filename not in catalog:
        print(f"❌ Book not found in catalog: {book_filename}")
        return

    # --- DOWNLOAD DECISION ---
    download_mode = "full"
    custom_name = book_filename
    slice_pages = None

    if book_filename in unit_index:
        print("\n🤔 How do you want to download?")
        print("   1. Full Book")
        print("   2. Specific Unit/Lesson")
        mode = input("👉 Enter choice (1-2): ").strip()
        
        if mode == "2":
            fname, start, end = handle_unit_selection(book_filename, unit_index[book_filename], std, subject)
            
            if fname:
                download_mode = "slice"
                custom_name = fname
                slice_pages = (start, end)
            else:
                return 

    # --- EXECUTION ---
    drive_id = catalog[book_filename]
    
    if download_mode == "full":
        download_file(drive_id, book_filename)
        print(f"✅ Full Book Saved: {book_filename}")
        
    elif download_mode == "slice":
        temp_file = ".temp_book.pdf"
        success = download_file(drive_id, temp_file, hidden=True)
        
        if success:
            slice_pdf(temp_file, custom_name, slice_pages[0], slice_pages[1])
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print("🧹 Cleaned up temporary files.")

if __name__ == "__main__":
    main()