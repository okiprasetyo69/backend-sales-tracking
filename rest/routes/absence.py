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

from rest.controllers import CisangkanController, AbsenceController


__author__ = 'oki'

bp = Blueprint(__name__, "absence")
    
@bp.route('/daily_absence/user', methods=["GET"])

def get_all_absence_daily():
    # Ex : http://127.0.0.1:7091/absence/user?page=1&limit=10&search=Dedy&order_direction=asc&order_by_column=username&start_date=2021-02-24
     
    absence_controller = AbsenceController()
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
        
    absences = absence_controller.get_absence_daily_user(page=page, limit=limit, search=search, column=column, direction=direction, dropdown=dropdown, start_date=start_date)
    
    response['error'] = 0
    response['data'] = absences
    return jsonify(response)
    
@bp.route('/absence/report/export', methods=["GET"])

def export_absence_users():
    #Ex : http://localhost:7091/absence/report/export?start_date=2020-01-01&end_date=2020-10-31
    absence_controller = AbsenceController()
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
    
    result = absence_controller.get_report_absence_users(page=page, limit=limit, start_date=start_date, end_date=end_date)   
    filename = "Report_Absence_Users.xlsx"
    
    response = make_response(send_file(result['file'], add_etags=False))
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Acc-ess-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response

@bp.route('/absence/report/total_check_in/export', methods=["GET"])

def export_total_checkin():
    #Ex : http://localhost:7091/absence/report/total_check_in/export?start_date=2021-01-05
    absence_controller = AbsenceController()
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
    
    result = absence_controller.get_export_total_check_in_user(page=page, limit=limit,start_date=start_date)  
    filename = "Report_Total_Check_In.xlsx"
    response = make_response(send_file(result['file'], add_etags=False))
    
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response

@bp.route('/absence/report/daily_absence/export', methods=["GET"])
def export_daily_absence_user():
    
    absence_controller = AbsenceController()
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
    
    result = absence_controller.get_export_daily_absence(page=page, limit=limit,start_date=start_date)  
    filename = "Report_Daily_Absence.xlsx"
    response = make_response(send_file(result['file'], add_etags=False))
    
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response

@bp.route('/absence/auto_check_out', methods=["GET"])
def auto_checkout_user():
    absence_controller = AbsenceController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    
    date = str(request.args.get('date'))
    user_id = str(request.args.get('user_id'))
    
    list_user_check_out = absence_controller.auto_check_out(user_id=user_id, date=date)
    
    response['error'] = 0
    response['data'] = list_user_check_out
    return jsonify(response)