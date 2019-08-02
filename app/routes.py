from app import (app, db, render_template,
                 redirect, url_for, request,
                 flash, jsonify, make_response,
                 send_file)

from flask_login import current_user, login_user, login_required, logout_user

from .models import User, Table, Food, Order, Visit


from .forms import (AddDishForm, StoreSettingForm,
                    RegistrationForm, LoginForm,
                    EditDishForm, EditCategoryForm,
                    CheckoutForm, AddTableForm,
                    EditTableForm, ConfirmForm,
                    TableSectionQueryForm, SearchTableForm,
                    DatePickForm, AddUserForm, EditUserForm)


from .utilities import (json_reader, store_picture,
                        generate_qrcode, activity_logger,
                        qrcode2excel)


from .printer import CloudPrint



CLIENT_ID = '24098347452-uojtb9hqnk2v9r5ueeo0f885lafo610u.apps.googleusercontent.com'

access_token = 'ya29.GltXBxONVQyY66i4DdtjalklrVxEEv58uV4Vre_JZJ4yR3ShwhrK2q-5SOh2MJqaEYmf-X8I04DqzRfLcfQAcATclRWwI7ZBBsV4yUtwHrLxtATS2r1ie1iblyOf'
CLIENT_SECRET = 'zVShfIvGSTY0se41gtAUHWp8'


from pathlib import Path
import json
from uuid import uuid4
from datetime import datetime, timedelta
import pytz
import pendulum as pen

# Some global viriables - read from config file.
tax_rate_in = json_reader(str(Path(app.root_path) /
                              'config.json')).get('TAX_RATE').get('Takeaway')

tax_rate_out = json_reader(str(Path(app.root_path) /
                              'config.json')).get('TAX_RATE').get('Inhouse Order')

base_url = "http://81fa9ca8.ngrok.io"

cloudprint = CloudPrint(access_token=access_token,
                        client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET)

timezone = 'Europe/Berlin' ## will be added from store setting page


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

                return redirect(url_for('boss_active_tables'))

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
                return redirect(url_for('boss_active_tables'))

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

    cur_mon = int(today.strftime("%-m"))

    start_cur_month = datetime(cur_year, cur_mon, 1).date()

    mon_range = 31

    cur_mon_dates = [int((start_cur_month + timedelta(days=n)).strftime("%-d")) \
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

        data['last_mon_dates'] = [int((start_last_mon + timedelta(days=n)).strftime("%-d")) \
                                    for n in range(mon_range)]

        data['last_mon_revenue_by_dates'] = [
                sum([order.totalPrice for order in paid_orders if
                     order.timeCreated.date() == start_last_mon + timedelta(days=n)])
                        for n in range(mon_range)]

    else:

        last_mon = 12

        start_last_mon = datetime(cur_year - 1, last_mon, 1).date()

        data['last_mon_dates'] = [int((start_last_mon + timedelta(days=n)).strftime("%-d")) \
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

    monthly_revenue_up_rate=None
    if last_mon_revenue == 0 or None:

        monthly_revenue_up_rate = "100%"

    else:
        monthly_revenue_up_rate = str(round(((cur_mon_revenue - last_mon_revenue) / last_mon_revenue), 2) * 100) + "%"

    foods = Food.query.all()

    order_counts = {food.name:
                        {"counts": sum([json.loads(order.items).get(food.name).get('quantity') \
                         for order in paid_orders \
                         if food.name in json.loads(order.items).keys()]),
                         "Img": food.image,
                         "ID": food.id} for food in foods}

    context = dict(title="Xstar Group",
                   cur_visits=cur_visits,
                   daily_visit_up_rate=daily_visit_up_rate,
                   cur_guests=cur_guests,
                   daily_guests_up_rate=daily_guests_up_rate,
                   cur_revenue=cur_revenue,
                   daily_revenue_up_rate=daily_revenue_up_rate,
                   cur_mon_revenue=cur_mon_revenue,
                   monthly_revenue_up_rate=monthly_revenue_up_rate,
                   order_counts=order_counts)

    return render_template("analytics.html", current_user=current_user, **context)


# Guest Facing Order Interface
@app.route("/takeaway/frontviews")
def food_frontview():

    dishes = Food.query.all()

    for dish in dishes:

        # Rewrite dish's image name
        dish.image = dish.image.split("/")[-1]

    # Commit the changes from the ORM Operation
    db.session.commit()

    categories = list(set([dish.category for dish in dishes]))

    return render_template('foodfrontview.html', dishes=dishes,
                           categories=categories, title='Xstar Bar', tel="+ 49 555555")


@app.route("/takeout/checkout", methods=["POST", "GET"])
def takeaway_checkout():

    if request.method == "POST":

        # Json Data Posted via AJAX
        json_data = request.get_json("details")

        details = json_data.get('details')

        price_dict = {i.get('itemName'): i.get('itemPrice') for i in details}

        food = [i.get('itemName') for i in details]

        unique_food = list(set(food))

        details = {dish: {'quantity': food.count(dish),
                          'price': float(price_dict.get(dish))} for dish in unique_food}

        order = Order(
            totalPrice=json_data.get('totalPrice'),
            orderNumber=str(uuid4().int),
            items=json.dumps(details),
            timeCreated=pen.now(tz="Europe/Berlin"),
            type="Out")

        db.session.add(order)
        db.session.commit()

        flash("Ihre Bestellung war erfolgreich bitte melden Sie sich bei den Kasse! ")

        return redirect(url_for('food_frontview'))

    return redirect(url_for('food_frontview'))


# Complete a takeaway order
app.route("/order/pickup", methods=["POST"])
def pickup_order():


    if request.method == "POST":


        json_data = request.get_json()


        print(json_data)

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



@app.route("/takeaway/order/<string:order_id>/checkout", methods=["POST","GET"])
def checkout_takeaway_admin(order_id):

    form = CheckoutForm()

    order = db.session.query(Order).get_or_404(int(order_id))

    order_items = json.loads(order.items)

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


        # Pay via cash
        if form.cash_submit.data:

            if form.coupon_amount.data:

                order.totalPrice = form.grandtotal.data - form.coupon_amount.data
                pay_via['coupon_amount'] = form.coupon_amount.data
                logging['Total'] = order.totalPrice


            elif form.discount_rate.data:

                order.totalPrice = form.grandtotal.data * form.discount_rate.data
                pay_via['discount_rate'] = form.discount_rate.data
                logging['Total'] = order.totalPrice


            pay_via["method"] = "Cash"

            logging['Pay'] = u'现金'

        # Pay via card
        elif form.card_submit.data:

            if form.coupon_amount.data:

                order.totalPrice = form.grandtotal.data - form.coupon_amount.data
                pay_via['coupon_amount'] = form.coupon_amount.data

                logging['Total'] = order.totalPrice

            elif form.discount_rate.data:

                order.totalPrice = form.grandtotal.data * form.discount_rate.data
                pay_via['discount_rate'] = form.discount_rate.data

                logging['Total'] = order.totalPrice

            pay_via['method'] = "Card"
            logging['Pay'] = u'卡'

        order.isPaid = True

        order.pay_via = json.dumps(pay_via)

        order.type = 'Out'
        logging['Type'] = u'外卖'

        db.session.commit()

        # Writing logs to the csv file
        activity_logger(order_id=order.id,
                        operation_type=u'结账',
                        page_name=u'外卖界面 > 订单结账',
                        descr=f'''结账订单号:{order.id}\n
                        支付方式:{logging.get('Pay')}\n
                        账单金额: {logging.get('Total')}\n
                        订单类型:{logging.get('Type')}\n''',
                        log_time=str(pen.now('Europe/Berlin')),
                        status=u'成功')

        flash(f"已经为订单{order.id}结账")

        return redirect(url_for('takeaway_orders_manage'))

    return render_template('takeaway_checkout_admin.html',
                           order=order,
                           order_items=order_items,
                           prices=prices,
                           form=form)


@app.route("/takeaway_orders/view")
@login_required
def takeaway_orders_manage():

    if not json.loads(current_user.container).get('inUse'):

        return render_template('suspension_error.html')

    orders = Order.query.filter(Order.type == "Out").all()

    # Filtering only orders today based on timezone Berlin
    orders = [order for order in orders if
              order.timeCreated.date() == pen.today(tz="Europe/Berlin").date()]

    # Convert json string to Python objects so that it can be used in Templates
    indexedDict = {order.id: json.loads(order.items) for order in orders}

    return render_template('takeaway_orders_view.html', orders=orders, items=indexedDict)


@app.route("/takeaway/orders/admin")
def takeaway_orders_admin():

    orders = Order.query.filter(Order.type=="Out").all()

    # Filtering only orders today based on timezone Berlin
    open_orders = [order for order in orders if
                    order.timeCreated.date() == pen.today(tz="Europe/Berlin").date()]

    return render_template('takeaway_orders_admin.html', open_orders=open_orders)


@app.route("/takeaway/order/<int:order_id>/edit")
def takeaway_order_edit(order_id):

    order = Order.query.get_or_404(int(order_id))

    ordered_items = json.loads(order.items)

    return render_template('takeaway_order_edit.html',
                           order=order,
                           ordered_items=ordered_items)


# Handling data transmissioned via Ajax
@app.route("/takeaway/order/update", methods=["POST"])
def update_takeaway_order():

    logging = {}

    ## Ajax Data Transmission

    if request.method=="POST":

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
                        log_time=str(pen.now('Europe/Berlin')),
                        status=u'成功')

        return "Ok"



@app.route("/admin/takeaway/orders/all")
@login_required
def all_out_orders():

    # Filter only takeaway orders
    orders = Order.query.filter(Order.type=="Out").all()

    return render_template('all_out_orders.html', title=u'外卖订单', orders=orders)



@app.route('/admin/view/open/alacarte/orders')
@login_required
def admin_view_alacarte_open_orders():

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid==False).all()

    cur_orders = [order for order in orders if
                   order.timeCreated.date() == pen.today(tz="Europe/Berlin").date()]


    items = {order.id: json.loads(order.items) for order in cur_orders}

    containers = {order.id: json.loads(order.container) for order in cur_orders}


    return render_template("admin_view_alalcarte_open_orders.html",
                           open_orders=cur_orders,
                           items=items,
                           containers=containers)


@app.route("/admin/alacarte/order/<int:order_id>/edit")
@login_required
def admin_alacarte_order_edit(order_id):

    order = Order.query.get_or_404(int(order_id))

    ordered_items = json.loads(order.items)

    container = json.loads(order.container)

    referrer = request.headers.get('Referer')

    return render_template('admin_alacarte_order_edit.html',
                           order=order,
                           ordered_items=ordered_items,
                           container=container,
                           referrer=referrer)


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
                        log_time=str(pen.now('Europe/Berlin')),
                        status=u'成功')

        return redirect(url_for('admin_view_alacarte_open_orders'))


@app.route('/admin/alacarte/order/<int:order_id>/cancel', methods=["GET", "POST"])
@login_required
def admin_cancel_alacarte_order(order_id):

    form = ConfirmForm()

    logging = {}

    order = db.session.query(Order).get_or_404(int(order_id))

    if form.validate_on_submit():

        if order:

            container = json.loads(order.container)

            container['isCancelled'] = True

            order.container = json.dumps(container)

            db.session.commit()

            # Writing logs to the csv file
            activity_logger(order_id=order.id,
                            operation_type=u'订单取消',
                            page_name=u'后台界面 > 餐桌情况(未结账)',
                            descr=f'''
                            取消订单号:{order.id}\n
                            桌子编号：{json.loads(order.container).get('table_name')}-{json.loads(order.container).get('seat_number')}\n
                            账单金额: {order.totalPrice}\n
                            订单类型:AlaCarte\n
                            {logging.get('remark')}\n''',
                            log_time=str(pen.now('Europe/Berlin')),
                            status=u'成功')

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
        Order.isPaid==True).all()



    ## ???
    # cur_orders = [order for order in orders if
    #               order.timeCreated.date() == pen.today(tz="Europe/Berlin").date()]


    cur_orders = orders

    items = {order.id: json.loads(order.items) for order in cur_orders}

    containers = {order.id: json.loads(order.container) for order in cur_orders}

    return render_template("admin_view_paid_alacarte_orders.html",
                           open_orders=cur_orders,
                           items=items,
                           containers=containers)


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

    return render_template('takeaway_view_order.html',
                           order=order,
                           ordered_items=ordered_items,
                           prices=prices,
                           referrer=referrer)


@app.route('/takeaway/revenue/current')
@login_required
def takeaway_cur_revenue():

    orders = Order.query.filter_by(type="Out").all()

    # Filtering only orders today based on timezone Berlin and paid orders
    cur_paid_orders = [order for order in orders
                       if order.timeCreated.date() == pen.today(tz="Europe/Berlin").date()
                       and order.isPaid]

    cur_revenue_sum = 0
    for order in cur_paid_orders:

        cur_revenue_sum += order.totalPrice


    cur_revenue_card = 0
    for order in cur_paid_orders:

        try:

            pay_details = json.loads(order.pay_via)
            if pay_details.get('method') == "Card":

                cur_revenue_card += order.totalPrice

        except:
            cur_revenue_card += 0

    cur_revenue_cash = 0
    for order in cur_paid_orders:

        try:

            pay_details = json.loads(order.pay_via)
            if pay_details.get('method') == "Cash":
                cur_revenue_cash += order.totalPrice

        except:
            cur_revenue_cash += 0

    revenues = {"All": cur_revenue_sum,
                'Card': cur_revenue_card,
                'Cash': cur_revenue_cash}

    return render_template('current_out_revenue.html', revenues=revenues)




# Takeaway order status view
@app.route("/status")
def display_status():

    #Filtering only Takeaway orders
    orders = Order.query.filter(Order.type=="Out").all()

    # Filtering only orders today based on timezone Berlin
    orders = [order for order in orders if
              order.timeCreated.date() == pen.today(tz="Europe/Berlin").date()]

    return render_template("takeaway_status.html", title="Bestell Status", orders=orders)




@app.route("/categories/view")
@login_required
def categories_view():

    with open(str(Path(app.root_path) / "categories.json")) as file:

        data = file.read()

    categories = json.loads(data)

    return render_template('allcategories.html',
                           title=u"菜品种类管理",
                           categories=categories)


@app.route("/categories/add", methods=['POST', "GET"])
@login_required
def add_category():

    with open(str(Path(app.root_path) / "categories.json")) as file:

        data = file.read()

    categories = json.loads(data)

    all_classes = list(set([i.get('Class') for i in categories]))

    all_categories = list(set([i.get('Subcategory') for i in categories]))


    from .forms import AddCategoryForm

    form = AddCategoryForm()


    form.name_class .choices.extend([(i, i) for i in all_classes])
    form.name_category.choices.extend([(i, i) for i in all_categories])

    if form.validate_on_submit():

        if not form.new_class.data:

            if form.new_category.data:

                categories.append({
                    'Class': form.name_class.data,
                    'Subcategory':form.new_category.data,
                    'Unit':form.unit_en.data
                })
            else:
                categories.append({
                    'Class': form.name_class.data,
                    'Subcategory': form.name_category.data,
                    'Unit': form.unit_en.data
                })

        else:

            if form.new_category.data:

                categories.append({
                    'Class': form.new_class.data,
                    'Subcategory': form.new_category.data,
                    'Unit': form.unit_en.data
                })
            else:
                categories.append({
                    'Class': form.new_class.data,
                    'Subcategory': form.name_category.data,
                    'Unit': form.unit_en.data
                })


        with open(str(Path(app.root_path) / "categories.json"), 'w') as file:

            json.dump(categories, file, indent=2)


        return redirect(url_for('categories_view'))




    return render_template('add_category.html',
                           title=u"添加菜品种类",
                           form=form)




@app.route("/categories/edit", methods=['POST', "GET"])
@login_required
def edit_category():

    with open(str(Path(app.root_path) / "categories.json")) as file:

        data = file.read()

    categories = json.loads(data)

    all_classes = list(set([i.get('Class') for i in categories]))

    all_categories = list(set([i.get('Subcategory') for i in categories]))


    from .forms import AddCategoryForm

    form = AddCategoryForm()


    form.name_class .choices.extend([(i, i) for i in all_classes])
    form.name_category.choices.extend([(i, i) for i in all_categories])

    if form.validate_on_submit():

        if not form.new_class.data:

            if form.new_category.data:

                categories.append({
                    'Class': form.name_class.data,
                    'Subcategory':form.new_category.data,
                    'Unit': form.unit_en.data
                })
            else:
                categories.append({
                    'Class': form.name_class.data,
                    'Subcategory': form.name_category.data,
                    'Unit': form.unit_en.data
                })

        else:

            if form.new_category.data:

                categories.append({
                    'Class': form.new_class.data,
                    'Subcategory': form.new_category.data,
                    'Unit': form.unit_en.data
                })
            else:
                categories.append({
                    'Class': form.new_class.data,
                    'Subcategory': form.name_category.data,
                    'Unit': form.unit_en.data
                })


        with open(str(Path(app.root_path) / "categories.json"), 'w') as file:

            json.dump(categories, file, indent=2)


        return redirect(url_for('categories_view'))


    return render_template('edit_category.html',
                           title=u"添加菜品种类",
                           form=form)






# All dish view route
@app.route('/alldishes')
@login_required
def all_dishes():

    dishes = Food.query.all()

    return render_template('alldishes.html', dishes=dishes)



# Add Dish
@app.route("/adddish", methods=["GET", "POST"])
@login_required
def add_dish():

    form = AddDishForm()


    with open(str(Path(app.root_path) / "categories.json")) as file:

        data = file.read()

    categories = json.loads(data)



    class_names = list(set([i.get("Class") for i in categories]))
    sub_categories = list(set([i.get("Subcategory") for i in categories]))


    # Extend new  labels and values to form class_name and category
    form.class_name.choices.extend([(i, i) for i in class_names])
    form.category.choices.extend([(i, i) for i in sub_categories])


    if request.method == "POST" and form.validate_on_submit():

        name = form.name.data
        class_name = form.class_name.data
        category = form.category.data
        description = form.description.data
        price = form.price.data
        eat_manner = form.eat_manner.data

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
                    class_name=class_name)

        db.session.add(dish)
        db.session.commit()

        flash(f"添加新菜品: {name}成功!")

        return redirect(url_for('all_dishes'))


    return render_template("adddish.html",
                           title=u"添加菜品",
                           form=form)



#Remove a dish
@app.route('/dish/<int:dish_id>/remove', methods=["GET", "POST"])
@login_required
def remove_dish(dish_id):


    food = Food.query.get_or_404(dish_id)

    db.session.delete(food)
    db.session.commit()

    flash(f"菜品{food.name}被删除!")

    return redirect(url_for("all_dishes"))




# Edit Dish
@app.route('/dish/<int:dish_id>/edit', methods=["GET", "POST"])
@login_required
def edit_dish(dish_id):

    form = EditDishForm()

    # Loading Json Data from categories.json config file
    with open(str(Path(app.root_path) / "categories.json")) as file:

        data = file.read()

    categories = json.loads(data)

    class_names = list(set([i.get("Class") for i in categories]))
    sub_categories = list(set([i.get("Subcategory") for i in categories]))

    # Extend new  labels and values to form class_name and category
    form.class_name.choices.extend([(i, i) for i in class_names])
    form.category.choices.extend([(i, i) for i in sub_categories])

    dish = db.session.query(Food).get_or_404(int(dish_id))


    if request.method=="POST":


        dish.name = form.name.data
        dish.category = form.category.data
        dish.class_name = form.class_name.data

        dish.price_gross = form.price.data
        dish.price_net_out = dish.price_gross / tax_rate_out
        dish.price_net_in = dish.price_gross / tax_rate_in

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

    return render_template("editdish.html", form=form, image=image_file)



@app.route('/qrcode/manage')
def qrcode_manage():


    tables = Table.query.all()


    table2qr = {table.name: json.loads(table.container).get('qrcodes') \
                for table in tables}

    return render_template('qrcode.html',
                           tables=tables,
                           table2qr=table2qr
                           )




@app.route('/view/qrcode/<string:qrcode_name>')
def view_qrcode(qrcode_name):

    qrcode = f"{qrcode_name}.png"

    table_name = qrcode_name.split('_')[0]

    seat_number = qrcode_name.split('_')[1]

    return render_template('view_qrcode.html',
                           qrcode=qrcode,
                           table_name=table_name,
                           seat_number=seat_number)


@app.route('/qrcode/export/<string:table_name>', methods=["POST", "GET"])
def export_qrcode(table_name):

    file = None
    if table_name.lower().strip() == "all":

        file = qrcode2excel(tables=[table.name for table in Table.query.all()])

    else:

        file = qrcode2excel(tables=[table_name])

    return send_file(file,
                     as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# Store Settings Route
@app.route("/settings", methods=["GET", "POST"])
@login_required
def set_store():

    form = StoreSettingForm()

    if form.validate_on_submit():

        # Transmitting data in the form into the dictionary
        data = {
          "STORE_NAME": form.store_name.data,
          "CITY": form.city.data,
          "STREET": form.street.data,
          "STREET NO.": form.street_no.data,
          "COUNTRY": form.country.data,
          "ZIP": form.zip.data,
          "TAX_ID": form.tax_id.data,
          "TAX_RATE": {"Takeaway": form.tax_rate_takeaway.data,
                       "Inhouse Order": form.tax_rate_InHouse.data}
               },

        with open(str(Path.cwd() / 'app' / 'config.json'), 'w') as f:

            json.dump(data, f, indent=2)

        flash(u"餐馆信息更新成功!")

        return redirect(url_for("set_store"))

    elif request.method == "GET":

        data = json_reader(file=str(Path.cwd() / 'app' / 'config.json'))
        form.store_name.data = data.get("STORE_NAME")
        form.street_no.data = data.get("STREET NO.")
        form.street.data = data.get("STREET")
        form.zip.data = data.get("ZIP")
        form.country.data = data.get('COUNTRY')
        form.city.data = data.get('CITY')
        form.tax_id.data = data.get('TAX_ID')
        form.tax_rate_InHouse.data = data.get("TAX_RATE").get("Inhouse Order")
        form.tax_rate_takeaway.data = data.get("TAX_RATE").get("Takeaway")
        form.logo.data = data.get('LOGO')


    return render_template("settings.html",
                           form=form,
                           title=u'餐馆设置')


@app.route('/admin/users/manage')
@login_required
def users_manage():

    referrer = request.headers.get('Referer')

    if current_user.permissions < 2:

        return render_template('auth_error.html', referrer=referrer)

    # Exclude the current logged in user - You can't delete your self
    users = User.query.filter(User.id != current_user.id,
                              User.permissions <= current_user.permissions).all()

    user2container = {user.id: json.loads(user.container) for user in users
                      if user.container is not None}

    user_in_use = {user.id: json.loads(user.container).get('inUse') for user in users}

    return render_template('users_manage.html',
                           users=users,
                           user2container=user2container,
                           user_in_use=user_in_use)


@app.route('/admin/users/add', methods=["GET", "POST"])
@login_required
def add_user():

    referrer = request.headers.get('Referer')

    form = AddUserForm()

    import string
    letter_string = string.ascii_uppercase
    letters = [letter for letter in letter_string]

    holder = [("Takeaway", u"外卖")]

    holder.extend([(i, i) for i in letters])

    # Instantiate some options for select fields
    form.section.choices.extend(holder)

    if request.method == "POST":

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
                    email=f"{str(uuid4())[:11]}@cnfrien.com")
        # Email attr will be deprecated

        user.set_password(password=password)

        db.session.add(user)

        db.session.commit()

        flash(message=f"已经创建跑堂{user.username}", category="success")

        return redirect(url_for('users_manage'))

    return render_template('add_user.html',
                           referrer=referrer,
                           form=form,
                           title=u"添加跑堂人员")


@app.route("/admin/user/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):

    referrer = request.headers.get('Referer')

    user = db.session.query(User).get_or_404(user_id)

    form = EditUserForm()

    import string
    letter_string = string.ascii_uppercase
    letters = [letter for letter in letter_string]

    holder = [("Takeaway", u"外卖")]

    holder.extend([(i, i) for i in letters])

    # Instantiate some options for select fields
    form.section.choices.extend(holder)

    if request.method=="POST":

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

    section = None
    if json.loads(user.container).get('section'):
        section = ", ".join(json.loads(user.container).get('section'))

    return render_template('edit_user.html',
                           form=form,
                           user=user,
                           referrer=referrer,
                           section=section)


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

    if request.method=="POST":

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
@app.route("/tables/view")
@login_required
def view_tables():

    tables = Table.query.all()

    return render_template("table_views.html",
                           tables=tables,
                           title="桌子管理")


# Admin Dashboard view active tables
@app.route('/admin/active/tables', methods=["POST", "GET"])
def admin_active_tables():

    form = SearchTableForm()

    # Filtering alacarte unpaid orders
    orders = Order.query.filter(
        Order.type == "In",
        Order.isPaid == False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    open_orders = [order for order in orders if
              order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
              not json.loads(order.container).get('isCancelled')]

    # Currently Open Tables
    open_tables = list(set([json.loads(order.container).get("table_name")
                            for order in open_orders]))

    # Extend the choices of current form
    form.select_table.choices.extend([(i, i) for i in open_tables])

    if form.validate_on_submit():

        selected_table = form.select_table.data
        open_tables = [table for table in open_tables if table==selected_table]

        return render_template('admin_active_tables.html',
                               form=form,
                               open_tables=open_tables)

    return render_template('admin_active_tables.html',
                           form=form,
                           open_tables=open_tables)


@app.route('/admin/transfer/table/<string:table_name>', methods=["POST", "GET"])
@login_required
def admin_transfer_table(table_name):

    from .forms import TransferTableForm

    form = TransferTableForm()

    all_tables = Table.query.all()

    # Filtering alacarte unpaid orders
    orders = db.session.query(Order).filter(
        Order.type=="In",
        Order.isPaid==False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    open_orders = [order for order in orders if
                   order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
                   not json.loads(order.container).get('isCancelled')]

    # Currently Open Tables
    open_tables = list(set([json.loads(order.container).get("table_name")
                            for order in open_orders]))

    available_tables = [table for table in all_tables if table.name not in open_tables]

    form.target_table.choices.extend([(table.name, f"{table.name} - {table.number}人") \
                                      for table in available_tables])

    if form.validate_on_submit():

        cur_table_orders = [order for order in open_orders \
                            if json.loads(order.container).get('table_name')==table_name]

        target_table = form.target_table.data

        for order in cur_table_orders:

            logging = {}
            logging['table_before'] = json.loads(order.container).get('table_name')
            logging['table_cur'] = target_table

            container = json.loads(order.container)

            container['table_name'] = target_table

            order.container = json.dumps(container)

            db.session.commit()

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
                            log_time=str(pen.now('Europe/Berlin')))

            flash(f"桌子{table_name}已经转至{target_table}!", category='success')

            return redirect(url_for('admin_active_tables'))

    form.cur_table.data = f"{table_name} - {Table.query.filter_by(name=table_name).first_or_404().number}人"

    return render_template("admin_transfer_table.html", form=form)


# Waiter views a table's aggregated order summary
@app.route("/admin/view/table/<string:table_name>", methods=["GET", "POST"])
def admin_view_table(table_name):

    # Check out form payment methods, discount and coupon code
    form = CheckoutForm()

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False).all()


    open_orders = [order for order in orders if
                   json.loads(order.container).get('table_name')==table_name and
                   order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
                   not json.loads(order.container).get('isCancelled')]
    # Add cond if order not cancelled

    # Check if a checkout button is clicked
    if request.method == "POST":


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

            order.isPaid = True

            order.pay_via = json.dumps(pay_via)

            db.session.commit()

            # Writing logs to the csv file
            activity_logger(order_id=order.id,
                            operation_type=u'结账',
                            page_name=u'跑堂界面 > 桌子详情',
                            descr=f'''结账订单号:{order.id}\n
                                    桌子编号：{json.loads(order.container).get('table_name')}-{json.loads(order.container).get('seat_number')}
                                    支付方式:{logging.get('Pay')}\n
                                    结账金额: {order.totalPrice}\n
                                    订单类型:AlaCarte\n''',
                            log_time=str(pen.now('Europe/Berlin')),
                            status=u'成功')

            return redirect(url_for('admin_active_tables'))

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

            'class_name':Food.query.filter_by(name=dish).first_or_404().class_name,

             } for dish in varieties}

    return render_template('admin_view_table_summary.html',
                           dishes=dishes,
                           table_name=table_name,
                           total_price=total_price,
                           form=form)


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

        return jsonify({'status':200})


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


    if form.validate_on_submit():


        suffix_url = "alacarte/interface"

        qrcodes = [generate_qrcode(table=form.name.data.upper(),
                                   base_url=base_url,
                                   suffix_url=suffix_url,
                                   seat=str(i+1)) for i in range(form.persons.data)]


        table = Table(
            name=form.name.data.upper(),
            number=form.persons.data,
            section=form.section.data,
            timeCreated=pen.now(tz="Europe/Berlin"),
            container=json.dumps({'isCalled': False,
                                  'payCalled': False,
                                  'qrcodes': qrcodes}),

            seats="\n".join([f"{form.name.data.upper()}-{i+1}" for \
                             i in range(form.persons.data)])
        )



        db.session.add(table)

        db.session.commit()

        flash(f"已经成功创建桌子：{form.name.data}")

        return redirect(url_for('view_tables'))


    return render_template("add_table.html",
                           form=form,
                           title="添加桌子")



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

            table.name = form.name.data.upper()
            table.number = form.persons.data
            table.section = form.section.data.upper()

            seats = "\n".join([f"{table.name}-{i+1}" for i in range(form.persons.data)])

            table.seats = seats

            suffix_url = "alacarte/interface"

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

    return render_template("edit_table.html",
                           title="修改桌子",
                           form=form,
                           seats=table.seats)


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


    return render_template("buffet_price_setting.html", title="自助餐价格设置")



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

    dishes = Food.query.all()

    for dish in dishes:

        # Rewrite dish's image name
        dish.image = dish.image.split("/")[-1]

    # Commit the changes from the ORM Operation
    db.session.commit()

    categories = list(set([dish.category for dish in dishes]))

    if table and table.is_on:

        return render_template('alacarte2.html', dishes=dishes,
                               categories=categories, title='Xstar Bar',
                               table_name=table_name,
                               seat_number=seat_number)
    else:

        msg = "Bestellung Service fuer diese Tisch steht noch nicht zu Verfuegung. Bitte melden Sie sich bei Gast Service"
        return render_template('table404.html', msg=msg)



@app.route("/alacarte/guest/checkout", methods=["GET", "POST"])
def alacarte_guest_checkout():

    if request.method == "POST":

        # Json Data Posted via AJAX
        json_data = request.json

        print(json_data)

        table_name = json_data.get('tableName').upper()
        seat_number = json_data.get('seatNumber')

        total_price = float(json_data.get('totalPrice'))

        details = json_data.get('details')

        price_dict = {Food.query.get_or_404(int(i.get('itemId'))).name:
                          Food.query.get_or_404(int(i.get('itemId'))).price_gross
                      for i in details}


        details = {
            Food.query.get_or_404(int(i.get('itemId'))).name:
               {'quantity': int(i.get('itemQuantity')),
                'price': float(price_dict.get(Food.query.get_or_404(int(i.get('itemId'))).name))}
                   for i in details}

        container = {'table_name': table_name,
                     'seat_number': seat_number,
                     'isCancelled': False}


        order = Order(
            totalPrice=total_price,
            orderNumber=str(uuid4().int),
            items=json.dumps(details),
            timeCreated=datetime.now(pytz.timezone("Europe/Berlin")),
            type="In",
            container=json.dumps(container))

        db.session.add(order)
        db.session.commit()

        return jsonify({"status_code": 200})


@app.route('/service/call/<string:table_name>/<string:seat_number>', methods=['GET', 'POST'])
def guest_call_service(table_name, seat_number):

    table = db.session.query(Table).filter_by(name=table_name.upper()).first_or_404()

    container = json.loads(table.container)

    container['isCalled'] = True

    table.container = json.dumps(container)

    db.session.commit()

    import pdfkit

    html = render_template("info_receipt.html",
                           table_name=table_name,
                           seat_number=seat_number)


    pdfkit.from_string(html, str(Path(app.root_path) / "out.pdf"))

    cloudprint.print_file(file=open(str(Path(app.root_path) / "Haijun_Du_CV_ZH.pdf"), "rb"),
                          title="Kellner",
                          printerids="3ab3234a-9392-c9bb-b787-47a8995392b9")

    flash('Ein Herr Ober kommt bald!!')

    return redirect(url_for('alacarte_navigate',
                            table_name=table_name,
                            seat_number=seat_number))



@app.route('/pay/call/<string:table_name>/<string:seat_number>',methods=['GET', 'POST'])
def guest_call_pay(table_name, seat_number):

    table = db.session.query(Table).filter_by(name=table_name.upper()).first_or_404()

    container = json.loads(table.container)

    container['payCalled'] = True

    table.container = json.dumps(container)

    db.session.commit()

    flash('In Ordnung, ein Mitarbeiter kommt bald mit Kasse.')

    return redirect(url_for('alacarte_navigate',
                            table_name=table_name,
                            seat_number=seat_number))


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
        Order.type=="In",
        Order.isPaid==False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin)
    orders = [order for order in orders if
              order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
                   not json.loads(order.container).get('isCancelled')]
    # Order is not cancelled added

    from collections import OrderedDict

    sections = {letter: letter + u"区" for letter in letters}

    # Currently Open Tables
    open_tables = list(set([json.loads(order.container).get("table_name")
                            for order in orders]))

    sections_2_tables = {section: [table
                        for table in Table.query.filter_by(
                        section=section).all()
                        if table.name in open_tables]
                        for section in sections.keys()
                         }

    ordered_sections = OrderedDict(sorted(sections_2_tables.items(), key=lambda t: t[0]))

    section_keys = list(ordered_sections.keys())

    keys2index = {key: section_keys.index(key) for key in section_keys}

    # If form submitted
    if form.validate_on_submit():

        with open(str(Path(app.root_path) / 'table_section.json')) as file:
            data = file.read()

        data = json.loads(data)

        data['START'] = form.start_section.data.upper()
        data['END'] = form.end_section.data.upper()

        # Update Json Data
        with open(str(Path(app.root_path) / 'table_section.json'), 'w') as file:
            json.dump(data, file, indent=2)

        start_index = keys2index.get(form.start_section.data.upper())
        end_index = keys2index.get(form.end_section.data.upper())

        selected_sections = section_keys[start_index: end_index+1]

        return render_template('alacarte_tables_view.html',
                               ordered_sections=ordered_sections,
                               form=form,
                               selected_sections=selected_sections)

    # Read the table config json data
    with open(str(Path(app.root_path) / 'table_section.json')) as file:
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
                           selected_sections=selected_sections)


# Waiter views a table's aggregated order summary
@app.route("/waiter/admin/view/table/<string:table_name>", methods=["GET", "POST"])
def view_table(table_name):

    # Check out form payment methods, discount and coupon code
    form = CheckoutForm()

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False).all()

    open_orders = [order for order in orders if
                   json.loads(order.container).get('table_name')==table_name and
                   order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
                   not json.loads(order.container).get('isCancelled')]

    # Add cond if order not cancelled
    # Check if a checkout button is clicked
    if request.method == "POST":

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

            order.isPaid = True

            order.pay_via = json.dumps(pay_via)

            db.session.commit()

            # Writing logs to the csv file
            activity_logger(order_id=order.id,
                            operation_type=u'结账',
                            page_name=u'跑堂界面 > 桌子详情',
                            descr=f'''结账订单号:{order.id}\n
                                    桌子编号：{json.loads(order.container).get('table_name')}-{json.loads(order.container).get('seat_number')}
                                    支付方式:{logging.get('Pay')}\n
                                    结账金额: {order.totalPrice}\n
                                    订单类型:AlaCarte\n''',
                            log_time=str(datetime.now(pytz.timezone('Europe/Berlin'))),
                            status=u'成功')

            return redirect(url_for('waiter_admin'))

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

    return render_template('view_table_summary.html',
                           dishes=dishes,
                           table_name=table_name,
                           total_price=total_price,
                           form=form)


@app.route("/alacarte/orders/manage")
def alacarte_orders_manage():

    # Filtering alacarte unpaid orders and the targeted table
    orders = db.session.query(Order).filter(
        Order.type == "In").all()

    cur_orders = [order for order in orders if
                   order.timeCreated.date() == pen.today(tz="Europe/Berlin").date()]


    items = {order.id: json.loads(order.items) for order in cur_orders}

    containers = {order.id: json.loads(order.container) for order in cur_orders}

    return render_template("alacarte_orders_admin.html",
                           open_orders=cur_orders,
                           items=items,
                           containers=containers)


@app.route("/alacarte/order/<int:order_id>/edit")
@login_required
def alacarte_order_edit(order_id):

    order = Order.query.get_or_404(int(order_id))

    ordered_items = json.loads(order.items)

    container = json.loads(order.container)

    return render_template('alacarte_order_edit.html',
                           order=order,
                           ordered_items=ordered_items,
                           container=container)


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
                            log_time=str(pen.now('Europe/Berlin')),
                            status=u'成功')

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
        Order.isPaid ==True).all()

    # Filtering only orders which happened the same day.(TZ: Berlin)
    orders = [order for order in orders if
              order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
              not json.loads(order.container).get('isCancelled')]
    # Order is not cancelled added

    # Currently Open Tables
    open_tables = list(set([json.loads(order.container).get("table_name")
                            for order in orders]))

    open_sections = list(set([Table.query.filter_by(name=table).first_or_404().section \
                     for table in open_tables]))

    open_sections.sort()

    return render_template('alacarte_revenue_by_waiter.html',
                           open_sections=open_sections)


@app.route('/revenue/alacarte/<string:section>')
@login_required
def revenue_by_section(section):

    paid_orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid==True).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    cur_paid_orders = [order for order in paid_orders if
                   order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
                   not json.loads(order.container).get('isCancelled')]


    cur_paid_section_orders = [order for order in cur_paid_orders \
                               if Table.query.filter_by(name=json.loads\
                                (order.container).get('table_name')).\
                                first_or_404().section==section]

    revenue = {}
    revenue['total'] = sum([order.totalPrice for order in cur_paid_section_orders])

    revenue['by_card'] = sum([order.totalPrice for order in cur_paid_section_orders if
                                    json.loads(order.pay_via).get('method')=="Card"])

    revenue['by_cash'] = sum([order.totalPrice for order in cur_paid_section_orders if
                                json.loads(order.pay_via).get('method') == "Cash"])

    return render_template('revenue_by_section.html',
                           section=section,
                           revenue=revenue)


@app.route("/tables/alacarte/active", methods=["POST", "GET"])
@login_required
def active_alacarte_tables():

    form = SearchTableForm()

    # Filtering alacarte unpaid orders
    orders = Order.query.filter(
        Order.type == "In",
        Order.isPaid==False).all()

    # Filtering only orders which happened the same day.(TZ: Berlin) + order is not cancelled
    open_orders = [order for order in orders if
              order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
              not json.loads(order.container).get('isCancelled')]


    # Currently Open Tables
    open_tables = list(set([json.loads(order.container).get("table_name")
                            for order in open_orders]))

    # Extend the choices of current form
    form.select_table.choices.extend([(i, i) for i in open_tables])


    if form.validate_on_submit():

        selected_table = form.select_table.data
        open_tables = [table for table in open_tables if table==selected_table]

        return render_template('active_alacarte_tables.html',
                               form=form,
                               open_tables=open_tables)

    return render_template('active_alacarte_tables.html',
                           form=form,
                           open_tables=open_tables)


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
    open_orders = [order for order in orders if
                   order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
                   not json.loads(order.container).get('isCancelled')]

    # Currently Open Tables
    open_tables = list(set([json.loads(order.container).get("table_name")
                            for order in open_orders]))

    available_tables = [table for table in all_tables if table.name not in open_tables]


    form.target_table.choices.extend([(table.name, f"{table.name} - {table.number}人") \
                                      for table in available_tables])

    if form.validate_on_submit():

        cur_table_orders = [order for order in open_orders \
                            if json.loads(order.container).get('table_name')==table_name]

        target_table = form.target_table.data

        for order in cur_table_orders:

            logging = {}
            logging['table_before'] = json.loads(order.container).get('table_name')
            logging['table_cur'] = target_table

            container = json.loads(order.container)

            container['table_name'] = target_table

            order.container = json.dumps(container)

            db.session.commit()

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
                            log_time=str(pen.now('Europe/Berlin')))

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
    orders = [order for order in orders if
              order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
              not json.loads(order.container).get('isCancelled')]

    # Currently Open Tables
    open_tables = list(set([json.loads(order.container).get("table_name")
                            for order in orders]))

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
    orders = [order for order in orders if
              order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
              not json.loads(order.container).get('isCancelled')]

    # Currently Open Tables
    open_tables = list(set([json.loads(order.container).get("table_name")
                            for order in orders]))

    tables = [Table.query.filter_by(name=table).first_or_404() for table in open_tables]

    status = [table.name for table in tables if json.loads(table.container).get('payCalled')]

    return jsonify(status)


@app.route('/view/log')
@login_required
def view_log():

    import pandas as pd

    df = pd.read_csv(str(Path(app.root_path) / 'logging.csv'))

    df['Time'] = pd.to_datetime(df['Time'])

    df.sort_values('Time', ascending=False, inplace=True)

    return render_template('view_log.html', df=df)


@app.route('/revenue/by/days' , methods=["POST", "GET"])
@login_required
def revenue_by_days():

    referrer = request.headers.get('Referer')

    paid_alacarte_orders = Order.query.filter(
        Order.isPaid==True, Order.type=="In").all()

    paid_out_orders = Order.query.filter(
        Order.isPaid==True, Order.type=="Out").all()

    form = DatePickForm()

    alacarte= {"Total": 0,
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
        out_total = sum([order.totalPrice for order \
                      in [order for order in paid_out_orders \
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

        return render_template('revenue_by_days.html',
                               referrer=referrer,
                               alacarte=alacarte,
                               out=out,
                               form=form)

    return render_template('revenue_by_days.html',
                           referrer=referrer,
                           form=form,
                           alacarte=alacarte,
                           out=out)


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

                 {"Total": sum([order.totalPrice for order in paid_orders if\
                            order.timeCreated.date() == start + timedelta(days=n)]),

                  "Total_Cash": sum([order.totalPrice for order in paid_orders if\
                                order.timeCreated.date() == start + timedelta(days=n)\
                                and json.loads(order.pay_via).get('method')=="Cash"]),

                  "Total_Card": sum([order.totalPrice for order in paid_orders if\
                                 order.timeCreated.date() == start + timedelta(days=n)\
                                 and json.loads(order.pay_via).get('method') == "Card"]),
                  } for n in range(7)}

    week2en = {u"星期一": "Monday",
               u"星期二": "Tuesday",
               u"星期三": "Wednesday",
               u"星期四": "Thursday",
               u"星期五": "Friday",
               u"星期六": "Saturday",
               u"星期天": "Sunday"}

    return render_template('revenue_by_week.html',
                           referrer=referrer,
                           weekdays2revenue=weekdays2revenue,
                           week2en=week2en)


@app.route('/revenue/by/month', methods=["POST", "GET"])
@login_required
def revenue_by_month():

    paid_orders = Order.query.filter(Order.isPaid==True).all()

    from calendar import monthrange

    today =datetime.now().date()

    cur_year = int(today.strftime("%Y"))

    cur_mon = int(today.strftime("%-m"))

    start = datetime(cur_year, cur_mon, 1).date()

    cur_mon_range = monthrange(cur_year, cur_mon)[1]

    referrer = request.headers.get('Referer')

    ordered_days2revenue = {

        (start + timedelta(days=n)).strftime("%-d"):

                 {"Total": sum([order.totalPrice for order in paid_orders if\
                            order.timeCreated.date() == start + timedelta(days=n)]),

                  "Total_Cash": sum([order.totalPrice for order in paid_orders if\
                                order.timeCreated.date() == start + timedelta(days=n)\
                                and json.loads(order.pay_via).get('method')=="Cash"]),

                  "Total_Card": sum([order.totalPrice for order in paid_orders if\
                                 order.timeCreated.date() == start + timedelta(days=n)\
                                 and json.loads(order.pay_via).get('method') == "Card"]),
                  } for n in range(cur_mon_range)}

    return render_template('revenue_by_month.html',
                           referrer=referrer,
                           ordered_days2revenue=ordered_days2revenue)


@app.route('/revenue/by/year', methods=["POST", "GET"])
@login_required
def revenue_by_year():

    referrer = request.headers.get('Referer')

    paid_orders = Order.query.filter(Order.isPaid == True).all()

    months2revenue = {

        str(month):

            {"Total": sum([order.totalPrice for order in paid_orders if\
                           order.timeCreated.date().strftime("%-m") == str(month)]),

             "Total_Cash": sum([order.totalPrice for order in paid_orders if \
                                order.timeCreated.date().strftime("%-m") == str(month) \
                                and json.loads(order.pay_via).get('method') == "Cash"]),

             "Total_Card": sum([order.totalPrice for order in paid_orders if \
                                order.timeCreated.date().strftime("%-m") == str(month) \
                                and json.loads(order.pay_via).get('method') == "Card"]),
             } for month in range(1, 13)}

    return render_template('revenue_by_year.html',
                           referrer=referrer,
                           months2revenue=months2revenue)


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
                   order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
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

    cur_orders = [order for order in orders if order.timeCreated.date() == pen.today(tz="Europe/Berlin").date()]

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
                   order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
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

            # Writing log to the csv file
            activity_logger(order_id=order.id,
                            operation_type=u'转台',
                            page_name='老板界面 > 已点餐桌子 > 转台',
                            descr=f'''\n
                            订单号:{order.id}\n
                            原桌子：{logging.get('table_before')}\n
                            新桌子:{logging.get('table_cur')}\n'
                            ''',
                            status=u'成功',
                            log_time=str(pen.now('Europe/Berlin')))

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
                   json.loads(order.container).get('table_name')==table_name and
                   order.timeCreated.date() == pen.today(tz="Europe/Berlin").date() and
                   not json.loads(order.container).get('isCancelled')]
    # Add cond if order not cancelled

    # Check if a checkout button is clicked
    if request.method == "POST":

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

            order.isPaid = True

            order.pay_via = json.dumps(pay_via)

            db.session.commit()

            # Writing logs to the csv file
            activity_logger(order_id=order.id,
                            operation_type=u'结账',
                            page_name=u'老板界面 > 桌子详情',
                            descr=f'''结账订单号:{order.id}\n
                                    桌子编号：{json.loads(order.container).get('table_name')}-{json.loads(order.container).get('seat_number')}
                                    支付方式:{logging.get('Pay')}\n
                                    结账金额: {order.totalPrice}\n
                                    订单类型:AlaCarte\n''',
                            log_time=str(pen.now('Europe/Berlin')),
                            status=u'成功')

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

    return render_template('boss_users_manage.html',
                           users=users,
                           user_in_use=user_in_use)


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

    return render_template('boss_add_user.html',
                           referrer=referrer,
                           form=form,
                           title=u"添加账户")


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

    return render_template('boss_edit_user.html',
                           form=form,
                           user=user,
                           referrer=referrer)


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

    return render_template('boss_update_password.html',
                           referrer=referrer,
                           form=form,
                           user=user)


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
                           form=form)


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

        # Writing logs to the csv file
        activity_logger(order_id=order.id,
                        operation_type=u'订单修改',
                        page_name=u'老板界面 > 餐桌情况(未结账) >订单修改',
                        descr=f'''
                        修改订单号: {order.id}\n
                        桌子编号：{json.loads(order.container).get('table_name')}-{json.loads(order.container).get('seat_number')}\n
                        修改前明细: {logging.get('before')}\n
                        修改后明细: {logging.get('after')}\n
                        修改前账单金额: {logging.get('price_before')}\n
                        修改后账单金额: {logging.get('price_after')}\n
                        订单类型: AlaCarte\n
                        {logging.get('remark', "")}\n''',
                        log_time=str(pen.now('Europe/Berlin')),
                        status=u'成功')

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
