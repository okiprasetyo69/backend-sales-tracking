import re
import os
import json
import pandas as pd
import sys
import pickle
import requests

from flask import Blueprint, jsonify, request, current_app, make_response, send_file
from flask_jwt import jwt_required, current_identity
from werkzeug.utils import secure_filename
from datetime import datetime, date
from ast import literal_eval

from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file
from rest.controllers import CustomerController, ApprovalController, UserController, AreaController, VisitController, CisangkanController, DeliveryController, EmployeeController

from rest.models import UserModel

__author__ = 'iswan'

bp = Blueprint(__name__, "cisangkan")


def __init__(self):
    self.user_model = UserModel()


def invalid_message():
    response = {
        'error': 1,
        'message': 'invalid credential',
        'data': []
    }
    return jsonify(response)

@bp.route('/cisangkan/retrackImageFromDB', methods=["GET"])
# @jwt_required
def test_function():
    cc = CisangkanController()    
    input = {}

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")
    
    successed = 0
    # set max range at 2000 or count yourself
    for i in range(1, 3000, 1):
        summaries = cc.get_visit_plan_summary_by_id(i)
        if(summaries):
            summary = summaries[0]
            saveImgToPath = False

            input["visit_images"] = json.loads(summary["visit_images"])
            visit_image = input["visit_images"][0]
            if(visit_image["image"].__len__() > 255):
                saveImgToPath = True

            if(saveImgToPath):
                input["id"] = i
                input["notes"] = summary["notes"]
                input["username"] = summary["create_by"]
                input["plan_id"] = summary["plan_id"]
                input["customer_code"] = summary["customer_code"]

                input["have_competitor"] = summary["have_competitor"]
                competitors = []
                if(input["have_competitor"] == 1):
                    competitors = json.loads(summary["competitor_images"])
                input["competitor_images"] = competitors
                input["create_by"] = summary["create_by"]
                input["category_visit"] = None
                input["create_date"] = summary["create_date"]

                cc.saveImageToPath2(input)
                input.pop("username")
                input.pop("create_date")

                updates = cc.update_summary_plan(input)
                if(updates):
                    successed += 1

    response = {}
    response['error'] = 0
    response['successed'] = successed

    return jsonify(response)


@bp.route('/cisangkan/mycustomer', methods=["GET"])
# @jwt_required
def mycustomer():
    response = {
        'error': 0,
        'message': 'my customer',
        'data': []
    }
    return jsonify(response)


@bp.route('/cisangkan/mycustomer/last_insert_today', methods=["POST"])
def get_last_customer_inserted_today():
    cc = CisangkanController()
    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("parameters incorrect", 500, 1, data=[])

    response = {
            'error': 1,
            'message': '',
            'data': []
        }
    
    user_id = request_data["username_code"]

    try:
        result = cc.get_last_mycustomer_inserted_today(user_id)
        obj = {}
        if result :
            obj['count'] = result[0]["last"]

        response = {
            'error': 0,
            'message': 'last customer inserted by {}'.format(str(user_id)),
            'data': obj
        }
    except:
        raise BadRequest("some error on server", 500, 1, data=[])

    return jsonify(response)


@bp.route('/cisangkan/mycustomer/summary', methods=["POST"])
# @jwt_required
def mycustomer_summary():
    cc = CisangkanController()
    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("parameters incorrect", 500, 1, data=[])

    try:
        username = request_data["username_code"]
        result = cc.get_total_mycustomer(username)
        
        response = {
            'error': 0,
            'message': 'my customer',
            'data': result
        }
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])
    return jsonify(response)


@bp.route('/cisangkan/mycustomer/search', methods=["POST"])
# @jwt_required
def mycustomer_searched():
    cc = CisangkanController()
    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("parameters incorrect", 500, 1, data=[])

    try:
        username_id = request_data["username_id"]
        search = request_data["search"]
        result = cc.get_searched_mycustomer(username_id, search)

        response = {
            'error': 0,
            'message': 'my customer',
            'data': result
        }
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])
    return jsonify(response)

@bp.route('/cisangkan/mycustomer/searchonly', methods=["POST"])
# @jwt_required
def mycustomer_searched_only():
    cc = CisangkanController()
    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("parameters incorrect", 500, 1, data=[])

    try:
        username_id = request_data["username_id"]
        search = request_data["search"]
        result = cc.get_searched_mycustomer_only(username_id, search)

        response = {
            'error': 0,
            'message': 'my customer',
            'data': result
        }
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])
    return jsonify(response)    


@bp.route('/cisangkan/customer/<customer_id>', methods=["GET"])
# @jwt_required
def customer_get(customer_id):
    cc = CisangkanController()
    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("parameters incorrect", 500, 1, data=[])

    try:
        customer_controller = CustomerController()
        result = customer_controller.get_customer_by_id(customer_id)
        response = {
            "prefix": "customer",
            "data_id": customer_id,
            # "type": "",
            "data": {
                "code": customer_id,
                "name": result['name'],
                "email": result['email'],
                "phone": result['phone'],
                "address": result['address'],
                "lng": result['lng'],
                "lat": result['lat'],
                # "username": result['username'],
                # "password": result['password'],
                # "nfcid": result['code'],
                # "contacts": result['contacts'],
                # "business_activity": result['business_activity'],
                "is_branch": result['is_branch'],
                "parent_code": result['parent_code']
            }
        }
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])
    return jsonify(response)

@bp.route('/cisangkan/mycustomer', methods=["PUT"])
#@jwt_required
def customer_update():
    cc = CisangkanController()
    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("Params is missing or error format, check double quotation", 500, 1, data=[])

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    try:
        customer_controller = CustomerController()
        update_data = request.get_json(silent=True)
        customer_id = update_data['code']
        update_data.pop('username')
        update_data.pop('api_key')

        result = customer_controller.update_customer(update_data, customer_id)

        response['error'] = 0
        response['message'] = 'Success update customer'
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])

    return jsonify(response)

@bp.route('/cisangkan/delivery_plan/<id>', methods=["PUT"])
#@jwt_required
def delivery_plan_update(id):
    cc = CisangkanController()
    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    strc = '"lat": ' + request_data["lat"] + ', "lng": ' + request_data["lat"] + ','

    d_data = {
        "delivery_id" : id,
        "str_coordinate": strc
    }

    try:
        result = cc.update_coordinate_delivery_plan(d_data)
        response = {
            "error": 0,
            "message": "success update delivery plan coordinates"
        }
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])
    return jsonify(response)

@bp.route('/cisangkan/update/user/customer', methods=["POST"])
def update_customers_sales():
    cc = CisangkanController()
    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    username = request_data["username_code"]
    customer_id = request_data["customer_id"]

    try:
        result = cc.update_customers_sales(username, customer_id)
        response = {
            "error": 1,
            "message": "customer exist",
            "data" : None
        }
        if(result == 1):
            response = {
                "error": 0,
                "message": "update customers user success",
                "data" : "ok"
            } 

    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])
    
    return jsonify(response)

@bp.route('/cisangkan/delete/customer', methods=["POST"])
# @jwt_required()
def delete_customer():
    cc = CisangkanController()
    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    username_id = request_data["username_id"]
    customer_id = request_data["customer_id"]

    try:
        result = cc.delete_customers_sales(username_id, customer_id)
        response = {
            "error": 1,
            "message": "wrong credential",
            "data" : None
        }
        
        if(result == 1):   
            data = "ok"
            response = {
                "error": 0,
                "message": "success delete customer",
                "data" : []
            } 

    except Exception as e:
        raise BadRequest(e, 500, 1, data=response)

    return jsonify(response)

@bp.route('/cisangkan/mycustomer', methods=['POST'])
# @jwt_required()
def create_mycustomer():
    
    cc = CisangkanController()

    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    customer_code = request_data['code']
    user_id = request_data['username_code']
    
    input = cc.sterilize_input(request_data)

    customer_controller = CustomerController()

    if customer_controller.check_customer_by_code(customer_code, None):
        raise BadRequest("exist", 422, 1, data=[])

    # approval by apps or superadmin
    input['is_approval'] = True
    input['approval_by'] = user_id

    response = {
        'error' : 1
    }

    customer = cc.create_mycustomer(input, user_id)

    if customer:
        response['error'] = 0
        response['message'] = 'Success create customer'
        response['data'] = []
    else:
        raise BadRequest('Failed create customer', 500, 1, data=[])

    return jsonify(response)    


@bp.route('/cisangkan/visit/plan/summary/update', methods=['PUT'])
# @jwt_required()
def update_visit_plan_summary_cisangkan():
    cc = CisangkanController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    try:
        update_data = request.get_json(silent=True)
        if(not cc.request_credential(update_data)): return invalid_message()
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])
    
    input = cc.sterilize_input(update_data)
    user_id = input["username"]
    input.pop("username")

    visit_controller = VisitController()
    summary_exist = visit_controller.check_visit_plan_summary(input["plan_id"], input["customer_code"])

    if summary_exist:
        summary_exist = summary_exist[0]
        input['id'] = summary_exist['id']

        visit_plan = cc.update_summary_plan(input)
    else:
        visit_plan = cc.create_summary_plan(input, user_id)

    if visit_plan:
        response['error'] = 0
        response['message'] = 'Success create or update visit plan summary'
    else:
        raise BadRequest('Failed create or update visit plan summary', 500, 1, data=[])

    return jsonify(response)


@bp.route('/cisangkan/visit/plan/summary/update_split_img', methods=['PUT'])
#@jwt_required()
def update_visit_plan_summary_cisangkan_split_img():
    cc = CisangkanController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    try:
        update_data = request.get_json(silent=True)
        if(not cc.request_credential(update_data)): return invalid_message()
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    # print("update_data : ",update_data)

    isLogistic = (1 if update_data.get('isLogistic') else None)
    isCollector = (1 if update_data.get('isCollector') else None)
    # print("isLogistic : ", isLogistic, " | isCollector : ", isCollector)
    input = cc.sterilize_input(update_data)

    input["isLogistic"] = isLogistic
    input["isCollector"]= isCollector
    
    # print("input_convert 0 : ", input)

    input_convert = cc.saveImageToPath(input)

    user_id = input_convert["username"]
    input_convert.pop("username")

    input_data = cc.sterilize_input_div(input_convert)

    visit_controller = VisitController()
    summary_exist = visit_controller.check_visit_plan_summary(input_data["plan_id"], input_data["customer_code"])

    if summary_exist:
        summary_exist = summary_exist[0]
        input_data['id'] = summary_exist['id']

        visit_plan = cc.update_summary_plan(input_data)
        msg = 'success update visit plan summary'
    else:
        visit_plan = cc.create_summary_plan(input_data, user_id)
        msg = 'success create visit plan summary'

    if visit_plan:
        response['error'] = 0
        response['message'] = msg
    else:
        raise BadRequest('Failed create or update visit plan summary', 500, 1, data=[])

    return jsonify(response)


@bp.route('/cisangkan/visit/plan/summary/collector', methods=['PUT'])
# @jwt_required()
def update_visit_plan_summary_cisangkan_collector():
    cc = CisangkanController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    try:
        update_data = request.get_json(silent=True)
        if(not cc.request_credential(update_data)): return invalid_message()
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    isLogistic = (1 if update_data.get('isLogistic') else None)
    isCollector = (1 if update_data.get('isCollector') else None)
    input = cc.sterilize_input(update_data)
    input["isLogistic"] = isLogistic
    input["isCollector"]= isCollector
    input_convert = cc.saveImageToPath(input)
    user_id = input_convert["username"]
    input_convert.pop("username")
    input_data = cc.sterilize_input_div(input_convert)
    visit_controller = VisitController()
    summary_exist = visit_controller.check_visit_plan_summary(input_data["plan_id"], input_data["customer_code"])

    if summary_exist:
        summary_exist = summary_exist[0]
        input_data['id'] = summary_exist['id']
        visit_plan = cc.update_summary_plan(input_data)
        msg = 'success update visit plan summary'
    else:
        visit_plan = cc.create_summary_plan_collector(input_data, user_id)
        msg = 'success create visit plan summary'

    if visit_plan:
        response['error'] = 0
        response['message'] = msg
    else:
        raise BadRequest('Failed create or update visit plan summary', 500, 1, data=[])

    return jsonify(response)


@bp.route('/cisangkan/visit/plan/<int:plan_id>/summary/<string:customer_code>', methods=["GET"])
@jwt_required()
def get_visit_plan_summary_split_img(plan_id, customer_code):
    visit_controller = VisitController()
    user_id = current_identity.id
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    cc = CisangkanController()
    visit_plan_summary = visit_controller.get_visit_plan_summary(plan_id=plan_id, customer_code=customer_code)
    output = cc.loadImageFromPath(visit_plan_summary)
    response['error'] = 0
    response['data'] = output
    return jsonify(response)


@bp.route('/cisangkan/delivery/plan/<int:plan_id>/summary/<string:customer_code>', methods=['PUT'])
@jwt_required()
def update_delivery_plan_summary_split_image(plan_id, customer_code):
    cc = CisangkanController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    try:
        update_data = request.get_json(silent=True)
        if(not cc.request_credential(update_data)): return invalid_message()
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    input = cc.sterilize_input(update_data)
    input["isLogistic"] = 1
    input_data = cc.saveImageToPath(input)
    user_id = input["username"]
    input.pop("username")
    input.pop("isLogistic")

    delivery_controller = DeliveryController()
    summary_exist = delivery_controller.check_delivery_plan_summary(plan_id, customer_code)

    if summary_exist:
        summary_exist = summary_exist[0]
        update_data['id'] = summary_exist['id']
        update_data['plan_id'] = plan_id
        update_data['customer_code'] = customer_code
        delivery_plan = delivery_controller.update_summary_plan(update_data)
    else:
        update_data['plan_id'] = plan_id
        update_data['customer_code'] = customer_code
        delivery_plan = delivery_controller.create_summary_plan(update_data, user_id)

    if delivery_plan:
        response['error'] = 0
        response['message'] = 'Success create or update delivery plan summary'
    else:
        raise BadRequest('Failed create or update delivery plan summary', 500, 1, data=[])

    return jsonify(response)

@bp.route('/cisangkan/delivery/plan/<int:plan_id>/summary/<string:customer_code>', methods=["GET"])
@jwt_required()
def get_delivery_plan_summary_split_img(plan_id, customer_code):
    delivery_controller = DeliveryController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    delivery_plan_summary = delivery_controller.get_delivery_plan_summary(plan_id=plan_id, customer_code=customer_code)
    output = cc.loadImageFromPath(delivery_plan_summary)
    response['error'] = 0
    response['data'] = delivery_plan_summary

    return jsonify(response)    

@bp.route('/cisangkan/packingslip/import/external', methods=['POST'])
def import_external_customer_file():
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    cisangkan_controller = CisangkanController()
    result = cisangkan_controller.import_packing_slip_file_csv()
    if result:
        response['error'] = 0
        response['message'] = 'Success Import Customer from external file'
    else:
        response['error'] = 1
        response['message'] = 'Failed Import Customer from external file'

    return jsonify(response)    

@bp.route('/testjointables', methods=['POST'])
def test_custom_join_tables():
    cc = CisangkanController()
    try:
        request_data = request.get_json(silent=True)
        if(not cc.request_credential(request_data)): return invalid_message()
    except:
        raise BadRequest("parameters incorrect", 500, 1, data=[])

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    try:
        user_id = request_data["user_id"]
        result = cc.socketCheckCollector(user_id)
        
        response = {
            'error': 0,
            'message': 'check socket',
            'data': result
        }
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])

    return jsonify(response)


@bp.route('/visit_summary/<job>/category', methods=['GET'])
@jwt_required()
def get_visit_category_by_job_function(job):
    today = date.today()
    now = datetime.now()
    start_date = today.strftime("%Y-%m-%d %H:%M:%S")
    end_date = now.strftime("%Y-%m-%d %H:%M:%S")

    user_ids = json.loads(request.args.get('user_id'))
    if not user_ids:
        raise BadRequest('Please input minimal one id user', 422, 1, data=[])
    if request.args.get('start_date'):
        start_date = request.args.get('start_date') + " 00:00:00"
    if request.args.get('end_date'):
        end_date = request.args.get('end_date') + " 23:59:59"

    # print("start : ", start_date, ", end : ", end_date)

    cc = CisangkanController()
    result = None
    if(job == 'sales'):
        try:
            result = cc.get_visit_category_sales(user_ids, start_date, end_date)
        except:
            raise BadRequest("parameters incorrect", 500, 1, data=[])
    if(job == 'collector'):
        try:
            result = cc.get_collect_method_collector(start_date, end_date)
        except:
            raise BadRequest("parameters incorrect", 500, 1, data=[])

    response = {
        'error': 0,
        'message': 'success',
        'data': result
    }

    return jsonify(response)

@bp.route('/user/total_online/export', methods=["GET"])

def export_user_total_online():
    cisangkan_controller = CisangkanController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    page = 1
    limit = 100000
    search = None
    column = None
    direction = None
    data_filter = None
    result = cisangkan_controller.get_export_total_online_user(page=page, limit=limit)   
    filename = "Report_Total_Online.xlsx"
    response = make_response(send_file(result['file'], add_etags=False))
    
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response

@bp.route('/user/total_start/export', methods=["GET"])

def export_user_total_start():
    cisangkan_controller = CisangkanController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    page = 1
    limit = 100000
    search = None
    column = None
    direction = None
    data_filter = None
    
    result = cisangkan_controller.get_export_total_start_user(page=page, limit=limit)   
    filename = "Report_Total_Start.xlsx"
    response = make_response(send_file(result['file'], add_etags=False))
    
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response

@bp.route('/user/total_stop/export', methods=["GET"])

def export_user_total_stop():
    cisangkan_controller = CisangkanController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    page = 1
    limit = 100000
    search = None
    column = None
    direction = None
    data_filter = None
    
    result = cisangkan_controller.get_export_total_stop_user(page=page, limit=limit)   
    filename = "Report_Total_Stop.xlsx"
    response = make_response(send_file(result['file'], add_etags=False))
    
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response

@bp.route('/user/total_check_in/export', methods=["GET"])

def export_total_checkin():
    cisangkan_controller = CisangkanController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    page = 1
    limit = 100000
    search = None
    column = None
    direction = None
    data_filter = None
    
    result = cisangkan_controller.get_export_total_check_in_user(page=page, limit=limit)   
    filename = "Report_Total_Check_In.xlsx"
    response = make_response(send_file(result['file'], add_etags=False))
    
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response

@bp.route('/report/<report_types>/export', methods=["GET"])

def export_report_type_user(report_types):
    
    #Ex API_URL : API_URL/report/total_online/export?start_date=2020-01-01&end_date=2020-10-31
    #Total Check In : PI_URL/report/total_check_in/export?start_date=2021-02-24
    cisangkan_controller = CisangkanController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    page = 1
    limit = 100000
    search = None
    column = None
    direction = None
    data_filter = None
    
    date = datetime.now()
    date_now = date.strftime("%y/%m/%d")
    start_date = request.args.get('start_date', default = date_now , type = str)
    end_date = request.args.get('end_date', default = date_now, type = str)
    
    if start_date == None or end_date == None :
        return response('Please Insert start date and end date', 422, 1, data=[])
        
    if report_types == 'total_online' :
        result = cisangkan_controller.get_export_total_online_user(page=page, limit=limit, start_date=start_date, end_date=end_date)   
        filename = "Report_Total_Online.xlsx"
    elif report_types == 'total_start' :
        result = cisangkan_controller.get_export_total_start_user(page=page, limit=limit,start_date=start_date, end_date=end_date)   
        filename = "Report_Total_Start.xlsx"
    elif report_types == 'total_stop' :
        result = cisangkan_controller.get_export_total_stop_user(page=page, limit=limit,start_date=start_date, end_date=end_date)   
        filename = "Report_Total_Stop.xlsx"
    elif report_types == 'total_check_in' :
        result = cisangkan_controller.get_export_total_check_in_user(page=page, limit=limit,start_date=start_date)   
        filename = "Report_Total_Check_In.xlsx"
    else :
        raise BadRequest('Please check type report', 422, 1, data=[])
    
    response = make_response(send_file(result['file'], add_etags=False))
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Acc-ess-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response

@bp.route('/report/absences/export', methods=["GET"])
def export_absence_users():
    cisangkan_controller = CisangkanController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    page = 1
    limit = 100000
    search = None
    column = None
    direction = None
    data_filter = None
    
    date = datetime.now()
    date_now = date.strftime("%y/%m/%d")
    start_date = request.args.get('start_date', default = date_now , type = str)
    end_date = request.args.get('end_date', default = date_now, type = str)
    
    result = cisangkan_controller.get_report_absence_users(page=page, limit=limit, start_date=start_date, end_date=end_date)   
    filename = "Report_Absence_Users.xlsx"
    
    response = make_response(send_file(result['file'], add_etags=False))
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Acc-ess-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response

@bp.route('/absence/user', methods=["GET"])

def get_all_absence_daily():
    # Ex : http://127.0.0.1:7091/absence/user?page=1&limit=10&search=Dedy&order_direction=asc&order_by_column=username&start_date=2021-02-24
    
    cisangkan_controller = CisangkanController()
    #cisangkan_privilege = current_identity.cisangkan_privilege
    response = {
        'error': 1,
        'message': '',
        'data': []
    } 
    
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    search = None
    column = None
    direction = None
    dropdown = False
    
    date = datetime.now()
    date_now = date.strftime("%y/%m/%d")
    start_date = request.args.get('start_date', default = date_now , type = str)
    
    if request.args.get('search'):
        search = request.args.get('search') 
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('dropdown'):
        dropdown = True
    
    absences = cisangkan_controller.get_absence_daily_user(page=page, limit=limit, search=search, column=column, direction=direction, dropdown=dropdown, start_date=start_date)
    
    response['error'] = 0
    response['data'] = absences

    return jsonify(response)
    
