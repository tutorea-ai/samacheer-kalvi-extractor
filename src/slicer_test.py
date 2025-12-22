import PyPDF2

def split_pdf(source_pdf, start_page, end_page, output_name):
    try:
        # 1. Open the Big Book
        with open(source_pdf, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            writer = PyPDF2.PdfWriter()

            # 2. Loop through the pages we want
            # (Note: Python starts at 0, so we subtract 1 from user input)
            for page_num in range(start_page - 1, end_page):
                page = reader.pages[page_num]
                writer.add_page(page)

            # 3. Save the Small Book
            with open(output_name, 'wb') as output_file:
                writer.write(output_file)
            
            print(f"✅ Success! Created '{output_name}' with {end_page - start_page + 1} pages.")

    except Exception as e:
        print(f"❌ Error: {e}")

# --- TEST IT ---
#-------------
# Change these numbers to test different pages!
split_pdf("class-10-term0-english.pdf", 10, 20, "unit_test.pdf")