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
                        terminal_templating, x_z_receipt_templating,
                        table_adder, formatter, is_business_hours,
                        daily_revenue_templating)

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

info = json_reader(str(Path.cwd() / 'app' / 'settings' / 'config.json'))

hours = info.get('BUSINESS_HOURS')

time_buffer_mins = int(info.get('BUFFET_TIME_BUFFER'))

max_rounds = int(info.get('ORDER_TIMES'))

date_format = "%Y.%m.%d"

datetime_format = "%Y.%m.%d %H:%M:%S"

tax_rate_in = float(company_info.get('tax_rate_in', 0.0))

tax_rate_out = float(company_info.get('tax_rate_out', 0.0))

base_url = "http://75aa4848.eu.ngrok.io"
suffix_url = "guest/navigation"

timezone = 'Europe/Berlin'

today = datetime.now(tz=pytz.timezone(timezone)).date()


# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():

    form = LoginForm()

    referrer = request.headers.get('Referer')

    if current_user.is_authenticated:

        # Check whether this account is in use
        if json.loads(current_user.container).get("inUse"):

            # According permission, route the user to the corresponding page
            if current_user.permissions <= 3:

                # Admin account
                if current_user.permissions == 2:

                    return redirect(url_for("index"))

                # Waiter account
                elif current_user.permissions == 1:

                    return redirect(url_for("waiter_admin"))

                # Take away Account
                elif current_user.permissions == 0:

                    return redirect(url_for("takeaway_orders_manage"))

            # Boss Account
            else:

                return redirect(url_for('index'))

        else:

            return render_template('suspension_error.html', referrer=referrer)

    elif form.validate_on_submit():

        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(password=form.password.data):

            flash(u"密码或者用户名无效!")
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')

        # Check whether this account is in use
        if json.loads(user.container).get("inUse"):

            # According permission, route the user to the corresponding page
            if user.permissions <= 3:

                # Admin account
                if user.permissions == 2:

                    return redirect(url_for("index"))

                # Waiter account
                elif user.permissions == 1:

                    return redirect(url_for("waiter_admin"))

                # Take away Account
                elif user.permissions == 0:

                    return redirect(url_for("takeaway_orders_manage"))

            # Boss Account
            else:
                return redirect(url_for('index'))

        else:

            return render_template('suspension_error.html', referrer=referrer)

    return render_template("login.html", form=form)


# Logout Route
@app.route('/logout')
def logout():

    logout_user()

    return redirect(url_for('login'))


# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():

    form = RegistrationForm()
    if form.validate_on_submit():

        username = form.username.data
        email = form.email.data

        user = User(username=username, email=email)

        # Class method to set the password_hash by password passed in the form
        user.set_password(password=form.password.data)

        db.session.add(user)
        db.session.commit()

        flash(f"Your Account {username} has been successfully created!!")

        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route('/analytics', methods=["GET", "POST"])
def return_analytics():

    today = datetime.now(pytz.timezone(timezone)).date()
    yesterday = datetime.now(pytz.timezone(timezone)).date() - timedelta(days=1)
    paid_orders = Order.query.filter(Order.isPaid == True).all()

    times = [f"0{i+1}:00" if i + 1 <= 9 else f"{i+1}:00" for i in range(23)]

    times.append("00:00")

    cur_order_counts_by_clock = [sum([order.totalPrice for order in paid_orders
                                         if order.timeCreated.date() == today
                                         and order.timeCreated.time()
                                         <= datetime.strptime(i, '%H:%M').time()]) for i in times]

    last_order_counts_by_clock = [sum([order.totalPrice for order in paid_orders
                                         if order.timeCreated.date() == yesterday
                                         and order.timeCreated.time()
                                         <= datetime.strptime(i, '%H:%M').time()]) for i in times]

    # Graphing part:

    # Weekly Data Computing and Plotting

    start = today - timedelta(days=today.weekday())

    cur_weekdays = [(start + timedelta(days=n)).strftime("%A") for n in range(7)]

    cur_week_revenue = [sum([order.totalPrice
                             for order in paid_orders if
                                order.timeCreated.date() == start + timedelta(days=n)])
                                    for n in range(7)]

    weekdays2revenue = {
        (start + timedelta(days=n)).strftime("%A"):
            sum([order.totalPrice for order in paid_orders if
                order.timeCreated.date() == start + timedelta(days=n)]) for n in range(7)}

    start_last_week = start - timedelta(days=7)

    last_weekdays = [(start_last_week + timedelta(days=n)).strftime("%A") for n in range(7)]

    last_week_revenue = [sum([order.totalPrice \
                             for order in paid_orders if \
                             order.timeCreated.date() == \
                              start_last_week + timedelta(days=n)]) \
                                    for n in range(7)]

    # Monthly Revenue
    # cur month
    cur_year = int(today.strftime("%Y"))

    cur_mon = int(today.strftime("%m"))

    start_cur_month = datetime(cur_year, cur_mon, 1).date()

    mon_range = 31

    cur_mon_dates = [int((start_cur_month + timedelta(days=n)).strftime("%d")) \
                        for n in range(mon_range)]

    cur_mon_revenue_by_dates = [sum([order.totalPrice \
                                   for order in paid_orders if \
                                    order.timeCreated.date() == start_cur_month\
                                     + timedelta(days=n)]) \
                                        for n in range(mon_range)]

    # Store data in a dict
    data = dict(
                weekdays2revenue=weekdays2revenue,
                cur_weekdays=cur_weekdays,
                cur_week_revenue=cur_week_revenue,
                last_weekdays=last_weekdays,
                last_week_revenue=last_week_revenue,
                cur_mon_dates=cur_mon_dates,
                cur_mon_revenue_by_dates=cur_mon_revenue_by_dates,
                cur_order_counts_by_clock=cur_order_counts_by_clock,
                last_order_counts_by_clock=last_order_counts_by_clock,
                times=times)

    # last month
    if cur_mon != 1:

        last_mon = cur_mon - 1

        start_last_mon = datetime(cur_year, last_mon, 1).date()

        data['last_mon_dates'] = [int((start_last_mon + timedelta(days=n)).strftime("%d"))
                                    for n in range(mon_range)]

        data['last_mon_revenue_by_dates'] = [
                sum([order.totalPrice for order in paid_orders if
                     order.timeCreated.date() == start_last_mon + timedelta(days=n)])
                        for n in range(mon_range)]

    else:

        last_mon = 12

        start_last_mon = datetime(cur_year - 1, last_mon, 1).date()

        data['last_mon_dates'] = [int((start_last_mon + timedelta(days=n)).strftime("%d"))
                                  for n in range(mon_range)]

        data['last_mon_revenue_by_dates'] = [
            sum([order.totalPrice for order in paid_orders if
                 order.timeCreated.date() == start_last_mon + timedelta(days=n)])
                        for n in range(mon_range)]

    return jsonify(data)


# Admin Index Page
@app.route("/")
@login_required
def index():

    # Software Licensing Time - 2 years
    admin_user = User.query.filter_by(permissions=100).first_or_404()

    deadline = admin_user.timeCreated + timedelta(days=365 * 2)

    if datetime.now(tz=None) >= deadline:

        logout_user()

        flash("软件使用权限到期，请及时联系我们续费以便后续使用.谢谢合作！")

        return redirect(url_for('login'))

    if not json.loads(current_user.container).get('inUse'):

        return render_template('suspension_error.html')

    today = datetime.now(pytz.timezone(timezone)).date()
    yesterday = datetime.now(pytz.timezone(timezone)).date() - timedelta(days=1)
    paid_orders = Order.query.filter(Order.isPaid==True).all()

    # Visits part
    visits = Visit.query.all()

    cur_visits = sum([v.count for v in visits
                      if v.timeVisited.date() ==
                      datetime.now(pytz.timezone(timezone)).date()])

    last_visits = sum([v.count for v in visits
                      if v.timeVisited.date() == yesterday])

    daily_visit_up_rate = None

    # Handling zero division error
    if last_visits == 0:

        daily_visit_up_rate = "100%"

    else:
        daily_visit_up_rate = str(round(((cur_visits - last_visits) / last_visits) * 100, 2)) + "%"

    # count customers who actually ordered.
    cur_guests = len([order for order in paid_orders \
                      if order.timeCreated.date() == today])

    last_guests = len([order for order in paid_orders \
                       if order.timeCreated.date() == yesterday])

    daily_guests_up_rate = None
    if last_guests == 0:
        daily_guests_up_rate = "100%"
    else:
        daily_guests_up_rate = str(round(((cur_guests - last_guests) / last_guests) * 100, 2)) + "%"

    # Revenue part
    cur_revenue = sum([order.totalPrice for order in paid_orders
                       if order.timeCreated.date() <= today])

    last_revenue = sum([order.totalPrice
                       for order in paid_orders
                       if order.timeCreated.date() <= yesterday])

    daily_revenue_up_rate = str(round(((cur_revenue - last_revenue) / last_revenue) * 100, 2)) + "%"

    from calendar import monthrange

    cur_year = int(today.strftime("%Y"))

    cur_mon = int(today.strftime("%m"))

    start_cur_mon = datetime(cur_year, cur_mon, 1).date()

    cur_mon_range = monthrange(cur_year, cur_mon)[1]

    end_cur_mon = datetime(cur_year, cur_mon, cur_mon_range).date()

    cur_mon_revenue = sum([order.totalPrice for order in paid_orders
                         if start_cur_mon <= order.timeCreated.date() <= end_cur_mon])

    last_mon = None
    start_last_mon = None
    last_mon_range = None
    end_last_mon = None

    if cur_mon != 1:
        last_mon = cur_mon - 1
        start_last_mon = datetime(cur_year, last_mon, 1).date()
        last_mon_range = monthrange(cur_year, last_mon)[1]
        end_last_mon = datetime(cur_year, last_mon, last_mon_range).date()

    else:
        last_mon = 12
        last_year = cur_year - 1
        start_last_mon = datetime(last_year, last_mon, 1).date()
        last_mon_range = monthrange(last_year, last_mon)[1]
        end_last_mon = datetime(last_year, last_mon, last_mon_range).date()

    last_mon_revenue = sum([order.totalPrice for order in paid_orders \
                           if start_last_mon <= order.timeCreated.date() <= end_last_mon])

    monthly_revenue_up_rate = None
    if last_mon_revenue == 0 or None:

        monthly_revenue_up_rate = "100%"

    else:
        monthly_revenue_up_rate = str(round(((cur_mon_revenue - last_mon_revenue) / last_mon_revenue), 0) * 100) + "%"

    foods = Food.query.all()

    order_counts = {food.name:
                        {"counts": sum([json.loads(order.items).get(food.name).get('quantity') \
                         for order in paid_orders \
                         if food.name in json.loads(order.items).keys()]),
                         "Img": food.image,
                         "ID": food.id} for food in foods}

    context = dict(title="总览",
                   cur_visits=cur_visits,
                   daily_visit_up_rate=daily_visit_up_rate,
                   cur_guests=cur_guests,
                   daily_guests_up_rate=daily_guests_up_rate,
                   cur_revenue=formatter(cur_revenue),
                   daily_revenue_up_rate=daily_revenue_up_rate,
                   cur_mon_revenue=formatter(cur_mon_revenue),
                   monthly_revenue_up_rate=monthly_revenue_up_rate,
                   order_counts=order_counts,
                   company_name=company_info.get('company_name'))

    return render_template("analytics.html", current_user=current_user, **context)


# Guest Facing Order Interface
@app.route("/takeaway/frontviews")
def food_frontview():

    dishes = Food.query.filter(Food.inUse == True).all()

    categories = set([dish.category for dish in dishes])

    context =dict(dishes=dishes,
                  categories=categories,
                  title='Xstar Takeout Food',
                  tel="+ 49 555555",
                  formatter=formatter)

    return render_template('foodfrontview.html', **context)


@app.route("/takeout/checkout", methods=["POST"])
def takeaway_checkout():

    try:

        # Json Data Posted via AJAX
        json_data = request.get_json("details")

        details = json_data.get('details')

        food = [i.get('itemName') for i in details]

        unique_food = list(set(food))

        details = {dish: {'quantity': food.count(dish),
                          'price': Food.query.filter_by(name=dish).first_or_404().price_gross}
                   for dish in unique_food}

        total_price = sum([i[1].get('quantity') * i[1].get('price')
                           for i in details.items()])

        order = Order(
            totalPrice=total_price,
            orderNumber=str(uuid4().int),
            items=json.dumps(details),
            timeCreated=datetime.now(tz=pytz.timezone(timezone)),
            type="Out",
            endTotal=total_price)

        db.session.add(order)
        db.session.commit()

        # Order Terminal Order Printing
        details = {key: {'quantity': items.get('quantity'),
                         'total': items.get('quantity') * items.get('price')}
                   for key, items in details.items()}

        vat = round((order.totalPrice / (1 + tax_rate_out)) * tax_rate_out, 2)

        context = {"details": details,
                   "company_name": company_info.get('company_name', ''),
                   "address": company_info.get('address'),
                   "now": format_datetime(datetime.now(), locale="de_DE"),
                   "tax_id": company_info.get('tax_id'),
                   "wait_number": order.id,
                   "total": formatter(order.totalPrice),
                   "VAT": formatter(vat)}

        temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'terminal_temp_out.docx')
        save_as = f"wait_receipt_{order.id}"

        # Read the printer setting data from the json file
        with open(str(Path(app.root_path) / "settings" / "printer.json"),
                  encoding="utf8") as file:

            data = file.read()

        data = json.loads(data)

        def master_printer():

            # Print Receipt
            terminal_templating(context=context,
                                temp_file=temp_file,
                                save_as=save_as,
                                printer=data.get('terminal').get('printer'))

        # Start the thread
        th = Thread(target=master_printer)
        th.start()

        return jsonify({'success': 'Ihre Bestellung war erfolgreich. Bitte melden Sie sich bei der Kasse!'})

    except:

        return jsonify({'error': 'Ups.... die Bestellung ist leider nicht erfolgreich. Bitte versuchen Sie es erneut'})


# Complete a takeaway order
app.route("/order/pickup", methods=["POST"])
def pickup_order():

    if request.method == "POST":

        json_data = request.get_json()

        print(json_data)

    return redirect(url_for('takeaway_orders_manage'))


@app.route('/takeaway/cancel/<int:order_id>')
@login_required
def cancel_out_order(order_id):

    order = db.session.query(Order).get_or_404(int(order_id))

    order.isCancelled = True

    db.session.commit()

    flash(f"外卖订单{order.id}已经取消", category="success")

    return redirect(url_for('takeaway_orders_manage'))


# Checkout a takeaway order ????
@app.route("/orders/<string:order_id>/checkout", methods=["GET", "POST"])
def checkout_order(order_id):

    order = Order.query.filter_by(id=int(order_id)).first()

    if order:

        if not order.isPaid:

            order.isPaid = True
            db.session.commit()

            flash(f"订单{order_id}已经结账成功!")

            return redirect(url_for('takeaway_orders_manage'))

        elif not order.isReady:

            order.isReady = True
            db.session.commit()

            flash(f"订单{order_id}备餐完毕!")

            return redirect(url_for('takeaway_orders_manage'))

        elif not order.isPickedUp:

            order.isPickedUp = True

            db.session.commit()

            flash(f"订单{order_id}取餐完毕!")

            return redirect(url_for('takeaway_orders_manage'))

    return redirect(url_for('takeaway_orders_manage'))


@app.route("/takeaway/order/<int:order_id>/checkout", methods=["POST", "GET"])
@login_required
def checkout_takeaway_admin(order_id):

    form = CheckoutForm()

    order = db.session.query(Order).get_or_404(int(order_id))

    order_items = json.loads(order.items)

    if not order.isCancelled:

        for key, details in order_items.items():

            item = Food.query.filter_by(name=key).first()

            if item:

                details["image"] = item.image
                details["descr"] = item.description
                details["price"] = item.price_gross
                details["class_name"] = item.class_name
                details["category"] = item.category

        prices = {'tax': round((order.totalPrice / (1 + tax_rate_out)) * tax_rate_out, 2),
                  'subtotal': round(order.totalPrice / (1 + tax_rate_out), 2)}

        # Logging Data Store
        logging = {}

        logging['Order ID'] = order.id

        if request.method == "POST":

            pay_via = {}

            # Set the settleID and settleTime
            settle_id = str(uuid4().int)
            settle_time = datetime.now(tz=pytz.timezone(timezone))

            # Pay via cash
            if form.cash_submit.data:

                if form.coupon_amount.data and form.discount_rate.data:

                    flash(f"不能同时使用折扣和代金券结账")
                    return redirect(url_for('checkout_takeaway_admin',
                                            order_id=order_id))

                if form.coupon_amount.data:

                    order.endTotal = order.totalPrice - form.coupon_amount.data

                    order.discount = form.coupon_amount.data

                    pay_via['coupon_amount'] = form.coupon_amount.data

                    logging['Total'] = order.totalPrice

                elif form.discount_rate.data:

                    order.endTotal = order.totalPrice * form.discount_rate.data
                    order.discount_rate = form.discount_rate.data

                    pay_via['discount_rate'] = form.discount_rate.data
                    logging['Total'] = order.totalPrice

                pay_via["method"] = "Cash"

                logging['Pay'] = u'现金'

            # Pay via card
            elif form.card_submit.data:

                if form.coupon_amount.data and form.discount_rate.data:

                    flash(f"不能同时使用折扣和代金券结账")
                    return redirect(url_for('checkout_takeaway_admin',
                                            order_id=order_id))

                if form.coupon_amount.data:

                    order.endTotal = order.totalPrice - form.coupon_amount.data

                    order.discount = form.coupon_amount.data

                    pay_via['coupon_amount'] = form.coupon_amount.data

                    logging['Total'] = order.totalPrice

                elif form.discount_rate.data:

                    order.endTotal = order.totalPrice * form.discount_rate.data

                    order.discount_rate = form.discount_rate.data

                    pay_via['discount_rate'] = form.discount_rate.data

                    logging['Total'] = order.totalPrice

                pay_via['method'] = "Card"
                logging['Pay'] = u'卡'

            order.settleTime = settle_time
            order.settleID = settle_id

            order.isPaid = True

            order.pay_via = json.dumps(pay_via)

            order.type = 'Out'
            logging['Type'] = u'外卖'

            db.session.commit()

            details = {key: {'quantity': items.get('quantity'),
                             'total': items.get('quantity') * items.get('price')}
                                for key, items in json.loads(order.items).items()}

            details_kitchen = {key: {'quantity': items.get('quantity'),
                                     'total': items.get('quantity') * items.get('price')}
                                        for key, items in order_items.items() if items.get("class_name") == "Food"}

            details_bar = {key: {'quantity': items.get('quantity'),
                                 'total': items.get('quantity') * items.get('price')}
                                    for key, items in order_items.items() if items.get("class_name") == "Drinks"}

            context_kitchen = {"details": details_kitchen,
                               "wait_number": order.id}

            kitchen_temp = str(Path(app.root_path) / 'static' / 'docx' / 'kitchen.docx')
            save_as_kitchen = f"meallist_kitchen_{order.id}"

            context_bar = {"details": details_bar,
                           "wait_number": order.id}

            bar_temp = str(Path(app.root_path) / 'static' / 'docx' / 'bar.docx')
            save_as_bar = f"meallist_bar_{order.id}"

            context = {"details": details,
                       "company_name": company_info.get('company_name', ''),
                       "address": company_info.get('address'),
                       "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "tax_id": company_info.get('tax_id'),
                       "wait_number": order.id,
                       "total": formatter(round(order.totalPrice, 2)),
                       "end_total": formatter(order.endTotal),
                       "pay_via": json.loads(order.pay_via).get('method', ""),
                       "discount": formatter(0),
                       "VAT": formatter((order.endTotal / tax_rate_out) * tax_rate_out)}

            if form.coupon_amount.data:

                context['discount'] = formatter(form.coupon_amount.data)

            elif order.discount_rate:

                context['discount'] = formatter((1 - form.discount_rate.data) * order.totalPrice)

            temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'receipt_temp_out.docx')
            save_as = f"receipt_{order.id}"

            # Read the printer setting data from the json file
            with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:

                data = file.read()

            data = json.loads(data)

            def master_printer():

                # Print Receipt
                receipt_templating(context=context,
                                   temp_file=temp_file,
                                   save_as=save_as,
                                   printer=data.get('receipt').get('printer')
                                   )

                # Print to kitchen
                kitchen_templating(context=context_kitchen,
                                   temp_file=kitchen_temp,
                                   save_as=save_as_kitchen,
                                   printer=data.get('kitchen').get('printer'))

                # Print to bar
                bar_templating(context=context_bar,
                               temp_file=bar_temp,
                               save_as=save_as_bar,
                               printer=data.get('bar').get('printer'))

            # Start the thread
            th = Thread(target=master_printer)
            th.start()

            try:
                # Writing logs to the csv file
                activity_logger(order_id=order.id,
                                operation_type=u'结账',
                                page_name=u'外卖界面 > 订单结账',
                                descr=f'''结账订单号:{order.id}\n
                                支付方式:{logging.get('Pay')}\n
                                账单金额: {order.totalPrice}\n
                                订单类型:{logging.get('Type')}\n''',
                                log_time=str(datetime.now(tz=pytz.timezone(timezone))),
                                status=u'成功')
            except:

                pass

            flash(f"已经为订单{order.id}结账")

            return redirect(url_for('takeaway_orders_manage'))

        context = dict(order=order,
                       order_items=order_items,
                       prices=prices,
                       form=form,
                       datetime_format=datetime_format,
                       formatter=formatter,
                       title=u"订单结账",
                       company_name=company_info.get('company_name'))

        return render_template('takeaway_checkout_admin.html', **context)

    else:

        flash(f'订单{order.id}不存在！')

        return redirect(url_for('takeaway_orders_manage'))


@app.route("/takeaway/orders/view")
@login_required
def takeaway_orders_manage():

    if not json.loads(current_user.container).get('inUse'):

        return render_template('suspension_error.html')

    orders = Order.query.filter(
        Order.type == "Out",
        Order.isCancelled == False).all()

    # Filtering only orders today based on timezone Berlin
    orders = [order for order in orders if
              order.timeCreated.date() == today]

    # Convert json string to Python objects so that it can be used in Templates
    indexedDict = {order.id: json.loads(order.items) for order in orders}

    context = dict(title=u"订单查看",
                   company_name=company_info.get('company_name'),
                   orders=orders,
                   items=indexedDict)

    return render_template('takeaway_orders_view.html', **context)


@app.route("/takeaway/orders/admin")
def takeaway_orders_admin():

    orders = Order.query.filter(
        Order.type == "Out").all()

    # Filtering only orders today based on timezone Berlin
    open_orders = [order for order in orders if order.timeCreated.date() == today]

    context = dict(title=u"订单查看",
                   company_name=company_info.get('company_name'),
                   open_orders=open_orders,
                   referrer=request.headers.get('Referer'),
                   datetime_format=datetime_format,
                   formatter=formatter)

    return render_template('takeaway_orders_admin.html', **context)


@app.route("/takeaway/order/<int:order_id>/edit")
def takeaway_order_edit(order_id):

    order = Order.query.get_or_404(int(order_id))

    ordered_items = json.loads(order.items)

    title = None
    if order.isPaid:

        title = "订单查看"

    else:

        title = "订单修改"

    context=dict(order=order,
                 ordered_items=ordered_items,
                 title=title,
                 company_name=company_info.get('company_name'),
                 referrer=request.headers.get('Referer'),
                 datetime_format=datetime_format,
                 formatter=formatter)

    return render_template('takeaway_order_edit.html', **context)


# Handling data transmissioned via Ajax
@app.route("/takeaway/order/update", methods=["POST"])
@login_required
def update_takeaway_order():

    logging = {}

    # Ajax Data Transmission
    if request.method == "POST":

        data = request.get_json('orderId')

        order_id = int(data.get("orderId"))

        order = db.session.query(Order).get_or_404(int(order_id))

        details = data.get('details')

        logging['before'] = "\n".join([f"{key}x{items.get('quantity')}" for (key, items) in json.loads(order.items).items()])

        logging['price_before'] = order.totalPrice

        if len(details) > 0:

            price_dict = {
                i.get('item'):
                    Food.query.filter_by(name=i.get('item')).first_or_404().price_gross
                for i in details}

            details = {
                detail.get('item'):
                    {'quantity': int(detail.get('quantity')),
                     'price': float(price_dict.get(detail.get('item')))}
                for detail in details}

            logging['after'] = "\n".join([f"{key}x{items.get('quantity')}" for (key, items) in details.items()])

            prices = [i[1].get('quantity') * i[1].get('price') for i in details.items()]

            order.totalPrice = sum(prices)

            order.items = json.dumps(details)

            db.session.commit()

            logging['price_after'] = order.totalPrice

            flash(f"已经修改订单:{order_id}", category="success")

        else:

            order.totalPrice = 0
            order.items = json.dumps({})

            db.session.commit()

            logging['price_after'] = 0
            logging['after'] = ""
            logging['remark'] = u'订单清空'

            flash(f"已经修改订单:{order_id}", category="success")

        try:

            # Writing logs to the csv file
            activity_logger(order_id=order.id,
                            operation_type=u'订单修改',
                            page_name=u'外卖界面 > 订单管理 >订单修改',
                            descr=f'''
                            修改订单号:{order.id}\n
                            修改前明细:{logging.get('before')}\n
                            修改后明细:{logging.get('after')}\n
                            修改前账单金额: {logging.get('price_before')}\n
                            修改后账单金额: {logging.get('price_after')}\n
                            订单类型:外卖\n
                            {logging.get('remark')}\n''',
                            log_time=str(datetime.now(tz=pytz.timezone('Europe/Berlin'))),
                            status=u'成功')
        except:

            pass

        return "Ok"


@app.route("/admin/takeaway/orders/all")
@login_required
def all_out_orders():

    referrer = request.headers.get('Referer')

    # Filter only takeaway orders
    orders = Order.query.filter(Order.type == "Out").all()

    context = dict(title=u'外卖订单',
                   orders=orders,
                   referrer=referrer,
                   company_name=company_info.get('company_name'),
                   formatter=formatter)

    return render_template('all_out_orders.html', **context)


@app.route('/admin/view/open/alacarte/orders')
@login_required
def admin_view_alacarte_open_orders():

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False,
        Order.isCancelled == False).all()

    cur_orders = [order for order in orders if
                  order.timeCreated.date() ==
                  datetime.now(tz=pytz.timezone(timezone)).date()]

    items = {order.id: json.loads(order.items) for order in cur_orders}

    context = dict(open_orders=cur_orders,
                   items=items,
                   datetime_format=datetime_format,
                   referrer=request.headers.get('Referer'),
                   title=u"餐桌情况(未结账)",
                   formatter=formatter)

    return render_template("admin_view_alalcarte_open_orders.html", **context)


@app.route("/admin/alacarte/order/<int:order_id>/edit")
@login_required
def admin_alacarte_order_edit(order_id):

    order = Order.query.get_or_404(int(order_id))

    ordered_items = json.loads(order.items)

    referrer = request.headers.get('Referer')

    context = dict(order=order,
                   ordered_items=ordered_items,
                   referrer=referrer,
                   str_referrer=str(referrer),
                   title=u"订单修改/查看",
                   datetime_format=datetime_format,
                   company_name=company_info.get('company_name'),
                   formatter=formatter)

    return render_template('admin_alacarte_order_edit.html', **context)


@app.route('/admin/alacarte/orders/update', methods=["GET", "POST"])
@login_required
def admin_update_alacarte_order():

    logging = {}

    if request.method == "POST":

        data = request.get_json('orderId')

        print(data)

        order_id = data.get('orderId')

        order = db.session.query(Order).get_or_404(int(order_id))

        logging['before'] = "\n".join([f"{key}x{items.get('quantity')}" \
                                       for (key, items) in json.loads(order.items).items()])

        details = data.get('details')

        logging['after'] = "\n".join([f"{i.get('item')}x{i.get('quantity')}" \
                                      for i in details])

        price_dict = {
            i.get('item'):
                Food.query.filter_by(name=i.get('item')).first_or_404().price_gross
                      for i in details}

        details = {
            detail.get('item'):
                {'quantity': int(detail.get('quantity')),
                 'price': float(price_dict.get(detail.get('item')))}
            for detail in details}

        prices = [i[1].get('quantity') * i[1].get('price') for i in details.items()]

        order.totalPrice = sum(prices)
        order.items = json.dumps(details)

        db.session.commit()

        try:

            # Writing logs to the csv file
            activity_logger(order_id=order.id,
                            operation_type=u'订单修改',
                            page_name=u'后台界面 > 餐桌情况(未结账) >订单修改',
                            descr=f'''
                            修改订单号:{order.id}\n
                            桌子编号：{json.loads(order.container).get('table_name')}-{json.loads(order.container).get('seat_number')}\n
                            修改前明细:{logging.get('before')}\n
                            修改后明细:{logging.get('after')}\n
                            修改前账单金额: {logging.get('price_before')}\n
                            修改后账单金额: {logging.get('price_after')}\n
                            订单类型:AlaCarte\n
                            {logging.get('remark')}\n''',
                            log_time=str(datetime.now(tz=pytz.timezone('Europe/Berlin'))),
                            status=u'成功')

        except:

            pass

        return redirect(url_for('admin_view_alacarte_open_orders'))


@app.route('/admin/alacarte/order/<int:order_id>/cancel', methods=["GET", "POST"])
@login_required
def admin_cancel_alacarte_order(order_id):

    form = ConfirmForm()

    logging = {}

    order = db.session.query(Order).get_or_404(int(order_id))

    if form.validate_on_submit():

        if order:

            order.isCancelled = True

            db.session.commit()

            try:

                # Writing logs to the csv file
                activity_logger(order_id=order.id,
                                operation_type=u'订单取消',
                                page_name=u'后台界面 > 餐桌情况(未结账)',
                                descr=f'''
                                取消订单号:{order.id}\n
                                桌子编号：{order.table_name}\n
                                账单金额: {order.totalPrice}\n
                                订单类型: AlaCarte\n
                                {logging.get('remark')}\n''',
                                log_time=str(datetime.now(tz=pytz.timezone('Europe/Berlin'))),
                                status=u'成功')

            except:

                pass

            return redirect(url_for('admin_view_alacarte_open_orders'))

    return render_template('admin_cancel_alacarte_order.html',
                           form=form,
                           order=order)


@app.route('/admin/view/paid/alacarte/orders')
@login_required
def admin_view_paid_alacarte_orders():

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == True).all()

    cancelled_orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isCancelled == True).all()

    cur_orders = orders + cancelled_orders

    items = {order.id: json.loads(order.items) for order in cur_orders}

    context = dict(open_orders=cur_orders,
                   items=items,
                   title=u"已完成订单",
                   referrer=request.headers.get('Referer'),
                   company_name=company_info.get('company_name'),
                   datetime_format=datetime_format,
                   formatter=formatter)

    return render_template("admin_view_paid_alacarte_orders.html", **context)


# View paid takeaway order
@app.route("/takeaway/order/<string:order_id>/view", methods=["GET", "POST"])
@login_required
def takeaway_order_view(order_id):

    order = Order.query.filter_by(id=int(order_id)).first()

    ordered_items = json.loads(order.items)

    for key, details in ordered_items.items():

        item = Food.query.filter_by(name=key).first()

        if item:

            details["image"] = item.image
            details["descr"] = item.description
            details["price"] = item.price_gross

    prices = {'tax': round((order.totalPrice / (1 + tax_rate_out))*tax_rate_out, 2),
              'subtotal': round(order.totalPrice / (1 + tax_rate_out), 2)}

    referrer = request.headers.get('Referer')

    context = dict(order=order,
                   ordered_items=ordered_items,
                   prices=prices,
                   referrer=referrer,
                   formatter=formatter,
                   title=u"查看外卖订单",
                   company_name=company_info.get('company_name'))

    return render_template('takeaway_view_order.html', **context)


@app.route('/takeaway/revenue/current')
@login_required
def takeaway_cur_revenue():

    orders = Order.query.filter_by(type="Out").all()

    # Filtering only orders today based on timezone Berlin and paid orders
    cur_paid_orders = [order for order in orders if
                       order.timeCreated.date() == today and order.isPaid]

    cur_revenue_sum = sum([order.totalPrice for order in cur_paid_orders])


    cur_revenue_card = sum([order.totalPrice for order in cur_paid_orders if
                            json.loads(order.pay_via).get('method') == "Card"])

    cur_revenue_cash = sum([order.totalPrice for order in cur_paid_orders if
                            json.loads(order.pay_via).get('method') == "Cash"])

    revenues = {"All": cur_revenue_sum,
                'Card': cur_revenue_card,
                'Cash': cur_revenue_cash}

    context = dict(revenues=revenues,
                   referrer=request.headers.get('Referer'),
                   company_name=company_info.get('company_name'),
                   title=u"当天营业额",
                   formatter=formatter)

    return render_template('current_out_revenue.html', **context)


# takeaway order status view
@app.route("/status")
def display_status():

    #Filtering only takeaway orders
    orders = Order.query.filter(
        Order.type == "Out",
        Order.isPaid == True).all()

    # Filtering only orders today based on timezone Berlin
    orders = [order for order in orders if
              order.timeCreated.date() == today]

    return render_template("takeaway_status.html",
                           title="Bestell Status",
                           orders=orders)


@app.route("/categories/view")
@login_required
def categories_view():

    with open(str(Path(app.root_path) / 'settings' / "categories.json"),
              'r',
              encoding="utf8") as file:

        data = file.read()

    categories = json.loads(data)

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"菜品种类管理",
                   company_name=company_info.get('company_name'),
                   categories=categories)

    return render_template('all_categories.html', **context)


@app.route("/categories/add", methods=['POST', "GET"])
@login_required
def add_category():

    with open(str(Path(app.root_path) / 'settings' / "categories.json")) as file:

        data = file.read()

    categories = json.loads(data)

    all_classes = list(set([i.get('Class') for i in categories]))

    all_categories = list(set([i.get('Subcategory') for i in categories]))

    from .forms import AddCategoryForm

    form = AddCategoryForm()

    form.name_class.choices.extend([(i, i) for i in all_classes])
    form.name_category.choices.extend([(i, i) for i in all_categories])

    if form.validate_on_submit() or request.method == "POST":

        categories.append({
                'Class': form.name_class.data,
                'Subcategory': form.new_category.data,
                'Unit': form.unit_en.data
        })

        with open(str(Path(app.root_path) / 'settings' / "categories.json"), 'w',
                  encoding="utf8") as file:

            json.dump(categories, file, indent=2)

        flash(f"新菜品分类{form.new_category.data}已经添加!", category='success')

        return redirect(url_for('categories_view'))

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"添加菜品种类",
                   company_name=company_info.get('company_name'),
                   form=form)

    return render_template('add_category.html', **context)


@app.route("/categories/edit/<string:subcategory>", methods=['POST', "GET"])
@login_required
def edit_category(subcategory):

    with open(str(Path(app.root_path) / 'settings' / "categories.json")) as file:

        data = file.read()

    categories = json.loads(data)

    category = [category for category in categories if
                category.get('Subcategory') == subcategory][0]

    all_classes = list(set([i.get('Class') for i in categories]))

    all_categories = list(set([i.get('Subcategory') for i in categories]))

    form = EditCategoryForm()

    form.name_class .choices.extend([(i, i) for i in all_classes])
    form.name_category.choices.extend([(i, i) for i in all_categories])

    if form.validate_on_submit() or request.method == "POST":

        categories.append({
            'Class': form.name_class.data,
            'Subcategory': form.cur_category.data,
            'Unit': form.unit_en.data
        })

        categories.remove(category)

        with open(str(Path(app.root_path) / 'settings' / "categories.json"), 'w') as file:

            json.dump(categories, file, indent=2)

        flash(f"菜品分类{form.cur_category.data}已经更新!", category='success')

        return redirect(url_for('categories_view'))

    form.name_class.data = category.get('Class', '')
    form.cur_category.data = category.get('Subcategory', '')
    form.unit_en.data = category.get('Unit', '')

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"修改菜品种类",
                   company_name=company_info.get('company_name'),
                   form=form)

    return render_template('edit_category.html', **context)


# Remove a dish
@app.route('/category/<string:subcategory>/remove', methods=["GET", "POST"])
@login_required
def remove_category(subcategory):

    with open(str(Path(app.root_path) / 'settings' / "categories.json")) as file:

        data = file.read()

    categories = json.loads(data)

    category = [category for category in categories if
                category.get('Subcategory') == subcategory][0]

    form = ConfirmForm()

    if form.validate_on_submit() or request.method == "POST":

        categories.remove(category)

        with open(str(Path(app.root_path) / 'settings' / "categories.json"),
                  mode='w',
                  encoding="utf8") as file:

            json.dump(categories, file, indent=2)

        flash(f"菜品分类{category.get('Subcategory', '')}已经被删除!", category='success')

        return redirect(url_for('categories_view'))

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"删除菜品种类",
                   company_name=company_info.get('company_name'),
                   form=form,
                   category=category)

    return render_template('remove_category.html', **context)


# All dish view route
@app.route('/alldishes')
@login_required
def all_dishes():

    dishes = Food.query.all()

    paid_orders = Order.query.filter(Order.isPaid == True).all()

    order_counts = {food.name:
                        {"counts": sum([json.loads(order.items).get(food.name).get('quantity')
                                    for order in paid_orders if food.name in json.loads(order.items).keys()]),
                         "Img": food.image,
                         "ID": food.id} for food in dishes}

    context = dict(dishes=dishes,
                   order_counts=order_counts,
                   title=u'菜品管理',
                   referrer=request.headers.get('Referer'),
                   company_name=company_info.get('company_name'))

    return render_template('all_dishes.html', **context)


# Add Dish
@app.route("/adddish", methods=["GET", "POST"])
@login_required
def add_dish():

    form = AddDishForm()

    with open(str(Path(app.root_path) / 'settings' / "categories.json")) as file:

        data = file.read()

    categories = json.loads(data)

    class_names = list(set([i.get("Class") for i in categories]))
    sub_categories = list(set([i.get("Subcategory") for i in categories]))

    # Extend new  labels and values to form class_name and category
    form.class_name.choices.extend([(i, i) for i in class_names])
    form.category.choices.extend([(i, i) for i in sub_categories])

    if request.method == "POST" or form.validate_on_submit():

        name = form.name.data
        class_name = form.class_name.data
        category = form.category.data
        description = form.description.data
        price = form.price.data
        eat_manner = form.eat_manner.data
        cn_desc = form.cn_name.data

        file = request.files["file"]
        image_path = None

        if file:

            # If file selected or existing and reset the image path again
            image_path = store_picture(file=file)

        dish = Food(name=name,
                    category=category,
                    description=description,
                    price_gross=price,
                    price_net_in=price / (1 + tax_rate_in),
                    price_net_out=price / (1 + tax_rate_out),
                    image=image_path,
                    eat_manner=eat_manner,
                    class_name=class_name,
                    inUse=True,
                    cn_description=cn_desc)

        db.session.add(dish)
        db.session.commit()

        flash(f"添加新菜品: {name}成功!")

        return redirect(url_for('all_dishes'))

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"添加菜品",
                   form=form,
                   company_name=company_info.get('company_name'))

    return render_template("add_dish.html", **context)


# Remove a dish
@app.route('/dish/<int:dish_id>/remove', methods=["GET", "POST"])
@login_required
def remove_dish(dish_id):

    form = ConfirmForm()
    food = Food.query.get_or_404(dish_id)

    if food:

        if form.validate_on_submit():

            db.session.delete(food)
            db.session.commit()
            flash(f"菜品{food.name}被删除!")

            return redirect(url_for("all_dishes"))

    context = dict(title=u"删除菜品",
                   referrer=request.headers.get('Referer'),
                   company_name=company_info.get('company_name'),
                   form=form,
                   dish=food)

    return render_template('remove_dish.html', **context)


# Edit Dish
@app.route('/dish/<int:dish_id>/edit', methods=["GET", "POST"])
@login_required
def edit_dish(dish_id):

    form = EditDishForm()

    # Loading Json Data from categories.json config file
    with open(str(Path(app.root_path) / 'settings' / "categories.json")) as file:

        data = file.read()

    categories = json.loads(data)

    class_names = list(set([i.get("Class") for i in categories]))
    sub_categories = list(set([i.get("Subcategory") for i in categories]))

    # Extend new  labels and values to form class_name and category
    form.class_name.choices.extend([(i, i) for i in class_names])
    form.category.choices.extend([(i, i) for i in sub_categories])

    dish = db.session.query(Food).get_or_404(int(dish_id))

    if request.method == "POST" or form.validate_on_submit():

        dish.name = form.name.data
        dish.category = form.category.data
        dish.class_name = form.class_name.data
        dish.cn_description = form.cn_name.data

        dish.price_gross = form.price.data
        dish.price_net_out = dish.price_gross / (1 + tax_rate_out)
        dish.price_net_in = dish.price_gross / (1 + tax_rate_in)

        dish.description = form.description.data

        dish.eat_manner = form.eat_manner.data

        file = request.files["file"]

        if file:

            # If dish image selected or existing and reset the dish image path again
            dish.image = store_picture(file=file)

        # Commit new changes
        db.session.commit()

        flash(f"菜品： {dish.name}修改成功!")

        return redirect(url_for("all_dishes"))

    form.name.data = dish.name
    form.category.data = dish.category
    form.class_name.data = dish.class_name
    form.eat_manner.data = dish.eat_manner
    form.price.data = dish.price_gross
    form.description.data = dish.description

    image_path = dish.image

    image = image_path.split("/")[-1]

    image_file = url_for('static', filename='img/' + image)

    context = dict(referrer=request.headers.get('Referer'),
                   form=form,
                   image=image_file,
                   title=u"修改菜品",
                   company_name=company_info.get('company_name'))

    return render_template("edit_dish.html", **context)


# Admin switch holiday on and off
@app.route('/dish/switch', methods=["POST"])
def switch_dish():

    # Handle Data From Ajax
    if request.method == "POST":

        data = request.json

        dish_id = data.get('dish_id')

        inUse = data.get('inUse')

        print(inUse)

        dish = db.session.query(Food).get_or_404(int(dish_id))

        dish.inUse = inUse

        db.session.commit()

        return jsonify({'status': 200})


@app.route('/holiday/manage')
@login_required
def holidays_manage():

    referrer = request.headers.get('Referer')

    holidays = Holiday.query.all()

    context = dict(referrer=referrer,
                   title=u"添加节假日",
                   company_name=company_info.get('company_name'),
                   holidays=holidays)

    return render_template("holiday_manage.html", **context)


@app.route('/holiday/add', methods=["GET", "POST"])
@login_required
def add_holiday():

    form = AddHolidayForm()

    referrer = request.headers.get('Referer')

    if form.validate_on_submit():

        name = form.name.data
        start = form.start_date.data
        end = form.end_date.data

        holiday = Holiday(name=name,
                          start=start,
                          end=end,
                          timeCreated=datetime.now(tz=pytz.timezone(timezone)),
                          inUse=True)

        db.session.add(holiday)
        db.session.commit()

        flash(f"已经成功添加节假日{holiday.name}", category='success')

        return redirect(url_for('holidays_manage'))

    context = dict(referrer=referrer,
                   title=u"添加节假日",
                   company_name=company_info.get('company_name'),
                   form=form)

    return render_template("add_holiday.html", **context)


@app.route('/holiday/edit/<int:holiday_id>', methods=["POST", "GET"])
@login_required
def edit_holiday(holiday_id):

    holiday = db.session.query(Holiday).get_or_404(int(holiday_id))

    form = EditHolidayForm()

    referrer = request.headers.get('Referer')

    context = dict(referrer=referrer,
                   title=u"添加节假日",
                   company_name=company_info.get('company_name'),
                   form=form)

    if holiday:

        if form.validate_on_submit():

            holiday.name = form.name.data
            holiday.start = form.start_date.data
            holiday.end = form.end_date.data

            db.session.commit()

            flash(f"已经成功更改节假日{holiday.name}!")

            return redirect(url_for('holidays_manage'))

    form.start_date.data = holiday.start
    form.end_date.data = holiday.end
    form.name.data = holiday.name

    return render_template("edit_holiday.html", **context)


@app.route('/holiday/remove/<int:holiday_id>', methods=["GET", "POST"])
@login_required
def remove_holiday(holiday_id):

    form = ConfirmForm()

    holiday = db.session.query(Holiday).get_or_404(int(holiday_id))

    if holiday:

        if form.validate_on_submit():

            db.session.delete(holiday)

            db.session.commit()

            flash(f"已经删除节假日{holiday.name}")

            return redirect(url_for('holidays_manage'))

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"删除节假日",
                   form=form,
                   holiday=holiday)

    return render_template("remove_holiday.html", **context)


# Admin switch holiday on and off
@app.route('/holiday/switch', methods=["POST"])
def switch_holiday():

    # Handle Data From Ajax
    if request.method == "POST":

        data = request.json

        holiday_id = data.get('holiday_id')

        inUse = data.get('inUse')

        print(inUse)

        holiday = db.session.query(Holiday).get_or_404(int(holiday_id))

        holiday.inUse = inUse

        db.session.commit()

        return jsonify({'status': 200})


@app.route('/qrcode/manage')
def qrcode_manage():

    tables = Table.query.all()

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"二维码管理",
                   tables=tables,
                   company_name=company_info.get('company_name'),
                   format=datetime_format)

    return render_template('qrcode.html', **context)


@app.route('/view/qrcodes/<int:table_id>')
def view_qrcodes(table_id):

    table = Table.query.get_or_404(int(table_id))

    tables = Table.query.all()

    table2qr = {table.name: json.loads(table.container).get('qrcodes')
                for table in tables}

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"查看所有二维码",
                   table2qr=table2qr,
                   company_name=company_info.get('company_name'),
                   table_name=table.name)

    return render_template('view_qrcodes.html', **context)


@app.route('/view/qrcode/<string:qrcode_name>')
def view_qrcode(qrcode_name):

    qrcode = f"{qrcode_name}.png"

    table_name = qrcode_name.split('_')[0]

    seat_number = qrcode_name.split('_')[1]

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"查看二维码",
                   qrcode=qrcode,
                   company_name=company_info.get('company_name'),
                   table_name=table_name,
                   seat_number=seat_number)

    return render_template('view_qrcode.html', **context)


@app.route('/qrcode/export/<string:table_name>', methods=["POST", "GET"])
def export_qrcode(table_name):

    file = None
    if table_name.lower().strip() == "all":

        file = qrcode2excel(tables=sorted([table.name for table in Table.query.all()]))

    else:

        file = qrcode2excel(tables=[table_name])

    import sys

    # if sys.platform == "win32":
    #
    #     import comtypes.client
    #
    #     xl = comtypes.client.CreateObject("excel.Application")
    #
    #     wb = xl.Workbooks.Open(file)
    #
    #     xl.Visible = True

    return send_file(file,
                     as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# Store Settings Route
@app.route("/settings", methods=["GET", "POST"])
@login_required
def set_store():

    form = StoreSettingForm()

    clocks = [(time(i, 0), f"0{i}:00") if i <= 9 else (time(i, 0), f"{i}:00") for i in range(24)]

    half_clocks = [(time(i, 30), f"0{i}:30") if i <= 9 else (time(i, 30), f"{i}:30") for i in range(24)]

    all_clocks = sorted(clocks + half_clocks)

    all_clocks.append((time(23, 59), "23:59"))

    form.business_hours_start_morning.choices.extend(all_clocks)

    form.business_hours_end_morning.choices.extend(all_clocks)

    form.business_hours_start_evening.choices.extend(all_clocks)
    form.business_hours_end_evening.choices.extend(all_clocks)

    if form.validate_on_submit() or request.method == "POST":

        print("Ok")

        # Save the logo file
        logo_file = form.logo.data

        if logo_file:

            logo_file.save(str(Path(app.root_path) / 'static' / 'img' / 'logo.png'))

        # Transmitting data in the form into the dictionary
        data = [{
          "STORE_NAME": form.store_name.data,
          "CITY": form.city.data,
          "STREET": form.street.data,
          "STREET NO.": form.street_no.data,
          "COUNTRY": form.country.data,
          "ZIP": form.zip.data,
          "TAX_ID": form.tax_id.data,
          "TAX_RATE": {"takeaway": form.tax_rate_takeaway.data,
                       "Inhouse Order": form.tax_rate_InHouse.data},
            "BUFFET_TIME_BUFFER": form.jp_buffet_time_buffer.data,
            "ORDER_TIMES": form.order_times.data,
            "ORDER_AMOUNT_PER_ROUND": form.order_amount_per_round.data,
            "BUSINESS_HOURS": {"MORNING": {"START": form.business_hours_start_morning.data,
                                           "END": form.business_hours_end_morning.data
                                           },

                               "EVENING": {"START": form.business_hours_start_evening.data,
                                           "END": form.business_hours_end_evening.data
                                           }},

            "ORDER_LIMIT": form.order_limit_per_round.data,
            "BUFFET_MODE": form.buffet_mode.data
        }]

        with open(str(Path(app.root_path) / 'settings' / 'config.json'), 'w') as f:

            json.dump(data, f, indent=2)

        flash(u"餐馆信息更新成功!")

        return redirect(url_for("set_store"))

    data = json_reader(file=str(Path(app.root_path) / 'settings' / 'config.json'))

    form.store_name.data = data.get("STORE_NAME")
    form.street_no.data = data.get("STREET NO.")
    form.street.data = data.get("STREET")
    form.zip.data = data.get("ZIP")
    form.country.data = data.get('COUNTRY')
    form.city.data = data.get('CITY')
    form.tax_id.data = data.get('TAX_ID')
    form.tax_rate_InHouse.data = data.get("TAX_RATE").get("Inhouse Order")
    form.tax_rate_takeaway.data = data.get("TAX_RATE").get("takeaway")
    form.jp_buffet_time_buffer.data = data.get('BUFFET_TIME_BUFFER')
    form.order_times.data = data.get('ORDER_TIMES')
    form.order_limit_per_round.data = data.get('ORDER_LIMIT','')
    form.buffet_mode.data = data.get('BUFFET_MODE')

    try:
        form.business_hours_start_morning.data = data.get('BUSINESS_HOURS').get('MORNING').get('START')
        form.business_hours_end_morning.data = data.get('BUSINESS_HOURS').get('MORNING').get('END')

        form.business_hours_start_evening.data = data.get('BUSINESS_HOURS').get('EVENING').get('START')
        form.business_hours_end_evening.data = data.get('BUSINESS_HOURS').get('EVENING').get('END')

    except AttributeError as e:

        print(str(e))

    logo = "logo.PNG"

    context = dict(referrer=request.headers.get('Referer'),
                   title=u'餐馆设置',
                   form=form,
                   company_name=company_info.get('company_name'),
                   logo=logo)

    return render_template("settings.html", **context)


@app.route('/admin/users/manage')
@login_required
def users_manage():

    referrer = request.headers.get('Referer')

    if current_user.permissions < 2:

        return render_template('auth_error.html', referrer=referrer)

    # Exclude the current logged in user - You can't delete your self
    users = User.query.filter(User.id != current_user.id,
                              User.permissions <= current_user.permissions).all()

    user2container = {user.id: ",".join(json.loads(user.container).get('section'))
                      for user in users if json.loads(user.container)}

    user_in_use = {user.id: json.loads(user.container).get('inUse') for user in users}

    context = dict(users=users,
                   user2container=user2container,
                   user_in_use=user_in_use,
                   referrer=request.headers.get('Referer'),
                   title=u'跑堂人员列表',
                   company_name=company_info.get('company_name'))

    return render_template('users_manage.html', **context)


@app.route('/admin/users/add', methods=["GET", "POST"])
@login_required
def add_user():

    referrer = request.headers.get('Referer')

    form = AddUserForm()

    import string
    letter_string = string.ascii_uppercase
    letters = [letter for letter in letter_string]

    holder = [("takeaway", u"外卖")]

    holder.extend([(i, i) for i in letters])

    # Instantiate some options for select fields
    form.section.choices.extend(holder)

    if request.method == "POST" or form.validate_on_submit():

        try:

            username = form.username.data
            alias = form.alias.data
            section = form.section.data
            password = form.password.data

            # By default permission for waiter/takeaway account is 1 and 0
            permissions = form.account_type.data

            user = User(username=username,
                        alias=alias,
                        container=json.dumps({"section": section, 'inUse': True}),
                        permissions=permissions,
                        email=f"{str(uuid4())}@cnfrien.com")
            # Email attr will be deprecated

            user.set_password(password=password)

            db.session.add(user)

            db.session.commit()

            flash(message=f"已经创建跑堂{user.username}", category="success")

            return redirect(url_for('users_manage'))

        except:

            flash(message=u"请不要重复添加账号", category="success")

            return redirect(url_for('users_manage'))

    context = dict(referrer=referrer,
                   company_name=company_info.get('company_name'),
                   form=form,
                   title=u"添加跑堂人员")

    return render_template('add_user.html', **context)


@app.route("/admin/user/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):

    referrer = request.headers.get('Referer')

    user = db.session.query(User).get_or_404(user_id)

    form = EditUserForm()

    import string
    letter_string = string.ascii_uppercase
    letters = [letter for letter in letter_string]

    holder = [("takeaway", u"外卖")]

    holder.extend([(i, i) for i in letters])

    # Instantiate some options for select fields
    form.section.choices.extend(holder)

    if request.method == "POST":

        user.username = form.username.data
        user.alias = form.alias.data

        container = json.loads(user.container)
        container['section'] = form.section.data

        user.container = json.dumps(container)

        db.session.commit()

        flash(message=f"已经更新跑堂{user.username}的资料", category="success")

        return redirect(url_for('users_manage'))

    form.username.data = user.username
    form.alias.data = user.alias
    form.section.data = json.loads(user.container).get('section')

    section = None
    if json.loads(user.container).get('section'):
        section = ", ".join(json.loads(user.container).get('section'))

    context = dict(title=u"修改跑堂资料",
                   form=form,
                   user=user,
                   referrer=referrer,
                   section=section,
                   company_name=company_info.get('company_name'))

    return render_template('edit_user.html', **context)


@app.route('/admin/user/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):

    referrer = request.headers.get('Referer')
    user = db.session.query(User).get_or_404(int(user_id))

    form = ConfirmForm()

    if form.validate_on_submit():

        db.session.delete(user)

        db.session.commit()

        flash(message=f"已经删除跑堂{user.alias}账号", category="danger")

        return redirect(url_for('users_manage'))

    return render_template('remove_user.html',
                           user=user,
                           referrer=referrer,
                           form=form)


@app.route('/admin/update/<int:user_id>/password', methods=["GET", "POST"])
@login_required
def update_password(user_id):

    user = db.session.query(User).get_or_404(int(user_id))

    referrer = request.headers.get('Referer')

    form = EditUserForm()

    if request.method == "POST" or form.validate_on_submit():

        user.set_password(password=form.password.data)

        db.session.commit()

        flash(f'已经为{user.alias}成功更新密码', category="success")

        return redirect(url_for('users_manage'))

    form.username.data = user.username

    form.alias.data = user.alias

    return render_template('update_password.html',
                           referrer=referrer,
                           form=form,
                           user=user)


# Table view function
@app.route("/adminpanel/tables/view")
@login_required
def view_tables():

    tables = Table.query.all()

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"桌子管理",
                   tables=tables,
                   company_name=company_info.get('company_name'),
                   format=datetime_format)

    return render_template("table_views.html", **context)


# Admin Dashboard view active tables
@app.route('/admin/active/tables', methods=["POST", "GET"])
def admin_active_tables():

    form = SearchTableForm()

    # Filtering alacarte unpaid orders
    orders = Order.query.filter(
        Order.type == "In",
        Order.isPaid == False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    open_orders = [order for order in orders if order.timeCreated.date()
                   == today and not order.isCancelled]

    # Currently Open Tables
    open_tables = list(set([order.table_name for order in open_orders]))

    # Extend the choices of current form
    form.select_table.choices.extend([(i, i) for i in open_tables])

    if form.validate_on_submit():

        selected_table = form.select_table.data
        open_tables = [table for table in open_tables if table == selected_table]

        return render_template('admin_active_tables.html',
                               form=form,
                               open_tables=open_tables)

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"已点餐桌子",
                   company_name=company_info.get('company_name'),
                   format=datetime_format,
                   form=form,
                   open_tables=open_tables)

    return render_template('admin_active_tables.html', **context)


@app.route('/admin/transfer/table/<string:table_name>', methods=["POST", "GET"])
@login_required
def admin_transfer_table(table_name):

    from .forms import TransferTableForm

    form = TransferTableForm()

    all_tables = Table.query.all()

    # Filtering alacarte unpaid orders
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    open_orders = [order for order in orders if
                   order.timeCreated.date() == today and not order.isCancelled]

    # Currently Open Tables
    open_tables = list(set([order.table_name for order in open_orders]))

    available_tables = [table for table in all_tables if table.name not in open_tables]

    form.target_table.choices.extend([(table.name, f"{table.name} - {table.number}人") \
                                      for table in available_tables])

    if form.validate_on_submit():

        cur_table_orders = [order for order in open_orders if
                            order.table_name == table_name]

        target_table = form.target_table.data

        for order in cur_table_orders:

            logging = {}
            logging['table_before'] = order.table_name
            logging['table_cur'] = target_table

            order.table_name = target_table

            db.session.commit()

            try:

                # Writing log to the csv file
                activity_logger(order_id=order.id,
                                operation_type=u'转台',
                                page_name='后台 > 桌子管理 > 已点餐桌子 > 转台',
                                descr=f'''\n
                                订单号:{order.id}\n
                                原桌子：{logging.get('table_before')}\n
                                新桌子:{logging.get('table_cur')}\n'
                                ''',
                                status=u'成功',
                                log_time=str(datetime.now(tz=pytz.timezone(timezone))))
            except:

                pass

            flash(f"桌子{table_name}已经转至{target_table}!", category='success')

            return redirect(url_for('admin_active_tables'))

    form.cur_table.data = f"{table_name} - {Table.query.filter_by(name=table_name).first_or_404().number}人"

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"转台",
                   company_name=company_info.get('company_name'),
                   format=datetime_format,
                   form=form)

    return render_template("admin_transfer_table.html", **context)


# Waiter views a table's aggregated order summary
@app.route("/admin/view/table/<string:table_name>", methods=["GET", "POST"])
def admin_view_table(table_name):

    # Check out form payment methods, discount and coupon code
    form = CheckoutForm()

    # Filtering InHouse unpaid orders and the targeted table and order not cancelled
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False,
        Order.table_name == table_name,
        Order.isCancelled == False).order_by(Order.timeCreated.desc()).all()

    if len(orders) > 0:

        order = orders[0]

        print(order)

        if order.timeCreated.date() == today:

            # Check if a checkout button is clicked
            if form.validate_on_submit() or request.method == "POST":

                # Set the settleID and settleTime
                settle_id = str(uuid4().int)
                settle_time = datetime.now(tz=pytz.timezone(timezone))

                logging = {}

                pay_via = {}

                # Pay via cash
                if form.cash_submit.data:

                    if form.coupon_amount.data and form.discount_rate.data:

                        flash(f"不能同时使用折扣和代金券结账")
                        return redirect(url_for('admin_view_table',
                                                table_name=table_name))

                    if form.coupon_amount.data:

                        order.discount = form.coupon_amount.data

                        order.endTotal = order.totalPrice - form.coupon_amount.data

                        pay_via['coupon_amount'] = form.coupon_amount.data

                    elif form.discount_rate.data:

                        order.discount_rate = form.discount_rate.data

                        order.endTotal = order.totalPrice * form.discount_rate.data
                        pay_via['discount_rate'] = form.discount_rate.data

                    pay_via["method"] = "Cash"
                    logging['Pay'] = u'现金'

                # Pay via card
                elif form.card_submit.data:

                    if form.coupon_amount.data and form.discount_rate.data:

                        flash(f"不能同时使用折扣和代金券结账")
                        return redirect(url_for('admin_view_table',
                                                table_name=table_name))

                    if form.coupon_amount.data:

                        order.discount = form.coupon_amount.data

                        order.endTotal = order.totalPrice - form.coupon_amount.data

                        pay_via['coupon_amount'] = form.coupon_amount.data

                    elif form.discount_rate.data:

                        order.discount_rate = form.discount_rate.data

                        order.endTotal = order.totalPrice * form.discount_rate.data

                        pay_via['discount_rate'] = form.discount_rate.data

                    pay_via['method'] = "Card"
                    logging['Pay'] = u'卡'

                order.settleTime = settle_time
                order.settleID = settle_id

                order.isPaid = True

                order.pay_via = json.dumps(pay_via)

                db.session.commit()

                try:

                    # Writing logs to the csv file
                    activity_logger(order_id=order.id,
                                    operation_type=u'结账',
                                    page_name=u'跑堂界面 > 桌子详情',
                                    descr=f'''结账订单号:{order.id}\n
                                            桌子编号：{order.table_name}-{order.seat_number}
                                            支付方式:{logging.get('Pay')}\n
                                            结账金额: {order.totalPrice}\n
                                            订单类型: AlaCarte\n''',
                                    log_time=str(datetime.now(tz=pytz.timezone(timezone))),
                                    status=u'成功')
                except:

                    pass

                dishes = json.loads(order.items)

                # Calculate the total for each dish in dishes
                for key, items in dishes.items():

                    items['total'] = items.get('quantity') * items.get('price')

                total_price = order.totalPrice

                context = {"details": dishes,
                           "company_name": company_info.get('company_name', ''),
                           "address": company_info.get('address'),
                           "now": format_datetime(datetime.now(), locale="de_DE"),
                           "tax_id": company_info.get('tax_id'),
                           "order_id": order.id,
                           "table_name": table_name,
                           "total": formatter(order.totalPrice),
                           "end_total": formatter(order.endTotal),
                           "pay_via": json.loads(order.pay_via).get('method', ""),
                           "VAT": formatter(
                               round((order.endTotal / tax_rate_in) * tax_rate_in, 2)),
                           'discount': formatter(0)}

                if form.coupon_amount.data:

                    context['discount'] = formatter(order.discount)

                if form.discount_rate.data:

                    context['discount'] = formatter(order.totalPrice \
                                                    * (1 - form.discount_rate.data))

                temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'receipt_temp_inhouse.docx')
                save_as = f"receipt_{order.id}"

                with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:

                    data = file.read()

                data = json.loads(data)

                printer = data.get('receipt').get('printer')

                def master_printer():

                    receipt_templating(context=context,
                                       temp_file=temp_file,
                                       save_as=save_as,
                                       printer=printer)

                th = Thread(target=master_printer)

                th.start()

                return redirect(url_for('admin_active_tables'))

            # Calculate the total price for this table
            total_price = order.totalPrice

            dishes = json.loads(order.items)

            subtype = order.subtype

            cuisines = {"mongo": u"蒙古餐",
                        "jpbuffet": u"日本餐"}

            batches = json.loads(order.dishes)

            number_of_kids = len(set([tuple(i.items())[0][1].get('order_by')
                            for i in batches if tuple(i.items())[0][1].get('is_kid') == 1]))

            number_of_adults = len(set([tuple(i.items())[0][1].get('order_by')
                            for i in batches if tuple(i.items())[0][1].get('is_kid') == 0]))

            section = Table.query.filter_by(name=table_name).first_or_404().section

            users = User.query.all()

            # Exclude the super user/ boss account
            section2user = {section: user for user in users if user.permissions != 100
                            and section in json.loads(user.container).get('section')}

            waiter_name = section2user.get(section).alias

            context = dict(title="桌子详情",
                           dishes=dishes,
                           table_name=table_name,
                           total_price=total_price,
                           form=form,
                           company_name=company_info.get('company_name'),
                           waiter_name=waiter_name,
                           referrer=request.headers.get('Referer'),
                           cuisines=cuisines,
                           subtype=subtype,
                           number_of_kids=number_of_kids,
                           number_of_adults=number_of_adults,
                           formatter=formatter)

            return render_template('admin_view_table_summary.html', **context)

        flash(f"{table_name}暂无订单！")
        return redirect(url_for('admin_active_tables'))

    flash(f"{table_name}暂无订单！")
    return redirect(url_for('admin_active_tables'))


# Guest switch table on and off
@app.route('/table/switch', methods=["POST"])
def switch_table():

    # Handle Data From Ajax
    if request.method == "POST":

        data = request.json

        table_name = data.get('tableName')

        status = data.get('isOn')

        print(status)

        table = db.session.query(Table).filter_by(name=table_name).first_or_404()

        table.is_on = status

        db.session.commit()

        return jsonify({'status': 200})


@app.route("/js/tables/add", methods=["POST"])
def js_add_table():

    data = request.json

    table_name = data.get('tableName')
    section = data.get("section")
    number = int(data.get('persons'))

    th = Thread(target=table_adder, args=(table_name, section,
                                          number, base_url, suffix_url, timezone,))

    # Checking Table duplicates
    # if Table.query.filter_by(name=table_name).first_or_404():
    #
    #     return jsonify({"error": f"{table_name}已经存在，请重新输入桌子名称"})

    th.start()

    return jsonify({"success": f"已经成功创建桌子：{table_name}"})


@app.route('/adminpanel/tables/add', methods=["GET", "POST"])
@login_required
def admin_add_table():

    referrer = request.headers.get('Referer')

    form = AddTableForm()

    import string

    letter_string = string.ascii_uppercase

    letters = [letter for letter in letter_string]

    form.section.choices.extend([(i, i) for i in letters])

    context = dict(referrer=referrer,
                   title=u"添加桌子",
                   company_name=company_info.get('company_name'),
                   format=datetime_format,
                   form=form)

    return render_template('add_table_via_js.html', **context)


# Table view function
@app.route("/table/<int:table_id>/edit", methods=["POST", "GET"])
@login_required
def edit_table(table_id):

    table = db.session.query(Table).get_or_404(table_id)

    form = EditTableForm()

    import string
    letter_string = string.ascii_uppercase
    letters = [letter for letter in letter_string]

    # Instantiate some options for select fields
    form.section.choices.extend([(i, i) for i in letters])

    if request.method == "POST":

        if table:

            table_name = form.name.data.upper()

            table.name = form.name.data.upper()
            table.number = form.persons.data
            table.section = form.section.data.upper()

            seats = "\n".join([f"{table_name}-{i+1}" for i in range(form.persons.data)])

            table.seats = seats

            qrcodes = [generate_qrcode(table=form.name.data.upper(),
                                       base_url=base_url,
                                       suffix_url=suffix_url,
                                       seat=str(i+1)) for i in range(form.persons.data)]

            container = {'isCalled': False,
                         'payCalled': False,
                         'qrcodes': qrcodes}

            table.container = json.dumps(container)

            db.session.commit()

            flash(f"桌子{table.name}更新成功")

            return redirect(url_for("view_tables"))

    form.name.data = table.name
    form.persons.data = table.number
    form.section.data = table.section

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"修改桌子",
                   company_name=company_info.get('company_name'),
                   format=datetime_format,
                   form=form,
                   seats=table.seats)

    return render_template("edit_table.html", **context)


# Remove table view function
@app.route("/tables/<string:table_name>/remove", methods=["POST", "GET"])
@login_required
def remove_table(table_name):

    form = ConfirmForm()

    table = db.session.query(Table).filter_by(name=table_name).first_or_404()

    if table:

        if form.validate_on_submit():

            db.session.delete(table)

            db.session.commit()

            flash(f"已经删除桌子{table.name}")

            return redirect(url_for('view_tables'))

        elif request.method == "GET":

            return render_template("remove_table.html",
                                   title="移除桌子",
                                   table=table,
                                   form=form)


# Buffet Price Setting View
@app.route("/buffet/price/settings", methods=["GET", "POST"])
@login_required
def buffet_price_settings():

    # Read the price setting data
    with open(str(Path(app.root_path) / "settings" / "buffet_price.json"), encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    context = dict(data=data,
                   title=u"自助餐价格设置",
                   company_name=company_info.get('company_name'),
                   formatter=formatter)

    return render_template("buffet_price_setting.html", **context)


@app.route('/buffet/price/settings/auth/<string:week_number>', methods=["POST", "GET"])
@login_required
def buffet_price_auth(week_number):

    form = AuthForm()

    user = current_user

    form.username.data = user.username

    if request.method == "POST" or form.validate_on_submit():

        if user is None or not user.check_password(password=form.password.data):

            flash(u"密码或者用户名无效!")
            return redirect(url_for('buffet_price_auth',
                                    week_number=week_number))

        return redirect(url_for("edit_buffet_price", week_number=week_number))

    context = dict(title="请输入账号密码修改自助餐",
                   user=current_user,
                   company_name=company_info.get('company_name'),
                   form=form,
                   week_number=week_number)

    return render_template("buffet_price_setting_auth.html", **context)


@app.route('/buffet/prices/edit/<string:week_number>', methods=["GET", "POST"])
@login_required
def edit_buffet_price(week_number):

    form = EditBuffetPriceForm()

    referrer = request.headers.get('Referer')

    # Read the price setting data
    with open(str(Path(app.root_path) / "settings" / "buffet_price.json"), encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    if form.validate_on_submit():

        data[week_number]['adult']['noon'] = form.price_for_adult_noon.data
        data[week_number]['adult']['after'] = form.price_for_adult_after.data

        data[week_number]['kid']['noon'] = form.price_for_kid_noon.data
        data[week_number]['kid']['after'] = form.price_for_kid_after.data

        data[week_number]['lastUpdate'] = datetime.now(tz=pytz.timezone(timezone)).strftime(datetime_format)

        data[week_number]['note'] = form.note.data

        with open(str(Path(app.root_path) / "settings" / "buffet_price.json"),
                  "w",
                  encoding="utf8") as file:

            json.dump(data, file, indent=2)

        flash(f"已经为{data.get(week_number).get('label')}的自助餐更新价格!", category='success')

        return redirect(url_for('buffet_price_settings'))

    form.week_number.data = data.get(week_number).get('label')

    form.price_for_adult_noon.data = data.get(week_number).get('adult').get('noon')
    form.price_for_adult_after.data = data.get(week_number).get('adult').get('after')

    form.price_for_kid_noon.data = data.get(week_number).get('kid').get('noon')
    form.price_for_kid_after.data = data.get(week_number).get('kid').get('after')

    context = dict(form=form,
                   title=u"修改自助餐价格",
                   company_name=company_info.get('company_name'),
                   referrer=referrer)

    return render_template("edit_buffet_price.html", **context)


# Table Order view by table name and seat number
@app.route("/alacarte/interface/<string:table_name>/<string:seat_number>")
def alacarte_navigate(table_name, seat_number):

    # Create a visit object from model and record it in db
    visit = Visit(count=1,
                  timeVisited=datetime.now(pytz.timezone('Europe/Berlin')))

    db.session.add(visit)
    db.session.commit()

    # Query Tables
    table = Table.query.filter_by(name=table_name).first_or_404()

    if not is_business_hours():

        context = dict(title="Gastnavigation",
                       table_name=table_name,
                       seat_number=seat_number,
                       is_business_hours=is_business_hours())

        return render_template("guest_index.html", **context)

    # if table existing and table is on
    if table and table.is_on:

        return render_template("alacarteindex.html",
                               table_name=table_name,
                               seat_number=seat_number,
                               title='alacarte')

    else:

        msg = "Diese Tisch steht noch nicht zu Verfuegung. Bitte melden Sie sich bei Gast Service"
        return render_template('table404.html', msg=msg)


# Guest Table Facing Order Interface by A LA CARTE
@app.route("/table/order/alacarte/<string:table_name>/<string:seat_number>")
def order_alacarte(table_name, seat_number):

    table = Table.query.filter_by(name=table_name).first_or_404()

    dishes = Food.query.filter(Food.inUse == True,
                               Food.eat_manner == "alacarte").all()

    for dish in dishes:

        # Rewrite dish's image name
        dish.image = dish.image.split("/")[-1]

    # Commit the changes from the ORM Operation
    db.session.commit()

    categories = list(set([dish.category for dish in dishes]))

    context = dict(referrer=request.headers.get('Referer'),
                   dishes=dishes,
                   categories=categories,
                   title=u"À la carte",
                   table_name=table_name,
                   seat_number=seat_number,
                   formatter=formatter)

    if table and table.is_on:

        return render_template('alacarte2.html', **context)

    else:

        msg = "Bestellung Service fuer diese Tisch steht noch nicht zu Verfuegung. Bitte melden Sie sich bei Gast Service"
        return render_template('table404.html', msg=msg)


@app.route("/alacarte/guest/checkout", methods=["GET", "POST"])
def alacarte_guest_checkout():

    if request.method == "POST":

        # Json Data Posted via AJAX
        json_data = request.json

        table_name = json_data.get('tableName').upper()
        seat_number = json_data.get('seatNumber')

        details = json_data.get('details')

        price_dict = {Food.query.get_or_404(int(i.get('itemId'))).name:
                          Food.query.get_or_404(int(i.get('itemId'))).price_gross
                      for i in details}

        details = {
            Food.query.get_or_404(int(i.get('itemId'))).name:
                {'quantity': int(i.get('itemQuantity')),
                 'price': float(price_dict.get(Food.query.get_or_404(int(i.get('itemId'))).name)),
                 'class_name': Food.query.get_or_404(int(i.get('itemId'))).class_name,
                 'order_by': seat_number}
            for i in details}

        total_price = sum([i[1].get('quantity') * i[1].get('price') for i in details.items()])

        # Check if this table is already associated with an open order
        orders = db.session.query(Order).filter(
            Order.type == "In",
            Order.isPaid == False,
            Order.isCancelled==False,
            Order.table_name == table_name).order_by(Order.timeCreated.desc()).all()

        if len(orders) > 0:

            order = orders[0]

            if order.timeCreated.date() != today:

                now = datetime.now(pytz.timezone(timezone))

                cur_max_id = max([order.id for order in Order.query.all()])

                # Create a new order for this table
                order = Order(
                    totalPrice=total_price,
                    endTotal=total_price,
                    orderNumber=str(uuid4().int),
                    items=json.dumps(details),
                    timeCreated=now,
                    type="In",
                    table_name=table_name,
                    seat_number=seat_number,
                    isCancelled=False,
                    dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                                  "order_id": cur_max_id + 1,
                                                                  "order_by":seat_number,
                                                                  "subtype":None}}]))

                db.session.add(order)
                db.session.commit()

            else:

                now = datetime.now(pytz.timezone(timezone))

                cur_items = json.loads(order.items)

                dishes = order.dishes

                if not dishes:

                    dishes = []

                else:

                    dishes = json.loads(order.dishes)

                dishes.append({datetime.timestamp(now): {"items": details,
                                                         "order_id": order.id,
                                                         "order_by": seat_number,
                                                         "subtype": None
                                                         }})

                order.dishes = json.dumps(dishes)

                cur_dishes = cur_items.keys()

                for dish, items in details.items():

                    if dish in cur_dishes:

                        cur_items[dish]['quantity'] = cur_items[dish]['quantity'] \
                                                      + items.get('quantity')

                    else:

                        cur_items[dish] = items

                order.items = json.dumps(cur_items)

                order.totalPrice = sum([i[1].get('quantity') * i[1].get('price')
                                        for i in cur_items.items()])

                db.session.commit()

                order.endTotal = order.totalPrice

                db.session.commit()

        else:

            now = datetime.now(pytz.timezone(timezone))

            cur_max_id = max([order.id for order in Order.query.all()])

            # Create a new order for this table
            order = Order(
                totalPrice=total_price,
                endTotal=total_price,
                orderNumber=str(uuid4().int),
                items=json.dumps(details),
                timeCreated=now,
                type="In",
                table_name=table_name,
                seat_number=seat_number,
                isCancelled=False,
                dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                              "order_id": cur_max_id + 1,
                                                              "order_by": seat_number,
                                                              "subtype": None
                                                              }}])
            )

            db.session.add(order)
            db.session.commit()

        details_kitchen = {key: {'quantity': items.get('quantity'),
                                 'total': items.get('quantity') * items.get('price')}
                           for key, items in details.items() if items.get("class_name") == "Food"}

        details_bar = {key: {'quantity': items.get('quantity'),
                             'total': items.get('quantity') * items.get('price')}
                       for key, items in details.items() if items.get("class_name") == "Drinks"}

        context_kitchen = {"details": details_kitchen,
                           "seat_number": seat_number,
                           "table_name": table_name,
                           "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        kitchen_temp = str(Path(app.root_path) / 'static' / 'docx' / 'kitchen_alacarte.docx')
        save_as_kitchen = f"alacarte_meallist_kitchen_{order.id}_{str(uuid4())}"

        context_bar = {"details": details_bar,
                       "seat_number": seat_number,
                       "table_name": table_name,
                       "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        bar_temp = str(Path(app.root_path) / 'static' / 'docx' / 'bar_alacarte.docx')
        save_as_bar = f"alacarte_meallist_bar_{order.id}_{str(uuid4())}"

        # Read the printer setting data from the json file
        with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
            data = file.read()

        data = json.loads(data)

        def master_printer():

            # Print to kitchen
            kitchen_templating(context=context_kitchen,
                               temp_file=kitchen_temp,
                               save_as=save_as_kitchen,
                               printer=data.get('kitchen').get('printer'))

            # Print to bar
            bar_templating(context=context_bar,
                           temp_file=bar_temp,
                           save_as=save_as_bar,
                           printer=data.get('bar').get('printer'))

        # Start the thread
        th = Thread(target=master_printer)
        th.start()

        return jsonify({"status_code": 200})


@app.route('/service/call', methods=['POST'])
def guest_call_service():

    data = request.json

    table_name = data.get('tableName')

    seat_number = data.get('seatNumber')

    is_paying = False

    table = db.session.query(Table).filter_by(name=table_name.upper()).first_or_404()

    container = json.loads(table.container)

    container['isCalled'] = True

    table.container = json.dumps(container)

    db.session.commit()

    from threading import Thread

    th = Thread(target=call2print, args=(table_name, seat_number, is_paying, ))
    th.start()

    return jsonify({"success": "In Ordnung, ein Mitarbeiter kommt bald"})


@app.route('/pay/call', methods=['POST'])
def guest_call_pay():

    data = request.json

    table_name = data.get('tableName')

    seat_number = data.get('seatNumber')

    is_paying = True

    table = db.session.query(Table).filter_by(name=table_name.upper()).first_or_404()

    container = json.loads(table.container)

    container['payCalled'] = True

    table.container = json.dumps(container)

    db.session.commit()

    from threading import Thread

    th = Thread(target=call2print, args=(table_name, seat_number, is_paying,))

    th.start()

    return jsonify({"success": "In Ordnung, ein Mitarbeiter kommt bald mit der Kasse"})


# Waiter Admin Section
# Waiter view alacarte function view
@app.route('/waiter/admin', methods=["GET", "POST"])
@login_required
def waiter_admin():

    # if Account suspended
    if not json.loads(current_user.container).get('inUse'):

        return render_template('suspension_error.html')

    tables = db.session.query(Table).all()

    for table in tables:
        container = json.loads(table.container)
        container['isCalled'] = False
        container['payCalled'] = False

        table.container = json.dumps(container)

        db.session.commit()

    form = TableSectionQueryForm()

    import string
    letter_string = string.ascii_uppercase
    letters = [letter for letter in letter_string]

    # Instantiate some options for select fields
    form.start_section.choices.extend([(i, i) for i in letters])
    form.end_section.choices.extend([(i, i) for i in letters])

    # Filtering alacarte unpaid orders
    orders = Order.query.filter(
        Order.type == "In",
        Order.isPaid == False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin)
    orders = [order for order in orders if
              order.timeCreated.date() == today and
                   not order.isCancelled]
    # Order is not cancelled added

    from collections import OrderedDict
    sections = {letter: letter + u"区" for letter in letters}

    # Currently Open Tables
    open_tables = list(set([order.table_name for order in orders]))

    sections_2_tables = {section: [table
                        for table in Table.query.filter_by(section=section).all()
                        if table.name in open_tables]
                        for section in sections.keys()
                         }

    ordered_sections = OrderedDict(sorted(sections_2_tables.items(), key=lambda t: t[0]))

    section_keys = list(ordered_sections.keys())

    keys2index = {key: section_keys.index(key) for key in section_keys}

    # If form submitted
    if form.validate_on_submit():

        with open(str(Path(app.root_path) / 'settings' / 'table_section.json')) as file:
            data = file.read()

        data = json.loads(data)

        data['START'] = form.start_section.data.upper()
        data['END'] = form.end_section.data.upper()

        # Update Json Data
        with open(str(Path(app.root_path) / 'settings' / 'table_section.json'), 'w') as file:
            json.dump(data, file, indent=2)

        start_index = keys2index.get(form.start_section.data.upper())
        end_index = keys2index.get(form.end_section.data.upper())

        selected_sections = section_keys[start_index: end_index+1]

        return render_template('alacarte_tables_view.html',
                               ordered_sections=ordered_sections,
                               form=form,
                               selected_sections=selected_sections)

    # Read the table config json data
    with open(str(Path(app.root_path) / 'settings' / 'table_section.json')) as file:
        data = file.read()

    data = json.loads(data)

    form.start_section.data = data.get('START')
    form.end_section.data = data.get('END')

    start_index = keys2index.get(form.start_section.data.upper())
    end_index = keys2index.get(form.end_section.data.upper())

    selected_sections = section_keys[start_index: end_index + 1]

    return render_template('alacarte_tables_view.html',
                           ordered_sections=ordered_sections,
                           form=form,
                           selected_sections=selected_sections,
                           company_name=company_info.get('company_name'),
                           title="订单查看")


# Waiter views a table's aggregated order summary
@app.route("/waiter/admin/view/table/<string:table_name>", methods=["GET", "POST"])
def view_table(table_name):

    # Check out form payment methods, discount and coupon code
    form = CheckoutForm()

    # Filtering ala carte unpaid orders and the targeted table and order not cancelled
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False,
        Order.table_name == table_name,
        Order.isCancelled == False).order_by(Order.timeCreated.desc()).all()

    if len(orders) > 0:

        order = orders[0]

        if order.timeCreated.date() == today:

            # Calculate the total price for this table
            total_price = order.totalPrice

            dishes = json.loads(order.items)

            # Add cond if order not cancelled
            # Check if a checkout button is clicked
            if request.method == "POST" or form.validate_on_submit():

                # Set settleId and SettleTime
                settle_id = str(uuid4().int)
                settle_time = datetime.now(tz=pytz.timezone(timezone))

                logging = {}

                pay_via = {}

                # Pay via cash
                if form.cash_submit.data:

                    if form.coupon_amount.data and form.discount_rate.data:

                        flash(f"不能同时使用折扣和代金券结账")
                        return redirect(url_for('admin_view_table',
                                                table_name=table_name))

                    if form.coupon_amount.data:

                        order.discount = form.coupon_amount.data

                        order.endTotal = order.totalPrice - form.coupon_amount.data

                        pay_via['coupon_amount'] = form.coupon_amount.data

                    elif form.discount_rate.data:

                        order.discount_rate = form.discount_rate.data
                        order.endTotal = order.totalPrice * form.discount_rate.data
                        pay_via['discount_rate'] = form.discount_rate.data

                    pay_via["method"] = "Cash"
                    logging['Pay'] = u'现金'

                # Pay via card
                elif form.card_submit.data:

                    if form.coupon_amount.data and form.discount_rate.data:

                        flash(f"不能同时使用折扣和代金券结账")
                        return redirect(url_for('admin_view_table',
                                                table_name=table_name))

                    if form.coupon_amount.data:

                        order.discount = form.coupon_amount.data

                        order.endTotal = order.totalPrice - form.coupon_amount.data

                        pay_via['coupon_amount'] = form.coupon_amount.data

                    elif form.discount_rate.data:

                        order.discount_rate = form.discount_rate.data

                        order.endTotal = order.totalPrice * form.discount_rate.data

                        pay_via['discount_rate'] = form.discount_rate.data

                    pay_via['method'] = "Card"
                    logging['Pay'] = u'卡'

                order.isPaid = True

                order.settleID = settle_id
                order.settleTime = settle_time

                order.pay_via = json.dumps(pay_via)

                db.session.commit()
                try:
                    # Writing logs to the csv file
                    activity_logger(order_id=order.id,
                                    operation_type=u'结账',
                                    page_name=u'跑堂界面 > 桌子详情',
                                    descr=f'''结账订单号:{order.id}\n
                                            桌子编号：{order.table_name}-{order.seat_number}
                                            支付方式:{logging.get('Pay')}\n
                                            结账金额: {order.totalPrice}\n
                                            订单类型:AlaCarte\n''',
                                    log_time=str(datetime.now(pytz.timezone('Europe/Berlin'))),
                                    status=u'成功')
                except:

                    pass

                # Calculate the totalf for each dish in dishes
                for key, items in dishes.items():

                    items['total'] = items.get('quantity') * items.get('quantity')

                context = {"details": dishes,
                           "company_name": company_info.get('company_name', ''),
                           "address": company_info.get('address'),
                           "now": format_datetime(datetime.now(), locale="de_DE"),
                           "tax_id": company_info.get('tax_id'),
                           "order_id": order.id,
                           "table_name": table_name,
                           "total": formatter(order.totalPrice),
                           "pay_via": json.loads(order.pay_via).get('method', ""),
                           "VAT": formatter(
                               round((order.endTotal / tax_rate_in) * tax_rate_in, 2)),
                           "end_total": formatter(order.endTotal),
                           'discount': formatter(0)}

                if form.coupon_amount.data:

                    context['discount'] = formatter(order.discount)

                if form.discount_rate.data:

                    context['discount'] = formatter((1 - order.discount_rate) * order.totalPrice)

                temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'receipt_temp_inhouse.docx')
                save_as = f"receipt_{order.id}"

                with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:

                    data = file.read()

                data = json.loads(data)

                printer = data.get('receipt').get('printer')

                def master_printer():

                    receipt_templating(context=context,
                                       temp_file=temp_file,
                                       save_as=save_as,
                                       printer=printer)

                th = Thread(target=master_printer)

                th.start()

                return redirect(url_for('waiter_admin'))

            section = Table.query.filter_by(name=table_name).first_or_404().section

            users = User.query.all()

            subtype = order.subtype

            cuisines = {"mongo": u"蒙古餐",
                        "jpbuffet": u"日本餐"}

            batches = json.loads(order.dishes)

            number_of_kids = len(set([tuple(i.items())[0][1].get('order_by')
                              for i in batches if tuple(i.items())[0][1].get('is_kid') == 1]))

            number_of_adults = len(set([tuple(i.items())[0][1].get('order_by')
                                for i in batches if tuple(i.items())[0][1].get('is_kid') == 0]))

            # Exclude the super user/ boss account
            section2user = {section: user for user in users if user.permissions != 100
                            and section in json.loads(user.container).get('section')}

            waiter_name = None

            if section2user == None:

                waiter_name = "Unbekannt"

            else:

                try:
                    waiter_name = section2user.get(section).alias

                except:
                    waiter_name = "Unbekannt"

            context = dict(title="桌子详情",
                           dishes=dishes,
                           table_name=table_name,
                           total_price=total_price,
                           form=form,
                           company_name=company_info.get('company_name'),
                           waiter_name=waiter_name,
                           referrer=request.headers.get('Referer'),
                           subtype=subtype,
                           cuisines=cuisines,
                           number_of_adults=number_of_adults,
                           number_of_kids=number_of_kids,
                           formatter=formatter)

            # Else just render page as get method
            return render_template('view_table_summary.html', **context)

        flash(f"桌子{table_name}暂无最新订单！", category="error")
        return redirect(url_for('waiter_admin'))

    flash(f"桌子{table_name}暂无任何订单！", category="error")
    return redirect(url_for('waiter_admin'))


@app.route("/alacarte/orders/manage")
def alacarte_orders_manage():

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).filter(
        Order.type == "In").all()

    cur_orders = [order for order in orders if order.timeCreated.date()
                  == today]


    items = {order.id: json.loads(order.items) for order in cur_orders}

    context = dict(title="订单管理",
                   open_orders=cur_orders,
                   items=items,
                   company_name=company_info.get('company_name'),
                   referrer=request.headers.get('Referer'),
                   datetime_format=datetime_format,
                   formatter=formatter)

    return render_template("alacarte_orders_admin.html", **context)


@app.route("/alacarte/order/<int:order_id>/edit")
@login_required
def alacarte_order_edit(order_id):

    order = Order.query.get_or_404(int(order_id))

    title = None

    if order.isPaid or order.isCancelled:

        title = "订单查看"

    else:

        title = "订单修改"

    ordered_items = json.loads(order.items)

    context = dict(title=title,
                   order=order,
                   ordered_items=ordered_items,
                   company_name=company_info.get('company_name'),
                   referrer=request.headers.get('Referer'),
                   datetime_format=datetime_format,
                   formatter=formatter
                   )

    return render_template('alacarte_order_edit.html', **context)


@app.route('/alacarte/orders/update', methods=["GET", "POST"])
@login_required
def update_alacarte_order():

    logging = {}

    if request.method =="POST":

        data = request.get_json('orderId')

        print(data)

        order_id = data.get('orderId')

        order = db.session.query(Order).get_or_404(int(order_id))


        logging['before'] = "\n".join([f"{key}x{items.get('quantity')}" \
                                       for (key, items) in json.loads(order.items).items()])

        details = data.get('details')

        logging['after'] = "\n".join([f"{i.get('item')}x{i.get('quantity')}" \
                                      for i in details])

        price_dict = {
            i.get('item'):
                Food.query.filter_by(name=i.get('item')).first_or_404().price_gross
                      for i in details}

        details = {
            detail.get('item'):
                {'quantity': int(detail.get('quantity')),
                 'price': float(price_dict.get(detail.get('item')))}
            for detail in details}

        prices = [i[1].get('quantity') * i[1].get('price') for i in details.items()]

        order.totalPrice = sum(prices)
        order.items = json.dumps(details)

        db.session.commit()

        try:

            # Writing logs to the csv file
            activity_logger(order_id=order.id,
                            operation_type=u'订单修改',
                            page_name=u'跑堂界面 > 订单管理 >订单修改',
                            descr=f'''
                            修改订单号:{order.id}\n
                            桌子编号：{json.loads(order.container).get('table_name')}-{json.loads(order.container).get('seat_number')}\n
                            修改前明细:{logging.get('before')}\n
                            修改后明细:{logging.get('after')}\n
                            修改前账单金额: {logging.get('price_before')}\n
                            修改后账单金额: {logging.get('price_after')}\n
                            订单类型:AlaCarte\n
                            {logging.get('remark')}\n''',
                            log_time=str(datetime.now(pytz.timezone('Europe/Berlin'))),
                            status=u'成功')
        except:

            pass

        return redirect(url_for('alacarte_orders_manage'))


@app.route('/alacarte/order/<int:order_id>/cancel', methods=["GET", "POST"])
@login_required
def cancel_alacarte_order(order_id):

    form = ConfirmForm()

    logging = {}

    order = db.session.query(Order).get_or_404(int(order_id))

    if form.validate_on_submit():

        if order:

            container = json.loads(order.container)

            container['isCancelled'] = True

            order.container = json.dumps(container)

            db.session.commit()

            try:

                # Writing logs to the csv file
                activity_logger(order_id=order.id,
                                operation_type=u'订单取消',
                                page_name=u'跑堂界面 > 订单管理 > 取消',
                                descr=f'''
                                取消订单号:{order.id}\n
                                桌子编号：{json.loads(order.container).get('table_name')}-{json.loads(order.container).get('seat_number')}\n
                                账单金额: {order.totalPrice}\n
                                订单类型:AlaCarte\n
                                {logging.get('remark')}\n''',
                                log_time=str(datetime.now(tz=pytz.timezone('Europe/Berlin'))),
                                status=u'成功')
            except:

                pass

            return redirect(url_for('alacarte_orders_admin'))

    return render_template('cancel_alacarte_order.html',
                           form=form,
                           order=order)


@app.route('/alacarte/revenue/breakdown')
@login_required
def render_revenue_by_waiter():

    # Filtering alacarte unpaid orders
    orders = Order.query.filter(
        Order.type == "In",
        Order.isPaid == True).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) Order is not cancelled added
    cur_orders = [order for order in orders if order.timeCreated.date() == today
                  and not order.isCancelled]

    # Currently Open Tables
    open_tables = list(set([order.table_name for order in cur_orders]))

    open_sections = list(set([Table.query.filter_by(name=table).first_or_404().section
                     for table in open_tables]))

    users = User.query.all()

    # Exclude the super user/ boss account
    sections2users = {section: user for user in users if user.permissions != 100
                      for section in open_sections if
                      section in json.loads(user.container).get('section')}

    open_sections.sort()

    context = dict(title="当天营业额",
                   open_sections=open_sections,
                   company_name=company_info.get('company_name'),
                   referrer=request.headers.get('Referer'),
                   sections2users=sections2users)

    return render_template('alacarte_revenue_by_waiter.html', **context)


@app.route("/revenue/view/auth/<string:user_name>/<string:section>",
           methods=["POST", "GET"])
@login_required
def revenue_view_auth(user_name, section):

    form = AuthForm()

    user = User.query.filter_by(username=user_name).first_or_404()

    form.username = user.username

    if request.method == "POST" or form.validate_on_submit():

        if user is None or not user.check_password(password=form.password.data):

            flash(u"密码或者用户名无效!")
            return redirect(url_for('revenue_view_auth',
                                    user_name=user_name,
                                    section=section))

        return redirect(url_for("revenue_by_section", section=section))

    context = dict(title="请输入账号密码查看营业额",
                   user=user,
                   company_name=company_info.get('company_name'),
                   referrer=request.headers.get('Referer'),
                   form=form
                   )

    return render_template("revenue_view_auth.html", **context)


@app.route('/revenue/alacarte/<string:section>')
@login_required
def revenue_by_section(section):

    paid_orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid==True).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    cur_paid_orders = [order for order in paid_orders if order.timeCreated.date()
                       == today and not order.isCancelled]

    cur_paid_section_orders = [order for order in cur_paid_orders
                               if Table.query.filter_by(name=order.table_name)\
                                   .first_or_404().section == section]

    revenue = {}
    revenue['total'] = sum([order.totalPrice for order in cur_paid_section_orders])

    revenue['by_card'] = sum([order.totalPrice for order in cur_paid_section_orders if
                                    json.loads(order.pay_via).get('method')=="Card"])

    revenue['by_cash'] = sum([order.totalPrice for order in cur_paid_section_orders if
                                json.loads(order.pay_via).get('method') == "Cash"])

    context = dict(title=f"今日营收统计 - 分区{section}",
                   company_name=company_info.get('company_name'),
                   referrer=request.headers.get('Referer'),
                   section=section,
                   revenue=revenue,
                   formatter=formatter)

    return render_template('revenue_by_section.html', **context)


@app.route("/tables/alacarte/active", methods=["POST", "GET"])
@login_required
def active_alacarte_tables():

    form = SearchTableForm()

    # Filtering alacarte unpaid orders
    orders = Order.query.filter(
        Order.type == "In",
        Order.isPaid == False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    open_orders = [order for order in orders if order.timeCreated.date() == today
                   and not order.isCancelled]

    # Currently Open Tables
    open_tables = list(set([order.table_name for order in open_orders]))

    # Extend the choices of current form
    form.select_table.choices.extend([(i, i) for i in open_tables])

    context = dict(title="已点餐桌子",
                   open_tables=open_tables,
                   company_name=company_info.get('company_name'),
                   referrer=request.headers.get('Referer'),
                   form=form)

    if form.validate_on_submit():

        selected_table = form.select_table.data
        open_tables = [table for table in open_tables if table == selected_table]

        context['open_tables'] = open_tables

        return render_template('active_alacarte_tables.html', **context)

    return render_template('active_alacarte_tables.html', **context)


@app.route('/transfer/table/<string:table_name>', methods=["POST", "GET"])
@login_required
def transfer_table(table_name):

    from .forms import TransferTableForm

    form = TransferTableForm()

    all_tables = Table.query.all()

    # Filtering alacarte unpaid orders
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    open_orders = [order for order in orders if order.timeCreated.date()
                   == today
                   and not order.isCancelled]

    # Currently Open Tables
    open_tables = list(set([order.table_name for order in open_orders]))

    available_tables = [table for table in all_tables if table.name not in open_tables]


    form.target_table.choices.extend([(table.name, f"{table.name} - {table.number}人") \
                                      for table in available_tables])

    if form.validate_on_submit():

        cur_table_orders = [order for order in open_orders \
                            if order.table_name==table_name]

        target_table = form.target_table.data

        for order in cur_table_orders:

            logging = {}
            logging['table_before'] = order.table_name
            logging['table_cur'] = target_table

            order.table_name = target_table

            db.session.commit()
            try:

                # Writing log to the csv file
                activity_logger(order_id=order.id,
                                operation_type=u'转台',
                                page_name='跑堂界面 > 已点餐桌子 > 转台',
                                descr=f'''\n
                                订单号:{order.id}\n
                                原桌子：{logging.get('table_before')}\n
                                新桌子:{logging.get('table_cur')}\n'
                                ''',
                                status=u'成功',
                                log_time=str(datetime.now(tz=pytz.timezone('Europe/Berlin'))))
            except:

                pass

            flash(f"桌子{table_name}已经转至{target_table}!", category='success')

            return redirect(url_for('active_alacarte_tables'))

    form.cur_table.data = f"{table_name} - {Table.query.filter_by(name=table_name).first_or_404().number}人"

    return render_template("transfer_table.html", form=form)


@app.route('/tables/status', methods=["GET", "POST"])
def return_table_status():

    # Filtering alacarte unpaid orders
    orders = Order.query.filter(
        Order.type == "In",
        Order.isPaid == False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin)
    open_orders = [order for order in orders if order.timeCreated.date() == today
                   and not order.isCancelled]

    # Currently Open Tables
    open_tables = list(set([order.table_name for order in open_orders]))

    tables = [Table.query.filter_by(name=table).first_or_404() for table in open_tables]

    status = [table.name for table in tables if json.loads(table.container).get('isCalled')]

    return jsonify(status)


# Return json data containing tables requesting to pay
@app.route('/tables/pay/requested', methods=["GET", "POST"])
def tables_pay_called():

    # Filtering alacarte unpaid orders
    orders = Order.query.filter(
        Order.type == "In",
        Order.isPaid == False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin)
    open_orders = [order for order in orders if order.timeCreated.date()
              == today and not order.isCancelled]

    # Currently Open Tables
    open_tables = list(set([order.table_name for order in open_orders]))

    tables = [Table.query.filter_by(name=table).first_or_404() for table in open_tables]

    status = [table.name for table in tables if json.loads(table.container).get('payCalled')]

    return jsonify(status)


@app.route('/view/logs')
@login_required
def view_logs():

    logs = Log.query.all()

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"后台操作记录",
                   company_name=company_info.get('company_name'),
                   logs=logs)

    # Exclude the header line from the csv file
    return render_template('view_logs.html', **context)


@app.route('/view/log/<int:log_id>')
@login_required
def view_log(log_id):

    log = Log.query.get_or_404(int(log_id))

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"查看操作记录",
                   company_name=company_info.get('company_name'),
                   log=log)

    return render_template('view_log.html', **context)


@app.route("/export/log")
@login_required
def export_log():

    file = str(Path(app.root_path) / 'cache' / 'logging.csv')

    import sys

    # if sys.platform == "win32":
    #
    #     import comtypes.client
    #
    #     xl = comtypes.client.CreateObject("excel.Application")
    #
    #     wb = xl.Workbooks.Open(file)
    #
    #     xl.Visible = True

    return send_file(file, as_attachment=True, mimetype="text/csv")


@app.route("/z/receipts/manage")
@login_required
def z_receipts_manage():

    with open(str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'),
              mode="rb") as pickle_out:
        data = pickle.load(pickle_out)

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"Z单(每日一次)",
                   company_name=company_info.get('company_name'),
                   data=data,
                   timestamp=datetime.timestamp(datetime.now()),
                   list=list,
                   datetime_format=datetime_format,
                   datetime=datetime)

    # return jsonify(data)
    return render_template("view_void_z_receipts.html", **context) \
        if len(data) == 0 else render_template("view_z_receipts.html", **context)


@app.route('/view/z/receipt/<string:timestamp>')
@login_required
def view_z_receipt(timestamp):

    paid_orders = Order.query.filter(Order.isPaid == True).order_by(Order.settleTime.desc()).all()

    unpaid_orders = Order.query.filter(Order.isPaid == False).order_by(Order.settleTime.desc()).all()

    with open(str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'),
              mode="rb") as pickle_out:
        data = pickle.load(pickle_out)

    first_order_time = unpaid_orders[-1].timeCreated

    first_pay_time = paid_orders[-1].settleTime

    from_time = None

    if len(data) == 0:

        from_time = min([first_order_time, first_pay_time])

    else:

        from_time = list(data[-1].items())[0][1].get('lastPrinted')

    now = datetime.fromtimestamp(float(timestamp))

    ranged_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                   from_time <= order.settleTime <= now]

    ranged_paid_out_orders = [order for order in paid_orders if order.type == "Out" and
                                   from_time <= order.settleTime <= now]

    gross_revenue1 = round(sum([order.totalPrice for order in ranged_paid_alacarte_orders]), 2)

    net_revenue1 = round(gross_revenue1 / (1 + tax_rate_in), 2)

    vat1 = gross_revenue1 - net_revenue1

    gross_revenue2 = sum([order.totalPrice for order in ranged_paid_out_orders])

    net_revenue2 = round(gross_revenue2 / (1 + tax_rate_out), 2)

    vat2 = gross_revenue2 - net_revenue2

    taxable_gross = gross_revenue1 + gross_revenue2

    taxable_net = net_revenue1 + net_revenue2

    total_vat = vat1 + vat2

    total_taxable_gross = gross_revenue2 + gross_revenue1

    filtered_paid_orders = ranged_paid_alacarte_orders + ranged_paid_out_orders

    percentage_discounts = sum([order.discount_rate * order.totalPrice for order
                                in filtered_paid_orders if order.discount_rate])

    total_discounts = sum([order.discount for order
                                in filtered_paid_orders if order.discount])

    cur_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                order.settleTime.date() == today]

    revenue_from_cur_paid_tables = sum([order.totalPrice for
                                        order in cur_paid_alacarte_orders])

    cur_unpaid_alacarte_orders = [order for order in unpaid_orders if
                                  order.type == "In" and
                                  order.timeCreated.date() == today]

    revenue_from_cur_unpaid_tables = sum([order.totalPrice for
                                            order in cur_unpaid_alacarte_orders])

    cur_paid_orders = [order for order in paid_orders
                       if order.settleTime.date() == today]

    cur_de_facto_revenue = sum([order.totalPrice for order in cur_paid_orders])

    dummy_cur_revenue = cur_de_facto_revenue + revenue_from_cur_unpaid_tables

    ranged_paid_orders_cash = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Cash"
                               and from_time <= order.settleTime <= now]

    ranged_paid_orders_card = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Card"
                               and from_time <= order.settleTime <= now]

    gross_cash_revenue = sum([order.totalPrice for order in ranged_paid_orders_cash])

    gross_card_revenue = sum([order.totalPrice for order in ranged_paid_orders_card])

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"打印Z单",
                   company_name=company_info.get('company_name'),
                   z_number=len(data)+1,
                   now=format_datetime(now, locale="de_DE"),
                   now_timestamp=datetime.timestamp(now),
                   gross_revenue1=formatter(gross_revenue1),
                   net_revenue1=net_revenue1,
                   vat1=formatter(vat1),
                   gross_revenue2=formatter(gross_revenue2),
                   net_revenue2=formatter(net_revenue2),
                   vat2=formatter(vat2),
                   taxable_gross=formatter(taxable_gross),
                   taxable_net=formatter(taxable_net),
                   total_vat=formatter(total_vat),
                   total_taxable_gross=formatter(total_taxable_gross),
                   percentage_discounts=formatter(percentage_discounts),
                   total_discounts=formatter(total_discounts),
                   gross_cash_revenue=formatter(gross_cash_revenue),
                   gross_card_revenue=formatter(gross_card_revenue),
                   dummy_cur_revenue=formatter(dummy_cur_revenue),
                   revenue_from_cur_paid_tables=formatter(revenue_from_cur_paid_tables),
                   revenue_from_cur_unpaid_tables=formatter(revenue_from_cur_unpaid_tables),
                   formatter=formatter)

    return render_template("view_z_receipt.html", **context)


@app.route('/view/printed/z/receipt/<string:from_timestamp>/<string:til_timestamp>/<string:z_number>')
@login_required
def view_printed_z_receipt(from_timestamp,
                           til_timestamp,
                           z_number):

    paid_orders = Order.query.filter(Order.isPaid == True).order_by(Order.settleTime.desc()).all()

    unpaid_orders = Order.query.filter(Order.isPaid == False).order_by(Order.settleTime.desc()).all()

    with open(str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'),
              mode="rb") as pickle_out:
        data = pickle.load(pickle_out)

    from_time = datetime.fromtimestamp(float(from_timestamp))

    til = datetime.fromtimestamp(float(til_timestamp))

    ranged_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                   from_time <= order.settleTime <= til]

    ranged_paid_out_orders = [order for order in paid_orders if order.type == "Out" and
                                   from_time <= order.settleTime <= til]

    gross_revenue1 = sum([order.totalPrice for order in ranged_paid_alacarte_orders])

    net_revenue1 = round(gross_revenue1 / (1 + tax_rate_in), 2)

    vat1 = gross_revenue1 - net_revenue1

    gross_revenue2 = sum([order.totalPrice for order in ranged_paid_out_orders])

    net_revenue2 = round(gross_revenue2 / (1 + tax_rate_out), 2)

    vat2 = gross_revenue2 - net_revenue2

    taxable_gross = gross_revenue1 + gross_revenue2

    taxable_net = net_revenue1 + net_revenue2

    total_vat = vat1 + vat2

    total_taxable_gross = gross_revenue2 + gross_revenue1

    filtered_paid_orders = ranged_paid_alacarte_orders + ranged_paid_out_orders

    percentage_discounts = sum([order.discount_rate * order.totalPrice for order
                                in filtered_paid_orders if order.discount_rate])

    total_discounts = sum([order.discount for order
                                in filtered_paid_orders if order.discount])

    cur_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                order.settleTime.date() == today]

    revenue_from_cur_paid_tables = sum([order.totalPrice for
                                        order in cur_paid_alacarte_orders])

    cur_unpaid_alacarte_orders = [order for order in unpaid_orders if
                                  order.type == "In" and
                                  order.timeCreated.date() == today]

    revenue_from_cur_unpaid_tables = sum([order.totalPrice for
                                            order in cur_unpaid_alacarte_orders])

    cur_paid_orders = [order for order in paid_orders
                       if order.settleTime.date() == today]

    cur_de_facto_revenue = sum([order.totalPrice for order in cur_paid_orders])

    dummy_cur_revenue = cur_de_facto_revenue + revenue_from_cur_unpaid_tables

    ranged_paid_orders_cash = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Cash"
                               and from_time <= order.settleTime <= til]

    ranged_paid_orders_card = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Card"
                               and from_time <= order.settleTime <= til]

    gross_cash_revenue = sum([order.totalPrice for order in ranged_paid_orders_cash])

    gross_card_revenue = sum([order.totalPrice for order in ranged_paid_orders_card])

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"查看历史Z单",
                   company_name=company_info.get('company_name'),
                   z_number=z_number,
                   now=format_datetime(til, locale="de_DE"),
                   gross_revenue1=formatter(gross_revenue1),
                   net_revenue1=formatter(net_revenue1),
                   vat1=formatter(vat1),
                   gross_revenue2=formatter(gross_revenue2),
                   net_revenue2=formatter(net_revenue2),
                   vat2=formatter(vat2),
                   taxable_gross=formatter(taxable_gross),
                   taxable_net=formatter(taxable_net),
                   total_vat=formatter(total_vat),
                   total_taxable_gross=formatter(total_taxable_gross),
                   percentage_discounts=formatter(percentage_discounts),
                   total_discounts=formatter(total_discounts),
                   gross_cash_revenue=formatter(gross_cash_revenue),
                   gross_card_revenue=formatter(gross_card_revenue),
                   dummy_cur_revenue=formatter(dummy_cur_revenue),
                   revenue_from_cur_paid_tables=formatter(revenue_from_cur_paid_tables),
                   revenue_from_cur_unpaid_tables=formatter(revenue_from_cur_unpaid_tables),
                   from_timestamp=from_timestamp,
                   til_timestamp=til_timestamp
                   )

    return render_template("view_printed_z_receipt.html", **context)


@app.route('/print/z/receipt/<string:date_time>', methods=["POST", "GET"])
@login_required
def print_z_receipt(date_time):

    til = datetime.fromtimestamp(float(date_time))

    paid_orders = Order.query.filter(Order.isPaid == True).order_by(Order.settleTime.desc()).all()

    unpaid_orders = Order.query.filter(Order.isPaid == False).order_by(Order.settleTime.desc()).all()

    with open(str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'),
              mode="rb") as pickle_out:
        data = pickle.load(pickle_out)

    first_pay_time = paid_orders[-1].settleTime

    first_order_time = unpaid_orders[-1].timeCreated

    from_time = None

    cur_z_receipt_printed = False

    if len(data) == 0:

        from_time = min([first_pay_time, first_order_time])

    else:

        from_time = list(data[-1].items())[0][1].get('lastPrinted')

        if from_time.date() == today:

            cur_z_receipt_printed = True

    now = til

    ranged_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                   from_time <= order.settleTime <= now]

    ranged_paid_out_orders = [order for order in paid_orders if order.type == "Out" and
                              from_time <= order.settleTime <= now]

    gross_revenue1 = sum([order.totalPrice for order in ranged_paid_alacarte_orders])

    net_revenue1 = round(gross_revenue1 / (1 + tax_rate_in), 2)

    vat1 = gross_revenue1 - net_revenue1

    gross_revenue2 = sum([order.totalPrice for order in ranged_paid_out_orders])

    net_revenue2 = round(gross_revenue2 / (1 + tax_rate_out), 2)

    vat2 = gross_revenue2 - net_revenue2

    taxable_gross = gross_revenue1 + gross_revenue2

    taxable_net = net_revenue1 + net_revenue2

    total_vat = vat1 + vat2

    total_taxable_gross = gross_revenue2 + gross_revenue1

    filtered_paid_orders = ranged_paid_alacarte_orders + ranged_paid_out_orders

    percentage_discounts = sum([order.discount_rate * order.totalPrice for order
                                in filtered_paid_orders if order.discount_rate])

    total_discounts = sum([order.discount for order
                           in filtered_paid_orders if order.discount])

    cur_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                order.settleTime.date() == today]

    revenue_from_cur_paid_tables = sum([order.totalPrice for
                                        order in cur_paid_alacarte_orders])

    cur_unpaid_alacarte_orders = [order for order in unpaid_orders if
                                  order.type == "In" and
                                  order.timeCreated.date() == today and not order.isCancelled]

    revenue_from_cur_unpaid_tables = sum([order.totalPrice for
                                          order in cur_unpaid_alacarte_orders])

    cur_paid_orders = [order for order in paid_orders
                       if order.settleTime.date() == today]

    cur_de_facto_revenue = sum([order.totalPrice for order in cur_paid_orders])

    dummy_cur_revenue = cur_de_facto_revenue + revenue_from_cur_unpaid_tables

    ranged_paid_orders_cash = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Cash"
                               and from_time <= order.settleTime <= now]

    ranged_paid_orders_card = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Card"
                               and from_time <= order.settleTime <= now]

    gross_cash_revenue = sum([order.totalPrice for order in ranged_paid_orders_cash])

    gross_card_revenue = sum([order.totalPrice for order in ranged_paid_orders_card])

    context = dict(
                   z_number=len(data) + 1,
                   now=format_datetime(now, locale="de_DE"),
                   gross_revenue1=formatter(gross_revenue1),
                   net_revenue1=formatter(net_revenue1),
                   vat1=formatter(vat1),
                   gross_revenue2=formatter(gross_revenue2),
                   net_revenue2=formatter(net_revenue2),
                   vat2=formatter(vat2),
                   taxable_gross=formatter(taxable_gross),
                   taxable_net=formatter(taxable_net),
                   total_vat=formatter(total_vat),
                   total_taxable_gross=formatter(total_taxable_gross),
                   percentage_discounts=formatter(percentage_discounts),
                   total_discounts=formatter(total_discounts),
                   gross_cash_revenue=formatter(gross_cash_revenue),
                   gross_card_revenue=formatter(gross_card_revenue),
                   dummy_cur_revenue=formatter(dummy_cur_revenue),
                   revenue_from_cur_paid_tables=formatter(revenue_from_cur_paid_tables),
                   revenue_from_cur_unpaid_tables=formatter(revenue_from_cur_unpaid_tables))

    temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'z_receipt_temp.docx')

    save_as = f"z_receipt_{str(uuid4())}"

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "printer.json"),
              encoding="utf8") as file:

        data1 = file.read()

    data1 = json.loads(data1)

    printer = data1.get('receipt').get('printer')

    def z_receipt_printer():

        x_z_receipt_templating(context=context,
                               temp_file=temp_file,
                               save_as=save_as,
                               printer=printer)

    th = Thread(target=z_receipt_printer)

    form = ConfirmForm()

    # if today's z receipt is not printed
    if not cur_z_receipt_printed:

        if len(cur_unpaid_alacarte_orders) > 0:

            if request.method == "POST" or form.validate_on_submit():

                th.start()

                if len(data) == 0:

                    data.append({1: {"printedFrom": from_time,
                                     "lastPrinted": now}})

                else:

                    data.append({len(data) + 1: {"printedFrom": from_time,
                                                 "lastPrinted": now}})

                with open(str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'),
                          mode="wb") as pickle_in:

                    pickle.dump(data, pickle_in)

                flash(f"Z单正在打印，请耐心等待.若未打印，\
                                请确认打印机是否处于打开状态及正确配置.", category='success')

                return redirect(url_for('z_receipts_manage'))

            context = dict(referrer=request.headers.get('Referer'),
                           title=u"打印Z单",
                           company_name=company_info.get('company_name'),
                           form=form)

            return render_template("print_z_receipt_confirm.html", **context)

        else:

            th.start()

            if len(data) == 0:

                data.append({1: {"printedFrom": from_time,
                                 "lastPrinted": now}})

            else:

                data.append({len(data) + 1: {"printedFrom": from_time,
                                             "lastPrinted": now}})

            with open(str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'),
                      mode="wb") as pickle_in:

                pickle.dump(data, pickle_in)

        flash(f"Z单正在打印，请耐心等待.若未打印，\
                    请确认打印机是否处于打开状态及正确配置.", category='success')

        return redirect(url_for('z_receipts_manage'))

    else:

        flash(f"今天已经打印过Z单，当天不能二次打印新的z单，但您可以查看和打印历史Z单.")
        return redirect(url_for('z_receipts_manage'))


@app.route('/print/printed/z/receipt/<string:from_timestamp>/<string:til_timestamp>/<string:z_number>')
@login_required
def print_printed_z_receipt(from_timestamp, til_timestamp, z_number):

    til = datetime.fromtimestamp(float(til_timestamp))

    paid_orders = Order.query.filter(Order.isPaid == True).order_by(Order.settleTime.desc()).all()

    unpaid_orders = Order.query.filter(Order.isPaid == False).order_by(Order.settleTime.desc()).all()

    from_time = datetime.fromtimestamp(float(from_timestamp))

    ranged_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                   from_time <= order.settleTime <= til]

    ranged_paid_out_orders = [order for order in paid_orders if order.type == "Out" and
                              from_time <= order.settleTime <= til]

    gross_revenue1 = sum([order.totalPrice for order in ranged_paid_alacarte_orders])

    net_revenue1 = round(gross_revenue1 / (1 + tax_rate_in), 2)

    vat1 = gross_revenue1 - net_revenue1

    gross_revenue2 = sum([order.totalPrice for order in ranged_paid_out_orders])

    net_revenue2 = round(gross_revenue2 / (1 + tax_rate_out), 2)

    vat2 = gross_revenue2 - net_revenue2

    taxable_gross = gross_revenue1 + gross_revenue2

    taxable_net = net_revenue1 + net_revenue2

    total_vat = vat1 + vat2

    total_taxable_gross = gross_revenue2 + gross_revenue1

    filtered_paid_orders = ranged_paid_alacarte_orders + ranged_paid_out_orders

    percentage_discounts = sum([order.discount_rate * order.totalPrice for order
                                in filtered_paid_orders if order.discount_rate])

    total_discounts = sum([order.discount for order
                           in filtered_paid_orders if order.discount])

    cur_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                order.settleTime.date() == today]

    revenue_from_cur_paid_tables = sum([order.totalPrice for
                                        order in cur_paid_alacarte_orders])

    cur_unpaid_alacarte_orders = [order for order in unpaid_orders if
                                  order.type == "In" and
                                  order.timeCreated.date() == today]

    revenue_from_cur_unpaid_tables = sum([order.totalPrice for
                                          order in cur_unpaid_alacarte_orders])

    cur_paid_orders = [order for order in paid_orders
                       if order.settleTime.date() == today]

    cur_de_facto_revenue = sum([order.totalPrice for order in cur_paid_orders])

    dummy_cur_revenue = cur_de_facto_revenue + revenue_from_cur_unpaid_tables

    ranged_paid_orders_cash = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Cash"
                               and from_time <= order.settleTime <= til]

    ranged_paid_orders_card = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Card"
                               and from_time <= order.settleTime <= til]

    gross_cash_revenue = sum([order.totalPrice for order in ranged_paid_orders_cash])

    gross_card_revenue = sum([order.totalPrice for order in ranged_paid_orders_card])

    context = dict(
                   z_number=z_number,
                   now=format_datetime(til, locale="de_DE"),
                   gross_revenue1=formatter(gross_revenue1),
                   net_revenue1=formatter(net_revenue1),
                   vat1=formatter(vat1),
                   gross_revenue2=formatter(gross_revenue2),
                   net_revenue2=formatter(net_revenue2),
                   vat2=formatter(vat2),
                   taxable_gross=formatter(taxable_gross),
                   taxable_net=formatter(taxable_net),
                   total_vat=formatter(total_vat),
                   total_taxable_gross=formatter(total_taxable_gross),
                   percentage_discounts=formatter(percentage_discounts),
                   total_discounts=formatter(total_discounts),
                   gross_cash_revenue=formatter(gross_cash_revenue),
                   gross_card_revenue=formatter(gross_card_revenue),
                   dummy_cur_revenue=formatter(dummy_cur_revenue),
                   revenue_from_cur_paid_tables=formatter(revenue_from_cur_paid_tables),
                   revenue_from_cur_unpaid_tables=formatter(revenue_from_cur_unpaid_tables))

    temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'z_receipt_temp.docx')

    save_as = f"z_receipt_{str(uuid4())}"

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "printer.json"),
              encoding="utf8") as file:

        data1 = file.read()

    data1 = json.loads(data1)

    printer = data1.get('receipt').get('printer')

    def z_receipt_printer():

        x_z_receipt_templating(context=context,
                               temp_file=temp_file,
                               save_as=save_as,
                               printer=printer)

    th = Thread(target=z_receipt_printer)

    th.start()

    flash(f"Z单正在打印，请耐心等待.若未打印，\
                请确认打印机是否处于打开状态及正确配置.", category='success')

    return redirect(url_for('z_receipts_manage'))


@app.route("/x/receipts/manage")
@login_required
def x_receipts_manage():

    with open(str(Path(app.root_path) / 'cache' / 'x_bon_settings.pickle'),
              mode="rb") as pickle_out:
        data = pickle.load(pickle_out)

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"X单(每日多次)",
                   company_name=company_info.get('company_name'),
                   data=data,
                   timestamp=datetime.timestamp(datetime.now()),
                   list=list,
                   datetime_format=datetime_format,
                   datetime=datetime)

    return render_template("view_void_x_receipts.html", **context) \
        if len(data) == 0 else render_template("view_x_receipts.html", **context)


@app.route('/view/x/receipt/<string:timestamp>')
@login_required
def view_x_receipt(timestamp):

    paid_orders = Order.query.filter(Order.isPaid == True).order_by(Order.settleTime.desc()).all()

    unpaid_orders = Order.query.filter(Order.isPaid == False).order_by(Order.settleTime.desc()).all()

    with open(str(Path(app.root_path) / 'cache' / 'x_bon_settings.pickle'),
              mode="rb") as pickle_out:
        data = pickle.load(pickle_out)

    first_order_time = unpaid_orders[-1].timeCreated

    first_pay_time = paid_orders[-1].settleTime

    from_time = min([first_pay_time, first_order_time])

    now = datetime.fromtimestamp(float(timestamp))

    ranged_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                   from_time <= order.settleTime <= now]

    ranged_paid_out_orders = [order for order in paid_orders if order.type == "Out" and
                                   from_time <= order.settleTime <= now]

    gross_revenue1 = sum([order.totalPrice for order in ranged_paid_alacarte_orders])

    net_revenue1 = round(gross_revenue1 / (1 + tax_rate_in), 2)

    vat1 = gross_revenue1 - net_revenue1

    gross_revenue2 = sum([order.totalPrice for order in ranged_paid_out_orders])

    net_revenue2 = round(gross_revenue2 / (1 + tax_rate_out), 2)

    vat2 = gross_revenue2 - net_revenue2

    taxable_gross = gross_revenue1 + gross_revenue2

    taxable_net = net_revenue1 + net_revenue2

    total_vat = vat1 + vat2

    total_taxable_gross = gross_revenue2 + gross_revenue1

    filtered_paid_orders = ranged_paid_alacarte_orders + ranged_paid_out_orders

    percentage_discounts = sum([order.discount_rate * order.totalPrice for order
                                in filtered_paid_orders if order.discount_rate])

    total_discounts = sum([order.discount for order
                                in filtered_paid_orders if order.discount])

    cur_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                order.settleTime.date() == today]

    revenue_from_cur_paid_tables = sum([order.totalPrice for
                                        order in cur_paid_alacarte_orders])

    cur_unpaid_alacarte_orders = [order for order in unpaid_orders if
                                  order.type == "In" and
                                  order.timeCreated.date() == today]

    revenue_from_cur_unpaid_tables = sum([order.totalPrice for
                                            order in cur_unpaid_alacarte_orders])

    cur_paid_orders = [order for order in paid_orders
                       if order.settleTime.date() == today]

    cur_de_facto_revenue = sum([order.totalPrice for order in cur_paid_orders])

    dummy_cur_revenue = cur_de_facto_revenue + revenue_from_cur_unpaid_tables

    ranged_paid_orders_cash = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Cash"
                               and from_time <= order.settleTime <= now]

    ranged_paid_orders_card = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Card"
                               and from_time <= order.settleTime <= now]

    gross_cash_revenue = sum([order.totalPrice for order in ranged_paid_orders_cash])

    gross_card_revenue = sum([order.totalPrice for order in ranged_paid_orders_card])

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"打印X单",
                   company_name=company_info.get('company_name'),
                   x_number=len(data)+1,
                   now=format_datetime(now, locale="de_DE"),
                   now_timestamp=datetime.timestamp(now),
                   gross_revenue1=formatter(gross_revenue1),
                   net_revenue1=formatter(net_revenue1),
                   vat1=formatter(vat1),
                   gross_revenue2=formatter(gross_revenue2),
                   net_revenue2=formatter(net_revenue2),
                   vat2=formatter(vat2),
                   taxable_gross=formatter(taxable_gross),
                   taxable_net=formatter(taxable_net),
                   total_vat=formatter(total_vat),
                   total_taxable_gross=formatter(total_taxable_gross),
                   percentage_discounts=formatter(percentage_discounts),
                   total_discounts=formatter(total_discounts),
                   gross_cash_revenue=formatter(gross_cash_revenue),
                   gross_card_revenue=formatter(gross_card_revenue),
                   dummy_cur_revenue=formatter(dummy_cur_revenue),
                   revenue_from_cur_paid_tables=formatter(revenue_from_cur_paid_tables),
                   revenue_from_cur_unpaid_tables=formatter(revenue_from_cur_unpaid_tables))

    return render_template("view_x_receipt.html", **context)


@app.route('/print/x/receipt/<string:date_time>')
@login_required
def print_x_receipt(date_time):

    til = datetime.fromtimestamp(float(date_time))

    paid_orders = Order.query.filter(Order.isPaid == True).order_by(Order.settleTime.desc()).all()

    unpaid_orders = Order.query.filter(Order.isPaid == False).order_by(Order.settleTime.desc()).all()

    with open(str(Path(app.root_path) / 'cache' / 'x_bon_settings.pickle'),
              mode="rb") as pickle_out:

        data = pickle.load(pickle_out)

    first_order_time = unpaid_orders[-1].timeCreated

    first_pay_time = paid_orders[-1].settleTime

    from_time = min([first_order_time, first_pay_time])

    now = til

    ranged_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                   from_time <= order.settleTime <= now]

    ranged_paid_out_orders = [order for order in paid_orders if order.type == "Out" and
                              from_time <= order.settleTime <= now]

    gross_revenue1 = sum([order.totalPrice for order in ranged_paid_alacarte_orders])

    net_revenue1 = round(gross_revenue1 / (1 + tax_rate_in), 2)

    vat1 = gross_revenue1 - net_revenue1

    gross_revenue2 = sum([order.totalPrice for order in ranged_paid_out_orders])

    net_revenue2 = round(gross_revenue2 / (1 + tax_rate_out), 2)

    vat2 = gross_revenue2 - net_revenue2

    taxable_gross = gross_revenue1 + gross_revenue2

    taxable_net = net_revenue1 + net_revenue2

    total_vat = vat1 + vat2

    total_taxable_gross = gross_revenue2 + gross_revenue1

    filtered_paid_orders = ranged_paid_alacarte_orders + ranged_paid_out_orders

    percentage_discounts = sum([order.discount_rate * order.totalPrice for order
                                in filtered_paid_orders if order.discount_rate])

    total_discounts = sum([order.discount for order
                           in filtered_paid_orders if order.discount])

    cur_paid_alacarte_orders = [order for order in paid_orders if order.type == "In" and
                                order.settleTime.date() == today]

    revenue_from_cur_paid_tables = sum([order.totalPrice for
                                        order in cur_paid_alacarte_orders])

    cur_unpaid_alacarte_orders = [order for order in unpaid_orders if
                                  order.type == "In" and
                                  order.timeCreated.date() == today]

    revenue_from_cur_unpaid_tables = sum([order.totalPrice for
                                          order in cur_unpaid_alacarte_orders])

    cur_paid_orders = [order for order in paid_orders
                       if order.settleTime.date() == today]

    cur_de_facto_revenue = sum([order.totalPrice for order in cur_paid_orders])

    dummy_cur_revenue = cur_de_facto_revenue + revenue_from_cur_unpaid_tables

    ranged_paid_orders_cash = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Cash"
                               and from_time <= order.settleTime <= now]

    ranged_paid_orders_card = [order for order in paid_orders if
                               json.loads(order.pay_via).get('method') == "Card"
                               and from_time <= order.settleTime <= now]

    gross_cash_revenue = sum([order.totalPrice for order in ranged_paid_orders_cash])

    gross_card_revenue = sum([order.totalPrice for order in ranged_paid_orders_card])

    context = dict(
                   z_number=len(data) + 1,
                   now=format_datetime(now, locale="de_DE"),
                   gross_revenue1=formatter(gross_revenue1),
                   net_revenue1=formatter(net_revenue1),
                   vat1=formatter(vat1),
                   gross_revenue2=formatter(gross_revenue2),
                   net_revenue2=formatter(net_revenue2),
                   vat2=formatter(vat2),
                   taxable_gross=formatter(taxable_gross),
                   taxable_net=formatter(taxable_net),
                   total_vat=formatter(total_vat),
                   total_taxable_gross=formatter(total_taxable_gross),
                   percentage_discounts=formatter(percentage_discounts),
                   total_discounts=formatter(total_discounts),
                   gross_cash_revenue=formatter(gross_cash_revenue),
                   gross_card_revenue=formatter(gross_card_revenue),
                   dummy_cur_revenue=formatter(dummy_cur_revenue),
                   revenue_from_cur_paid_tables=formatter(revenue_from_cur_paid_tables),
                   revenue_from_cur_unpaid_tables=formatter(revenue_from_cur_unpaid_tables))

    temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'x_receipt_temp.docx')

    save_as = f"x_receipt_{str(uuid4())}"

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "printer.json"),
              encoding="utf8") as file:

        data1 = file.read()

    data1 = json.loads(data1)

    printer = data1.get('receipt').get('printer')

    def x_receipt_printer():

        x_z_receipt_templating(context=context,
                               temp_file=temp_file,
                               save_as=save_as,
                               printer=printer)

    th = Thread(target=x_receipt_printer)

    th.start()

    if len(data) == 0:

        data.append({1: {"lastPrinted": now}})

    else:

        data.append({len(data)+1: {"lastPrinted": now}})

    with open(str(Path(app.root_path) / 'cache' / 'x_bon_settings.pickle'),
              mode="wb") as pickle_in:

        pickle.dump(data, pickle_in)

    flash(f"X单正在打印，请耐心等待.若未打印，\
                    请确认打印机是否处于打开状态及正确配置.", category='success')

    return redirect(url_for('x_receipts_manage'))


@app.route('/revenue/by/days', methods=["POST", "GET"])
@login_required
def revenue_by_days():

    today = datetime.now(tz=pytz.timezone(timezone)).date()

    referrer = request.headers.get('Referer')

    paid_alacarte_orders = Order.query.filter(
                            Order.isPaid == True,
                            Order.type == "In").all()

    cur_paid_alacarte_orders = [order for order in paid_alacarte_orders if
                                order.timeCreated.date() == datetime.now(
                                    tz=pytz.timezone(timezone)
                                ).date()]

    # Compute the current used sections from Ala Carte
    cur_used_sections = list(set([Table.query.filter_by(name=order.table_name).first_or_404().section
                        for order in paid_alacarte_orders if order.timeCreated.date() == today]))

    paid_out_orders = Order.query.filter(
        Order.isPaid == True,
        Order.type == "Out").all()

    form = DatePickForm()

    alacarte= {"Total": formatter(0),
               "Total_Card": formatter(0),
               "Total_Cash": formatter(0)}

    if form.validate_on_submit() or request.method == "POST":

        start = form.start_date.data
        end = form.end_date.data

        # Accumulating for in/alacarte orders
        alacarte_total = sum(
                           [order.totalPrice for order in
                            [order for order in paid_alacarte_orders
                             if start <= order.timeCreated.date() <= end]])

        ala_cash_total = sum(
                           [order.totalPrice for order in
                            [order for order in paid_alacarte_orders
                             if start <= order.timeCreated.date() <= end
                             and json.loads(order.pay_via).get('method') == "Cash"]])

        ala_card_total = sum(
                            [order.totalPrice for order in
                             [order for order in paid_alacarte_orders
                              if start <= order.timeCreated.date() <= end
                              and json.loads(order.pay_via).get('method') == "Card"]])

        alacarte = {'Total': formatter(alacarte_total),
                    'Total_Cash': formatter(ala_cash_total),
                    'Total_Card': formatter(ala_card_total)}

        # Filtered paid alacarte orders
        filtered_paid_alacarte_orders = [order for order in paid_alacarte_orders
                                         if start <= order.timeCreated.date() <= end]

        # Compute used sections during the DateRange
        filtered_used_sections = list(set([Table.query.filter_by(name=order.table_name).first_or_404().section
                                      for order in paid_alacarte_orders if start <= order.timeCreated.date() <= end]))

        from collections import OrderedDict

        revenue_by_sections = {section:
                                {"Cash": formatter(sum([order.totalPrice for order in [order for order in filtered_paid_alacarte_orders
                                          if Table.query.filter_by(name=order.table_name).first_or_404().section == section
                                          and json.loads(order.pay_via).get('method') == "Cash"]])),

                                  "Card": formatter(sum([order.totalPrice for order in [order for order in filtered_paid_alacarte_orders
                                        if Table.query.filter_by(name=order.table_name).first_or_404().section == section
                                        and json.loads(order.pay_via).get('method') == "Card"]])),

                                  "Total": formatter(sum([order.totalPrice for order in [order for order in filtered_paid_alacarte_orders
                                          if Table.query.filter_by(name=order.table_name).first_or_404().section == section]]))

                                      } for section in filtered_used_sections}

        revenue_by_sections = OrderedDict(sorted(revenue_by_sections.items(), key=lambda t: t[0]))

        # Accumulating for out orders
        out_total = sum([order.totalPrice for order
                      in [order for order in paid_out_orders
                          if start <= order.timeCreated.date() <= end]])

        out_cash_total = sum([order.totalPrice for order in
                             [order for order in paid_out_orders
                              if start <= order.timeCreated.date() <= end
                              and json.loads(order.pay_via).get('method') == "Cash"]])

        out_card_total = sum(
                            [order.totalPrice for order in
                             [order for order in paid_out_orders
                              if start <= order.timeCreated.date() <= end
                              and json.loads(order.pay_via).get('method') == "Card"]])

        out = {'Total': formatter(out_total),
                'Total_Cash': formatter(out_cash_total),
                'Total_Card': formatter(out_card_total)}

        final_card_total = out_card_total + ala_card_total

        final_cash_total = out_cash_total + ala_cash_total

        final_total = final_card_total + final_cash_total

        context = dict(referrer=referrer,
                       alacarte=alacarte,
                       out=out,
                       form=form,
                       company_name=company_info.get('company_name'),
                       revenue_by_sections=revenue_by_sections,
                       title=u"日结",
                       formatter=formatter,
                       final_card_total=formatter(final_card_total),
                       final_cash_total=formatter(final_cash_total),
                       final_total=formatter(final_total),
                       start=format_datetime(start, locale="de_DE"),
                       end=format_datetime(end, locale="de_DE"))

        # Print the daily receipt
        if form.print.data:

            save_as = f"daily_revenue_report_{str(uuid4())}"

            th = Thread(target=daily_revenue_templating, args=(context, save_as, ))

            th.start()

            flash(f"日结报告正在打印，若未正常打印，请检查打印机是否正确配置或者处于打开状态")

        return render_template('revenue_by_days.html', **context)

    from collections import OrderedDict

    revenue_by_sections = {section: {"Cash": formatter(sum([order.totalPrice for order in [order for order in cur_paid_alacarte_orders
                                             if Table.query.filter_by(name=order.table_name).first_or_404().section
                                             == section and json.loads(order.pay_via).get('method') == "Cash"]])),

                                  "Card": formatter(sum([order.totalPrice for order in [order for order in cur_paid_alacarte_orders
                                             if Table.query.filter_by(name=order.table_name).first_or_404().section
                                             == section and json.loads(order.pay_via).get('method') == "Card"]])),

                                  "Total": formatter(sum([order.totalPrice for order in [order for order in cur_paid_alacarte_orders
                                              if Table.query.filter_by(name=order.table_name).first_or_404().section == section]]))

                                  } for section in cur_used_sections}

    revenue_by_sections = OrderedDict(sorted(revenue_by_sections.items(),
                                             key=lambda t: t[0]))

    form.start_date.data = datetime.now(tz=pytz.timezone(timezone)).date()
    form.end_date.data = datetime.now(tz=pytz.timezone(timezone)).date()

    # Aggregate today's out orders
    out_total = sum([order.totalPrice for order
                     in [order for order in paid_out_orders
                        if order.timeCreated.date() ==
                         datetime.now(tz=pytz.timezone(timezone)).date()]])

    out_cash_total = sum([order.totalPrice for order in
                          [order for order in paid_out_orders
                           if order.timeCreated.date() ==
                           datetime.now(tz=pytz.timezone(timezone)).date()
                           and json.loads(order.pay_via).get('method') == "Cash"]])

    out_card_total = sum(
        [order.totalPrice for order in
         [order for order in paid_out_orders
          if order.timeCreated.date() == datetime.now(
             tz=pytz.timezone(timezone)).date()
              and json.loads(order.pay_via).get('method') == "Card"]])

    out = {'Total': formatter(out_total),
           'Total_Cash': formatter(out_cash_total),
           'Total_Card': formatter(out_card_total)}

    # Accumulating for in/alacarte orders
    alacarte_total = sum(
        [order.totalPrice for order in
         [order for order in paid_alacarte_orders
          if order.timeCreated.date() == today]])

    ala_cash_total = sum(
        [order.totalPrice for order in
         [order for order in paid_alacarte_orders
          if order.timeCreated.date() == today
          and json.loads(order.pay_via).get('method') == "Cash"]])

    ala_card_total = sum(
        [order.totalPrice for order in
         [order for order in paid_alacarte_orders
          if order.timeCreated.date() == today
          and json.loads(order.pay_via).get('method') == "Card"]])

    alacarte = {'Total': formatter(alacarte_total),
                'Total_Cash': formatter(ala_cash_total),
                'Total_Card': formatter(ala_card_total)}

    final_card_total = out_card_total + ala_card_total

    final_cash_total = out_cash_total + ala_cash_total

    final_total = final_card_total + final_cash_total

    # Wrap all info in a dict for templating mapping.
    context = dict(referrer=referrer,
                   form=form,
                   out=out,
                   company_name=company_info.get('company_name'),
                   revenue_by_sections=revenue_by_sections,
                   alacarte=alacarte,
                   title=u"日结",
                   formatter=formatter,
                   final_card_total=formatter(final_card_total),
                   final_cash_total=formatter(final_cash_total),
                   final_total=formatter(final_total),
                   start=today,
                   end=today)

    return render_template('revenue_by_days.html', **context)


@app.route('/revenue/by/week', methods=["POST", "GET"])
@login_required
def revenue_by_week():

    referrer = request.headers.get('Referer')

    paid_orders = Order.query.filter(Order.isPaid == True).all()

    from datetime import datetime, timedelta

    today = datetime.now().date()

    start = today - timedelta(days=today.weekday())

    weekdays2revenue = {

        (start + timedelta(days=n)).strftime("%A"):

                 {"Total": formatter(sum([order.totalPrice for order in paid_orders if\
                            order.timeCreated.date() == start + timedelta(days=n)])),

                  "Total_Cash": formatter(sum([order.totalPrice for order in paid_orders if\
                                order.timeCreated.date() == start + timedelta(days=n)\
                                and json.loads(order.pay_via).get('method')=="Cash"])),

                  "Total_Card": formatter(sum([order.totalPrice for order in paid_orders if\
                                 order.timeCreated.date() == start + timedelta(days=n)\
                                 and json.loads(order.pay_via).get('method') == "Card"])),
                  } for n in range(7)}

    week2en = {u"星期一": "Monday",
               u"星期二": "Tuesday",
               u"星期三": "Wednesday",
               u"星期四": "Thursday",
               u"星期五": "Friday",
               u"星期六": "Saturday",
               u"星期天": "Sunday"}

    context = dict(referrer=referrer,
                   company_name=company_info.get('company_name'),
                   weekdays2revenue=weekdays2revenue,
                   week2en=week2en,
                   title=u"星期结")

    return render_template('revenue_by_week.html', **context)


@app.route('/revenue/by/month', methods=["POST", "GET"])
@login_required
def revenue_by_month():

    paid_orders = Order.query.filter(Order.isPaid==True).all()

    from calendar import monthrange

    today =datetime.now().date()

    cur_year = int(today.strftime("%Y"))

    cur_mon = int(today.strftime("%m"))

    start = datetime(cur_year, cur_mon, 1).date()

    cur_mon_range = monthrange(cur_year, cur_mon)[1]

    referrer = request.headers.get('Referer')

    ordered_days2revenue = {

        (start + timedelta(days=n)).strftime("%d"):

                 {"Total": formatter(sum([order.totalPrice for order in paid_orders if\
                            order.timeCreated.date() == start + timedelta(days=n)])),

                  "Total_Cash": formatter(sum([order.totalPrice for order in paid_orders if\
                                order.timeCreated.date() == start + timedelta(days=n)\
                                and json.loads(order.pay_via).get('method')=="Cash"])),

                  "Total_Card": formatter(sum([order.totalPrice for order in paid_orders if\
                                 order.timeCreated.date() == start + timedelta(days=n)\
                                 and json.loads(order.pay_via).get('method') == "Card"])),
                  } for n in range(cur_mon_range)}

    context = dict(referrer=referrer,
                   company_name=company_info.get('company_name'),
                   ordered_days2revenue=ordered_days2revenue,
                   title=u"月结")

    return render_template('revenue_by_month.html', **context)


@app.route('/revenue/by/year', methods=["POST", "GET"])
@login_required
def revenue_by_year():

    referrer = request.headers.get('Referer')

    paid_orders = Order.query.filter(Order.isPaid == True).all()

    months2revenue = {

        str(month):

            {"Total": formatter(sum([order.totalPrice for order in paid_orders if
                   str(int(order.timeCreated.date().strftime("%m"))) == str(month)])),

             "Total_Cash": formatter(sum([order.totalPrice for order in paid_orders if
                            str(int(order.timeCreated.date().strftime("%m"))) == str(month)
                            and json.loads(order.pay_via).get('method') == "Cash"])),

             "Total_Card": formatter(sum([order.totalPrice for order in paid_orders if
                            str(int(order.timeCreated.date().strftime("%m"))) == str(month)
                            and json.loads(order.pay_via).get('method') == "Card"])),
             } for month in range(1, 13)}

    context = dict(referrer=referrer,
                   company_name=company_info.get('company_name'),
                   months2revenue=months2revenue,
                   title=u"年结")

    return render_template('revenue_by_year.html', **context)


# Boss Interface
# Boss Dashboard view active tables
@app.route('/super', methods=["POST", "GET"])
@login_required
def boss_active_tables():

    referrer = request.headers.get('Referer')

    if current_user.permissions < 3:

        return render_template('auth_error.html', referrer=referrer)

    form = SearchTableForm()

    # Filtering alacarte unpaid orders
    orders = Order.query.filter(
        Order.type == "In",
        Order.isPaid == False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    open_orders = [order for order in orders if
                   order.timeCreated.date() == today and
                   not json.loads(order.container).get('isCancelled')]

    # Currently Open Tables
    open_tables = list(set([json.loads(order.container).get("table_name")
                            for order in open_orders]))

    # Extend the choices of current form
    form.select_table.choices.extend([(i, i) for i in open_tables])

    if form.validate_on_submit():

        selected_table = form.select_table.data
        open_tables = [table for table in open_tables if table == selected_table]

        return render_template('boss_active_tables.html',
                               form=form,
                               open_tables=open_tables)

    return render_template('boss_active_tables.html',
                           form=form,
                           open_tables=open_tables,
                           referrer=referrer)


@app.route('/super/revenue/by/day', methods=["GET", "POST"])
@login_required
def boss_daily_revenue():

    referrer = request.headers.get('Referer')

    paid_alacarte_orders = Order.query.filter(
        Order.isPaid, Order.type == "In").all()

    paid_out_orders = Order.query.filter(
        Order.isPaid, Order.type == "Out").all()

    form = DatePickForm()

    alacarte = {"Total": 0,
                "Total_Card": 0,
                "Total_Cash": 0}

    out = {"Total": 0,
           "Total_Card": 0,
           "Total_Cash": 0}

    if form.validate_on_submit():
        start = form.start_date.data
        end = form.end_date.data

        # Accumulating for in/alacarte orders
        alacarte_total = sum(
            [order.totalPrice for order in
             [order for order in paid_alacarte_orders
              if start <= order.timeCreated.date() <= end]])

        ala_cash_total = sum(
            [order.totalPrice for order in
             [order for order in paid_alacarte_orders
              if start <= order.timeCreated.date() <= end
              and json.loads(order.pay_via).get('method') == "Cash"]])

        ala_card_total = sum(
            [order.totalPrice for order in
             [order for order in paid_alacarte_orders
              if start <= order.timeCreated.date() <= end
              and json.loads(order.pay_via).get('method') == "Card"]])

        alacarte = {'Total': alacarte_total,
                    'Total_Cash': ala_cash_total,
                    'Total_Card': ala_card_total}

        # Accumulating for out orders
        out_total = sum([order.totalPrice for order
                         in [order for order in paid_out_orders
                             if start <= order.timeCreated.date() <= end]])

        out_cash_total = sum([order.totalPrice for order in
                              [order for order in paid_out_orders
                               if start <= order.timeCreated.date() <= end
                               and json.loads(order.pay_via).get('method') == "Cash"]])

        out_card_total = sum(
            [order.totalPrice for order in
             [order for order in paid_out_orders
              if start <= order.timeCreated.date() <= end
              and json.loads(order.pay_via).get('method') == "Card"]])

        out = {'Total': out_total,
               'Total_Cash': out_cash_total,
               'Total_Card': out_card_total}

        return render_template('daily_revenue_boss.html',
                               referrer=referrer,
                               alacarte=alacarte,
                               out=out,
                               form=form)

    return render_template('daily_revenue_boss.html',
                           referrer=referrer,
                           form=form,
                           alacarte=alacarte,
                           out=out)


@app.route('/boss/view/open/alacarte/orders')
@login_required
def boss_view_alacarte_open_orders():

    referrer = request.headers.get('Referer')

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False).all()

    cur_orders = [order for order in orders if order.timeCreated.date()
                  == today]

    items = {order.id: json.loads(order.items) for order in cur_orders}

    containers = {order.id: json.loads(order.container) for order in cur_orders}

    return render_template("boss_view_alalcarte_open_orders.html",
                           open_orders=cur_orders,
                           items=items,
                           containers=containers,
                           referrer=referrer)


@app.route('/boss/transfer/table/<string:table_name>', methods=["POST", "GET"])
@login_required
def boss_transfer_table(table_name):

    from .forms import TransferTableForm

    form = TransferTableForm()

    all_tables = Table.query.all()

    # Filtering alacarte unpaid orders
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    open_orders = [order for order in orders if
                   order.timeCreated.date() == today and
                   not json.loads(order.container).get('isCancelled')]

    # Currently Open Tables
    open_tables = list(set([json.loads(order.container).get("table_name")
                            for order in open_orders]))

    available_tables = [table for table in all_tables if table.name not in open_tables]

    form.target_table.choices.extend([(table.name, f"{table.name} - {table.number}人")
                                      for table in available_tables])

    if form.validate_on_submit():

        cur_table_orders = [order for order in open_orders
                            if json.loads(order.container).get('table_name') == table_name]

        target_table = form.target_table.data

        for order in cur_table_orders:

            logging = {'table_before': json.loads(order.container).get('table_name'), 'table_cur': target_table}

            container = json.loads(order.container)

            container['table_name'] = target_table

            order.container = json.dumps(container)

            db.session.commit()

            try:
                # Writing log to the csv file
                activity_logger(order_id=order.id,
                                operation_type=u'转台',
                                page_name='老板界面 > 已点餐桌子 > 转台',
                                descr=f'''\n
                                订单号:{order.id}\n
                                原桌子：{logging.get('table_before')}\n
                                新桌子:{logging.get('table_cur')}\n'
                                操作人:{current_user.username}\n
                                ''',
                                status=u'成功',
                                log_time=str(datetime.now(tz=pytz.timezone('Europe/Berlin'))))
            except:

                pass

            flash(f"桌子{table_name}已经转至{target_table}!", category='success')

            return redirect(url_for('boss_active_tables'))

    form.cur_table.data = f"{table_name} - {Table.query.filter_by(name=table_name).first_or_404().number}人"

    return render_template("boss_transfer_table.html", form=form)


# Waiter views a table's aggregated order summary
@app.route("/boss/view/table/<string:table_name>", methods=["GET", "POST"])
@login_required
def boss_view_table(table_name):

    # Check out form payment methods, discount and coupon code
    form = CheckoutForm()

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False).all()

    open_orders = [order for order in orders if
                   json.loads(order.container).get('table_name') == table_name and
                   order.timeCreated.date() == today and
                   not json.loads(order.container).get('isCancelled')]

    # Add cond if order not cancelled
    # Check if a checkout button is clicked
    if request.method == "POST" or form.validate_on_submit():

        # Set the settleID and settleTime
        settle_id = str(uuid4().int)
        settle_time = datetime.now(tz=pytz.timezone(timezone))

        for order in open_orders:

            logging = {}

            pay_via = {}

            # Pay via cash
            if form.cash_submit.data:

                if form.coupon_amount.data:

                    order.totalPrice = order.totalPrice -\
                                       (form.coupon_amount.data/len(open_orders))

                    pay_via['coupon_amount'] = form.coupon_amount.data/len(open_orders)

                elif form.discount_rate.data:

                    order.totalPrice = order.totalPrice * form.discount_rate.data
                    pay_via['discount_rate'] = form.discount_rate.data

                pay_via["method"] = "Cash"
                logging['Pay'] = u'现金'

            # Pay via card
            elif form.card_submit.data:

                if form.coupon_amount.data:

                    order.totalPrice = order.totalPrice -\
                                       (form.coupon_amount.data/len(open_orders))

                    pay_via['coupon_amount'] = form.coupon_amount.data/len(open_orders)

                elif form.discount_rate.data:

                    order.totalPrice = order.totalPrice * form.discount_rate.data
                    pay_via['discount_rate'] = form.discount_rate.data

                pay_via['method'] = "Card"
                logging['Pay'] = u'卡'

            order.settleID = settle_id
            order.settleTime = settle_time

            order.isPaid = True

            order.pay_via = json.dumps(pay_via)

            db.session.commit()

            try:

                # Writing logs to the csv file
                activity_logger(order_id=order.id,
                                operation_type=u'结账',
                                page_name=u'老板界面 > 桌子详情',
                                descr=f'''结账订单号:{order.id}\n
                                        桌子编号：{json.loads(order.container).get('table_name')}-{json.loads(order.container).get('seat_number')}
                                        支付方式:{logging.get('Pay')}\n
                                        结账金额: {order.totalPrice}\n
                                        订单类型:AlaCarte\n''',
                                log_time=str(datetime.now(tz=pytz.timezone('Europe/Berlin'))),
                                status=u'成功')

            except:

                pass

            return redirect(url_for('boss_active_tables'))

    # Else just render page as get method
    # Calculate the total price for this table
    total_price = sum([order.totalPrice for order in open_orders])

    dish_varieties = [[key for key in (json.loads(order.items).keys())] for order in open_orders]

    varieties = []
    for x in dish_varieties:
        varieties.extend(x)

    varieties = list(set(varieties))

    dishes = {
        dish:
            {
            'quantity': sum([json.loads(order.items).get(dish).get('quantity')
                             for order in open_orders if json.loads(order.items).get(dish)]),

            'price': Food.query.filter_by(name=dish).first_or_404().price_gross,

            'class_name': Food.query.filter_by(name=dish).first_or_404().class_name,

             } for dish in varieties}

    return render_template('boss_view_table_summary.html',
                           dishes=dishes,
                           table_name=table_name,
                           total_price=total_price,
                           form=form)


@app.route('/boss/view/paid/alacarte/orders')
@login_required
def boss_view_paid_alacarte_orders():

    referrer = request.headers.get('Referer')

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == True).all()

    cur_orders = orders

    items = {order.id: json.loads(order.items) for order in cur_orders}

    containers = {order.id: json.loads(order.container) for order in cur_orders}

    return render_template("boss_view_paid_alacarte_orders.html",
                           open_orders=cur_orders,
                           items=items,
                           containers=containers,
                           referrer=referrer)


# The boss view all the takeaway orders
@app.route("/boss/takeaway/orders/all")
@login_required
def boss_all_out_orders():

    # Filter only takeaway orders
    orders = Order.query.filter(Order.type == "Out").all()
    return render_template('boss_all_out_orders.html',
                           title=u'外卖订单',
                           orders=orders)


@app.route('/boss/users/manage')
@login_required
def boss_users_manage():

    referrer = request.headers.get('Referer')

    if current_user.permissions < 100:

        return render_template('auth_error.html', referrer=referrer)

    # Exclude the current logged in user - You can't delete your self
    users = User.query.filter(User.id != current_user.id).all()

    user_in_use = {user.id: json.loads(user.container).get('inUse') for user in users}

    context = dict(users=users,
                   user_in_use=user_in_use,
                   referrer=request.headers.get('Referer'),
                   title=u'账户管理',
                   company_name=company_info.get('company_name'))

    return render_template('boss_users_manage.html', **context)


@app.route('/boss/users/add', methods=["GET", "POST"])
@login_required
def boss_add_user():

    referrer = request.headers.get('Referer')

    if current_user.permissions < 100:

        return render_template('auth_error.html', referrer=referrer)

    form = AddUserForm()

    if request.method == "POST":

        username = form.username.data
        alias = form.alias.data
        permissions = form.permissions.data
        password = form.password.data

        user = User(username=username,
                    alias=alias,
                    container=json.dumps({'inUse': True, 'section': ["Admin"]}),
                    permissions=permissions,
                    email=f"{str(uuid4())[:11]}@cnfrien.com")

        # Email attr will be deprecated
        user.set_password(password=password)

        db.session.add(user)

        db.session.commit()

        flash(message=f"已经创建账号{user.username}", category="success")

        return redirect(url_for('boss_users_manage'))

    context=dict(referrer=referrer,
                 form=form,
                 title=u"添加账户",
                 company_name=company_info.get('company_name'))

    return render_template('boss_add_user.html', **context)


@app.route("/boss/user/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def boss_edit_user(user_id):

    referrer = request.headers.get('Referer')

    if current_user.permissions < 100:

        return render_template('auth_error.html', referrer=referrer)

    user = db.session.query(User).get_or_404(user_id)

    form = EditUserForm()

    if request.method == "POST":

        user.username = form.username.data
        user.permissions = form.permissions.data

        db.session.commit()

        flash(message=f"已经更新账号{user.username}的资料", category="success")

        return redirect(url_for('boss_users_manage'))

    form.username.data = user.username
    form.permissions.data = user.permissions

    context = dict(title="修改账号",
                   form=form,
                   user=user,
                   company_name=company_info.get('company_name'),
                   referrer=request.headers.get('Referer')
                   )

    return render_template('boss_edit_user.html',
                           **context)


@app.route('/boss/update/<int:user_id>/password', methods=["GET", "POST"])
@login_required
def boss_update_password(user_id):

    user = db.session.query(User).get_or_404(int(user_id))

    referrer = request.headers.get('Referer')

    if current_user.permissions < 100:

        return render_template('auth_error.html', referrer=referrer)

    form = EditUserForm()

    if request.method == "POST":

        user.set_password(password=form.password.data)

        db.session.commit()

        flash(f'已经为{user.username}成功更新密码', category="success")

        return redirect(url_for('boss_users_manage'))

    form.username.data = user.username

    context = dict(title="修改账号密码",
                   form=form,
                   user=user,
                   company_name=company_info.get('company_name'),
                   referrer=request.headers.get('Referer')
                   )

    return render_template('boss_update_password.html', **context)


@app.route('/boss/user/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
def boss_delete_user(user_id):

    referrer = request.headers.get('Referer')
    user = db.session.query(User).get_or_404(int(user_id))

    if current_user.permissions < 100:

        return render_template('auth_error.html', referrer=referrer)

    form = ConfirmForm()

    if form.validate_on_submit():

        db.session.delete(user)

        db.session.commit()

        flash(message=f"已经删除账号:{user.username}", category="danger")

        return redirect(url_for('boss_users_manage'))

    return render_template('boss_remove_user.html',
                           user=user,
                           referrer=referrer,
                           form=form,
                           company_name=company_info.get('company_name'))


# boss / admin switch user on and off
@app.route('/user/switch', methods=["POST"])
def switch_user():

    # Handle Data From Ajax
    if request.method == "POST":

        data = request.json

        user_id = data.get('userId')

        status = data.get('inUse')

        user = db.session.query(User).get_or_404(int(user_id))

        container = json.loads(user.container)

        container['inUse'] = status

        user.container = json.dumps(container)

        db.session.commit()

        return jsonify({'status': 200})


@app.route("/boss/alacarte/order/<int:order_id>/edit")
@login_required
def boss_alacarte_order_edit(order_id):

    order = Order.query.get_or_404(int(order_id))

    ordered_items = json.loads(order.items)

    container = json.loads(order.container)

    referrer = request.headers.get('Referer')

    return render_template('boss_alacarte_order_edit.html',
                           order=order,
                           ordered_items=ordered_items,
                           container=container,
                           referrer=referrer)


@app.route('/boss/alacarte/orders/update', methods=["GET", "POST"])
@login_required
def boss_update_alacarte_order():

    logging = {}

    if request.method == "POST":

        data = request.get_json('orderId')

        order_id = data.get('orderId')

        order = db.session.query(Order).get_or_404(int(order_id))

        logging['before'] = "\n".join([f"{key}x{items.get('quantity')}"
                                       for (key, items) in json.loads(order.items).items()])

        details = data.get('details')

        logging['after'] = "\n".join([f"{i.get('item')}x{i.get('quantity')}"
                                      for i in details])

        price_dict = {
            i.get('item'):
                Food.query.filter_by(name=i.get('item')).first_or_404().price_gross
                      for i in details}

        details = {
            detail.get('item'):
                {'quantity': int(detail.get('quantity')),
                 'price': float(price_dict.get(detail.get('item')))}
            for detail in details}

        prices = [i[1].get('quantity') * i[1].get('price') for i in details.items()]

        order.totalPrice = sum(prices)
        order.items = json.dumps(details)

        db.session.commit()

        # Init a log object
        log = Log()
        log.order_id = order.id
        log.operation = u'订单修改'
        log.page = u'老板界面 > 餐桌情况(未结账) >订单修改'
        log.desc = f'''
                    修改订单号: {order.id}\n
                    桌子编号：{json.loads(order.container).get('table_name')}-{json.loads(order.container).get('seat_number')}\n
                    修改前明细: {logging.get('before')}\n
                    修改后明细: {logging.get('after')}\n
                    修改前账单金额: {logging.get('price_before')}\n
                    修改后账单金额: {logging.get('price_after')}\n
                    订单类型: AlaCarte\n
                    {logging.get('remark', "")}\n'''
        log.time = str(datetime.now(tz=pytz.timezone('Europe/Berlin')))
        log.status = 'Erfolgreich'

        db.session.add(log)
        db.session.commit()

        return redirect(url_for('boss_view_alacarte_open_orders'))


# View paid takeaway order
@app.route("/boss/view/takeaway/order/<string:order_id>/view", methods=["GET", "POST"])
@login_required
def boss_takeaway_order_view(order_id):

    order = Order.query.filter_by(id=int(order_id)).first()

    ordered_items = json.loads(order.items)

    for key, details in ordered_items.items():

        item = Food.query.filter_by(name=key).first()

        if item:

            details["image"] = item.image
            details["descr"] = item.description
            details["price"] = item.price_gross

    prices = {'tax': round((order.totalPrice / (1 + tax_rate_out))*tax_rate_out, 2),
              'subtotal': round(order.totalPrice / (1 + tax_rate_out), 2)}

    referrer = request.headers.get('Referer')

    return render_template('boss_takeaway_view_order.html',
                           order=order,
                           ordered_items=ordered_items,
                           prices=prices,
                           referrer=referrer)


@app.route("/view/meallists")
@login_required
def view_meallists():

    # Filtering alacarte unpaid orders and the targeted table
    unpaid_alacarte_orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False).all()

    cur_unpaid_alacarte_orders = [order for order in unpaid_alacarte_orders if
                  order.timeCreated.date() == today]

    paid_out_orders = db.session.query(Order).filter(
        Order.type == "Out",
        Order.isPaid == True).all()

    cur_paid_out_orders = [order for order in paid_out_orders if
                                  order.timeCreated.date() == today]

    out_meals = [{datetime.timestamp(order.timeCreated):
                      {"items": json.loads(order.items), "order_id": order.id}}
                 for order in cur_paid_out_orders]

    alacarte_meals = [patch for order in
                      cur_unpaid_alacarte_orders for patch in json.loads(order.dishes)]

    meals = out_meals + alacarte_meals

    orders = unpaid_alacarte_orders + paid_out_orders

    cur_orders = [order for order in orders if
                  order.timeCreated.date() == today]

    cuisines = {"In": "InHouse",
                "Out": u"外卖"}

    type_dict = {order.id: cuisines.get(order.type) for order in cur_orders}

    table_dict = {order.id: order.table_name for order in cur_orders}

    context = dict(meals=meals,
                   type_dict=type_dict,
                   table_dict=table_dict,
                   referrer=request.headers.get('Referer'),
                   title=u"菜品打印",
                   datetime_format=datetime_format,
                   company_name=company_info.get('company_name'),
                   datetime=datetime,
                   Order=Order,
                   float=float)

    # return jsonify(meals)
    return render_template("view_meallists.html", **context)


@app.route("/print/meallist/<string:timestamp>")
@login_required
def print_meallist(timestamp):

    # Filtering alacarte unpaid orders and the targeted table
    unpaid_alacarte_orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False).all()

    cur_unpaid_alacarte_orders = [order for order in unpaid_alacarte_orders if
                                  order.timeCreated.date() == today]

    paid_out_orders = db.session.query(Order).filter(
        Order.type == "Out",
        Order.isPaid == True).all()

    cur_paid_out_orders = [order for order in paid_out_orders if
                           order.timeCreated.date() == today]

    out_meals = [{str(datetime.timestamp(order.timeCreated)):
                      {"items": json.loads(order.items), "order_id": order.id}}
                 for order in cur_paid_out_orders]

    alacarte_meals = [patch for order in
                      cur_unpaid_alacarte_orders for patch in json.loads(order.dishes)]

    meals = out_meals + alacarte_meals

    meal = [meal.get(timestamp) for meal in meals if meal.get(timestamp)][0]

    order = Order.query.get_or_404(int(meal.get('order_id')))

    ordered_items = meal.get('items')

    details_kitchen = {key: {'quantity': items.get('quantity'),
                             'total': items.get('quantity') * items.get('price')}
                       for key, items in ordered_items.items() if items.get("class_name") == "Food"}

    details_bar = {key: {'quantity': items.get('quantity'),
                         'total': items.get('quantity') * items.get('price')}
                   for key, items in ordered_items.items() if items.get("class_name") == "Drinks"}

    context_kitchen = None

    context_bar = None

    kitchen_temp = None

    bar_temp = None

    if order.type == "In":

        kitchen_temp = str(Path(app.root_path) / 'static' / 'docx' / 'kitchen_alacarte.docx')

        bar_temp = str(Path(app.root_path) / 'static' / 'docx' / 'bar_alacarte.docx')

        context_kitchen = {"details": details_kitchen,
                           "table_name": order.table_name,
                           "now": format_datetime(datetime.now(), locale="de_DE")}

        context_bar = {"details": details_bar,
                       "table_name": order.table_name,
                       "now": format_datetime(datetime.now(), locale="de_DE")}

    else:

        kitchen_temp = str(Path(app.root_path) / 'static' / 'docx' / 'kitchen.docx')

        bar_temp = str(Path(app.root_path) / 'static' / 'docx' / 'bar.docx')

        context_kitchen = {"details": details_kitchen,
                           "wait_number": order.id}

        context_bar = {"details": details_bar,
                       "wait_number": order.id}

    save_as_kitchen = f"meallist_kitchen_{order.id}_{str(uuid4().int)}"

    save_as_bar = f"meallist_bar_{order.id}_{str(uuid4().int)}"

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    def master_printer():

        # Print to kitchen
        kitchen_templating(context=context_kitchen,
                           temp_file=kitchen_temp,
                           save_as=save_as_kitchen,
                           printer=data.get('kitchen').get('printer'))

        # Print to bar
        bar_templating(context=context_bar,
                       temp_file=bar_temp,
                       save_as=save_as_bar,
                       printer=data.get('bar').get('printer'))

    # Start the thread
    th = Thread(target=master_printer)
    th.start()

    # Marked as printed
    if not order.mealPrinted:

        order.mealPrinted = True
        db.session.commit()

    flash(f"订单{order.id}的菜品正在打印，请耐心等待.如菜品未打印，\
            请确认打印机是否处于打开状态及正确配置.", category='success')

    return redirect(url_for('view_meallists'))


@app.route("/view/meallist/<string:timestamp>")
@login_required
def view_meallist(timestamp):

    # Filtering alacarte unpaid orders and the targeted table
    unpaid_alacarte_orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False).all()

    cur_unpaid_alacarte_orders = [order for order in unpaid_alacarte_orders if
                                  order.timeCreated.date() == today]

    paid_out_orders = db.session.query(Order).filter(
        Order.type == "Out",
        Order.isPaid == True).all()

    cur_paid_out_orders = [order for order in paid_out_orders if
                           order.timeCreated.date() == today]

    out_meals = [{str(datetime.timestamp(order.timeCreated)):
                      {"items": json.loads(order.items), "order_id": order.id}}
                 for order in cur_paid_out_orders]

    alacarte_meals = [patch for order in
                      cur_unpaid_alacarte_orders for patch in json.loads(order.dishes)]

    meals = out_meals + alacarte_meals

    print(meals)

    meal = [meal.get(timestamp) for meal in meals if meal.get(timestamp)][0]

    print(meal)

    order = Order.query.get_or_404(int(meal.get('order_id')))

    context = dict(meals=meals,
                   meal=meal,
                   timeOrdered=datetime.fromtimestamp(float(timestamp)).strftime(datetime_format),
                   ordered_items=meal.get('items'),
                   referrer=request.headers.get('Referer'),
                   order=order,
                   title=u"查看菜品",
                   datetime_format=datetime_format,
                   timestamp=timestamp,
                   company_name=company_info.get('company_name'),
                   formatter=formatter)

    return render_template('view_meallist.html', **context)


@app.route("/view/printing/receipts")
@login_required
def view_printing_receipts():

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).all()

    cur_orders = [order for order in orders if
                  order.timeCreated.date() == today]

    context = dict(open_orders=cur_orders,
                   referrer=request.headers.get('Referer'),
                   title=u"发票打印",
                   datetime_format=datetime_format,
                   company_name=company_info.get('company_name'))

    return render_template("view_receipts.html", **context)


@app.route('/print/receipt/<int:order_id>')
@login_required
def print_receipt(order_id):

    order = Order.query.get_or_404(int(order_id))

    if not order.isPaid:

        flash(f"打印失败，请先为订单{order.id}结账，再打印发票。", category='success')

        return redirect(url_for('view_printing_receipts'))

    dishes = json.loads(order.items)

    table_name = order.table_name

    total_price = order.totalPrice

    tax_rate = None

    if order.type == "In":

        tax_rate = tax_rate_in

    else:

        tax_rate = tax_rate_out

    context = {"details": dishes,
               "company_name": company_info.get('company_name', ''),
               "address": company_info.get('address'),
               "now": format_datetime(datetime.now(), locale="de_DE"),
               "tax_id": company_info.get('tax_id'),
               "order_id": order.id,
               "table_name": table_name,
               "total": formatter(total_price),
               "pay_via": json.loads(order.pay_via).get('method', ""),
               "VAT": formatter(
                   round((total_price / tax_rate) * tax_rate, 2))}

    temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'receipt_temp_inhouse.docx')
    save_as = f"receipt_{order.id}"

    with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    printer = data.get('receipt').get('printer')

    def master_printer():

        receipt_templating(context=context,
                           temp_file=temp_file,
                           save_as=save_as,
                           printer=printer)

    th = Thread(target=master_printer)

    th.start()

    flash(f"订单{order.id}的发票正在打印，请耐心等待.如未打印，\
                请确认打印机是否处于打开状态及正确配置.", category='success')

    return redirect(url_for('view_printing_receipts'))


@app.route('/view/receipt/<int:order_id>')
@login_required
def view_receipt(order_id):

    order = Order.query.get_or_404(int(order_id))

    ordered_items = json.loads(order.items)

    total = round(order.totalPrice, 2)

    vat = None

    if order.type == "In":

        vat = (order.endTotal / (1 + tax_rate_in)) * tax_rate_in

    else:

        vat = (order.endTotal / (1 + tax_rate_out)) * tax_rate_out

    context = dict(order=order,
                   ordered_items=ordered_items,
                   referrer=request.headers.get('Referer'),
                   title=u"查看发票",
                   datetime_format=datetime_format,
                   company_name=company_info.get('company_name'),
                   total=formatter(total),
                   end_total=formatter(order.endTotal),
                   vat=formatter(round(vat, 2)),
                   formatter=formatter,
                   discount=formatter(order.totalPrice - order.endTotal))

    return render_template("view_receipt.html", **context)


# Printer section for managing, delete and add etc.
@app.route("/printers/manage")
@login_required
def printers_manage():

    with open(str(Path(app.root_path) / "settings" / "printer.json"),
              encoding="utf8") as file:

        data = file.read()

    data = json.loads(data)

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"打印设置",
                   company_name=company_info.get('company_name'),
                   format=datetime_format,
                   data=data)

    return render_template("printer_manage.html", **context)


@app.route("/printers/<string:terminal>/edit", methods=["GET", "POST"])
@login_required
def edit_printer(terminal):

    form = EditPrinterForm()

    with open(str(Path(app.root_path)
                  / "settings"
                  / "printer.json"), encoding="utf8") as file:

        data = file.read()

    data = json.loads(data)

    if request.method == "POST":

        data[terminal]['printer'] = form.printer.data

        # Writing the new settings to the json data file
        with open(str(Path(app.root_path) / "settings" / "printer.json"),
                  mode='w',
                  encoding="utf8") as file:

            json.dump(data, file, indent=2)

        return redirect(url_for('printers_manage'))

    form.printer.data = data.get(terminal).get('printer')
    form.terminal.data = data.get(terminal).get('cn_key')

    context = dict(referrer=request.headers.get('Referer'),
                   title=u"修改打印设置",
                   company_name=company_info.get('company_name'),
                   format=datetime_format,
                   form=form)

    return render_template("edit_printer.html", **context)


@app.route("/printer/switch", methods=["POST"])
def switch_printer():

    # Handle Data From Ajax
    if request.method == "POST":

        data = request.json

        terminal = data.get('terminalName')

        status = data.get('isOn')

        with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
            data = file.read()

        data = json.loads(data)

        data[terminal]['is_on'] = status

        # Writing the new settings to the json data file
        with open(str(Path(app.root_path) / "settings" / "printer.json"), 'w', encoding="utf8") as file:
            json.dump(data, file, indent=2)

        return jsonify({'status': 200})


# Index page for all cuisines
@app.route('/guest/navigation/<string:table_name>/<string:seat_number>')
def guest_navigate(table_name, seat_number):

    info = json_reader(str(Path.cwd() / 'app' / 'settings' / 'config.json'))

    hours = info.get('BUSINESS_HOURS')

    buffet = info.get('BUFFET_MODE').strip()

    is_jp_buffet = None

    if buffet == "jpbuffet":

        is_jp_buffet = True

    elif buffet == "mongo":

        is_jp_buffet = False

    am_start = hours.get('MORNING', '').get('START', '').split(":")
    am_end = hours.get('MORNING', '').get('END', '').split(":")

    pm_start = hours.get('EVENING', '').get('START', '').split(":")
    pm_end = hours.get('EVENING', '').get('END', '').split(":")

    morning_start = time(int(am_start[0]), int(am_start[1]))

    morning_end = time(int(am_end[0]), int(am_end[1]))

    evening_start = time(int(pm_start[0]), int(pm_start[1]))

    evening_end = time(int(pm_end[0]), int(pm_end[1]))

    # Create a visit object from model and record it in db
    visit = Visit(count=1,
                  timeVisited=datetime.now(pytz.timezone('Europe/Berlin')))

    db.session.add(visit)
    db.session.commit()

    # Query Tables
    table = Table.query.filter_by(name=table_name).first_or_404()

    # if table existing and table is on
    if not table or not table.is_on:
        msg = "Diese Tisch steht noch nicht zu Verfuegung. " \
              "Bitte melden Sie sich bei Gast Service"
        return render_template('table404.html', msg=msg)

    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False,
        Order.isCancelled == False,
        Order.table_name == table_name).order_by(Order.timeCreated.desc()).all()

    if len(orders) > 0:

        order = orders[0]

        if order.timeCreated.date() == today:

            batches = json.loads(order.dishes)

            active_seats = []

            for batch in batches:

                last_ordered = list(batch.keys())[0]

                seat = batch.get(last_ordered).get('order_by')

                active_seats.append(seat)

            # If the current seat has already ordered
            if seat_number in active_seats:

                for batch in batches:

                    last_ordered = list(batch.keys())[0]

                    # The guest didn't order buffet
                    if batch.get(last_ordered).get('order_by') == seat_number \
                            and not batch.get(last_ordered).get('subtype'):

                        return redirect(url_for('alacarte_navigate',
                                                table_name=table_name,
                                                seat_number=seat_number))

                    if batch.get(last_ordered).get('order_by') == seat_number \
                            and batch.get(last_ordered).get('subtype') == "jpbuffet":

                        if int(batch.get(last_ordered).get('is_kid')) == 0:

                            return redirect(url_for('jpbuffet_index',
                                                    table_name=table_name,
                                                    seat_number=seat_number,
                                                    is_kid=0,
                                                    ))

                        return redirect(url_for('jpbuffet_index',
                                                    table_name=table_name,
                                                    seat_number=seat_number,
                                                    is_kid=1))

                    elif batch.get(last_ordered).get('order_by') == seat_number \
                            and batch.get(last_ordered).get('subtype') == "mongo":

                        if int(batch.get(last_ordered).get('is_kid')) == 0:

                            return redirect(url_for('mongo_index',
                                                    table_name=table_name,
                                                    seat_number=seat_number,
                                                    is_kid=0))

                        return redirect(url_for('mongo_index',
                                                table_name=table_name,
                                                seat_number=seat_number,
                                                is_kid=1))

    from string import ascii_uppercase

    letters = list(ascii_uppercase)[:8]

    weekday2letter = dict(zip(list(range(1, 7)), letters))

    # Add the index alphabet for Sunday
    weekday2letter[0] = "G"

    cur_week_num = int(datetime.now(tz=pytz.timezone(timezone)).strftime("%w"))

    buffet_price_kid = None

    buffet_price_adult = None

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "buffet_price.json"),
              encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    price_info = data.get(weekday2letter.get(cur_week_num))

    if morning_start <= datetime.now(tz=pytz.timezone(timezone)).time() <= morning_end:

        buffet_price_kid = price_info.get('kid').get('noon')

        buffet_price_adult = price_info.get('adult').get('noon')

    elif evening_start <= datetime.now(tz=pytz.timezone(timezone)).time() <= evening_end:

        buffet_price_kid = price_info.get('kid').get('after')

        buffet_price_adult = price_info.get('adult').get('after')

    if not is_business_hours():

        context = dict(title="Gastnavigation",
                       table_name=table_name,
                       seat_number=seat_number,
                       is_business_hours=is_business_hours(),
                       is_jp_buffet=is_jp_buffet)

        return render_template("guest_index.html", **context)

    context = dict(title="Gastnavigation",
                   table_name=table_name,
                   seat_number=seat_number,
                   buffet_price_kid=formatter(buffet_price_kid),
                   buffet_price_adult=formatter(buffet_price_adult),
                   is_business_hours=is_business_hours(),
                   is_jp_buffet=is_jp_buffet)

    return render_template("guest_index.html", **context)


@app.route('/mongo/index/<string:table_name>/<string:seat_number>/<int:is_kid>')
def mongo_index(table_name, seat_number, is_kid):

    context = dict(title="Startseite - Mongo Buffet",
                   table_name=table_name,
                   seat_number=seat_number,
                   is_kid=is_kid)

    return render_template("mongo_index.html", **context)


#  Mongo Order view by table name and seat number
@app.route("/mongobuffet/interface/<string:table_name>/<string:seat_number>/<int:is_kid>")
def mongo_guest_order(table_name, seat_number, is_kid):

    info = json_reader(str(Path.cwd() / 'app' / 'settings' / 'config.json'))

    hours = info.get('BUSINESS_HOURS')

    am_start = hours.get('MORNING', '').get('START', '').split(":")
    am_end = hours.get('MORNING', '').get('END', '').split(":")

    pm_start = hours.get('EVENING', '').get('START', '').split(":")
    pm_end = hours.get('EVENING', '').get('END', '').split(":")

    morning_start = time(int(am_start[0]), int(am_start[1]))

    morning_end = time(int(am_end[0]), int(am_end[1]))

    evening_start = time(int(pm_start[0]), int(pm_start[1]))

    evening_end = time(int(pm_end[0]), int(pm_end[1]))

    cur_time = datetime.now(tz=pytz.timezone(timezone)).time()

    # if not in business hours: redirect to the navigation page
    if not (morning_start <= cur_time <= morning_end
            or evening_start <= cur_time <= evening_end):

        flash("noch Ausserhalb Geschäftszeiten!",
              category="error")

        return redirect(url_for('guest_navigate',
                                table_name=table_name,
                                seat_number=seat_number))

    # More cond to filter the mongo dishes
    dishes = Food.query.filter(Food.inUse == True,
                               Food.eat_manner == "special").all()

    drinks = Food.query.filter(Food.inUse == True,
                               Food.class_name == "Drinks").all()

    food = list(set(dishes + drinks))

    from string import ascii_uppercase

    letters = list(ascii_uppercase)[:8]

    weekday2letter = dict(zip(list(range(1, 7)), letters))

    # Add the index alphabet for Sunday
    weekday2letter[0] = "G"

    cur_week_num = int(datetime.now(tz=pytz.timezone(timezone)).strftime("%w"))

    buffet_price = None

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "buffet_price.json"),
              encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    price_info = data.get(weekday2letter.get(cur_week_num))

    print(weekday2letter.get(cur_week_num))

    if morning_start <= datetime.now(tz=pytz.timezone(timezone)).time() <= morning_end:

        if is_kid:

            buffet_price = price_info.get('kid').get('noon')

        else:

            buffet_price = price_info.get('adult').get('noon')

    elif evening_start <= datetime.now(tz=pytz.timezone(timezone)).time() <= evening_end:

        if is_kid:

            buffet_price = price_info.get('kid').get('after')
        else:

            buffet_price = price_info.get('adult').get('after')

    details = {
        "mongo_buffet_"+seat_number:
            {'quantity': 1,
             'price': buffet_price,
             'class_name': "Food",
             'order_by': seat_number,
             'is_kid': is_kid}
    }

    # Check if this table is already associated with an open order
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False,
        Order.table_name == table_name).order_by(Order.timeCreated.desc()).all()

    if len(orders) > 0:

        order = orders[0]

        if order.timeCreated.date() != today:

            now = datetime.now(pytz.timezone(timezone))

            cur_max_id = max([order.id for order in Order.query.all()])

            # Create a new order for this table
            order = Order(
                totalPrice=buffet_price,
                endTotal=buffet_price,
                orderNumber=str(uuid4().int),
                items=json.dumps(details),
                timeCreated=now,
                type="In",
                table_name=table_name,
                seat_number=seat_number,
                isCancelled=False,
                dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                              "order_id": cur_max_id + 1,
                                                              "order_by": seat_number,
                                                              "is_kid": is_kid,
                                                              "subtype": "mongo"}}]),
                subtype="mongo")

            db.session.add(order)
            db.session.commit()

        else:

            now = datetime.now(pytz.timezone(timezone))

            cur_items = json.loads(order.items)

            if "mongo_buffet" + seat_number not in cur_items.keys():

                dishes = order.dishes

                if not dishes:

                    dishes = []

                else:

                    dishes = json.loads(order.dishes)

                dishes.append({datetime.timestamp(now): {"items": details,
                                                         "order_id": order.id,
                                                         "order_by": seat_number,
                                                         "is_kid": is_kid,
                                                         "subtype":"mongo"
                                                         }})

                order.dishes = json.dumps(dishes)

                cur_dishes = cur_items.keys()

                for dish, items in details.items():

                    if dish in cur_dishes:

                        # Buffet qty can only be 1
                        cur_items[dish]['quantity'] = 1

                    else:

                        cur_items[dish] = items

                order.items = json.dumps(cur_items)

                order.totalPrice = sum([i[1].get('quantity') * i[1].get('price')
                                        for i in cur_items.items()])

                db.session.commit()

                order.endTotal = order.totalPrice

                db.session.commit()

    else:

        now = datetime.now(pytz.timezone(timezone))

        cur_max_id = max([order.id for order in Order.query.all()])

        # Create a new order for this table
        order = Order(
            totalPrice=buffet_price,
            endTotal=buffet_price,
            orderNumber=str(uuid4().int),
            items=json.dumps(details),
            timeCreated=now,
            type="In",
            table_name=table_name,
            seat_number=seat_number,
            isCancelled=False,
            dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                          "order_id": cur_max_id + 1,
                                                          "order_by": seat_number,
                                                          "is_kid": is_kid,
                                                          "subtype":"mongo"
                                                          }}]),
            subtype="mongo"
        )

        db.session.add(order)
        db.session.commit()

    context = dict(
        title="Mongo Buffet",
        food=food,
        table_name=table_name,
        seat_number=seat_number,
        referrer=request.headers.get('Referer'),
        is_kid=is_kid,
        formatter=formatter)

    return render_template("mongo.html", **context)


@app.route("/mongo/guest/checkout", methods=["POST", "GET"])
def mongo_guest_checkout():

    if request.method == "POST":

        print("Ok")

        # Json Data Posted via AJAX
        json_data = request.json

        table_name = json_data.get('tableName').upper()
        seat_number = json_data.get('seatNumber')

        details = json_data.get('details')

        price_dict = {Food.query.get_or_404(int(i.get('itemId'))).name:
                          Food.query.get_or_404(int(i.get('itemId'))).price_gross
                      for i in details}

        details = {
            Food.query.get_or_404(int(i.get('itemId'))).name:
                {'quantity': int(i.get('itemQuantity')),
                 'price': float(price_dict.get(Food.query.get_or_404(int(i.get('itemId'))).name)),
                 'class_name': Food.query.get_or_404(int(i.get('itemId'))).class_name,
                 'order_by': seat_number}
            for i in details}

        total_price = sum([i[1].get('quantity') * i[1].get('price')
                           for i in details.items()])

        # Check if this table is already associated with an open order
        orders = db.session.query(Order).filter(
            Order.type == "In",
            Order.isPaid == False,
            Order.table_name == table_name).order_by(Order.timeCreated.desc()).all()

        if len(orders) > 0:

            order = orders[0]

            if order.timeCreated.date() != today:

                now = datetime.now(pytz.timezone(timezone))

                cur_max_id = max([order.id for order in Order.query.all()])

                # Create a new order for this table
                order = Order(
                    totalPrice=total_price,
                    endTotal=total_price,
                    orderNumber=str(uuid4().int),
                    items=json.dumps(details),
                    timeCreated=now,
                    type="In",
                    table_name=table_name,
                    seat_number=seat_number,
                    isCancelled=False,
                    dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                                  "order_id": cur_max_id + 1}}]))

                db.session.add(order)
                db.session.commit()

            else:

                now = datetime.now(pytz.timezone(timezone))

                cur_items = json.loads(order.items)

                dishes = order.dishes

                if not dishes:

                    dishes = []

                else:

                    dishes = json.loads(order.dishes)

                dishes.append({datetime.timestamp(now): {"items": details,
                                                         "order_id": order.id}})

                order.dishes = json.dumps(dishes)

                cur_dishes = cur_items.keys()

                for dish, items in details.items():

                    if dish in cur_dishes:

                        cur_items[dish]['quantity'] = cur_items[dish]['quantity'] \
                                                      + items.get('quantity')

                    else:

                        cur_items[dish] = items

                order.items = json.dumps(cur_items)

                order.totalPrice = sum([i[1].get('quantity') * i[1].get('price')
                                        for i in cur_items.items()])

                db.session.commit()

                order.endTotal = order.totalPrice

                db.session.commit()

        else:

            now = datetime.now(pytz.timezone(timezone))

            cur_max_id = max([order.id for order in Order.query.all()])

            # Create a new order for this table
            order = Order(
                totalPrice=total_price,
                endTotal=total_price,
                orderNumber=str(uuid4().int),
                items=json.dumps(details),
                timeCreated=now,
                type="In",
                table_name=table_name,
                seat_number=seat_number,
                isCancelled=False,
                dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                              "order_id": cur_max_id + 1}}])
            )

            db.session.add(order)
            db.session.commit()

        details_kitchen = {key: {'quantity': items.get('quantity'),
                                 'total': items.get('quantity') * items.get('price')}
                           for key, items in details.items() if items.get("class_name") == "Food"}

        details_bar = {key: {'quantity': items.get('quantity'),
                             'total': items.get('quantity') * items.get('price')}
                       for key, items in details.items() if items.get("class_name") == "Drinks"}

        context_kitchen = {"details": details_kitchen,
                           "seat_number": seat_number,
                           "table_name": table_name,
                           "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        kitchen_temp = str(Path(app.root_path) / 'static' / 'docx' / 'kitchen_alacarte.docx')
        save_as_kitchen = f"alacarte_meallist_kitchen_{order.id}_{str(uuid4())}"

        context_bar = {"details": details_bar,
                       "seat_number": seat_number,
                       "table_name": table_name,
                       "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        bar_temp = str(Path(app.root_path) / 'static' / 'docx' / 'bar_alacarte.docx')
        save_as_bar = f"alacarte_meallist_bar_{order.id}_{str(uuid4())}"

        # Read the printer setting data from the json file
        with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
            data = file.read()

        data = json.loads(data)

        def master_printer():

            # Print to kitchen
            kitchen_templating(context=context_kitchen,
                               temp_file=kitchen_temp,
                               save_as=save_as_kitchen,
                               printer=data.get('kitchen').get('printer'))

            # Print to bar
            bar_templating(context=context_bar,
                           temp_file=bar_temp,
                           save_as=save_as_bar,
                           printer=data.get('bar').get('printer'))

        # Start the thread
        th = Thread(target=master_printer)
        th.start()

        return jsonify({"status_code": 200})


@app.route("/jp/buffet/next/order/<string:table_name>/<string:seat_number>",
           methods=["GET", "POST"])
def get_next_round_time(table_name, seat_number):

    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False,
        Order.isCancelled == False,
        Order.subtype == "jpbuffet",
        Order.table_name == table_name).order_by(Order.timeCreated.desc()).all()

    if len(orders) > 0:

        order = orders[0]

        batches = json.loads(order.dishes)

        dt_objs = []

        for batch in batches:

            last_ordered = list(batch.keys())[0]

            dt_obj = datetime.fromtimestamp(float(last_ordered))

            if batch.get(last_ordered).get('order_by') == seat_number \
                    and batch.get(last_ordered).get('subtype') == "jpbuffet":
                dt_objs.append(dt_obj)

        if len(dt_objs) > 0:

            last_ordered = max(dt_objs)

            next_round_time = last_ordered + timedelta(minutes=time_buffer_mins)

            return jsonify({"success": str(next_round_time)})

        return jsonify({"error": "no next round time available"})

    return jsonify({"error": "no data"})


@app.route('/jp/buffet/index/<string:table_name>/<string:seat_number>/<int:is_kid>')
def jpbuffet_index(table_name, seat_number, is_kid):

    context = dict(title="Startseite - Japan Buffet ",
                   table_name=table_name,
                   seat_number=seat_number,
                   is_kid=is_kid)

    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False,
        Order.isCancelled == False,
        Order.subtype == "jpbuffet",
        Order.table_name == table_name).order_by(Order.timeCreated.desc()).all()

    if len(orders) > 0:

        order = orders[0]

        batches = json.loads(order.dishes)

        dt_objs = []

        for batch in batches:

            last_ordered = list(batch.keys())[0]

            dt_obj = datetime.fromtimestamp(float(last_ordered))

            if batch.get(last_ordered).get('order_by') == seat_number \
                    and batch.get(last_ordered).get('subtype') == "jpbuffet":

                dt_objs.append(dt_obj)

        if len(dt_objs) > 0:

            last_ordered = max(dt_objs)

            next_round_time = last_ordered + timedelta(minutes=time_buffer_mins)

            context["next_round_time"] = str(next_round_time)

            time_delta = next_round_time.minute - datetime.now().minute

            context['timedelta'] = time_delta

    return render_template("jp_buffet_index.html", **context)


# Table Order view by table name and seat number
@app.route("/japanbuffet/interface/<string:table_name>/<string:seat_number>/<int:is_kid>")
def jpbuffet_order(table_name, seat_number, is_kid):

    info = json_reader(str(Path.cwd() / 'app' / 'settings' / 'config.json'))

    hours = info.get('BUSINESS_HOURS')

    order_limit = int(info.get('ORDER_LIMIT'))

    am_start = hours.get('MORNING', '').get('START', '').split(":")
    am_end = hours.get('MORNING', '').get('END', '').split(":")

    pm_start = hours.get('EVENING', '').get('START', '').split(":")
    pm_end = hours.get('EVENING', '').get('END', '').split(":")

    morning_start = time(int(am_start[0]), int(am_start[1]))

    morning_end = time(int(am_end[0]), int(am_end[1]))

    evening_start = time(int(pm_start[0]), int(pm_start[1]))

    evening_end = time(int(pm_end[0]), int(pm_end[1]))

    cur_time = datetime.now(tz=pytz.timezone(timezone)).time()

    # if not in business hours: redirect to the navigation page
    if not (morning_start <= cur_time <= morning_end
            or evening_start <= cur_time <= evening_end):
        flash("noch Ausserhalb Geschäftszeiten!",
              category="error")

        return redirect(url_for('guest_navigate',
                                table_name=table_name,
                                seat_number=seat_number))

    # special_dishes = Food.query.filter(Food.inUse == True,
    #                                    Food.eat_manner == "special",
    #                                    Food.class_name == "Food").all()

    jpbuffet_dishes = Food.query.filter(Food.inUse == True,
                                        Food.eat_manner == "jpbuffet",
                                        Food.class_name == "Food").all()

    dishes = jpbuffet_dishes

    categories = set([dish.category for dish in dishes])

    context = dict(title="Japan Buffet",
                   table_name=table_name,
                   seat_number=seat_number,
                   is_kid=is_kid,
                   dishes=dishes,
                   referrer=request.headers.get('Referer'),
                   formatter=formatter,
                   order_limit=order_limit,
                   categories=categories)

    return render_template("jp_buffet.html", **context)


# jpbuffet order by category
@app.route("/japanbuffet/<string:cate>/interface/<string:table_name>/<string:seat_number>/<int:is_kid>")
def jpbuffet_order_by_category(table_name, seat_number, is_kid, cate):

    info = json_reader(str(Path.cwd() / 'app' / 'settings' / 'config.json'))

    hours = info.get('BUSINESS_HOURS')

    order_limit = int(info.get('ORDER_LIMIT'))

    am_start = hours.get('MORNING', '').get('START', '').split(":")
    am_end = hours.get('MORNING', '').get('END', '').split(":")

    pm_start = hours.get('EVENING', '').get('START', '').split(":")
    pm_end = hours.get('EVENING', '').get('END', '').split(":")

    morning_start = time(int(am_start[0]), int(am_start[1]))

    morning_end = time(int(am_end[0]), int(am_end[1]))

    evening_start = time(int(pm_start[0]), int(pm_start[1]))

    evening_end = time(int(pm_end[0]), int(pm_end[1]))

    cur_time = datetime.now(tz=pytz.timezone(timezone)).time()

    # if not in business hours: redirect to the navigation page
    if not (morning_start <= cur_time <= morning_end
            or evening_start <= cur_time <= evening_end):
        flash("noch Ausserhalb Geschäftszeiten!",
              category="error")

        return redirect(url_for('guest_navigate',
                                table_name=table_name,
                                seat_number=seat_number))

    # special_dishes = Food.query.filter(Food.inUse == True,
    #                                    Food.eat_manner == "special",
    #                                    Food.class_name == "Food").all()

    jpbuffet_dishes = Food.query.filter(Food.inUse == True,
                                        Food.eat_manner == "jpbuffet",
                                        Food.class_name == "Food",
                                        Food.category == cate).all()

    dishes = jpbuffet_dishes

    categories = set([dish.category for dish in Food.query.all()
                      if dish.eat_manner == "jpbuffet"])

    context = dict(title="Japan Buffet",
                   table_name=table_name,
                   seat_number=seat_number,
                   is_kid=is_kid,
                   dishes=dishes,
                   referrer=request.headers.get('Referer'),
                   formatter=formatter,
                   order_limit=order_limit,
                   categories=categories)

    return render_template("jp_buffet.html", **context)


# jpbuffet order by category
@app.route("/japanbuffet/special/interface/<string:table_name>/<string:seat_number>/<int:is_kid>")
def jpbuffet_order_special(table_name, seat_number, is_kid):

    info = json_reader(str(Path.cwd() / 'app' / 'settings' / 'config.json'))

    hours = info.get('BUSINESS_HOURS')

    order_limit = int(info.get('ORDER_LIMIT'))

    am_start = hours.get('MORNING', '').get('START', '').split(":")
    am_end = hours.get('MORNING', '').get('END', '').split(":")

    pm_start = hours.get('EVENING', '').get('START', '').split(":")
    pm_end = hours.get('EVENING', '').get('END', '').split(":")

    morning_start = time(int(am_start[0]), int(am_start[1]))

    morning_end = time(int(am_end[0]), int(am_end[1]))

    evening_start = time(int(pm_start[0]), int(pm_start[1]))

    evening_end = time(int(pm_end[0]), int(pm_end[1]))

    cur_time = datetime.now(tz=pytz.timezone(timezone)).time()

    # if not in business hours: redirect to the navigation page
    if not (morning_start <= cur_time <= morning_end
            or evening_start <= cur_time <= evening_end):
        flash("noch Ausserhalb Geschäftszeiten!",
              category="error")

        return redirect(url_for('guest_navigate',
                                table_name=table_name,
                                seat_number=seat_number))

    special_dishes = Food.query.filter(Food.inUse == True,
                                       Food.eat_manner == "special",
                                       Food.class_name == "Food").all()

    dishes = special_dishes

    categories = set([dish.category for dish in Food.query.all()
                      if dish.eat_manner == "jpbuffet"])

    context = dict(title="Japan Buffet",
                   table_name=table_name,
                   seat_number=seat_number,
                   is_kid=is_kid,
                   dishes=dishes,
                   referrer=request.headers.get('Referer'),
                   formatter=formatter,
                   order_limit=order_limit,
                   categories=categories)

    return render_template("jp_buffet_special.html", **context)


@app.route("/jp/buffet/guest/checkout", methods=["POST", "GET"])
def jpbuffet_guest_checkout():

    info = json_reader(str(Path.cwd() / 'app' / 'settings' / 'config.json'))

    hours = info.get('BUSINESS_HOURS')

    time_buffer_mins = int(info.get('BUFFET_TIME_BUFFER'))

    max_rounds = int(info.get('ORDER_TIMES'))

    am_start = hours.get('MORNING', '').get('START', '').split(":")
    am_end = hours.get('MORNING', '').get('END', '').split(":")

    pm_start = hours.get('EVENING', '').get('START', '').split(":")
    pm_end = hours.get('EVENING', '').get('END', '').split(":")

    morning_start = time(int(am_start[0]), int(am_start[1]))

    morning_end = time(int(am_end[0]), int(am_end[1]))

    evening_start = time(int(pm_start[0]), int(pm_start[1]))

    evening_end = time(int(pm_end[0]), int(pm_end[1]))

    from string import ascii_uppercase

    letters = list(ascii_uppercase)[:8]

    weekday2letter = dict(zip(list(range(1, 7)), letters))

    # Add the index alphabet for Sunday
    weekday2letter[0] = "G"

    cur_week_num = int(datetime.now(tz=pytz.timezone(timezone)).strftime("%w"))

    buffet_price = None

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "buffet_price.json"),
              encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    price_info = data.get(weekday2letter.get(cur_week_num))

    if request.method == "POST":

        # Json Data Posted via AJAX
        json_data = request.json

        table_name = json_data.get('tableName').upper()
        seat_number = json_data.get('seatNumber')
        is_kid = int(json_data.get('isKid'))

        print(is_kid)

        buffet_price = None

        if morning_start <= datetime.now(tz=pytz.timezone(timezone)).time() <= morning_end:

            if is_kid:

                buffet_price = price_info.get('kid').get('noon')

            else:

                buffet_price = price_info.get('adult').get('noon')

        elif evening_start <= datetime.now(tz=pytz.timezone(timezone)).time() <= evening_end:

            if is_kid:

                buffet_price = price_info.get('kid').get('after')

            else:

                buffet_price = price_info.get('adult').get('after')

        print(buffet_price)

        total_price = float(json_data.get('totalPrice'))

        details = json_data.get('details')

        price_dict = {Food.query.get_or_404(int(i.get('itemId'))).name:
                          Food.query.get_or_404(int(i.get('itemId'))).price_gross
                      for i in details}

        details = {
            Food.query.get_or_404(int(i.get('itemId'))).name:
                {'quantity': int(i.get('itemQuantity')),
                 'price': float(price_dict.get(Food.query.get_or_404(int(i.get('itemId'))).name)),
                 'class_name': Food.query.get_or_404(int(i.get('itemId'))).class_name,
                 'order_by': seat_number,
                 "subtype": "jpbuffet",
                 "is_kid": is_kid}
            for i in details}

        total_price = sum([i[1].get('quantity') * i[1].get('price') for i in details.items()])

        # Check if this table is already associated with an open order
        orders = db.session.query(Order).filter(
            Order.type == "In",
            Order.isPaid == False,
            Order.table_name == table_name,
            Order.isCancelled == False).order_by(Order.timeCreated.desc()).all()

        if len(orders) > 0:

            order = orders[0]
            # So that this table has no new open orders
            if order.timeCreated.date() != today:

                now = datetime.now(pytz.timezone(timezone))

                cur_max_id = max([order.id for order in Order.query.all()])

                # Create a new order for this table
                order = Order(
                    totalPrice=total_price + buffet_price,
                    endTotal=total_price + buffet_price,
                    orderNumber=str(uuid4().int),
                    items=json.dumps(details),
                    timeCreated=now,
                    type="In",
                    table_name=table_name,
                    seat_number=seat_number,
                    isCancelled=False,
                    dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                                  "order_id": cur_max_id + 1,
                                                                  'order_by': seat_number,
                                                                  "subtype": "jpbuffet",
                                                                  "is_kid": is_kid,
                                                                  "is_drink_or_special": False}}]),
                    subtype="jpbuffet")

                db.session.add(order)
                db.session.commit()

            else:

                now = datetime.now(pytz.timezone(timezone))

                cur_items = json.loads(order.items)

                batches = json.loads(order.dishes)

                # check if the last_ordered time is buffered

                dt_objs = []

                for batch in batches:

                    last_ordered = list(batch.keys())[0]

                    dt_obj = datetime.fromtimestamp(float(last_ordered))

                    if batch.get(last_ordered).get('order_by') == seat_number \
                            and batch.get(last_ordered).get('subtype') == "jpbuffet":

                        dt_objs.append(dt_obj)

                if len(dt_objs) > 0:

                    last_ordered = max(dt_objs)

                    first_time_ordered = min(dt_objs)

                    next_round_time = last_ordered + timedelta(minutes=time_buffer_mins)

                    last_round_time = first_time_ordered + \
                                      timedelta(minutes=time_buffer_mins*max_rounds)

                    now = datetime.now(tz=None)

                    # Over passed the max dining time 150 minutes
                    if now > last_round_time:

                        minutes = time_buffer_mins * max_rounds

                        return jsonify({"error": f"Sie haben schon die maximale Mahlzeiten "
                                                 f"von {minutes} Minuten überschritten"})

                    if now <= next_round_time:

                        time_delta = next_round_time.minute - now.minute

                        # if time_delta > 0:

                        return jsonify({"error": f"Sie müssen leider "
                                                 f"noch {time_delta} Minute bis nächste Runde warten!"})

                buffet_seats = set([tuple(i.items())[0][1].get('order_by') for i in batches
                                if tuple(i.items())[0][1].get('subtype') == "jpbuffet"])

                dishes = order.dishes

                if not dishes:

                    dishes = []

                else:

                    dishes = json.loads(order.dishes)

                dishes.append({datetime.timestamp(now): {"items": details,
                                                         "order_id": order.id,
                                                         "order_by": seat_number,
                                                         "subtype": "jpbuffet",
                                                         "is_kid": is_kid,
                                                         "is_drink_or_special": False}})

                order.dishes = json.dumps(dishes)

                cur_dishes = cur_items.keys()

                for dish, items in details.items():

                    if dish in cur_dishes:

                        cur_items[dish]['quantity'] = cur_items[dish]['quantity'] \
                                                      + items.get('quantity')

                    else:

                        cur_items[dish] = items

                order.items = json.dumps(cur_items)

                if seat_number in buffet_seats:

                    order.totalPrice = len(buffet_seats) * buffet_price + \
                                       sum([i[1].get('quantity') * i[1].get('price') \
                                            for i in cur_items.items()])
                else:

                    order.totalPrice = len(buffet_seats) * buffet_price + \
                                       sum([i[1].get('quantity') * i[1].get('price') \
                                            for i in cur_items.items()]) + buffet_price

                db.session.commit()

                # Reset the end price of an order to be the total price
                order.endTotal = order.totalPrice

                db.session.commit()

        else:

            now = datetime.now(pytz.timezone(timezone))

            cur_max_id = max([order.id for order in Order.query.all()])

            # Create a new order for this table
            order = Order(
                totalPrice=total_price + buffet_price,
                endTotal=total_price + buffet_price,
                orderNumber=str(uuid4().int),
                items=json.dumps(details),
                timeCreated=now,
                type="In",
                table_name=table_name,
                seat_number=seat_number,
                isCancelled=False,
                dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                              "order_id": cur_max_id + 1,
                                                              "order_by": seat_number,
                                                              "is_kid": is_kid,
                                                              "subtype": "jpbuffet",
                                                              "is_drink_or_special": False}}]),
                subtype="jpbuffet"
            )

            db.session.add(order)
            db.session.commit()

        details_kitchen = {key: {'quantity': items.get('quantity'),
                                 'total': items.get('quantity') * items.get('price')}
                           for key, items in details.items() if items.get("class_name") == "Food"}

        details_bar = {key: {'quantity': items.get('quantity'),
                             'total': items.get('quantity') * items.get('price')}
                       for key, items in details.items() if items.get("class_name") == "Drinks"}

        context_kitchen = {"details": details_kitchen,
                           "seat_number": seat_number,
                           "table_name": table_name,
                           "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        kitchen_temp = str(Path(app.root_path) / 'static' / 'docx' / 'kitchen_alacarte.docx')
        save_as_kitchen = f"alacarte_meallist_kitchen_{order.id}_{str(uuid4())}"

        context_bar = {"details": details_bar,
                       "seat_number": seat_number,
                       "table_name": table_name,
                       "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        bar_temp = str(Path(app.root_path) / 'static' / 'docx' / 'bar_alacarte.docx')
        save_as_bar = f"alacarte_meallist_bar_{order.id}_{str(uuid4())}"

        # Read the printer setting data from the json file
        with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
            data = file.read()

        data = json.loads(data)

        def master_printer():

            # Print to kitchen
            kitchen_templating(context=context_kitchen,
                               temp_file=kitchen_temp,
                               save_as=save_as_kitchen,
                               printer=data.get('kitchen').get('printer'))

            # Print to bar
            bar_templating(context=context_bar,
                           temp_file=bar_temp,
                           save_as=save_as_bar,
                           printer=data.get('bar').get('printer'))

        # Start the thread
        th = Thread(target=master_printer)
        th.start()

        return jsonify({"success": "Ihre Bestellung ist an die Küche gesendet!"})


# Guest order drinks
@app.route("/guest/order/drinks/<string:table_name>/<string:seat_number>/<int:is_kid>")
def guest_order_drinks(table_name, seat_number, is_kid):

    all_drinks = Food.query.filter(Food.inUse == True,
                                   Food.class_name == "Drinks").all()

    jpbuffet_drinks = Food.query.filter(Food.inUse == True,
                                        Food.eat_manner == "jpbuffet",
                                        Food.class_name == "Drinks").all()

    dishes = all_drinks + jpbuffet_drinks

    context = dict(title="Japan Buffet",
                   table_name=table_name,
                   seat_number=seat_number,
                   is_kid=is_kid,
                   dishes=dishes,
                   referrer=request.headers.get('Referer'),
                   formatter=formatter)

    return render_template("guest_drinks.html", **context)


@app.route('/guest/drinks/checkout', methods=["POST"])
def guest_drinks_checkout():

    info = json_reader(str(Path.cwd() / 'app' / 'settings' / 'config.json'))

    hours = info.get('BUSINESS_HOURS')

    am_start = hours.get('MORNING', '').get('START', '').split(":")
    am_end = hours.get('MORNING', '').get('END', '').split(":")

    pm_start = hours.get('EVENING', '').get('START', '').split(":")
    pm_end = hours.get('EVENING', '').get('END', '').split(":")

    morning_start = time(int(am_start[0]), int(am_start[1]))

    morning_end = time(int(am_end[0]), int(am_end[1]))

    evening_start = time(int(pm_start[0]), int(pm_start[1]))

    evening_end = time(int(pm_end[0]), int(pm_end[1]))

    from string import ascii_uppercase

    letters = list(ascii_uppercase)[:8]

    weekday2letter = dict(zip(list(range(1, 7)), letters))

    # Add the index alphabet for Sunday
    weekday2letter[0] = "G"

    cur_week_num = int(datetime.now(tz=pytz.timezone(timezone)).strftime("%w"))

    buffet_price = None

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "buffet_price.json"),
              encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    price_info = data.get(weekday2letter.get(cur_week_num))

    if request.method == "POST":

        # Json Data Posted via AJAX
        json_data = request.json

        table_name = json_data.get('tableName').upper()
        seat_number = json_data.get('seatNumber')
        is_kid = int(json_data.get('isKid'))

        print(is_kid)

        buffet_price = None

        if morning_start <= datetime.now(tz=pytz.timezone(timezone)).time() <= morning_end:

            if is_kid:

                buffet_price = price_info.get('kid').get('noon')

            else:

                buffet_price = price_info.get('adult').get('noon')

        elif evening_start <= datetime.now(tz=pytz.timezone(timezone)).time() <= evening_end:

            if is_kid:

                buffet_price = price_info.get('kid').get('after')

            else:

                buffet_price = price_info.get('adult').get('after')

        print(buffet_price)

        total_price = float(json_data.get('totalPrice'))

        details = json_data.get('details')

        price_dict = {Food.query.get_or_404(int(i.get('itemId'))).name:
                          Food.query.get_or_404(int(i.get('itemId'))).price_gross
                      for i in details}

        details = {
            Food.query.get_or_404(int(i.get('itemId'))).name:
                {'quantity': int(i.get('itemQuantity')),
                 'price': float(price_dict.get(Food.query.get_or_404(int(i.get('itemId'))).name)),
                 'class_name': Food.query.get_or_404(int(i.get('itemId'))).class_name,
                 'order_by': seat_number,
                 "subtype": "jpbuffet",
                 "is_kid": is_kid}
            for i in details}

        total_price = sum([i[1].get('quantity') * i[1].get('price') for i in details.items()])

        # Check if this table is already associated with an open order
        orders = db.session.query(Order).filter(
            Order.type == "In",
            Order.isPaid == False,
            Order.table_name == table_name).order_by(Order.timeCreated.desc()).all()

        if len(orders) > 0:

            order = orders[0]
            # So that this table has no new open orders
            if order.timeCreated.date() != today:

                now = datetime.now(pytz.timezone(timezone))

                cur_max_id = max([order.id for order in Order.query.all()])

                # Create a new order for this table
                order = Order(
                    totalPrice=total_price + buffet_price,
                    endTotal=total_price + buffet_price,
                    orderNumber=str(uuid4().int),
                    items=json.dumps(details),
                    timeCreated=now,
                    type="In",
                    table_name=table_name,
                    seat_number=seat_number,
                    isCancelled=False,
                    dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                                  "order_id": cur_max_id + 1,
                                                                  'order_by': seat_number,
                                                                  "subtype": None,
                                                                  "is_kid": is_kid,
                                                                  "is_drink_or_special": True}}]),
                    subtype="jpbuffet")

                db.session.add(order)
                db.session.commit()

            else:

                now = datetime.now(pytz.timezone(timezone))

                cur_items = json.loads(order.items)

                batches = json.loads(order.dishes)

                buffet_seats = set([tuple(i.items())[0][1].get('order_by') for i in batches
                                    if tuple(i.items())[0][1].get('subtype') == "jpbuffet"])

                dishes = order.dishes

                if not dishes:

                    dishes = []

                else:

                    dishes = json.loads(order.dishes)

                dishes.append({datetime.timestamp(now): {"items": details,
                                                         "order_id": order.id,
                                                         "order_by": seat_number,
                                                         "subtype": None,
                                                         "is_kid": is_kid,
                                                         "is_drink_or_special": True}})

                order.dishes = json.dumps(dishes)

                cur_dishes = cur_items.keys()

                for dish, items in details.items():

                    if dish in cur_dishes:

                        cur_items[dish]['quantity'] = cur_items[dish]['quantity'] \
                                                      + items.get('quantity')

                    else:

                        cur_items[dish] = items

                order.items = json.dumps(cur_items)

                if seat_number in buffet_seats:

                    order.totalPrice = len(buffet_seats) * buffet_price + \
                                       sum([i[1].get('quantity') * i[1].get('price') \
                                            for i in cur_items.items()])
                else:

                    order.totalPrice = len(buffet_seats) * buffet_price + \
                                       sum([i[1].get('quantity') * i[1].get('price') \
                                            for i in cur_items.items()]) + buffet_price

                db.session.commit()

                order.endTotal = order.totalPrice

                db.session.commit()

        else:

            now = datetime.now(pytz.timezone(timezone))

            cur_max_id = max([order.id for order in Order.query.all()])

            # Create a new order for this table
            order = Order(
                totalPrice=total_price + buffet_price,
                endTotal=total_price + buffet_price,
                orderNumber=str(uuid4().int),
                items=json.dumps(details),
                timeCreated=now,
                type="In",
                table_name=table_name,
                seat_number=seat_number,
                isCancelled=False,
                dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                              "order_id": cur_max_id + 1,
                                                              "order_by": seat_number,
                                                              "is_kid": is_kid,
                                                              "subtype": None,
                                                              "is_drink_or_special": True}}]),
                subtype="jpbuffet"
            )

            db.session.add(order)
            db.session.commit()

        details_bar = {key: {'quantity': items.get('quantity'),
                             'total': items.get('quantity') * items.get('price')}
                       for key, items in details.items()
                       if items.get("class_name") == "Drinks"}

        context_bar = {"details": details_bar,
                       "seat_number": seat_number,
                       "table_name": table_name,
                       "now": format_datetime(datetime.now(), locale="de_DE")}

        bar_temp = str(Path(app.root_path) / 'static' / 'docx' / 'bar_alacarte.docx')
        save_as_bar = f"jpbuffet_meallist_bar_{order.id}_{str(uuid4())}"

        # Read the printer setting data from the json file
        with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
            data = file.read()

        data = json.loads(data)

        def master_printer():

            # Print to bar
            bar_templating(context=context_bar,
                           temp_file=bar_temp,
                           save_as=save_as_bar,
                           printer=data.get('bar').get('printer'))

        # Start the thread
        th = Thread(target=master_printer)
        th.start()

        return jsonify({"success": "Ihre Bestellung ist an die Bar gesendet!"})


@app.route("/japanbuffet/special/checkout", methods=["POST"])
def jpbuffet_special_checkout():

    info = json_reader(str(Path.cwd() / 'app' / 'settings' / 'config.json'))

    hours = info.get('BUSINESS_HOURS')

    am_start = hours.get('MORNING', '').get('START', '').split(":")
    am_end = hours.get('MORNING', '').get('END', '').split(":")

    pm_start = hours.get('EVENING', '').get('START', '').split(":")
    pm_end = hours.get('EVENING', '').get('END', '').split(":")

    morning_start = time(int(am_start[0]), int(am_start[1]))

    morning_end = time(int(am_end[0]), int(am_end[1]))

    evening_start = time(int(pm_start[0]), int(pm_start[1]))

    evening_end = time(int(pm_end[0]), int(pm_end[1]))

    from string import ascii_uppercase

    letters = list(ascii_uppercase)[:8]

    weekday2letter = dict(zip(list(range(1, 7)), letters))

    # Add the index alphabet for Sunday
    weekday2letter[0] = "G"

    cur_week_num = int(datetime.now(tz=pytz.timezone(timezone)).strftime("%w"))

    buffet_price = None

    # Read the printer setting data from the json file
    with open(str(Path(app.root_path) / "settings" / "buffet_price.json"),
              encoding="utf8") as file:
        data = file.read()

    data = json.loads(data)

    price_info = data.get(weekday2letter.get(cur_week_num))

    if request.method == "POST":

        # Json Data Posted via AJAX
        json_data = request.json

        table_name = json_data.get('tableName').upper()
        seat_number = json_data.get('seatNumber')
        is_kid = int(json_data.get('isKid'))

        print(is_kid)

        buffet_price = None

        if morning_start <= datetime.now(tz=pytz.timezone(timezone)).time() <= morning_end:

            if is_kid:

                buffet_price = price_info.get('kid').get('noon')

            else:

                buffet_price = price_info.get('adult').get('noon')

        elif evening_start <= datetime.now(tz=pytz.timezone(timezone)).time() <= evening_end:

            if is_kid:

                buffet_price = price_info.get('kid').get('after')

            else:

                buffet_price = price_info.get('adult').get('after')

        print(buffet_price)

        total_price = float(json_data.get('totalPrice'))

        details = json_data.get('details')

        price_dict = {Food.query.get_or_404(int(i.get('itemId'))).name:
                          Food.query.get_or_404(int(i.get('itemId'))).price_gross
                      for i in details}

        details = {
            Food.query.get_or_404(int(i.get('itemId'))).name:
                {'quantity': int(i.get('itemQuantity')),
                 'price': float(price_dict.get(Food.query.get_or_404(int(i.get('itemId'))).name)),
                 'class_name': Food.query.get_or_404(int(i.get('itemId'))).class_name,
                 'order_by': seat_number,
                 "subtype": "jpbuffet",
                 "is_kid": is_kid}
            for i in details}

        total_price = sum([i[1].get('quantity') * i[1].get('price') for i in details.items()])

        # Check if this table is already associated with an open order
        orders = db.session.query(Order).filter(
            Order.type == "In",
            Order.isPaid == False,
            Order.table_name == table_name).order_by(Order.timeCreated.desc()).all()

        if len(orders) > 0:

            order = orders[0]
            # So that this table has no new open orders
            if order.timeCreated.date() != today:

                now = datetime.now(pytz.timezone(timezone))

                cur_max_id = max([order.id for order in Order.query.all()])

                # Create a new order for this table
                order = Order(
                    totalPrice=total_price + buffet_price,
                    endTotal=total_price + buffet_price,
                    orderNumber=str(uuid4().int),
                    items=json.dumps(details),
                    timeCreated=now,
                    type="In",
                    table_name=table_name,
                    seat_number=seat_number,
                    isCancelled=False,
                    dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                                  "order_id": cur_max_id + 1,
                                                                  'order_by': seat_number,
                                                                  "subtype": None,
                                                                  "is_kid": is_kid,
                                                                  "is_drink_or_special": True}}]),
                    subtype="jpbuffet")

                db.session.add(order)
                db.session.commit()

            else:

                now = datetime.now(pytz.timezone(timezone))

                cur_items = json.loads(order.items)

                batches = json.loads(order.dishes)

                buffet_seats = set([tuple(i.items())[0][1].get('order_by') for i in batches
                                    if tuple(i.items())[0][1].get('subtype') == "jpbuffet"])

                dishes = order.dishes

                if not dishes:

                    dishes = []

                else:

                    dishes = json.loads(order.dishes)

                dishes.append({datetime.timestamp(now): {"items": details,
                                                         "order_id": order.id,
                                                         "order_by": seat_number,
                                                         "subtype": None,
                                                         "is_kid": is_kid,
                                                         "is_drink_or_special": True}})

                order.dishes = json.dumps(dishes)

                cur_dishes = cur_items.keys()

                for dish, items in details.items():

                    if dish in cur_dishes:

                        cur_items[dish]['quantity'] = cur_items[dish]['quantity'] \
                                                      + items.get('quantity')

                    else:

                        cur_items[dish] = items

                order.items = json.dumps(cur_items)

                if seat_number in buffet_seats:

                    order.totalPrice = len(buffet_seats) * buffet_price + \
                                       sum([i[1].get('quantity') * i[1].get('price') \
                                            for i in cur_items.items()])
                else:

                    order.totalPrice = len(buffet_seats) * buffet_price + \
                                       sum([i[1].get('quantity') * i[1].get('price') \
                                            for i in cur_items.items()]) + buffet_price

                db.session.commit()

                order.endTotal = order.totalPrice

                db.session.commit()

        else:

            now = datetime.now(pytz.timezone(timezone))

            cur_max_id = max([order.id for order in Order.query.all()])

            # Create a new order for this table
            order = Order(
                totalPrice=total_price + buffet_price,
                endTotal=total_price + buffet_price,
                orderNumber=str(uuid4().int),
                items=json.dumps(details),
                timeCreated=now,
                type="In",
                table_name=table_name,
                seat_number=seat_number,
                isCancelled=False,
                dishes=json.dumps([{datetime.timestamp(now): {"items": details,
                                                              "order_id": cur_max_id + 1,
                                                              "order_by": seat_number,
                                                              "is_kid": is_kid,
                                                              "subtype": None,
                                                              "is_drink_or_special": True}}]),
                subtype="jpbuffet"
            )

            db.session.add(order)
            db.session.commit()

        details_kitchen = {key: {'quantity': items.get('quantity'),
                             'total': items.get('quantity') * items.get('price')}
                       for key, items in details.items()
                       if items.get("class_name") == "Food"}

        context_kitchen = {"details": details_kitchen,
                       "seat_number": seat_number,
                       "table_name": table_name,
                       "now": format_datetime(datetime.now(), locale="de_DE")}

        kitchen_temp = str(Path(app.root_path) / 'static' / 'docx' / 'kitchen_alacarte.docx')

        save_as_kitchen = f"jpbuffet_meallist_kitchen_{order.id}_{str(uuid4())}"

        # Read the printer setting data from the json file
        with open(str(Path(app.root_path) / "settings" / "printer.json"), encoding="utf8") as file:
            data = file.read()

        data = json.loads(data)

        def master_printer():

            # Print to bar
            kitchen_templating(context=context_kitchen,
                               temp_file=kitchen_temp,
                               save_as=save_as_kitchen,
                               printer=data.get('kitchen').get('printer'))

        # Start the thread
        th = Thread(target=master_printer)
        th.start()

        return jsonify({"success": "Ihre Bestellung ist an die Kueche gesendet!"})



