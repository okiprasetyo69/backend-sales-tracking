import re
import os
import json
import pandas as pd

from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity
from werkzeug.utils import secure_filename
from datetime import datetime


from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file
from rest.controllers import VisitEyeController, AreaController

__author__ = 'junior'

bp = Blueprint(__name__, "visiteye")


@bp.route('/visiteye/user', methods=["GET"])
def user_visiteye_all_list():
    """

    :return:
    """
    visiteye_controller = VisitEyeController()

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
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')

    user = visiteye_controller.get_all_user_data(page=page, limit=limit, search=search, column=column, direction=direction)

    response['error'] = 0
    response['data'] = user

    return jsonify(response)


@bp.route('/visiteye/customer', methods=["GET"])
def get_visiteye_all_customer():
    """
    Get List all customer
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/customer"
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
    visiteye_controller = VisitEyeController()
    area_controller = AreaController()

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
    data_filter = None
    result_area = []
    list_area = []
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)
        data_filter = data_filter[0]
    if data_filter:
        if data_filter['area']:
            list_polygon_area = []
            for area_id in data_filter['area']:
                try:
                    polygon_area = area_controller.get_area_by_id(area_id)
                    if polygon_area:
                        # add list area
                        list_area.append(polygon_area)
                        # Construct for polygon area
                        list_markers = []
                        markers = polygon_area['markers']
                        for mark in markers:
                            list_markers.append(str(mark['lat'])+' '+str(mark['lng']))
                        if list_markers:
                            list_markers.append(list_markers[0])
                            list_polygon_area.append("(({0}))".format(", ".join(x for x in list_markers)))
                except Exception as e:
                    pass

            if list_polygon_area:
                try:
                    result_area = visiteye_controller.get_all_customer_by_area(list_polygon_area)
                except Exception as e:
                    pass

        if data_filter['user_id']:
            user_customer = visiteye_controller.get_customer_from_user_id(data_filter['user_id'])
            if user_customer:
                if result_area:
                    result_area = [i for i in result_area if i in user_customer]
                else:
                    result_area = user_customer

    customer = visiteye_controller.get_all_customer_data(
        page=page, limit=limit, search=search, column=column, direction=direction, list_customer=result_area
    )

    response['error'] = 0
    response['data'] = customer

    return jsonify(response)


@bp.route('/visiteye/customer/report', methods=['GET'])
@jwt_required()
def get_all_visiteye_customer_report():
    """
    Get List Sales Invoice
    :return:
    """
    visiteye_controller = VisitEyeController()
    area_controller = AreaController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    search = None
    data_filter = None
    result_area = []
    list_area = []
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)
        data_filter = data_filter[0]
    if data_filter:
        if data_filter['area']:
            list_polygon_area = []
            for area_id in data_filter['area']:
                try:
                    polygon_area = area_controller.get_area_by_id(area_id)
                    if polygon_area:
                        # add list area
                        list_area.append(polygon_area)
                        # Construct for polygon area
                        list_markers = []
                        markers = polygon_area['markers']
                        for mark in markers:
                            list_markers.append(str(mark['lat'])+' '+str(mark['lng']))
                        if list_markers:
                            list_markers.append(list_markers[0])
                            list_polygon_area.append("(({0}))".format(", ".join(x for x in list_markers)))
                except Exception as e:
                    # raise BadRequest(e, 422, 1, data=[])
                    # print(e)
                    pass

            if list_polygon_area:
                try:
                    result_area = visiteye_controller.get_all_customer_by_area(list_polygon_area)
                except Exception as e:
                    raise BadRequest(e, 422, 1, data=[])

        if data_filter['user_id']:
            user_customer = visiteye_controller.get_customer_from_user_id(data_filter['user_id'])
            if user_customer:
                if result_area:
                    result_area = [i for i in result_area if i in user_customer]
                else:
                    result_area = user_customer
    if result_area:
        customer = visiteye_controller.get_all_customer_report(
            list_customer=result_area, data_filter=data_filter, search=search
        )

        if customer:
            if customer['data'] is not None:
                customer['data']['area'] = list_area
        response['error'] = 0
        response['data'] = customer
    else:
        response['error'] = 0
        response['message'] = "No customer in this area"
        response['data'] = []

    return jsonify(response)


@bp.route('/visiteye/customer/<customer_id>', methods=["GET"])
@jwt_required()
def get_visiteye_customer_by_id(customer_id):
    """
    Get customer Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    visiteye_controller = VisitEyeController()
    customer = visiteye_controller.get_customer_by_id(customer_id)

    response['error'] = 0
    response['data'] = customer
    return jsonify(response)


@bp.route('/visiteye/customer/import/external', methods=['POST'])
def import_external_customer_file():
    """
    Customer import excel
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "files:<file>"
        "http://localhost:7091/customer/import"
    :endpoint:
        POST /customer/import
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "Import Success"
        }
    """
    # allowed_extensions = {'xls', 'xlsx'}
    # user_id = current_identity.id
    # sales_customer = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-customers']
    # permissions = sales_customer['rule'][4]
    #
    # if permissions == 10:
    #     if current_identity.permissions_group is not None:
    #         sales_customer = current_identity.permissions_group['setting']['data']['setting-data']['data'][
    #             'setting-data-customers']
    #         permissions = sales_customer['rule'][4]
    #     else:
    #         permissions = 0

    customer_controller = VisitEyeController()
    # table_name = 'customer'
    # today = datetime.today()
    # today = today.strftime("%Y%m%d")

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    result = customer_controller.import_customer_new_format()
    if result:
        response['error'] = 0
        response['message'] = 'Success Import Customer from external file'
    else:
        response['error'] = 1
        response['message'] = 'Failed Import Customer from external file'

    return jsonify(response)
