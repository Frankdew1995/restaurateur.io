import time
from PIL import Image, ImageDraw, ImageFont
from uuid import uuid4
import os
import json

from app import app, redirect, url_for, render_template, flash, db, jsonify

from pathlib import Path

import pyqrcode

from datetime import datetime, timedelta
import pytz

from app.models import Table, User

import subprocess

from babel.dates import format_date, format_datetime, format_time
from babel.numbers import format_decimal, format_percent

import pusher
import requests

import sys
import platform

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

    font_ttf = str(Path(app.root_path) / 'static' / 'fonts' / 'OpenSans-Bold.ttf')

    file_name = table + "_" + seat

    image = pyqrcode.create(url)

    save_abs_path = str(Path(app.root_path) / 'static' / 'qrcode' / f"{file_name}.png")

    image.png(save_abs_path, scale=5)

    img = Image.new('RGB', (60, 60), color="white")

    w, h = img.size

    d = ImageDraw.Draw(img)

    fnt = ImageFont.truetype(font_ttf, 3)

    w_text, h_text = d.textsize(table+"-"+seat, font=fnt)

    d.text(((w - w_text) / 2, (h - h_text) / 2), table+"-"+seat, fill="black")

    qrcode = Image.open(save_abs_path)

    w_qrcode, h_qrcode = qrcode.size

    qrcode.paste(img, ((w_qrcode - w) // 2, (h_qrcode - h) // 2))

    qrcode.save(save_abs_path)

    return f"{file_name}.png"


def activity_logger(order_id, operation_type,
                    page_name, descr,
                    status, log_time):
    try:
        from .models import Log
        from app import db

        log = Log()

        log.order_id = order_id
        log.status = status
        log.operation = operation_type
        log.desc = descr
        log.time = log_time
        log.page = page_name

        db.session.add(log)

        db.session.commit()

    except Exception as e:

        print(str(e))

    import csv

    row = (order_id, operation_type, page_name, descr, status, log_time)

    with open(str(Path(app.root_path) / 'cache' / 'logging.csv'),
              mode="a",
              encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerow(row)

    file.close()


def qrcode2excel(tables):

    import json
    import xlsxwriter

    save_abs_path = str(Path(app.root_path) / 'cache' / 'qrcode.xlsx')

    # Create an new Excel file and add a worksheet.
    workbook = xlsxwriter.Workbook(save_abs_path)

    # worksheet = workbook.add_worksheet()

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

        #         logo = str(Path(app.root_path) / 'static' / 'img' / 'logo.png')
        #
        # # If logo existing, then inserts the LOGO into receipt
        # if Path(logo).exists():
        #
        #     p = doc.tables[1].rows[0].cells[0].add_paragraph()
        #
        #     r = p.add_run()
        #
        #     r.add_picture(logo)

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

                if wait_end - wait_start > 30:
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

                if wait_end - wait_start > 30:
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

                if wait_end - wait_start > 30:
                    break
            else:
                subprocess.Popen(f'{printer_path} {out_save_path} "{printer}"', shell=True)
                break

        return "ok"


def terminal_templating(context,
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
    if data.get('terminal').get('is_on'):

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

                if wait_end - wait_start > 30:
                    break
            else:
                subprocess.Popen(f'{printer_path} {out_save_path} "{printer}"', shell=True)
                break

        return "ok"


def call2print(table_name, seat_number, is_paying, **kwargs):

    # Jinja Templating in word doc
    from docxtpl import DocxTemplate

    temp_file = None

    if is_paying:

        temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'pay.docx')

    else:

        temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'info.docx')

    abs_save_path = str(Path(app.root_path) / 'static' / 'out' / f'info_{table_name}.docx')

    now = datetime.now(tz=pytz.timezone("Europe/Berlin"))

    doc = DocxTemplate(temp_file)

    context = dict(table_name=table_name,
                   seat_number=seat_number,
                   now=format_datetime(now, locale="de_DE"))

    if "pay_with" in kwargs.keys():

        context['pay_with'] = kwargs['pay_with']

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
    wait_start = time.time()
    while True:
        if not Path(out_save_path).exists():
            time.sleep(0.5)
            wait_end = time.time()

            if wait_end - wait_start > 30:
                break
        else:
            subprocess.Popen(f'{printer_path} {out_save_path} "{printer_name}"', shell=True)
            break

    return "ok"


def pay2print(table_name, seat_number, is_paying, pay_with):

    # Jinja Templating in word doc
    from docxtpl import DocxTemplate

    temp_file = None

    if is_paying:

        temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'pay.docx')

    else:

        temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'info.docx')

    abs_save_path = str(Path(app.root_path) / 'static' / 'out' / f'info_{pay_with}_{table_name}.docx')

    now = datetime.now(tz=pytz.timezone("Europe/Berlin"))

    doc = DocxTemplate(temp_file)

    context = dict(table_name=table_name,
                   seat_number=seat_number,
                   now=format_datetime(now, locale="de_DE"),
                   pay_with=pay_with)

    doc.render(context)
    doc.save(abs_save_path)

    # Docx to PDF Conversion
    out_save_path = str(Path(app.root_path) / 'static' / 'out' / f'info_{pay_with}_{table_name}.pdf')

    # if the pdf info file doesn't exist
    if not Path(out_save_path).is_file():

        docx2pdf(doc_in=abs_save_path,
                 pdf_out=out_save_path)

    # Print the PDF info from the thermal printer
    printer_path = str(Path(app.root_path) / 'utils' / 'printer' / 'PDFtoPrinter')

    printer_name = "Star TSP100 Cutter (TSP143) eco"

    import subprocess
    # call the command to print the pdf file
    wait_start = time.time()
    while True:
        if not Path(out_save_path).exists():
            time.sleep(0.5)
            wait_end = time.time()

            if wait_end - wait_start > 30:
                break
        else:
            subprocess.Popen(f'{printer_path} {out_save_path} "{printer_name}"', shell=True)
            break

    return "ok"


def void_pickle_dumper(r_type):

    '''
    :param r_type: receipt type z or x
    :return:
    '''

    import pickle

    r_type = r_type.lower()

    with open(str(Path(app.root_path) / 'cache' / f'{r_type}_bon_settings.pickle'),
              mode="wb") as pickle_in:

        pickle.dump([], pickle_in)

    return pickle_in

def x_z_receipt_templating(context,
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

                if wait_end - wait_start > 30:
                    break
            else:
                subprocess.Popen(f'{printer_path} {out_save_path} "{printer}"', shell=True)
                break

        return "ok"


def table_adder(table_name, section, number,
                base_url, suffix_url, timezone):

    qrcodes = [generate_qrcode(table=table_name,
                               base_url=base_url,
                               suffix_url=suffix_url,
                               seat=str(i + 1)) for i in range(number)]

    table = Table(
        name=table_name,
        number=number,
        section=section,
        timeCreated=datetime.now(tz=pytz.timezone(timezone)),
        container=json.dumps({'isCalled': False,
                              'payCalled': False,
                              'qrcodes': qrcodes}),

        seats="\n".join([f"{table_name}-{i+1}" for
                         i in range(number)]))

    db.session.add(table)

    db.session.commit()


def formatter(number):

    if number == 0:

        number = '{:.2f}'.format(round(number, 2))

        number = number.replace(".", ",")

        return number

    number = format_decimal(round(float(number), 2), locale="de_DE")

    if len(number.split(",")) == 1:

        number = number + ",00"

        return number

    if len(number.split(",")[1]) == 1:

        number = number + "0"

        return number

    return number


def is_business_hours():

    timezone = "Europe/Berlin"

    from datetime import time as t

    info = json_reader(str(Path(app.root_path) / 'settings' / 'config.json'))

    hours = info.get('BUSINESS_HOURS')

    am_start = hours.get('MORNING', '').get('START', '').split(":")
    am_end = hours.get('MORNING', '').get('END', '').split(":")

    pm_start = hours.get('EVENING', '').get('START', '').split(":")
    pm_end = hours.get('EVENING', '').get('END', '').split(":")

    morning_start = t(int(am_start[0]), int(am_start[1]))

    morning_end = t(int(am_end[0]), int(am_end[1]))

    evening_start = t(int(pm_start[0]), int(pm_start[1]))

    evening_end = t(int(pm_end[0]), int(pm_end[1]))

    cur_time = datetime.now(tz=pytz.timezone(timezone)).time()

    # if not in business hours: redirect to the navigation page
    if not (morning_start <= cur_time <= morning_end
            or evening_start <= cur_time <= evening_end):

        return False

    return True


def daily_revenue_templating(context,
                             save_as):

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

    # Printer name
    printer = data.get('receipt').get('printer')

    temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'daily_revenue_temp.docx')

    # if the printer is on
    if data.get('receipt').get('is_on'):

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

                if wait_end - wait_start > 30:
                    break
            else:
                subprocess.Popen(f'{printer_path} {out_save_path} "{printer}"', shell=True)
                break

        return "ok"


def trigger_event(channel, event, response):

    info = json_reader(str(Path(app.root_path) / 'settings' / 'credentials.json'))

    # read Pusher credentials
    creds = info.get('PUSHER')
    app_id = creds.get('APP_ID')
    key = creds.get('KEY')
    secret = creds.get('SECRET')
    cluster = creds.get('CLUSTER')
    ssl = creds.get('SSL')

    channels_client = pusher.Pusher(

        app_id=app_id,
        key=key,
        secret=secret,
        cluster=cluster,
        ssl=ssl
    )

    channels_client.trigger(channel, event, response)


def start_ngrok(port):

    root_path = str(Path(app.root_path).parent)

    print(root_path)
    # Mac OS
    if platform.system() == "Darwin":

        exec_path = str(Path(app.root_path) / 'utils' / 'ngrok' / "mac")

        os.chdir(exec_path)

        executable = './ngrok'

        subprocess.Popen([executable, 'http', '-region=eu', str(port)])

        os.chdir(root_path)

    # Win32 or Linux
    else:

        bit_version = None

        executable = None

        if sys.maxsize > 2**32:

            bit_version = 64
            executable = str(Path(app.root_path) / 'utils'
                             / 'ngrok' / str(bit_version) / 'ngrok')

        else:

            bit_version = 32
            executable = str(Path(app.root_path) / 'utils'
                             / 'ngrok' / str(bit_version) / 'ngrok')

        subprocess.Popen([executable, 'http', '-region=eu', str(port)])

    localhost_url = "http://localhost:4040/api/tunnels"  # Url with tunnel details
    time.sleep(1)
    tunnel_url = requests.get(localhost_url).text  # Get the tunnel information
    j = json.loads(tunnel_url)
    tunnel_url = j['tunnels'][0]['public_url']  # Do the parsing of the get
    tunnel_url = tunnel_url.replace("https", "http")

    # Read the creds data from the config
    settings = json_reader(str(Path(app.root_path) / 'settings' / 'credentials.json'))

    # Writing the new public tunnel url to config file
    settings.update({"PUBLIC_TUNNEL_URL": tunnel_url})

    data = [settings]

    with open(str(Path(app.root_path) / 'settings' / "credentials.json"), 'w', encoding="utf8") as file:

        json.dump(data, file, indent=2)

    print(tunnel_url)
    return tunnel_url


def is_xz_printed(timestamp, r_type):

    r_type = r_type.lower()

    import pickle

    with open(str(Path(app.root_path) / 'cache' / f'{r_type}_bon_settings.pickle'),
              mode="rb") as pickle_out:

        data = pickle.load(pickle_out)

    printed_timestamps = []

    for record in data:

        print(record)

        key = list(record.keys())[0]

        last_printed = record.get(key).get('lastPrinted')
        last_timestamp = last_printed.timestamp()
        printed_timestamps.append(last_timestamp)

    return timestamp in printed_timestamps