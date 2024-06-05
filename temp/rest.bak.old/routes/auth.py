import json
import base64
import io
import codecs
import os

from flask import Blueprint, current_app, jsonify, request, make_response, send_file, render_template
from flask_jwt import jwt_required, current_identity
from werkzeug.local import LocalProxy
from flask_mail import Message

from rest.exceptions import BadRequest
from rest.helpers import fcm, socketio, USERS_NOTIF, mail
from rest.controllers import UserController, EmployeeController, SalesController, SalesActivityController, \
    LogisticActivityController, SalesController, SettingController, BranchesController, DivisionController
# from rest.sockets.notif import USERS_NOTIF
bp = Blueprint(__name__, 'auth')
_jwt = LocalProxy(lambda: current_app.extensions['jwt'])


@bp.route("/auth", methods=['POST'])
def auth():
    """
    :example:
        curl -i -x POST -F "username=username_user" -F "password=password_user" 'http://localhost:7091/auth'
    :param:
        :form: username: string
        :form: password: string
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": 'success',
            "data": {
                "name":
                "user_id":
                "email":
                "username":
                "jwt_access_token":
            }
        }
    """
    user_controller = UserController()
    employee_controller = EmployeeController()

    try:
        request_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    username = request_data["username"]
    password = request_data["password"]

    if request_data.get('type'):
        tipe_login = request_data['type']
    else:
        tipe_login = 'mobile'

    field_validator = []
    # TODO: Validate Username and Password
    if not username:
        error = dict()
        error['field'] = 'username'
        error['messages'] = 'Username is missing'
        field_validator.append(error)
    if not password:
        error = dict()
        error['field'] = 'password'
        error['messages'] = 'Password is missing'
        field_validator.append(error)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    username = username.lower()

    if username != 'slsdata' and username != 'adm0001' and username != 'slsdatajkt' and username != 'admbnd':
        if user_controller.check_user_is_login(username, tipe_login):
            raise BadRequest("User is already login in another device", 422, 1, data=[])

    user = user_controller.get_user_data_login(username)
    # employee = employee_controller.get_employee_by_id(user['employee_id'])
    # print(user)
    # TODO: Set Jwt Token
    identity = _jwt.authentication_callback(username, password)

    if identity:
        jwt_access_token = _jwt.jwt_encode_callback(identity)
        jwt_access_token = jwt_access_token.decode("utf8")
        # mobile_privilege = None
        # if user['employee']['job_function'] == 'supervisor' or user['employee']['job_function'] == 'manager':
        #     mobile_privilege = 'manager'
        # elif user['employee']['job_function'] == 'driver' or user['employee']['job_function'] == 'crew':
        #     mobile_privilege = 'logistic'
        # elif user['employee']['job_function'] == 'sales':
        #     mobile_privilege = 'sales'
        data_username = user['username']
        data_user_id = user['id']
        data_name = user['employee']['name']
        data_email = user['email']
        if user['employee'].get('nip'):
            data_nip = user['employee']['nip']
        else:
            data_nip = None
        if user['mobile_no'].get('device_code'):
            data_phone = user['mobile_no']['device_code']
        else:
            data_phone = None
        data_branch = user['branch']
        data_division = user['division']
        data_permissions = user['permissions']
        data_jwt_access_token = jwt_access_token
        if user['employee'].get('job_function'):
            if user['employee']['job_function'] == 'driver' or user['employee']['job_function'] == 'crew':
                data_mobile_privilege = 'logistic'
            else:
                data_mobile_privilege = user['employee']['job_function']
        else:
            data_mobile_privilege = None
        data_setting = user['setting']
        if data_user_id == 1:
            branch_controller = BranchesController()
            data_branch_privilege_id = branch_controller.get_list_all_branch_id()

            division_controller = DivisionController()
            data_division_privilege_id = division_controller.get_list_all_division_id()
        else:
            data_branch_privilege_id = user['branch_privilege_id']
            data_division_privilege_id = user['division_privilege_id']
        data_is_supervisor_sales = user['employee']['is_supervisor_sales']
        data_is_supervisor_logistic = user['employee']['is_supervisor_logistic']
        data_is_collector_only = user['employee']['is_collector_only']
        data_is_can_collect = user['employee']['is_can_collect']
        response = {
            "error": 0,
            "message": 'success',
            "data": {
                "id": data_user_id,
                "username": data_username,
                "name": data_name,
                "email": data_email,
                'nip': data_nip,
                'phone': data_phone,
                'branch': data_branch,
                'division': data_division,
                "permissions": data_permissions,
                "jwt_access_token": data_jwt_access_token,
                "mobile_privilege": data_mobile_privilege,
                "branch_privilege_id": data_branch_privilege_id,
                "division_privilege_id": data_division_privilege_id,
                "is_supervisor_sales": data_is_supervisor_sales,
                "is_supervisor_logistic": data_is_supervisor_logistic,
                "is_collector_only": data_is_collector_only,
                "is_can_collect": data_is_can_collect,
                "setting": data_setting
            }
        }
        res = user_controller.create_login_status(username, tipe_login)
        return jsonify(response)
		
    else:
        raise BadRequest("Wrong username or password", 500, 1, data=[])


@bp.route('/auth/<username>', methods=["GET"])
@jwt_required()
def get_all_user_login_status(username):
    """
    Get List all area
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/area"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    user_controller = UserController()
    user_id = current_identity.id
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    user = user_controller.get_user_login_data(username=username)

    response['error'] = 0
    response['data'] = user

    return jsonify(response)


@bp.route('/auth/<username>/<type_login>/delete', methods=["DELETE"])
@jwt_required()
def delete_user_login_status(username, type_login):
    """
    Get List all area
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/area"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    user_controller = UserController()
    user_id = current_identity.id
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    result = user_controller.delete_user_login(username=username, tipe_login=type_login)
    if result == 0:
        response['error'] = 0
        response['message'] = 'Success delete user login'
    else:
        response['error'] = 1
        response['message'] = 'Failed delete user login'

    return jsonify(response)


@bp.route('/auth/all/delete', methods=["POST"])
def delete_all_user_login_status():
    """
    Get List all area
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/area"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    user_controller = UserController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    result = user_controller.delete_all_user_login()
    if result == 0:
        response['error'] = 0
        response['message'] = 'Success delete all user login'
    else:
        response['error'] = 1
        response['message'] = 'Failed delete all user login'

    return jsonify(response)


@bp.route("/logout", methods=['POST'])
@jwt_required()
def logout():
    """
    :example:
        curl -i -x POST -F "username=username_user" -F "password=password_user" 'http://localhost:7091/auth'
    :param:
        :form: username: string
        :form: password: string
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": 'success',
            "data": {
                "name":
                "user_id":
                "email":
                "username":
                "jwt_access_token":
            }
        }
    """
    user_controller = UserController()
    user_id = current_identity.id
    username = current_identity.username

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    try:
        request_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    if request_data is not None:
        if request_data.get('type'):
            tipe_login = request_data['type']
        else:
            tipe_login = 'mobile'
    else:
        tipe_login = 'mobile'

    result = user_controller.delete_user_login(username, tipe_login)

    if result or result==0:
        if tipe_login == 'mobile':
            res = user_controller.delete_device_token(user_id)
            if res or result==0:
                response['error'] = 0
                response['message'] = 'Success delete user login and delete device token'
            else:
                raise BadRequest('Failed delete device token', 500, 1, data=[])
        else:
            response['error'] = 0
            response['message'] = 'Success delete user login'
    else:
        raise BadRequest('Failed delete user login', 500, 1, data=[])
    return jsonify(response)


@bp.route("/device_token", methods=['POST'])
@jwt_required()
def device_token():
    """
    :example:
        curl -i -x POST 'http://localhost:7091/device_token'
    :param:
        :form: token: string
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": 'success update token',
            "data": {}
        }
    """
    user_controller = UserController()
    user_id = current_identity.id

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    try:
        update_data = request.get_json(silent=True)
        update_data['user_id'] = user_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    result = user_controller.update_device_token(update_data)
    if result:
        response['error'] = 0
        response['message'] = 'Success update device token'
    else:
        raise BadRequest('Failed update device token', 500, 1, data=[])

    return jsonify(response)


@bp.route("/test_fcm", methods=['POST'])
@jwt_required()
def test_fcm():
    """

    """
    response = {
        'error': 0,
        'message': 'sucess send fcm',
        'data': []
    }
    registration_id = 'fy4qzuUZyuI:APA91bGzqOuL9Ubl8_GFcmntP4Lxzr7r4naowtBLtWTdE2GtE3pSV4vUPzC78hG-fXPAzcz2PTkr-GzfgWasL1XMFQ7zkpHxrvxqhzQNY9eY-Q5c35FEUH0YjCnkwobzdAs6Lka79hrJ'
    registration_ids = ['fy4qzuUZyuI:APA91bGzqOuL9Ubl8_GFcmntP4Lxzr7r4naowtBLtWTdE2GtE3pSV4vUPzC78hG-fXPAzcz2PTkr-GzfgWasL1XMFQ7zkpHxrvxqhzQNY9eY-Q5c35FEUH0YjCnkwobzdAs6Lka79hrJ', 'caTg4QoyScc:APA91bF84L1Mjpqo_MkqniKOwtToBre3NoUvfT_F1Ppw59bYxPR4X9gNr4R-2hfzAHS0XLCaoXs1tczz-NPR2YyIrHhkEiFxr9JAF4lS--aQUH-oktyZ1bol_pvKn63nQp3rydmIUMZD']
    message_title = 'ini dari title notif'
    message_body = 'ini body notif'
    data_message = {
         "title": "ini title data!",
         "text": "ini teh text data",
         "type": "break_time",
         "description": 300
    }
    # print(type(registration_ids))
    try:
        # fcm.notify_single_device(
        #     registration_id=registration_id,
        #     message_title=message_title,
        #     message_body=message_body,
        #     data_message=data_message
        # )
        fcm.notify_multiple_devices(
            registration_ids=registration_ids,
            message_title=message_title,
            message_body=message_body,
            data_message=data_message
        )
        # fcm.notify_single_device(
        #     registration_id=registration_id,
        #     data_message=data_message
        # )
    except Exception as e:
        print(e)

    return jsonify(response)


@bp.route('/test/image/<id_image>', methods=["GET"])
def download_test_image(id_image):
    """
    :example:
        curl -i -x PUT
        -H "Authorization:JWT <token>"
        "http://localhost:7091/generate"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success generate"
        }
    """
    sales_controller = SalesController()
    result = sales_controller.test_image(id_image)
    filename = result['filename']
    file = base64.decodebytes(result['file'].encode('ascii'))
    # file = result['file']
    # file = json.dumps(base64.b64encode(result['file']).decode('utf-8'))


    # pdf_file = os.path.join(current_app.config['UPLOAD_FOLDER'] + '/' + str(year), filename)
    # # logo_path = '{}/kota_bandung_logo.png'.format(current_app.config['STATIC_FOLDER'])
    # # watermark_path = '{}/kota_bandung_logo_wm.png'.format(current_app.config['STATIC_FOLDER'])
    # # rendered = render_template('skrd_template.html', logo=logo_path, watermark=watermark_path)
    # # css = ['{}/style.css'.format(current_app.config['STATIC_FOLDER'])]
    # # pdf = pdfkit.from_string(rendered, False, css=css)
    #
    response = make_response(send_file(io.BytesIO(file), add_etags=False, mimetype='image/jpeg'))
    response.headers['Content-Type'] = 'image/jpeg'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/test/oauth', methods=["GET"])
@jwt_required()
def test_oaut_permission():
    """
    :example:
        curl -i -x PUT
        -H "Authorization:JWT <token>"
        "http://localhost:7091/generate"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success generate"
        }
    """
    personal = current_identity.permissions

    return jsonify(personal)


@bp.route('/test/oauth/group', methods=["GET"])
@jwt_required()
def test_oaut_permission_group():
    """
    :example:
        curl -i -x PUT
        -H "Authorization:JWT <token>"
        "http://localhost:7091/generate"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success generate"
        }
    """
    group = current_identity.permissions_group

    return jsonify(group)


@bp.route('/test/emit', methods=["GET"])
def test_emit_nodejs():
    """
    :example:
        curl -i -x PUT
        -H "Authorization:JWT <token>"
        "http://localhost:7091/generate"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success generate"
        }
    """
    user_id = 1
    message = None
    # if user_controller.check_user_by_id(user_id):
    for rec in USERS_NOTIF:
        if rec['user_id'] == user_id:
            rec['total'] += 1
            message = rec

    if message:
        pass
    else:
        USERS_NOTIF.append({
            "user_id": user_id,
            "total": 1,
        })
        message = {
            "user_id": user_id,
            "total": 1,
        }

    response = {
        'error': 0,
        'message': 'sucess test emit',
        'data': USERS_NOTIF
    }
    socketio.emit('notif-{}'.format(user_id), [message], broadcast=True)

    return jsonify(response)


@bp.route('/test/notif', methods=["GET"])
def test_notif_nodejs():
    """
    :example:
        curl -i -x PUT
        -H "Authorization:JWT <token>"
        "http://localhost:7091/generate"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success generate"
        }
    """
    response = {
        'error': 0,
        'message': 'sucess test emit',
        'data': USERS_NOTIF
    }
    return jsonify(response)


@bp.route('/test/email', methods=["GET"])
def test_send_email():
    """
    :example:
        curl -i -x PUT
        -H "Authorization:JWT <token>"
        "http://localhost:7091/generate"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success generate"
        }
    """
    sales_controller = SalesController()
    setting_controller = SettingController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    result = sales_controller.get_sales_payment_mobile_by_id(1)
    random_code = setting_controller.get_print_unique_code()
    # try:
    #     # subject = "TEST EMAIL SENDMAIL"
    #     # msg = Message(
    #     #     subject=subject,
    #     #     recipients=["naftalyunior@gmail.com"]
    #     # )
    #     # msg.body = "testing send mail via python"
    #     # mail.send(msg)
    #     response = {
    #         'error': 0,
    #         'message': 'succes test send mail',
    #         'data': 'succes test send mail'
    #     }
    # except Exception as e:
    #     print(e)
    #     response = {
    #         'error': 1,
    #         'message': 'failed test send mail',
    #         'data': 'failed test send mail'
    #     }
    if result:
        try:
            if result['invoice'] is not None:
                sales_rep = result['user']['employee_name']
                payment_code = result['code']
                payment_date = result['payment_date']
                payment = result['invoice']
                amount_total = result['invoice_amount']
                amount_payment = result['payment_amount']
                amount_diff = amount_total - amount_payment
                unique_code = random_code
                # str_amount_total = "Rp {:,}".format(amount_total)
                # str_amount_payment = "Rp {:,}".format(amount_payment)
                # str_amount_diff = "Rp {:,}".format(amount_diff)

                subject = "PAYMENT INVOICE {0}".format(result['customer_code'])
                msg = Message(
                    subject,
                    recipients=["naftalyunior@gmail.com"]
                )
                msg.html = render_template(
                    'email_template.html', sales_rep=sales_rep, payment_code=payment_code, payment_date=payment_date,
                    payment=payment, amount_total=amount_total, amount_payment=amount_payment, amount_diff=amount_diff,
                    unique_code=unique_code
                )
                mail.send(msg)
                response['error'] = 0
                response['message'] = 'Email Sent'
                response['data'] = result
            else:
                raise BadRequest("Payment don't have detail payment info", 422, 1, data=[])
        except Exception as e:
            print(e)
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest('Payment id not exist', 500, 1, data=[])
    return jsonify(response)


@bp.route('/testlog/<job>/<id_user>/breadcrumb', methods=['POST'])
def breadcrumb_log_test(job, id_user):
    """
    Create new data activity
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/activity/sales"
    :endpoint:
        POST /activity/sales
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    sa_controller = SalesActivityController()
    la_controller = LogisticActivityController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if job == 'sales':
        # TODO: Get Json Data From FE
        try:
            request_data = request.get_json(silent=True)
        except:
            raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

        result = sa_controller.create_breadcrumb(request_data, id_user)

        if result:
            response['error'] = 0
            response['message'] = 'log breadcrumb has been created'
        else:
            raise BadRequest('Failed log breadcrumb', 500, 1, data=[])
    elif job == 'logistic':
        # TODO: Get Json Data From FE
        try:
            request_data = request.get_json(silent=True)
        except:
            raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

        result = la_controller.create_breadcrumb(request_data, id_user)

        if result:
            response['error'] = 0
            response['message'] = 'log breadcrumb has been created'
        else:
            raise BadRequest('Failed log breadcrumb', 500, 1, data=[])

    return jsonify(response)


@bp.context_processor
def utility_processor():
    def format_price(amount):
        return "Rp {:,}".format(amount)
    return dict(format_price=format_price)