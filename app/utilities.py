import time
from PIL import Image
from uuid import uuid4
import os
import json

from app import app

from pathlib import Path

import pyqrcode

from datetime import datetime
import pytz

from app.models import Table, User

import subprocess

# Save Image and return image path
def store_picture(file):

    '''
    :param file: souce file where the input file is located - String
    :return: return the file name + extension as a String object
    '''

    file_name, file_extension = os.path.splitext(file.filename)

    file_name = str(uuid4())

    full_filename = file_name + file_extension

    save_abs_path = str(Path(app.root_path) / 'static' / 'img' / full_filename)

    print(save_abs_path)

    output_size = (700, 400)
    i = Image.open(file)
    i.thumbnail(output_size)
    i.save(save_abs_path)

    return full_filename


def json_reader(file):

    with open(file) as f:

        data = json.load(f)

    return data[0]


def generate_qrcode(table, seat, base_url, suffix_url):

    url = f"{base_url}/{suffix_url}/{table}/{seat}"

    file_name = table + "_" + seat

    image = pyqrcode.create(url)

    save_abs_path = str(Path(app.root_path) / 'static' / 'qrcode' / f"{file_name}.png")

    image.png(save_abs_path, scale=5)

    return f"{file_name}.png"


def activity_logger(order_id, operation_type,
                    page_name, descr,
                    status, log_time):
    import csv

    row = (order_id, operation_type, page_name, descr, status, log_time)

    with open(str(Path(app.root_path) / 'logging.csv'), "a", encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerow(row)

    file.close()


def qrcode2excel(tables):

    import json
    import xlsxwriter

    save_abs_path = str(Path(app.root_path) / 'Downloads' / 'qrcode.xlsx')

    # Create an new Excel file and add a worksheet.
    workbook = xlsxwriter.Workbook(save_abs_path)

    for table_name in tables:

        worksheet = workbook.add_worksheet(table_name)

        # Widen the first column to make the text clearer.
        worksheet.set_column('A:A', 30)

        worksheet.write("A1", u"桌号")

        worksheet.write("B1", u"二维码")

        table = Table.query.filter_by(name=table_name).first_or_404()

        seats2qrcode = [(i.split('.')[0], i) for i in json.loads(table.container).get('qrcodes')]

        row = 2

        for items in seats2qrcode:

            img_path = str(Path(app.root_path) / 'static' / 'qrcode' / items[1])

            # Insert an image.
            worksheet.write(f'A{row}', items[0])
            worksheet.insert_image(f'B{row}', img_path)

            row += 12

    workbook.close()

    return save_abs_path


def html2pdf():

    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader('./templates'))

    template = env.get_template("info_receipt.html")

    template_vars = {"table_name": "A1",
                     "seat_number": "10"}

    html = template.render(template_vars)

    html_file = open("rest.html", "w")

    html_file.write(html)
    html_file.close()


# Word to PDF Converter
def docx2pdf(doc_in, pdf_out):

    """
    :param doc_in word file path
    :param pdf_out pdf file save path
    """
    import comtypes.client

    pdf_format_code = 17

    try:
        word = comtypes.client.CreateObject("word.Application")
        if os.path.exists(pdf_out):
            os.remove(pdf_out)

        doc = word.Documents.Open(doc_in, ReadOnly=1)
        doc.SaveAs(pdf_out, FileFormat=pdf_format_code)
        doc.Close()
        word.Quit()

        return pdf_out

    # If failing natively, then call LibreOffice to convert the docx to pdf
    except Exception as e:

        file = doc_in

        out_folder = str(Path(app.root_path) / 'static' / 'out' / 'receipts')

        LIBRE_OFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"

        subprocess.Popen([LIBRE_OFFICE, '--headless', '--convert-to', 'pdf', '--outdir',
                              out_folder, file])

        print([LIBRE_OFFICE, '--convert-to', 'pdf', file])

        return pdf_out


def receipt_templating(context,
                       temp_file,
                       save_as,
                       printer):

    '''
    :param context: a dictionary key-value pair
    :param temp_file: template file path for receipt printing(Takeout and InHouse)
    :param save_as: the file name without file extension
    :param printer: the printer name for printing the receipt
    :return: "ok. if successfully printed
    '''

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    # if the printer is on
    if data.get('receipt').get('is_on'):

        from docxtpl import DocxTemplate

        doc = DocxTemplate(temp_file)

        logo = str(Path(app.root_path) / 'static' / 'img' / 'logo.png')

        # If logo existing, then inserts the LOGO into receipt
        if Path(logo).exists():

            p = doc.tables[1].rows[0].cells[0].add_paragraph()

            r = p.add_run()

            r.add_picture(logo)

        doc.render(context)

        abs_save_path = str(Path(app.root_path) / 'static' / 'out' / 'receipts' / f'{save_as}.docx')

        out_save_path = str(Path(app.root_path) / 'static' / 'out' / 'receipts' / f'{save_as}.pdf')

        doc.save(abs_save_path)

        docx2pdf(doc_in=abs_save_path,
                 pdf_out=out_save_path)

        # Print the PDF info from the thermal printer
        printer_path = str(Path(app.root_path) / 'utils' / 'printer' / 'PDFtoPrinter')

        import subprocess
        # call the command to print the pdf file
        wait_start = time.time()
        while True:
            if not Path(out_save_path).exists():
                time.sleep(0.5)
                wait_end = time.time()

                if wait_end - wait_start > 15:
                    break
            else:
                subprocess.Popen(f'{printer_path} {out_save_path} "{printer}"', shell=True)
                break

        return "ok"


def kitchen_templating(context,
                       temp_file,
                       save_as,
                       printer):

    '''
    :param context: a dictionary key-value pair
    :param temp_file: template file path for receipt printing(Takeout and InHouse)
    :param save_as: the file name without file extension
    :return: "ok. if successfully printed
     '''

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    # if the printer is on
    if data.get('kitchen').get('is_on'):

        from docxtpl import DocxTemplate

        doc = DocxTemplate(temp_file)

        doc.render(context)

        abs_save_path = str(Path(app.root_path) / 'static' / 'out' / 'receipts' / f'{save_as}.docx')

        out_save_path = str(Path(app.root_path) / 'static' / 'out' / 'receipts' / f'{save_as}.pdf')

        doc.save(abs_save_path)

        docx2pdf(doc_in=abs_save_path,
                 pdf_out=out_save_path)

        # Print the PDF info from the thermal printer
        printer_path = str(Path(app.root_path) / 'utils' / 'printer' / 'PDFtoPrinter')

        import subprocess
        # call the command to print the pdf file
        wait_start = time.time()
        while True:
            if not Path(out_save_path).exists():
                time.sleep(0.5)
                wait_end = time.time()

                if wait_end - wait_start > 15:
                    break
            else:
                subprocess.Popen(f'{printer_path} {out_save_path} "{printer}"', shell=True)
                break

        return "ok"


def bar_templating(context,
                   temp_file,
                   save_as,
                   printer):

    '''
   :param context: a dictionary key-value pair
   :param temp_file: template file path for receipt printing(Takeout and InHouse)
   :param save_as: the file name without file extension
   :return: "ok. if successfully printed
    '''

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    # if the printer is on
    if data.get('bar').get('is_on'):

        from docxtpl import DocxTemplate

        doc = DocxTemplate(temp_file)

        doc.render(context)

        abs_save_path = str(Path(app.root_path) / 'static' / 'out' / 'receipts' / f'{save_as}.docx')

        out_save_path = str(Path(app.root_path) / 'static' / 'out' / 'receipts' / f'{save_as}.pdf')

        doc.save(abs_save_path)

        docx2pdf(doc_in=abs_save_path,
                 pdf_out=out_save_path)

        # Printer EXE Path
        printer_path = str(Path(app.root_path) / 'utils' / 'printer' / 'PDFtoPrinter')

        import subprocess
        # call the command to print the pdf file
        wait_start = time.time()
        while True:
            if not Path(out_save_path).exists():
                time.sleep(0.5)
                wait_end = time.time()

                if wait_end - wait_start > 15:
                    break
            else:
                subprocess.Popen(f'{printer_path} {out_save_path} "{printer}"', shell=True)
                break

        return "ok"


def call2print(table_name):

    # Jinja Templating in word doc
    from docxtpl import DocxTemplate

    temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'info.docx')

    abs_save_path = str(Path(app.root_path) / 'static' / 'out' / f'info_{table_name}.docx')

    doc = DocxTemplate(temp_file)
    context = dict(table_name=table_name,
                   now=str(datetime.now(tz=pytz.timezone("Europe/Berlin"))))
    doc.render(context)
    doc.save(abs_save_path)

    # Docx to PDF Conversion
    out_save_path = str(Path(app.root_path) / 'static' / 'out' / f'info_{table_name}.pdf')

    # if the pdf info file doesn't exist
    if not Path(out_save_path).is_file():

        docx2pdf(doc_in=abs_save_path,
                 pdf_out=out_save_path)

    # Print the PDF info from the thermal printer
    printer_path = str(Path(app.root_path) / 'utils' / 'printer' / 'PDFtoPrinter')

    printer_name = "Star TSP100 Cutter (TSP143) eco"

    import subprocess
    # call the command to print the pdf file
    subprocess.Popen(f'{printer_path} {out_save_path} "{printer_name}"', shell=True)







