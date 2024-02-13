from pdf2docx import Converter
import mammoth


def pdf_to_docx(pdf_path):
    # Convert the PDF to a DOCX file
    docx_path = pdf_path.replace('.pdf', '.docx')
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None)
    cv.close()
    return docx_path


def docx_to_html(docx_path):
    with open(docx_path, "rb") as docx_file:
        result = mammoth.convert_to_html(docx_file)
        html_content = result.value
    return html_content
