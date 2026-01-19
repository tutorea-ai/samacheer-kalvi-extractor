import os
from pathlib import Path
from datetime import datetime

# === CONFIGURATION ===
# Update this path to point to your Module 1 folder
CONTENT_ROOT = Path("/home/dravidkumar/test_m1_and_m2/content-qa-lp/samacheer-kalvi").resolve() 

def count_files(directory, extension):
    return len(list(directory.rglob(f"*.{extension}")))

def run_audit():
    print(f"\n📊 PROJECT STATUS REPORT: SAMACHEER KALVI AUTOMATION")
    print(f"📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Location: {CONTENT_ROOT}")
    print("=" * 65)
    print(f"{'CLASS':<10} | {'HTML PAGES':<15} | {'SOURCE (MD)':<15} | {'STATUS'}")
    print("-" * 65)

    total_html = 0
    total_md = 0

    # Check Classes 6-12
    for class_num in range(6, 13):
        class_dir = CONTENT_ROOT / str(class_num)
        backend_dir = CONTENT_ROOT / "backend" / "english" / str(class_num)
        
        # Count HTML (Check both root and backend locations)
        h_count = count_files(class_dir, "html") + count_files(backend_dir, "html")
        
        # Count MD (Always in backend/english/class/english)
        m_count = count_files(CONTENT_ROOT, "md") # Simplified global search for that class
        # To be specific, let's look in the class specific folders if possible, 
        # but a global count per class number in filename is safer for a quick report.
        m_count = 0
        for md_file in CONTENT_ROOT.rglob("*.md"):
            if f"/{class_num}/" in str(md_file) or f"Class{class_num}" in md_file.name:
                m_count += 1

        status = "✅ COMPLETE" if h_count > 10 else "⚠️ IN PROGRESS"
        if h_count == 0: status = "⏳ PENDING"

        print(f"{class_num:<10} | {h_count:<15} | {m_count:<15} | {status}")
        
        total_html += h_count
        total_md += m_count

    print("=" * 65)
    print(f"🚀 TOTAL ASSETS GENERATED: {total_html + total_md}")
    print(f"   - Web Pages (HTML):   {total_html}")
    print(f"   - Source Files (MD):  {total_md}")
    print("=" * 65)

if __name__ == "__main__":
    run_audit()