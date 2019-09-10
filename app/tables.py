from app import (app, db, render_template,
                 redirect, url_for, request,
                 flash, jsonify, send_file)

from flask_login import current_user, login_user, login_required, logout_user

from .models import User, Table, Food, Order, Visit, Log, Holiday

from .forms import (AddDishForm, StoreSettingForm,
                    RegistrationForm, LoginForm,
                    EditDishForm, CheckoutForm,
                    AddTableForm, EditTableForm,
                    ConfirmForm, TableSectionQueryForm,
                    SearchTableForm, DatePickForm,
                    AddUserForm, EditUserForm,
                    EditPrinterForm, EditBuffetPriceForm,
                    AddHolidayForm, EditHolidayForm,
                    AddCategoryForm, EditCategoryForm,
                    AuthForm)

from .utilities import (json_reader, store_picture,
                        generate_qrcode, activity_logger,
                        qrcode2excel, call2print, receipt_templating,
                        bar_templating, kitchen_templating,
                        terminal_templating, x_z_receipt_templating)

from pathlib import Path
import json
from uuid import uuid4
from datetime import datetime, timedelta, time
import pytz
from threading import Thread
from werkzeug.utils import secure_filename
import pickle
from babel.dates import format_date, format_datetime, format_time
from babel.numbers import format_decimal, format_percent

# Some global variables - read from config file.

info = json_reader(str(Path.cwd() / 'app' / 'settings' / 'config.json'))


company_info = {
            "tax_rate_out": info.get('TAX_RATE').get('takeaway'),
            "tax_rate_in": info.get('TAX_RATE').get('Inhouse Order'),
            "company_name": info.get('STORE_NAME'),
            "address": f'{info.get("STREET")} {info.get("STREET NO.")}, {info.get("ZIP")} {info.get("CITY")}',
            "tax_id": info.get('TAX_ID'),

        }

hours = info.get('BUSINESS_HOURS')

time_buffer_mins = int(info.get('BUFFET_TIME_BUFFER'))

max_rounds = int(info.get('ORDER_TIMES'))

date_format = "%Y.%m.%d"

datetime_format = "%Y.%m.%d %H:%M:%S"

tax_rate_in = float(company_info.get('tax_rate_in', 0.0))

tax_rate_out = float(company_info.get('tax_rate_out', 0.0))

base_url = "http://4cb0771c.ngrok.io"
suffix_url = "guest/navigation"

timezone = 'Europe/Berlin'

today = datetime.now(tz=pytz.timezone(timezone)).date()


# Table view function
@app.route("/tables/add", methods=["POST", "GET"])
@login_required
def add_table():

    form = AddTableForm()
    import string
    letter_string = string.ascii_uppercase
    letters = [letter for letter in letter_string]

    # Instantiate some options for select fields
    form.section.choices.extend([(i, i) for i in letters])

    if form.validate_on_submit() or request.method == "POST":

        table_name = form.name.data.upper()

        # Check Duplicates
        if not Table.query.filter_by(name=table_name).first_or_404():

            qrcodes = [generate_qrcode(table=form.name.data.upper(),
                                       base_url=base_url,
                                       suffix_url=suffix_url,
                                       seat=str(i+1)) for i in range(form.persons.data)]

            table = Table(
                name=form.name.data.upper(),
                number=form.persons.data,
                section=form.section.data,
                timeCreated=datetime.now(tz=pytz.timezone("Europe/Berlin")),
                container=json.dumps({'isCalled': False,
                                      'payCalled': False,
                                      'qrcodes': qrcodes}),

                seats="\n".join([f"{form.name.data.upper()}-{i+1}" for
                                 i in range(form.persons.data)])
            )

            db.session.add(table)

            db.session.commit()

            flash(f"已经成功创建桌子：{form.name.data}")

            return redirect(url_for('view_tables'))

        else:

            flash(f"{table_name}已经存在，请重新输入桌子名称")

            return redirect(url_for('add_table'))

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"添加桌子",
                   company_name=company_info.get('company_name'),
                   format=datetime_format,
                   form=form)

    return render_template("add_table.html", **context)
