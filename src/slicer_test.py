import PyPDF2

def split_pdf(source_pdf, start_page, end_page, output_name):
    with open(source_pdf, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()

        for page_num in range(start_page - 1, end_page):
            writer.add_page(reader.pages[page_num])

        with open(output_name, 'wb') as output_file:
            writer.write(output_file)

    print(f"✅ Created: {output_name}")

# ---- CONFIGURATION (EDIT ONLY THIS PART) ----
books = {
    "class-6-term1.pdf": {
        "science": (5, 120),
        "social_science": (121, 210)
    },
    "class-6-term2.pdf": {
        "science": (6, 115),
        "social_science": (116, 205)
    },
    "class-6-term3.pdf": {
        "science": (7, 118),
        "social_science": (119, 208)
    },
    "class-7-term1.pdf": {
        "science": (8, 130),
        "social_science": (131, 240)
    },
    "class-7-term2.pdf": {
        "science": (9, 135),
        "social_science": (136, 245)
    },
    "class-7-term3.pdf": {
        "science": (10, 140),
        "social_science": (141, 250)
    }
}
# --------------------------------------------

for source_pdf, subjects in books.items():
    for subject, (start, end) in subjects.items():
        output_name = source_pdf.replace(".pdf", f"-{subject}.pdf")
        split_pdf(source_pdf, start, end, output_name)
