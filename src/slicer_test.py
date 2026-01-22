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
    "Class-6-term1.pdf": {
        "science": (4, 107),
        "social_science": (109, 216)
    },
    "Class-6-term2.pdf": {
        "science": (5, 100),
        "social_science": (101, 200)
    },
    "Class-6-term3.pdf": {
        "science": (4, 84),
        "social_science": (89, 224)
    },
    "Class-7-term1.pdf": {
        "science": (4, 102),
        "social_science": (103, 200)
    },
    "Class-7-term2.pdf": {
        "science": (4, 97),
        "social_science": (98, 182)
    },
    "Class-7-term3.pdf": {
        "science": (4, 106),
        "social_science": (107, 224)
    }
}
# --------------------------------------------

for source_pdf, subjects in books.items():
    for subject, (start, end) in subjects.items():
        output_name = source_pdf.replace(".pdf", f"-{subject}.pdf")
        split_pdf(source_pdf, start, end, output_name)
