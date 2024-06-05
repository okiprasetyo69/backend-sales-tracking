import re
import json
import requests

from flask import Blueprint, jsonify, request, current_app, make_response, send_file
from flask_jwt import jwt_required, current_identity

from rest.exceptions import BadRequest
from rest.helpers import Validator
from rest.controllers import SalesActivityController, LogisticActivityController, CisangkanController

__author__ = 'junior'

bp = Blueprint(__name__, "activity")


@bp.route('/activity/<job>', methods=['POST'])
@jwt_required()
def tap_nfc(job):
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
    user_id = current_identity.id
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

        result = sa_controller.create(request_data, user_id)

        if result:
            response['error'] = 0
            response['message'] = 'Log activity has been created'
        else:
            raise BadRequest('Failed log activity', 500, 1, data=[])
    elif job == 'logistic':
        # TODO: Get Json Data From FE
        try:
            request_data = request.get_json(silent=True)
        except:
            raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

        result = la_controller.create(request_data, user_id)

        if result:
            response['error'] = 0
            response['message'] = 'Log activity has been created'
        else:
            raise BadRequest('Failed log activity', 500, 1, data=[])
    else:
        raise BadRequest('Only sales and logistic have activity', 422, 1, data=[])

    return jsonify(response)


@bp.route('/activity/<job>', methods=["GET"])
@jwt_required()
def get_all_activity(job):
    """
    Get List all Activity
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/activity/<job>"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    sa_controller = SalesActivityController()
    la_controller = LogisticActivityController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

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
    if job == 'sales':
        result = sa_controller.get_all_activity_data(
            page=page, limit=limit, search=search, column=column, direction=direction,
            branch_privilege=branch_privilege, division_privilege=division_privilege
        )
    elif job == 'logistic':
        result = la_controller.get_all_activity_data(
            page=page, limit=limit, search=search, column=column, direction=direction,
            branch_privilege=branch_privilege,

        )
    else:
        raise BadRequest('Only sales and logistic have activity', 422, 1, data=[])

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/activity/report/<job>', methods=["GET"])
@jwt_required()
def get_all_activity_report(job):
    """
    Get List all Activity
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/activity/<job>"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    sa_controller = SalesActivityController()
    la_controller = LogisticActivityController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

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
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)
    if job == 'sales':
        result = sa_controller.get_all_activity_data_by_visit_plan(
            page=page, limit=limit, search=search, column=column, direction=direction,
            branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
        )

    elif job == 'collector':
        result = sa_controller.get_all_activity_data_by_visit_plan_collector(
            page=page, limit=limit, search=search, column=column, direction=direction,
            branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
        )

    elif job == 'logistic':
        result = la_controller.get_all_activity_data_by_delivery_plan(
            page=page, limit=limit, search=search, column=column, direction=direction,
            branch_privilege=branch_privilege, data_filter=data_filter
        )
    else:
        raise BadRequest('Only sales and logistic have activity', 422, 1, data=[])

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/activity/report/<job>/export', methods=["GET"])
@jwt_required()
def export_all_activity_report(job):
    """
    Get List all Activity
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/activity/<job>"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    sa_controller = SalesActivityController()
    la_controller = LogisticActivityController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

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
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)
    # 
    # print("job is : ", job)
    # 
    if job == 'sales':
        result = sa_controller.get_all_export_activity_data_by_visit_plan(
            page=page, limit=limit, search=search, column=column, direction=direction,
            branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
        )

    elif job == 'collector':
        result = sa_controller.get_all_export_activity_data_by_visit_plan_collector(
            page=page, limit=limit, search=search, column=column, direction=direction,
            branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
        )        
        
    elif job == 'logistic':
        result = la_controller.get_all_export_activity_data_by_delivery_plan(
            page=page, limit=limit, search=search, column=column, direction=direction,
            branch_privilege=branch_privilege, data_filter=data_filter
        )
    else:
        raise BadRequest('Only sales and logistic have activity', 422, 1, data=[])
    if job == 'sales':
        if data_filter:
            data_filter = data_filter[0]

            # if filter user lebih dari 1
            gabs = []
            if data_filter['user_id']:
                cc = CisangkanController()
                for user in data_filter['user_id']:
                    username = cc.getUsernameById(user)
                    gabs.append(username)

                # print("gabs :", "_".join(gabs))
            #
              
            if data_filter['start_date'] and not data_filter['user_id']:
                filename = 'Report_visit_plan_all_{0}_{1}.xlsx'.format(data_filter['start_date'],
                                                                       data_filter['end_date'])
            elif data_filter['user_id'] and not data_filter['start_date']:
                filename = 'Report_visit_plan_{0}_all.xlsx'.format(data_filter['user_id'])
            else:
                filename = 'Report_visit_plan_{0}_{1}_{2}.xlsx'.format(
                    "_".join(gabs) , data_filter['start_date'], data_filter['end_date']
                )
                # print("filename1 : ", filename)
        else:
            filename = 'Report_visit_plan_all.xlsx'

    elif job == 'logistic':
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date'] and not data_filter['user_id']:
                filename = 'Report_delivery_plan_all_{0}_{1}.xlsx'.format(data_filter['start_date'],
                                                                          data_filter['end_date'])
            elif data_filter['user_id'] and not data_filter['start_date']:
                filename = 'Report_delivery_plan_{0}_all.xlsx'.format(data_filter['user_id'])
            else:
                filename = 'Report_delivery_plan_{0}_{1}_{2}.xlsx'.format(
                    data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
                )
        else:
            filename = 'Report_delivery_plan_all.xlsx'
    else:
        filename = 'Report_plan_all.xlsx'

    # print("filename2 : ", filename)

    response = make_response(send_file(result['file'], add_etags=False))
    
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/activity/report/<job>/export/pdf', methods=["GET"])
@jwt_required()
def export_pdf_all_activity_report(job):
    """
    Get List all Activity
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/activity/<job>"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    sa_controller = SalesActivityController()
    la_controller = LogisticActivityController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = 1
    limit = 10000
    search = None
    column = None
    direction = None
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)
    if job == 'sales':
        result = sa_controller.get_all_export_pdf_activity_data_by_visit_plan(
            page=page, limit=limit, search=search, column=column, direction=direction,
            branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
        )
    elif job == 'logistic':
        result = la_controller.get_all_export_pdf_activity_data_by_delivery_plan(
            page=page, limit=limit, search=search, column=column, direction=direction,
            branch_privilege=branch_privilege, data_filter=data_filter
        )
    else:
        raise BadRequest('Only sales and logistic have activity', 422, 1, data=[])
    if job == 'sales':
        if data_filter:
            filename = 'Report_visit_plan_filter.pdf'
            # data_filter = data_filter[0]
            # if data_filter['start_date'] and not data_filter['user_id']:
            #     filename = 'Report_visit_plan_all_{0}_{1}.pdf'.format(data_filter['start_date'],
            #                                                           data_filter['end_date'])
            # elif data_filter['user_id'] and not data_filter['start_date']:
            #     filename = 'Report_visit_plan_{0}_all.pdf'.format(data_filter['user_id'])
            # else:
            #     filename = 'Report_visit_plan_{0}_{1}_{2}.pdf'.format(
            #         data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
            #     )
        else:
            filename = 'Report_visit_plan_all.pdf'

    elif job == 'collector':
        if data_filter:
            filename = 'Report_visit_plan_collector_filter.pdf'
        else:
            filename = 'Report_visit_plan_collector_all.pdf'

    elif job == 'logistic':
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date'] and not data_filter['user_id']:
                filename = 'Report_delivery_plan_all_{0}_{1}.pdf'.format(data_filter['start_date'],
                                                                         data_filter['end_date'])
            elif data_filter['user_id'] and not data_filter['start_date']:
                filename = 'Report_delivery_plan_{0}_all.pdf'.format(data_filter['user_id'])
            else:
                filename = 'Report_delivery_plan_{0}_{1}_{2}.pdf'.format(
                    data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
                )
        else:
            filename = 'Report_delivery_plan_all.pdf'
    else:
        filename = 'Report_plan_all.pdf'

    response = make_response(result['file'])
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/activity/<job>/break_time', methods=['POST'])
@jwt_required()
def break_time_log(job):
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
    user_id = current_identity.id
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
            request_data['delivery_plan_id'] = None
        except:
            raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

        result = sa_controller.create_break_time(request_data, user_id)

        if result:
            response['error'] = 0
            response['message'] = 'log break time has been created'
        else:
            raise BadRequest('Failed log break time', 500, 1, data=[])
    elif job == 'logistic':
        # TODO: Get Json Data From FE
        try:
            request_data = request.get_json(silent=True)
            request_data['visit_plan_id'] = None
        except:
            raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

        result = la_controller.create_break_time(request_data, user_id)

        if result:
            response['error'] = 0
            response['message'] = 'log break time has been created'
        else:
            raise BadRequest('Failed log break time', 500, 1, data=[])
    else:
        raise BadRequest('Only sales and logistic have activity', 422, 1, data=[])

    return jsonify(response)


@bp.route('/activity/<job>/idle_time', methods=['POST'])
@jwt_required()
def idle_time_log(job):
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
    user_id = current_identity.id
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
            request_data['delivery_plan_id'] = None
        except:
            raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

        result = sa_controller.create_idle_time(request_data, user_id)

        if result:
            response['error'] = 0
            response['message'] = 'log idle time has been created'
        else:
            raise BadRequest('Failed log idle time', 500, 1, data=[])
    elif job == 'logistic':
        # TODO: Get Json Data From FE
        try:
            request_data = request.get_json(silent=True)
            request_data['visit_plan_id'] = None
        except:
            raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

        result = la_controller.create_idle_time(request_data, user_id)

        if result:
            response['error'] = 0
            response['message'] = 'log idle time has been created'
        else:
            raise BadRequest('Failed log idle time', 500, 1, data=[])
    else:
        raise BadRequest('Only sales and logistic have activity', 422, 1, data=[])

    return jsonify(response)


@bp.route('/activity/<job>/breadcrumb', methods=['POST'])
@jwt_required()
def breadcrumb_log(job):
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
    user_id = current_identity.id
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

        result = sa_controller.create_breadcrumb(request_data, user_id)

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

        result = la_controller.create_breadcrumb(request_data, user_id)

        if result:
            response['error'] = 0
            response['message'] = 'log breadcrumb has been created'
        else:
            raise BadRequest('Failed log breadcrumb', 500, 1, data=[])

    return jsonify(response)


@bp.route('/activity/<job>/breadcrumb', methods=['GET'])
@jwt_required()
def breadcrumb_list_log(job):
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
    user_id = current_identity.id
    sa_controller = SalesActivityController()
    la_controller = LogisticActivityController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if job == 'sales':
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))
        plan_id = int(request.args.get('plan_id'))
        search = None
        column = None
        direction = None
        if request.args.get('search'):
            search = request.args.get('search')
        if request.args.get('order_by_column'):
            column = request.args.get('order_by_column')
            direction = request.args.get('order_direction')

        log_breadcrumb = sa_controller.get_all_breadcrumb_data(
            page=page, limit=limit, search=search, column=column, plan_id=plan_id, direction=direction
        )
    elif job == 'logistic':

        # TODO: Get Json Data From FE
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))
        plan_id = int(request.args.get('plan_id'))
        search = None
        column = None
        direction = None
        if request.args.get('search'):
            search = request.args.get('search')
        if request.args.get('order_by_column'):
            column = request.args.get('order_by_column')
            direction = request.args.get('order_direction')

        log_breadcrumb = la_controller.get_all_breadcrumb_data(
            page=page, limit=limit, search=search, column=column, plan_id=plan_id, direction=direction
        )
    else:
        log_breadcrumb = []

    response['error'] = 0
    response['data'] = log_breadcrumb

    return jsonify(response)
