import requests
import os
import json
import PyPDF2
import gdown

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
    if not hidden:
        print(f"\n⬇️  Connecting to Google Drive (ID: {file_id})...")
    else:
        print(f"⚙️  Fetching source file for slicing...")
    
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, filename, quiet=hidden, fuzzy=True)
        
        if not hidden: 
            print(f"✅ Download Success: {filename}")
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
def handle_unit_selection(book_key, index_data, std, subject):
    # --- 1. EXTRACT METADATA ---
    meta = index_data.get("meta", {"prelim_pages": 0, "total_pdf_pages": 999})
    offset = meta["prelim_pages"]
    max_pages = meta["total_pdf_pages"]
    
    units = index_data.get("units", [])
    if not units:
        print("❌ Error: JSON format is empty or incorrect.")
        return None, None, None

    # --- 2. SHOW UNIT MENU FIRST ---
    print(f"\n📚 Available Units in {subject}:")
    for i, unit in enumerate(units, 1):
        u_num = unit.get("unit")
        month = unit.get("month", "")
        print(f"   {i}. Unit {u_num} ({month})")
    
    try:
        unit_choice = int(input(f"👉 Select Unit (1-{len(units)}): ")) - 1
        selected_unit = units[unit_choice]
    except (ValueError, IndexError):
        print("❌ Invalid unit selection.")
        return None, None, None

    # --- 3. BUILD LESSON MENU FOR SELECTED UNIT ---
    unit_num = selected_unit.get("unit")
    lessons = []
    
    for category in ["prose", "poem", "supplementary", "play"]:
        if category in selected_unit:
            item = selected_unit[category]
            label = f"{category.capitalize()}: {item['title']}"
            
            lessons.append({
                "label": label,
                "book_page": item['page'],
                "clean_name": f"Unit{unit_num}-{category.capitalize()}-{item['title'].replace(' ', '').replace('(', '').replace(')', '')}"
            })
    
    # Sort by page (just in case)
    lessons.sort(key=lambda x: x["book_page"])
    
    # --- 4. SHOW LESSON MENU ---
    print(f"\n📖 Lessons in Unit {unit_num}:")
    for i, lesson in enumerate(lessons, 1):
        print(f"   {i}. {lesson['label']} (Starts at pg {lesson['book_page']})")
    
    try:
        lesson_choice = int(input(f"👉 Select Lesson (1-{len(lessons)}): ")) - 1
        selected = lessons[lesson_choice]
    except (ValueError, IndexError):
        print("❌ Invalid lesson selection.")
        return None, None, None

    # --- 5. CALCULATE PDF RANGES ---
    start_pdf_page = selected["book_page"] + offset
    
    # Find end page: Look for next lesson in ANY unit
    all_lessons_sorted = []
    for u in units:
        for cat in ["prose", "poem", "supplementary", "play"]:
            if cat in u:
                all_lessons_sorted.append(u[cat]['page'])
    
    all_lessons_sorted.sort()
    
    # Find the next page after current
    next_pages = [p for p in all_lessons_sorted if p > selected["book_page"]]
    
    if next_pages:
        next_lesson_book_page = next_pages[0]
        end_pdf_page = (next_lesson_book_page + offset) - 1
    else:
        print("⚠️ Note: This is the last lesson. Extracting till end of book.")
        end_pdf_page = max_pages

    # --- 6. RESULT ---
    sub_short = subject[:3]
    final_name = f"Class-{std}-{sub_short}-{selected['clean_name']}.pdf"

    print(f"\n🧮 Calculated Range: PDF Pages {start_pdf_page} to {end_pdf_page}")
    return final_name, start_pdf_page, end_pdf_page


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

   # ... inside main() function ...
# --- DOWNLOAD DECISION ---
    download_mode = "full"
    custom_name = book_filename
    slice_pages = None

    # 1. SELECT THE DATA SOURCE
    target_data = None
    
    # Determine the specific key to look for inside the JSON
    if std in ["6", "7"]:
        # Case A: Class 6 & 7 use "term1", "term2", "term3"
        target_key = f"term{term}"
    else:
        # Case B: Class 8-12 use "term0" (Standard for full books)
        target_key = "term0"

    # Now check if that key exists in the loaded JSON file
    if target_key in unit_index:
        target_data = unit_index[target_key]

    # 2. SHOW MENU (If we found valid slicing data)
    if target_data:
        print("\n🤔 How do you want to download?")
        print("   1. Full Book")
        print("   2. Specific Unit/Lesson")
        mode = input("👉 Enter choice (1-2): ").strip()
        
        if mode == "2":
            # We pass 'target_data' which contains the specific 'meta' and 'units'
            fname, start, end = handle_unit_selection(book_filename, target_data, std, subject)
            
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
        # --- NEW SMART LOGIC ---
        source_file = "temp_source.pdf"  # Use a visible name, not hidden
        needs_cleanup = False

        # 1. Check if you ALREADY have the full book downloaded
        if os.path.exists(book_filename):
            print(f"⚡ Found local full book: '{book_filename}'")
            print("   Using local file for slicing (No download needed!)")
            source_file = book_filename
            success = True
        else:
            # 2. If not, download it to a temp file
            # CRITICAL: Force delete any old corrupt temp file first
            if os.path.exists(source_file):
                os.remove(source_file)
                
            success = download_file(drive_id, source_file, hidden=True)
            needs_cleanup = True

        # 3. Perform the slice
        if success:
            slice_pdf(source_file, custom_name, slice_pages[0], slice_pages[1])
            
            # Only delete the source if it was a temporary download
            if needs_cleanup and os.path.exists(source_file):
                os.remove(source_file)
                print("🧹 Cleaned up temporary source file.")
if __name__ == "__main__":
    main()