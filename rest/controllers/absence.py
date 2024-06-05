import re
import json
import time
import pandas as pd
import dateutil.parser
import numpy
import os
import base64
import sys
import xlsxwriter
import pdfkit

from pprint import pprint
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template
from flask_jwt import jwt_required, current_identity

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql, date_range
from rest.helpers.validator import safe_format, safe_invalid_format_message
from rest.models import CustomerModel, UserModel, BranchesModel, DivisionModel, \
    CisangkanCustomerModel, AbsenceDailyModel, AbsenceTotalOnlineModel
    
from rest.models.orm import VisitPlanModel as VisitPlanModelAlchemy

__author__ = 'oki'

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJuYmYiOjE1NzQwNjUwODQsImV4cCI6MTU3NDY2OTg4NCwiaWRlbnRpdHkiOjEsImlhdCI6MTU3NDA2NTA4NH0.pC9h5aOYLjhq7FX_XxIV-MOfhwOG3zUfwjcln35qCdY"

class AbsenceController(object) : 
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.absence_daily = AbsenceDailyModel()
        self.absence_total_online = AbsenceTotalOnlineModel()
        
    def get_absence_daily_user(self, page: int, limit: int, search: str, column: str, direction: str, dropdown: bool, start_date:str):
        
        absence = {}
        data = []
        start = page * limit - limit
        date = datetime.now()
        date_now = date.strftime("%Y-%m-%d")
        
        order = """ ORDER BY usr.username ASC """
        where = " WHERE DATE(vp.date) = '"+date_now+"' GROUP BY sa.user_id "
        
        order_count = """ ORDER BY usr.username ASC """
        where_count = " WHERE DATE(vp.date) = '"+date_now+"' GROUP BY sa.user_id "
        
        if start_date is None :
            where = "WHERE DATE(vp.date) = '"+date_now+"' GROUP BY sa.user_id"
            where_count = " WHERE DATE(vp.date) = '"+date_now+"' GROUP BY sa.user_id "
            
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
            #order_count = """ORDER BY {0} {1}""".format(column, direction)
            
        if search :
            where = " WHERE DATE(vp.date) = '"+date_now+"' AND emp.name LIKE '%{0}%' GROUP BY sa.user_id ".format(search)
            where_count = " WHERE DATE(vp.date) = '"+date_now+"' AND emp.name LIKE '%{0}%' GROUP BY sa.user_id ".format(search)
            
        if start_date : 
            where = " WHERE DATE(vp.date) = '"+start_date+"' GROUP BY sa.user_id "
            where_count = " WHERE DATE(vp.date) = '"+start_date+"' GROUP BY sa.user_id "
            
        if search and start_date :
            where = " WHERE DATE(vp.date) = '"+start_date+"' AND emp.name LIKE '%{0}%' GROUP BY sa.user_id ".format(search)
            where_count = " WHERE DATE(vp.date) = '"+start_date+"' AND emp.name LIKE '%{0}%' GROUP BY sa.user_id ".format(search)    
            
        select = " sa.user_id, usr.username, emp.name, COUNT(DISTINCT(vp.date)) as total_online, b.total_start, c.total_stop "
        join = """ as sa 
        LEFT JOIN(SELECT COUNT(DISTINCT(DATE(tap_nfc_date))) total_start, user_id FROM `sales_activity` WHERE tap_nfc_type LIKE '%START' AND DATE(tap_nfc_date) = '""" +start_date+"""' GROUP BY user_id) b ON sa.user_id = b.user_id
        LEFT JOIN(SELECT COUNT(DISTINCT(DATE(tap_nfc_date))) total_stop, user_id FROM `sales_activity` WHERE tap_nfc_type LIKE '%STOP' AND DATE(tap_nfc_date) = '""" +start_date+"""' GROUP BY user_id) c ON sa.user_id = c.user_id
        JOIN `users` as usr ON sa.user_id=usr.id 
        JOIN `employee` as emp ON emp.id=usr.employee_id
        JOIN `visit_plan` as vp ON vp.user_id = usr.id
        """
       
        select_count = " COUNT(*) "
        join_count = """ as sa
        JOIN `users` as usr ON sa.user_id=usr.id 
        JOIN `employee` as emp ON emp.id=usr.employee_id
        JOIN `visit_plan` as vp ON vp.user_id = usr.id
        """
        
        #get data params
        absence_user_data = self.absence_daily.get_all_absences(self.cursor, select=select, join=join, where=where, order=order, start=start,  limit=limit)

        #count total data
        queryCount = self.absence_daily.get_absences_for_count(self.cursor, select=select_count, join=join_count, where=where_count, order=order_count)
        count = len(queryCount)
        
        #count filtering
        queryCountFilter = self.absence_daily.get_absences_for_count(self.cursor, select=select_count, join=join_count, where=where_count, order=order_count)
        count_filter = len(queryCountFilter)
        

        if absence_user_data :
            for item in absence_user_data :
                if item['total_start'] is None :
                    item['total_start'] = 0
                if item['total_stop'] is None :
                    item['total_stop'] = 0
                data.append(item)

        absence['data'] = data
        absence['total'] = count
        absence['total_filter'] = count_filter

        #paginate
        #TODO: Check Has Next and Prev
        if absence['total'] > page * limit:
            absence['has_next'] = True
        else:
            absence['has_next'] = False
        if limit <= page * count - count:
            absence['has_prev'] = True
        else:
            absence['has_prev'] = False
        
        return absence    
        
    def get_report_absence_users(self, page: int, limit: int, start_date:str, end_date:str):
        result_data = {}
        cycle = {}
        data = []
        start = page * limit - limit
        
        #query for total stop user
        order = """ORDER BY usr.username"""
        where = "WHERE sa.tap_nfc_date >= '"+start_date+"' AND sa.tap_nfc_date <= '"+end_date+"' AND sa.tap_nfc_type LIKE '%STOP' GROUP BY sa.user_id"
        select = "sa.user_id, usr.username, emp.name, COUNT(DISTINCT(DATE(sa.tap_nfc_date))) total_stop"
        join = """ as sa JOIN `users` as usr ON sa.user_id = usr.id 
        JOIN `employee` as emp ON emp.id = usr.employee_id"""
        
        total_stop_data = self.absence_daily.get_total_user_stop(
            self.cursor, select=select, join=join, where=where, order=order
        )
        # end query total stop user
        
        # query for total start user
        order_start = """ORDER BY usr.username"""
        where_start = "WHERE sa.tap_nfc_date >= '"+start_date+"' AND sa.tap_nfc_date <= '"+end_date+"' AND sa.tap_nfc_type LIKE '%START' GROUP BY sa.user_id"
        select_start = "sa.user_id, usr.username, emp.name, COUNT(DISTINCT(DATE(sa.tap_nfc_date))) total_start"
        join_start = """ as sa JOIN `users` as usr ON sa.user_id = usr.id 
        JOIN `employee` as emp ON emp.id = usr.employee_id"""
        
        total_start_data = self.absence_daily.get_total_user_start(self.cursor, select=select_start, join=join_start, where=where_start, order=order_start)
        # end query total start user
        
        #query for total online user
        order_online = """ORDER BY usr.username"""
        where_online = "WHERE vp.date >= '"+start_date+"' AND vp.date <= '"+end_date+"' GROUP BY usr.username"        
        select_online = "vp.user_id, usr.username, emp.name, COUNT(DISTINCT(vp.date)) total_on"
        join_online = """ as vp JOIN `users` as usr ON vp.user_id = usr.id 
        JOIN `employee` as emp ON emp.id = usr.employee_id"""
        
        total_online_data = self.absence_total_online.get_total_user_online(self.cursor, select=select_online, join=join_online, where=where_online, order=order_online)
        
        # end query total online user 
        output = BytesIO()    
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Report Absence Users')
        header_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color':'#00b0f0'
            }
        )
        highlight_format = workbook.add_format(
            {
                'bold': 0,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#f1f1f1'
            }
        )
        worksheet.write('A1', 'No.', header_format)
        worksheet.write('B1', 'ID User', header_format)
        worksheet.write('C1', 'User Name', header_format)
        worksheet.write('D1', 'Nama', header_format)
        worksheet.write('E1', 'Total Online', header_format)
        worksheet.write('F1', 'Total Start', header_format)
        worksheet.write('G1', 'Total Stop', header_format)  
        
        data_rows = 1
        for item in total_online_data :
            worksheet.write(data_rows, 0, data_rows)
            worksheet.write(data_rows, 1, item['user_id'])
            worksheet.write(data_rows, 2, item['username'])
            worksheet.write(data_rows, 3, item['name'])
            worksheet.write(data_rows, 4, item['total_on'])           
            data_rows += 1
            
        data_rows_start = data_rows - len(total_online_data)
        for item in total_start_data :
            worksheet.write(data_rows_start, 5, item['total_start'])           
            data_rows_start += 1
            
        data_rows_stop =  data_rows - len(total_online_data)
        for item in total_stop_data :
            worksheet.write(data_rows_stop, 6, item['total_stop'])           
            data_rows_stop += 1
            
        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output
       
        return result_data
    
    def get_export_total_check_in_user(self, page: int, limit: int, start_date:str):
        result_data = {}
        cycle = {}
        data = []
        start = page * limit - limit
        
        order = """ORDER BY usr.username, sa.tap_nfc_date"""
        where = "WHERE sa.tap_nfc_type = 'IN' AND DATE(sa.tap_nfc_date) = '"+start_date+"'"
        select = "usr.username, emp.name, usrgrp.group_name, cs.name AS location, sa.tap_nfc_date AS check_in_date"
        join = """ as sa JOIN `users` as usr ON sa.user_id = usr.id 
        JOIN `customer` as cs ON cs.code = sa.nfc_code 
        JOIN `employee` as emp ON usr.employee_id = emp.id
        JOIN `user_groups` as usrgrp ON usr.user_group_id = usrgrp.id"""
     
        total_check_in_data = self.absence_daily.get_total_user_check_in(
            self.cursor, select=select, join=join, where=where, order=order
        )
                
        output = BytesIO()    
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Total Check In')
        header_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color':'#00b0f0'
            }
        )
        highlight_format = workbook.add_format(
            {
                'bold': 0,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#f1f1f1'
            }
        )
        worksheet.write('A1', 'No.', header_format)
        worksheet.write('B1', 'UserName', header_format)
        worksheet.write('C1', 'Nama', header_format)
        worksheet.write('D1', 'Kategori', header_format)
        worksheet.write('E1', 'Lokasi Check In', header_format)
        worksheet.write('F1', 'Waktu Check In', header_format)
        
        data_rows = 1
        for item in total_check_in_data :
            worksheet.write(data_rows, 0, data_rows)
            worksheet.write(data_rows, 1, item['username'])
            worksheet.write(data_rows, 2, item['name'])
            worksheet.write(data_rows, 3, item['group_name'])
            worksheet.write(data_rows, 4, item['location']) 
            worksheet.write(data_rows, 5, item['check_in_date'].strftime("%d-%m-%Y %H:%M:%S"))           
            data_rows += 1
            
        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output
       
        return result_data
    
    def get_export_daily_absence(self, page: int, limit: int, start_date:str) :
        result_data = {}
        cycle = {}
        data = []
        start = page * limit - limit
        
        order = """ ORDER BY usr.username ASC """
        where = " WHERE DATE(vp.date) = '"+start_date+"' GROUP BY sa.user_id "
        
        select = " sa.user_id, usr.username, emp.name, COUNT(DISTINCT(vp.date)) as total_online, b.total_start, c.total_stop "
        join = """ as sa 
        LEFT JOIN(SELECT COUNT(DISTINCT(DATE(tap_nfc_date))) total_start, user_id FROM `sales_activity` WHERE tap_nfc_type LIKE '%START' AND DATE(tap_nfc_date) = '""" +start_date+"""' GROUP BY user_id) b ON sa.user_id = b.user_id
        LEFT JOIN(SELECT COUNT(DISTINCT(DATE(tap_nfc_date))) total_stop, user_id FROM `sales_activity` WHERE tap_nfc_type LIKE '%STOP' AND DATE(tap_nfc_date) = '""" +start_date+"""' GROUP BY user_id) c ON sa.user_id = c.user_id
        JOIN `users` as usr ON sa.user_id=usr.id 
        JOIN `employee` as emp ON emp.id=usr.employee_id
        JOIN `visit_plan` as vp ON vp.user_id = usr.id
        """
        
        absence_user_data = self.absence_daily.get_daily_absence_report(self.cursor, select=select, join=join, where=where, order=order)
        
        output = BytesIO()    
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Report Daily Absence')
        header_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color':'#00b0f0'
            }
        )
        highlight_format = workbook.add_format(
            {
                'bold': 0,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#f1f1f1'
            }
        )
        worksheet.write('A1', 'No.', header_format)
        worksheet.write('B1', 'User ID', header_format)
        worksheet.write('C1', 'User Name', header_format)
        worksheet.write('D1', 'Name', header_format)
        worksheet.write('E1', 'Total Start', header_format)
        worksheet.write('F1', 'Total Stop', header_format)
        worksheet.write('G1', 'Total Online', header_format)
        
        data_rows = 1
        for item in absence_user_data :
            if item['total_start'] is None :
                item['total_start'] = 0
            if item['total_stop'] is None :
                item['total_stop'] = 0
            data.append(item)
            
            worksheet.write(data_rows, 0, data_rows)
            worksheet.write(data_rows, 1, item['user_id'])
            worksheet.write(data_rows, 2, item['username'])
            worksheet.write(data_rows, 3, item['name'])
            worksheet.write(data_rows, 4, item['total_start'])
            worksheet.write(data_rows, 5, item['total_stop']) 
            worksheet.write(data_rows, 6, item['total_online'])           
            data_rows += 1
            
        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output
       
        return result_data
    
    def auto_check_out(self, user_id:int, date:str):
        
        absence = {}
        data = []
        inserted = []
        order = """ORDER BY id"""
        order_limit =  """ORDER BY id LIMIT 1"""
        where = "WHERE user_id = "+user_id+" AND DATE(tap_nfc_date) = '"+date+"'"
        where_stop = "WHERE user_id = "+user_id+" AND DATE(tap_nfc_date) = '"+date+"' AND tap_nfc_type= 'STOP'"
        select = "id, user_id, visit_plan_id, nfc_code, tap_nfc_date, tap_nfc_type"
        
        #get user dont have stop
        user_have_stop = self.absence_daily.get_user_stop_status(self.cursor, select=select, where=where_stop, order=order)
        
        #get user
        user_activity = self.absence_daily.get_user_stop_status(self.cursor, select=select, where=where, order=order_limit)
        
        if user_have_stop :
            print('User have stop')
            
        else :
            print('User dont have stop') 
            try:
                for itmActivity in user_activity :
                    nfc_date_value = itmActivity['tap_nfc_date']
                    nfc_date_value = nfc_date_value.replace(minute=0, hour=19, second=0)
                    
                    user_id = itmActivity['user_id']
                    visit_plan_id = itmActivity['visit_plan_id']
                    nfc_code = 1 
                    tap_nfc_date = str(nfc_date_value)
                    tap_nfc_type = 'STOP'
                    route_breadcrumb = None
                    distance = None
                    total_distance = None
                    create_date = str(nfc_date_value)
                    update_date = str(nfc_date_value)
                                        
                    insert = self.absence_daily.insert_into_db(self.cursor, user_id=user_id, visit_plan_id=visit_plan_id,nfc_code=nfc_code,route_breadcrumb=route_breadcrumb,distance=distance, total_distance=total_distance, tap_nfc_date=tap_nfc_date, tap_nfc_type=tap_nfc_type, create_date=create_date,update_date=update_date)
                    
                    inserted.append(itmActivity)
                    mysql.connection.commit()
                     
            except Exception as e:
                raise BadRequest(e, 200, 1, data=[])
        
        absence['data'] = user_have_stop
        absence['inserted'] = inserted
        return absence
      
                