import re
import json
import io
import time
import base64
import pandas as pd
import dateutil.parser
import xlsxwriter
import pdfkit

from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template
from collections import OrderedDict

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import SalesOrderModel, SalesPaymentModel, RequestOrderModel, CustomerModel, UserModel, \
    EmployeeModel, BranchesModel, DivisionModel, RequestOrderProductModel, RequestOrderImageModel, DeliveryModel, \
    SalesPaymentMobileModel, VisitPlanModel, PackingSlipModel

__author__ = 'Junior'


class SalesController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.ro_model = RequestOrderModel()
        self.rop_model = RequestOrderProductModel()
        self.roi_model = RequestOrderImageModel()
        self.so_model = SalesOrderModel()
        self.sp_model = SalesPaymentModel()
        self.spm_model = SalesPaymentMobileModel()
        self.customer_model = CustomerModel()
        self.user_model = UserModel()
        self.employee_model = EmployeeModel()
        self.branch_model = BranchesModel()
        self.division_model = DivisionModel()
        self.delivery_model = DeliveryModel()
        self.visit_plan_model = VisitPlanModel()
        self.packing_slip_model = PackingSlipModel()

    # TODO: Controller for test
    def test_image(self, _id: int):
        try:
            result = self.roi_model.get_all_request_order_image(self.cursor, _id)[0]
        except Exception as e:
            print(e)
        return result

    # TODO: controllers request order
    def create_request_order(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create request order

        :param create_data: dict
        :param user_id: int
        :return:
            Request Order Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            create = self.ro_model.insert_into_db(
                self.cursor, date=today, user_id=user_id, customer_code=create_data['customer_code'],
                is_special_order=create_data['is_special_order'], contacts=create_data['contacts'],
                delivery_address=create_data['delivery_address'], lat=create_data['lat'], lng=create_data['lng'],
                notes=create_data['notes'], create_date=today, update_date=today
            )
            mysql.connection.commit()
            # last_insert_id = mysql.connection.insert_id()
            last_insert_id = self.cursor.lastrowid
            print(last_insert_id)
            update_data = {
                "id": last_insert_id,
                "code": "REQ-{0:04}".format(last_insert_id)
            }
            update = self.ro_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
            if create_data['product'] is not None:
                product = create_data['product']
                for rec in product:
                    product_data = {
                        "request_orders_id": last_insert_id,
                        "item_name": rec['item_name'],
                        "qty": rec['qty']
                    }
                    try:
                        self.rop_model.insert_into_db(
                            self.cursor, request_orders_id=product_data['request_orders_id'],
                            item_name=product_data['item_name'], qty=product_data['qty'],
                            create_date=today, update_date=today
                        )
                        mysql.connection.commit()
                    except Exception as e:
                        print(e)
                        pass
            if create_data['files'] is not None:
                file = create_data['files']
                filename = '{}.jpg'.format(update_data['code'])
                image_data = {
                    "request_orders_id": last_insert_id,
                    "file": file,
                    "filename": filename
                }
                try:
                    self.roi_model.insert_into_db(
                        self.cursor, request_orders_id=image_data['request_orders_id'],
                        filename=image_data['filename'], file=image_data['file'],
                        create_date=today, update_date=today
                    )
                    mysql.connection.commit()
                except Exception as e:
                    print(e)

        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return last_insert_id

    def get_all_sales_request_data(
            self, page: int, limit: int, search: str, column: str, direction: str, customer_code: str,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of Request Order
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: customer_code: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            list Request Orders Object
        """
        request_orders = {}
        data = []
        start = page * limit - limit
        order_flag = False
        order = ''
        if customer_code:
            where = "WHERE `customer_code` = '{}' ".format(customer_code)
        else:
            where = "WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) ".format(
                ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
        where_original = where
        if column:
            if column == 'employee':
                order_flag = True
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'division':
                order_flag = True
                order = """ORDER BY d.division_name {0}""".format(direction)
            elif column == 'branch':
                order_flag = True
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'customer':
                order_flag = True
                order = """ORDER BY c.name {0}""".format(direction)
            else:
                if search:
                    order = """ORDER BY ro.{0} {1}""".format(column, direction)
                else:
                    order = """ORDER BY {0} {1}""".format(column, direction)

        if customer_code:
            ro_data = self.ro_model.get_all_request_order(self.cursor, start=start, limit=limit, where=where,
                                                          order=order)
            count = self.ro_model.get_count_all_request_order(self.cursor, where=where)
            count_filter = count
        else:
            select = "ro.*"
            select_count = "ro.id"
            join = """as ro LEFT JOIN `users` as u ON ro.user_id = u.id 
                    LEFT JOIN `customer` as c ON ro.customer_code = c.code
                    LEFT JOIN `employee` as e ON u.employee_id = e.id 
                    LEFT JOIN `branches` as b ON u.branch_id = b.id 
                    LEFT JOIN `divisions` as d ON u.division_id = d.id"""
            if search:
                where += """AND (ro.code LIKE '%{0}%' OR b.name LIKE '%{0}%' OR d.division_name LIKE '%{0}%' 
                OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)
            if data_filter:
                data_filter = data_filter[0]
                if data_filter['start_date']:
                    where += """AND (ro.date >= '{0} 00:00:00' AND ro.date <= '{1} 23:59:59') """.format(
                        data_filter['start_date'], data_filter['end_date']
                    )
                if data_filter['user_id']:
                    where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
                if data_filter['branch_id']:
                    where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
                if data_filter['division_id']:
                    where += """AND u.division_id IN ({0}) """.format(
                        ", ".join(str(x) for x in data_filter['division_id']))
            ro_data = self.ro_model.get_all_request_order(
                self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
            )
            count_filter = self.ro_model.get_count_all_request_order(
                self.cursor, select=select_count, join=join, where=where
            )
            count = self.ro_model.get_count_all_request_order(
                self.cursor, select=select_count, join=join, where=where_original
            )

        if ro_data:
            for ro in ro_data:
                if ro['create_date'] is not None:
                    ro['create_date'] = str(ro['create_date'])
                if ro['update_date'] is not None:
                    ro['update_date'] = str(ro['update_date'])
                if ro['customer_code'] is not None:
                    try:
                        ro['customer'] = self.customer_model.get_customer_by_id(self.cursor, ro['customer_code'],
                                                                                select="code, name, address, "
                                                                                       "lng, lat")[0]
                    except:
                        ro['customer'] = {}
                else:
                    ro['customer'] = {}
                if ro['user_id'] is not None:
                    try:
                        ro['user'] = self.user_model.get_user_by_id(self.cursor, ro['user_id'],
                                                                    select="id, employee_id, branch_id, division_id")[0]
                        if ro['user']['employee_id'] is not None:
                            try:
                                ro['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, ro['user']['employee_id'], select="name")[0]['name']
                            except:
                                ro['user']['employee_name'] = None
                        else:
                            ro['user']['employee_name'] = None
                        if ro['user']['branch_id'] is not None:
                            try:
                                ro['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, ro['user']['branch_id'], select="name")[0]['name']
                            except:
                                ro['user']['branch_name'] = None
                        else:
                            ro['user']['branch_name'] = None
                        if ro['user']['division_id'] is not None:
                            try:
                                ro['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, ro['user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                ro['user']['division_name'] = None
                        else:
                            ro['user']['division_name'] = None
                    except:
                        ro['user'] = {}
                else:
                    ro['user'] = {}
                try:
                    result_product = self.rop_model.get_all_request_order_product(self.cursor, ro['id'])
                    ro['product'] = []
                    for rec in result_product:
                        ro['product'].append({
                            'product_name': rec['item_name'],
                            'quantity': rec['qty']
                        })
                except Exception as e:
                    print(e)
                    ro['product'] = []

                # try:
                #     result_image = self.roi_model.get_all_request_order_image(self.cursor, ro['id'])[0]
                #     ro['files'] = result_image['file']
                # except Exception as e:
                #     print(e)
                #     ro['files'] = []
                data.append(ro)
        request_orders['data'] = data
        request_orders['total'] = count
        request_orders['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if request_orders['total'] > page * limit:
            request_orders['has_next'] = True
        else:
            request_orders['has_next'] = False
        if limit <= page * count - count:
            request_orders['has_prev'] = True
        else:
            request_orders['has_prev'] = False
        return request_orders

    def get_all_export_sales_request_data(
            self, page: int, limit: int, search: str, column: str, direction: str, customer_code: str,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of Request Order
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: customer_code: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            list Request Orders Object
        """
        result_data = {}
        data = []
        start = page * limit - limit
        order = ''
        if customer_code:
            where = "WHERE `customer_code` = '{}' ".format(customer_code)
        else:
            where = "WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) ".format(
                ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
        where_original = where
        if column:
            if column == 'employee':
                order_flag = True
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'division':
                order_flag = True
                order = """ORDER BY d.division_name {0}""".format(direction)
            elif column == 'branch':
                order_flag = True
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'customer':
                order_flag = True
                order = """ORDER BY c.name {0}""".format(direction)
            else:
                if search:
                    order = """ORDER BY ro.{0} {1}""".format(column, direction)
                else:
                    order = """ORDER BY {0} {1}""".format(column, direction)

        if customer_code:
            ro_data = self.ro_model.get_all_request_order(self.cursor, start=start, limit=limit, where=where,
                                                          order=order)
            count = self.ro_model.get_count_all_request_order(self.cursor, where=where)
            count_filter = count
        else:
            select = "ro.*"
            select_count = "ro.id"
            join = """as ro LEFT JOIN `users` as u ON ro.user_id = u.id 
                    LEFT JOIN `customer` as c ON ro.customer_code = c.code
                    LEFT JOIN `employee` as e ON u.employee_id = e.id 
                    LEFT JOIN `branches` as b ON u.branch_id = b.id 
                    LEFT JOIN `divisions` as d ON u.division_id = d.id"""
            if search:
                where += """AND (ro.code LIKE '%{0}%' OR b.name LIKE '%{0}%' OR d.division_name LIKE '%{0}%' 
                OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)
            if data_filter:
                tmp_data_filter = data_filter[0]
                if tmp_data_filter['start_date']:
                    where += """AND (ro.date >= '{0} 00:00:00' AND ro.date <= '{1} 23:59:59') """.format(
                        tmp_data_filter['start_date'], tmp_data_filter['end_date']
                    )
                if tmp_data_filter['user_id']:
                    where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['user_id']))
                if tmp_data_filter['branch_id']:
                    where += """AND u.branch_id IN ({0}) """.format(
                        ", ".join(str(x) for x in tmp_data_filter['branch_id']))
                if tmp_data_filter['division_id']:
                    where += """AND u.division_id IN ({0}) """.format(
                        ", ".join(str(x) for x in tmp_data_filter['division_id']))
            ro_data = self.ro_model.get_all_request_order(
                self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
            )
            count_filter = self.ro_model.get_count_all_request_order(
                self.cursor, select=select_count, join=join, where=where
            )
            count = self.ro_model.get_count_all_request_order(
                self.cursor, select=select_count, join=join, where=where_original
            )

        if ro_data:
            for ro in ro_data:
                if ro['create_date'] is not None:
                    ro['create_date'] = str(ro['create_date'])
                if ro['update_date'] is not None:
                    ro['update_date'] = str(ro['update_date'])
                if ro['customer_code'] is not None:
                    try:
                        ro['customer'] = self.customer_model.get_customer_by_id(self.cursor, ro['customer_code'],
                                                                                select="code, name, address, "
                                                                                       "lng, lat")[0]
                    except:
                        ro['customer'] = {}
                else:
                    ro['customer'] = {}
                if ro['user_id'] is not None:
                    try:
                        ro['user'] = self.user_model.get_user_by_id(self.cursor, ro['user_id'],
                                                                    select="id, employee_id, branch_id, division_id")[0]
                        if ro['user']['employee_id'] is not None:
                            try:
                                ro['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, ro['user']['employee_id'], select="name")[0]['name']
                            except:
                                ro['user']['employee_name'] = None
                        else:
                            ro['user']['employee_name'] = None
                        if ro['user']['branch_id'] is not None:
                            try:
                                ro['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, ro['user']['branch_id'], select="name")[0]['name']
                            except:
                                ro['user']['branch_name'] = None
                        else:
                            ro['user']['branch_name'] = None
                        if ro['user']['division_id'] is not None:
                            try:
                                ro['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, ro['user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                ro['user']['division_name'] = None
                        else:
                            ro['user']['division_name'] = None
                    except:
                        ro['user'] = {}
                else:
                    ro['user'] = {}
                try:
                    result_product = self.rop_model.get_all_request_order_product(self.cursor, ro['id'])
                    ro['product'] = []
                    for rec in result_product:
                        ro['product'].append({
                            'product_name': rec['item_name'],
                            'quantity': rec['qty']
                        })
                except Exception as e:
                    print(e)
                    ro['product'] = []

                try:
                    result_image = self.roi_model.get_all_request_order_image(self.cursor, ro['id'])[0]
                    ro['files'] = result_image['file']
                except Exception as e:
                    print(e)
                    ro['files'] = []
                data.append(ro)
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Request Order')
        merge_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter'
            }
        )
        # Header sheet
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date'] and not data_filter['user_id']:
                worksheet.merge_range(
                    'A1:F1',
                    'REQUEST ORDER (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                        data_filter['start_date'], data_filter['end_date']
                    ),
                    merge_format
                )
            elif data_filter['user_id'] and not data_filter['start_date']:
                worksheet.merge_range(
                    'A1:F1',
                    'REQUEST ORDER (USER: {0}, TANGGAL: ALL)'.format(", ".join(x for x in data_filter['username'])),
                    merge_format
                )
            else:
                worksheet.merge_range(
                    'A1:F1',
                    'REQUEST ORDER (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                        ", ".join(x for x in data_filter['username']), data_filter['start_date'],
                        data_filter['end_date']
                    ),
                    merge_format
                )
        else:
            worksheet.merge_range('A1:F1', 'REQUEST ORDER (USER: ALL, TANGGAL: ALL)', merge_format)

        worksheet.write('A3', 'NO REQUEST ORDER', merge_format)
        worksheet.write('B3', 'TANGGAL', merge_format)
        worksheet.write('C3', 'BRANCH', merge_format)
        worksheet.write('D3', 'DIVISION', merge_format)
        worksheet.write('E3', 'CUSTOMER', merge_format)
        worksheet.write('F3', 'PIC', merge_format)
        worksheet.write('G3', 'ORDER TYPE', merge_format)
        worksheet.write('H3', 'DELIVERY ADDRESS', merge_format)
        worksheet.write('I3', 'SALES REP', merge_format)
        worksheet.write('J3', 'ORDER', merge_format)
        worksheet.write('K3', 'ORDER BY IMAGE', merge_format)
        worksheet.write('L3', 'NOTES', merge_format)

        data_rows = 3
        for rec in data:
            if rec['is_special_order'] == 1:
                order_type = "Special Order"
            else:
                order_type = "Reguler Order"
            if rec['product']:
                string_product = []
                for prod in rec['product']:
                    name_prod = "Product Name : {0} - Quantity : {1}".format(prod['product_name'], prod['quantity'])
                    string_product.append(name_prod)
                order_product = ", ".join(string_product)
            else:
                order_product = ""
            if rec['files']:
                order_by_image = "Iya"
            else:
                order_by_image = "Tidak"
            worksheet.write(data_rows, 0, rec['code'])
            worksheet.write(data_rows, 1, rec['date'])
            worksheet.write(data_rows, 2, rec['user']['branch_name'])
            worksheet.write(data_rows, 3, rec['user']['division_name'])
            worksheet.write(data_rows, 4, rec['customer_code'])
            worksheet.write(data_rows, 5, rec['contacts'])
            worksheet.write(data_rows, 6, order_type)
            worksheet.write(data_rows, 7, rec['delivery_address'])
            worksheet.write(data_rows, 8, rec['user']['employee_name'])
            worksheet.write(data_rows, 9, order_product)
            worksheet.write(data_rows, 10, order_by_image)
            worksheet.write(data_rows, 11, rec['notes'])
            data_rows += 1

        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_all_export_pdf_sales_request_data(
            self, page: int, limit: int, search: str, column: str, direction: str, customer_code: str,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of Request Order
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: customer_code: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            list Request Orders Object
        """
        result_data = {}
        data = []
        start = page * limit - limit
        order = ''
        if customer_code:
            where = "WHERE `customer_code` = '{}' ".format(customer_code)
        else:
            where = "WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) ".format(
                ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
        where_original = where
        if column:
            if column == 'employee':
                order_flag = True
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'division':
                order_flag = True
                order = """ORDER BY d.division_name {0}""".format(direction)
            elif column == 'branch':
                order_flag = True
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'customer':
                order_flag = True
                order = """ORDER BY c.name {0}""".format(direction)
            else:
                if search:
                    order = """ORDER BY ro.{0} {1}""".format(column, direction)
                else:
                    order = """ORDER BY {0} {1}""".format(column, direction)

        if customer_code:
            ro_data = self.ro_model.get_all_request_order(self.cursor, start=start, limit=limit, where=where,
                                                          order=order)
            count = self.ro_model.get_count_all_request_order(self.cursor, where=where)
            count_filter = count
        else:
            select = "ro.*"
            select_count = "ro.id"
            join = """as ro LEFT JOIN `users` as u ON ro.user_id = u.id 
                    LEFT JOIN `customer` as c ON ro.customer_code = c.code
                    LEFT JOIN `employee` as e ON u.employee_id = e.id 
                    LEFT JOIN `branches` as b ON u.branch_id = b.id 
                    LEFT JOIN `divisions` as d ON u.division_id = d.id"""
            if search:
                where += """AND (ro.code LIKE '%{0}%' OR b.name LIKE '%{0}%' OR d.division_name LIKE '%{0}%' 
                OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)
            if data_filter:
                tmp_data_filter = data_filter[0]
                if tmp_data_filter['start_date']:
                    where += """AND (ro.date >= '{0} 00:00:00' AND ro.date <= '{1} 23:59:59') """.format(
                        tmp_data_filter['start_date'], tmp_data_filter['end_date']
                    )
                if tmp_data_filter['user_id']:
                    where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['user_id']))
                if tmp_data_filter['branch_id']:
                    where += """AND u.branch_id IN ({0}) """.format(
                        ", ".join(str(x) for x in tmp_data_filter['branch_id']))
                if tmp_data_filter['division_id']:
                    where += """AND u.division_id IN ({0}) """.format(
                        ", ".join(str(x) for x in tmp_data_filter['division_id']))
            ro_data = self.ro_model.get_all_request_order(
                self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
            )
            count_filter = self.ro_model.get_count_all_request_order(
                self.cursor, select=select_count, join=join, where=where
            )
            count = self.ro_model.get_count_all_request_order(
                self.cursor, select=select_count, join=join, where=where_original
            )

        if ro_data:
            for ro in ro_data:
                if ro['create_date'] is not None:
                    ro['create_date'] = str(ro['create_date'])
                if ro['update_date'] is not None:
                    ro['update_date'] = str(ro['update_date'])
                if ro['customer_code'] is not None:
                    try:
                        ro['customer'] = self.customer_model.get_customer_by_id(self.cursor, ro['customer_code'],
                                                                                select="code, name, address, "
                                                                                       "lng, lat")[0]
                    except:
                        ro['customer'] = {}
                else:
                    ro['customer'] = {}
                if ro['user_id'] is not None:
                    try:
                        ro['user'] = self.user_model.get_user_by_id(self.cursor, ro['user_id'],
                                                                    select="id, employee_id, branch_id, division_id")[0]
                        if ro['user']['employee_id'] is not None:
                            try:
                                ro['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, ro['user']['employee_id'], select="name")[0]['name']
                            except:
                                ro['user']['employee_name'] = None
                        else:
                            ro['user']['employee_name'] = None
                        if ro['user']['branch_id'] is not None:
                            try:
                                ro['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, ro['user']['branch_id'], select="name")[0]['name']
                            except:
                                ro['user']['branch_name'] = None
                        else:
                            ro['user']['branch_name'] = None
                        if ro['user']['division_id'] is not None:
                            try:
                                ro['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, ro['user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                ro['user']['division_name'] = None
                        else:
                            ro['user']['division_name'] = None
                    except:
                        ro['user'] = {}
                else:
                    ro['user'] = {}
                try:
                    result_product = self.rop_model.get_all_request_order_product(self.cursor, ro['id'])
                    ro['product'] = []
                    for rec in result_product:
                        ro['product'].append({
                            'product_name': rec['item_name'],
                            'quantity': rec['qty']
                        })
                except Exception as e:
                    print(e)
                    ro['product'] = []

                try:
                    result_image = self.roi_model.get_all_request_order_image(self.cursor, ro['id'])[0]
                    ro['files'] = result_image['file']
                except Exception as e:
                    print(e)
                    ro['files'] = []
                data.append(ro)

        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date'] and not data_filter['user_id']:
                head_title = 'REQUEST ORDER (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            elif data_filter['user_id'] and not data_filter['start_date']:
                head_title = 'REQUEST ORDER (USER: {0}, TANGGAL: ALL)'.format(
                    ", ".join(x for x in data_filter['username'])
                )
            else:
                head_title = 'REQUEST ORDER (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                    ", ".join(x for x in data_filter['username']), data_filter['start_date'],
                    data_filter['end_date']
                )
        else:
            head_title = 'REQUEST ORDER (USER: ALL, TANGGAL: ALL)'

        head_table = OrderedDict()
        head_table['no'] = "NO REQUEST ORDER"
        head_table['tanggal'] = "TANGGAL"
        head_table['branch'] = "BRANCH"
        head_table['division'] = "DIVISION"
        head_table['customer'] = "CUSTOMER"
        head_table['pic'] = "PIC"
        head_table['order_type'] = "ORDER TYPE"
        head_table['address'] = "DELIVERY ADDRESS"
        head_table['sales'] = "SALES REP"
        head_table['order'] = "ORDER"
        head_table['order_image'] = "ORDER BY IMAGE"
        head_table['notes'] = "NOTES"
        body_table = []
        for rec in data:
            data_body = OrderedDict()
            if rec['is_special_order'] == 1:
                order_type = "Special Order"
            else:
                order_type = "Reguler Order"
            if rec['product']:
                string_product = []
                for prod in rec['product']:
                    name_prod = "Product Name : {0} - Quantity : {1}".format(prod['product_name'], prod['quantity'])
                    string_product.append(name_prod)
                order_product = ", ".join(string_product)
            else:
                order_product = ""
            if rec['files']:
                order_by_image = "Iya"
            else:
                order_by_image = "Tidak"
            data_body['no'] = rec['code']
            data_body['tanggal'] = rec['date']
            data_body['branch'] = rec['user']['branch_name']
            data_body['division'] = rec['user']['division_name']
            data_body['customer'] = rec['customer_code']
            data_body['pic'] = rec['contacts']
            data_body['order_type'] = order_type
            data_body['address'] = rec['delivery_address']
            data_body['sales'] = rec['user']['employee_name']
            data_body['order'] = order_product
            data_body['order_image'] = order_by_image
            data_body['notes'] = rec['notes']
            body_table.append(data_body)
        # rendered = render_template(
        #     'report_template.html', head_title=head_title, head_table=head_table,
        #     head_customer_table=head_customer_table, body_table=body_table, category="sales"
        # )
        rendered = render_template(
            'report_template.html', head_title=head_title, head_table=head_table, body_table=body_table
        )
        output = pdfkit.from_string(rendered, False)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_all_sales_request_by_customer(self, page: int, limit: int, customer: str, user_id: int, username: str):
        """
        Get List Of Request Order
        :param: page: int
        :param: limit: int
        :param: customer: str
        :param: user_id: int
        :param: username: str
        :return:
            list Request Orders Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        # today = "2018-07-27"

        result = {}
        data = []
        start = page * limit - limit

        # TODO: Get Reqeust order list
        where = """WHERE `customer_code` = '{0}' AND `date` LIKE '{1}%' 
        AND `user_id` = {2}""".format(customer, today, user_id)
        ro_data = self.ro_model.get_all_request_order(self.cursor, where=where, start=start, limit=limit)
        count_ro = self.ro_model.get_count_all_request_order(self.cursor, where=where)
        count_ro_filter = count_ro

        if ro_data:
            for ro in ro_data:
                if ro['create_date'] is not None:
                    ro['create_date'] = str(ro['create_date'])
                if ro['update_date'] is not None:
                    ro['update_date'] = str(ro['update_date'])
                if ro['customer_code'] is not None:
                    try:
                        ro['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, ro['customer_code'], select="code, name, address, lng, lat"
                        )[0]
                    except:
                        ro['customer'] = {}
                else:
                    ro['customer'] = {}
                if ro['user_id'] is not None:
                    try:
                        ro['user'] = self.user_model.get_user_by_id(self.cursor, ro['user_id'],
                                                                    select="id, employee_id, branch_id, division_id")[0]
                        if ro['user']['employee_id'] is not None:
                            try:
                                ro['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, ro['user']['employee_id'], select="name")[0]['name']
                            except:
                                ro['user']['employee_name'] = None
                        else:
                            ro['user']['employee_name'] = None
                        if ro['user']['branch_id'] is not None:
                            try:
                                ro['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, ro['user']['branch_id'], select="name")[0]['name']
                            except:
                                ro['user']['branch_name'] = None
                        else:
                            ro['user']['branch_name'] = None
                        if ro['user']['division_id'] is not None:
                            try:
                                ro['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, ro['user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                ro['user']['division_name'] = None
                        else:
                            ro['user']['division_name'] = None
                    except:
                        ro['user'] = {}
                else:
                    ro['user'] = {}
                try:
                    result_product = self.rop_model.get_all_request_order_product(self.cursor, ro['id'])
                    ro['product'] = []
                    for rec in result_product:
                        ro['product'].append({
                            'product_name': rec['item_name'],
                            'quantity': rec['qty']
                        })
                except Exception as e:
                    print(e)
                    ro['product'] = []

                try:
                    result_image = self.roi_model.get_all_request_order_image(self.cursor, ro['id'])[0]
                    ro['files'] = result_image['file']
                except Exception as e:
                    print(e)
                    ro['files'] = []
                ro['type'] = 'Request Order'
                data.append(ro)

        # TODO: Get Sales Order
        # where = """WHERE `invoice_code` is NULL AND `customer_code` = '{0}'
        # AND `user_code` = '{1}'""".format(customer, username)
        where = """WHERE `invoice_code` is NULL AND `customer_code` = '{0}'""".format(customer)
        so_data = self.so_model.get_all_sales_order(self.cursor, where=where, start=start, limit=limit)
        count_so = self.so_model.get_count_all_sales_order(self.cursor, where=where)
        count_so_filter = count_so

        if so_data:
            for so in so_data:
                if so['packing_slip_code'] is not None and so['invoice_code'] is not None:
                    so['status'] = 'invoiced'
                elif so['packing_slip_code'] is not None and so['invoice_code'] is None:
                    so['status'] = 'Packing Slip'
                else:
                    so['status'] = 'Open Order'
                if so['product'] is not None:
                    so['product'] = json.loads(so['product'])
                if so['create_date'] is not None:
                    so['create_date'] = str(so['create_date'])
                if so['invoice_date'] is not None:
                    so['invoice_date'] = str(so['invoice_date'])
                if so['packing_slip_date'] is not None:
                    so['packing_slip_date'] = str(so['packing_slip_date'])
                if so['customer_code'] is not None:
                    try:
                        so['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, so['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        so['customer'] = {}
                else:
                    so['customer'] = {}
                if so['user_code'] is not None:
                    try:
                        so['user'] = self.user_model.get_user_by_username(self.cursor, so['user_code'],
                                                                          select="id, employee_id, branch_id, "
                                                                                 "division_id")[0]
                        if so['user']['employee_id'] is not None:
                            try:
                                so['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, so['user']['employee_id'], select="name")[0]['name']
                            except:
                                so['user']['employee_name'] = None
                        else:
                            so['user']['employee_name'] = None
                        if so['user']['branch_id'] is not None:
                            try:
                                so['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, so['user']['branch_id'], select="name")[0]['name']
                            except:
                                so['user']['branch_name'] = None
                        else:
                            so['user']['branch_name'] = None
                        if so['user']['division_id'] is not None:
                            try:
                                so['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, so['user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                so['user']['division_name'] = None
                        else:
                            so['user']['division_name'] = None
                    except:
                        so['user'] = {}
                else:
                    so['user'] = {}

                so['type'] = 'Sales Order'
                data.append(so)

        print(count_ro)
        print(count_so)
        count = count_ro + count_so
        count_filter = count_ro_filter + count_so_filter

        result['data'] = data
        result['total'] = count
        result['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if result['total_filter'] > page * limit:
            result['has_next'] = True
        else:
            result['has_next'] = False
        if limit <= page * count_filter - count_filter:
            result['has_prev'] = True
        else:
            result['has_prev'] = False
        return result

    def get_all_sales_request_by_list_customer(self, page: int, limit: int, customer: list, user_id: int,
                                               username: str):
        """
        Get List Of Request Order
        :param: page: int
        :param: limit: int
        :param: customer: list
        :param: user_id: int
        :param: username: str
        :return:
            list Request Orders Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        # today = "2018-06-22"

        result = {}
        data = []
        start = page * limit - limit

        # TODO: Get Reqeust order list
        where = """WHERE `customer_code` IN ('{0}') AND `date` LIKE '{1}%' 
        AND `user_id` = {2}""".format("', '".join(x for x in customer), today, user_id)
        ro_data = self.ro_model.get_all_request_order(self.cursor, where=where, start=start, limit=limit)
        count_ro = self.ro_model.get_count_all_request_order(self.cursor, where=where)
        count_ro_filter = count_ro

        if ro_data:
            for ro in ro_data:
                if ro['create_date'] is not None:
                    ro['create_date'] = str(ro['create_date'])
                if ro['update_date'] is not None:
                    ro['update_date'] = str(ro['update_date'])
                if ro['customer_code'] is not None:
                    try:
                        ro['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, ro['customer_code'], select="code, name, address, lng, lat"
                        )[0]
                    except:
                        ro['customer'] = {}
                else:
                    ro['customer'] = {}
                if ro['user_id'] is not None:
                    try:
                        ro['user'] = self.user_model.get_user_by_id(self.cursor, ro['user_id'],
                                                                    select="id, employee_id, branch_id, division_id")[0]
                        if ro['user']['employee_id'] is not None:
                            try:
                                ro['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, ro['user']['employee_id'], select="name")[0]['name']
                            except:
                                ro['user']['employee_name'] = None
                        else:
                            ro['user']['employee_name'] = None
                        if ro['user']['branch_id'] is not None:
                            try:
                                ro['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, ro['user']['branch_id'], select="name")[0]['name']
                            except:
                                ro['user']['branch_name'] = None
                        else:
                            ro['user']['branch_name'] = None
                        if ro['user']['division_id'] is not None:
                            try:
                                ro['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, ro['user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                ro['user']['division_name'] = None
                        else:
                            ro['user']['division_name'] = None
                    except:
                        ro['user'] = {}
                else:
                    ro['user'] = {}
                try:
                    result_product = self.rop_model.get_all_request_order_product(self.cursor, ro['id'])
                    ro['product'] = []
                    for rec in result_product:
                        ro['product'].append({
                            'product_name': rec['item_name'],
                            'quantity': rec['qty']
                        })
                except Exception as e:
                    print(e)
                    ro['product'] = []

                try:
                    result_image = self.roi_model.get_all_request_order_image(self.cursor, ro['id'])[0]
                    ro['files'] = result_image['file']
                except Exception as e:
                    print(e)
                    ro['files'] = []

                ro['type'] = 'Request Order'
                data.append(ro)

        result['data'] = data
        result['total'] = count_ro
        result['total_filter'] = count_ro_filter

        # TODO: Check Has Next and Prev
        if result['total_filter'] > page * limit:
            result['has_next'] = True
        else:
            result['has_next'] = False
        if limit <= page * count_ro_filter - count_ro_filter:
            result['has_prev'] = True
        else:
            result['has_prev'] = False
        return result

    def get_request_order_by_id(self, _id: int):
        """
        Get Request Order Information Data

        :param _id: int
        :return:
            Request Order Object
        """
        request_order = self.ro_model.get_request_order_by_id(self.cursor, _id)

        if len(request_order) == 0:
            raise BadRequest("This request order not exist", 500, 1, data=[])
        else:
            request_order = request_order[0]
            if request_order['create_date'] is not None:
                request_order['create_date'] = str(request_order['create_date'])
            if request_order['update_date'] is not None:
                request_order['update_date'] = str(request_order['update_date'])
            if request_order['customer_code'] is not None:
                try:
                    request_order['customer'] = self.customer_model.get_customer_by_id(
                        self.cursor, request_order['customer_code'], select="code, name, address, lng, lat")[0]
                except:
                    request_order['customer'] = {}
            else:
                request_order['customer'] = {}
            if request_order['user_id'] is not None:
                try:
                    request_order['user'] = self.user_model.get_user_by_id(
                        self.cursor, request_order['user_id'], select="id, employee_id, branch_id, division_id")[0]
                    if request_order['user']['employee_id'] is not None:
                        try:
                            request_order['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                self.cursor, request_order['user']['employee_id'], select="name")[0]['name']
                        except:
                            request_order['user']['employee_name'] = None
                    else:
                        request_order['user']['employee_name'] = None
                    if request_order['user']['branch_id'] is not None:
                        try:
                            request_order['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, request_order['user']['branch_id'], select="name")[0]['name']
                        except:
                            request_order['user']['branch_name'] = None
                    else:
                        request_order['user']['branch_name'] = None
                    if request_order['user']['division_id'] is not None:
                        try:
                            request_order['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, request_order['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            request_order['user']['division_name'] = None
                    else:
                        request_order['user']['division_name'] = None
                except:
                    request_order['user'] = {}
            else:
                request_order['user'] = {}

        return request_order

    def get_all_request_product_data(self, _id: int):
        """
        Get Request Order Product Information Data

        :param _id: int
        :return:
            Request Order Object
        """
        product = {}
        data = []
        ro_data = self.rop_model.get_all_request_order_product(self.cursor, _id)
        count = self.rop_model.get_count_all_request_order_product(self.cursor, _id)
        if ro_data:
            for emp in ro_data:
                if emp['create_date'] is not None:
                    emp['create_date'] = str(emp['create_date'])
                if emp['update_date'] is not None:
                    emp['update_date'] = str(emp['update_date'])
                data.append(emp)
        product['data'] = data
        product['total'] = count

        # TODO: Check Has Next and Prev
        product['has_next'] = False
        product['has_prev'] = False
        return product

    def get_all_request_image_data(self, _id: int):
        """
        Get Request Order Images Information Data

        :param _id: int
        :return:
            Request Order Object
        """
        images = {}
        data = []
        ro_data = self.roi_model.get_all_request_order_image(self.cursor, _id)
        count = self.roi_model.get_count_all_request_order_image(self.cursor, _id)
        if ro_data:
            for emp in ro_data:
                if emp['file'] is not None:
                    emp['file'] = emp['file']
                if emp['create_date'] is not None:
                    emp['create_date'] = str(emp['create_date'])
                if emp['update_date'] is not None:
                    emp['update_date'] = str(emp['update_date'])
                data.append(emp)
        images['data'] = data
        images['total'] = count

        # TODO: Check Has Next and Prev
        images['has_next'] = False
        images['has_prev'] = False
        return images

    # TODO: controllers sales order
    def import_so(self, file, user_id: 'int'):
        """
        import sales order
        :param file: file
        :param user_id: int
        :return:
        """
        headers = ['Created date and time', 'Sales order',
                   'Customer code', 'Name', 'Status', 'Item number',
                   'Product name', 'Brand name', 'Branch code', 'Division code', 'Quantity',
                   'Unit price', 'Line amount gross', 'Discount', 'Total discount',
                   'Net amount', 'DPP', 'PPN', 'Notes', 'Packing slip', 'Packing slip date', 'Invoice',
                   'Invoice date', 'Sales code']
        batch_data = []
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_excel(file, sheet_name=0, skiprows=0)
        for idx in df.columns:
            if idx not in headers:
                raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])
        # TODO: Get Parent Sales Order
        df_parent = df[
            ['Sales order', 'Created date and time', 'Customer code', 'Status', 'Notes', 'Packing slip',
             'Packing slip date', 'Invoice', 'Invoice date', 'Branch code', 'Division code', 'Sales code']]
        df_parent.set_index("Sales order", inplace=True)
        df_parent = df_parent.groupby('Sales order').last()
        df_parent.columns = ['create_date', 'customer_code', 'status', 'notes', 'packing_slip_code',
                             'packing_slip_date', 'invoice_code', 'invoice_date', 'branch_code',
                             'division_code', 'user_code']
        df_parent.index.names = ['code']
        # df_parent['user_code'] = df_parent['sales_group'].str.split('-').str[1]
        # df_parent['cycle_number'] = df_parent['sales_group'].str.split('-').str[2]
        # df_parent['branch_code'] = df_parent['site_id'].str[:2]
        # df_parent['division_code'] = df_parent['site_id'].str[2:]
        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)

        # TODO: Get Product from sales order
        for idx in df_parent_json:
            df_product = df[['Item number', 'Product name', 'Brand name', 'Branch code', 'Division code', 'Quantity',
                             'Unit price', 'Line amount gross', 'Discount', 'Total discount', 'Net amount',
                             'DPP', 'PPN']].loc[df['Sales order'] == idx]
            df_product.columns = ['item_number', 'product_name', 'brand_name', 'branch_code', 'division_code',
                                  'quantity', 'unit_price', 'line_amount_gross', 'discount', 'total_discount',
                                  'net_amount', 'dpp', 'dpn']
            # df_product = df_product[['Item number', 'Product name']]
            df_product_list = df_product.to_dict('record')
            df_parent_json[idx]['product'] = df_product_list
            df_parent_json[idx]['invoice_amount'] = 0
            for prod in df_product_list:
                df_parent_json[idx]['invoice_amount'] += int(prod['net_amount'])

        for key, val in df_parent_json.items():
            value = val
            value['code'] = key
            if value['create_date']:
                value['create_date'] = dateutil.parser.parse(value['create_date']).strftime("%Y-%m-%d %H:%M:%S")
            else:
                value['create_date'] = None
            if value['packing_slip_date']:
                value['packing_slip_date'] = dateutil.parser.parse(value['packing_slip_date']).strftime("%Y-%m-%d")
            else:
                value['packing_slip_date'] = None
            if value['invoice_date']:
                value['invoice_date'] = dateutil.parser.parse(value['invoice_date']).strftime("%Y-%m-%d")
            else:
                value['invoice_date'] = None
            value['import_date'] = today
            value['update_date'] = today
            value['import_by'] = user_id
            if value['branch_code'] is not None:
                try:
                    branch_id = self.branch_model.get_branches_by_code(self.cursor, code=value['branch_code'])[0]
                    value['branch_id'] = branch_id['id']
                except:
                    value['branch_id'] = None
            else:
                value['branch_id'] = None
            if value['division_code'] is not None:
                try:
                    division_id = self.division_model.get_division_by_code(
                        self.cursor, code=value['division_code'], _id=None
                    )[0]
                    value['division_id'] = division_id['id']
                except:
                    value['division_id'] = None
            else:
                value['division_id'] = None
            del value['branch_code']
            del value['division_code']
            batch_data.append(value)

        truncate = self.so_model.delete_table(self.cursor)

        for rec in batch_data:
            try:
                result = self.so_model.import_insert(self.cursor, rec, 'code')
                mysql.connection.commit()
            except Exception as e:
                # raise BadRequest(e, 200, 1, data=[])
                pass

        return True

    def import_so_file(self, filename: str, filename_origin: str, table: str, user_id: int):
        """

        :param filename:
        :param filename_origin:
        :param table:
        :param user_id:
        :return:
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.so_model.import_insert_file(self.cursor, file_name=filename,
                                                      file_name_origin=filename_origin, table=table,
                                                      create_date=today, update_date=today, create_by=user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def get_all_sales_order_data(
            self, page: int, limit: int, search: str, column: str, direction: str, branch_privilege: list,
            division_privilege: list, data_filter: list
    ):
        """
        Get List Of Sales Order
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :return:
            list Sales Orders Object
        """
        sales_orders = {}
        data = []
        start = page * limit - limit
        order = ''
        # Without Invoiced
        # where = """WHERE (so.invoice_code is NULL AND (so.status != "canceled" OR so.status is NULL))
        # AND (so.branch_id IN ({0}) AND so.division_id IN ({1})) """.format(
        #     ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        # )
        # With Invoiced
        where = """WHERE (so.status != "canceled" OR so.status is NULL) 
        AND (so.branch_id IN ({0}) AND so.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        where_original = where
        if column:
            if column == 'employee':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'customer':
                order = """ORDER BY c.name {0}""".format(direction)
            else:
                order = """ORDER BY so.{0} {1}""".format(column, direction)
        select = "so.*"
        select_count = "so.code"
        join = """as so LEFT JOIN `users` as u ON so.user_code = u.username 
                        LEFT JOIN `customer` as c ON so.customer_code = c.code
                        LEFT JOIN `employee` as e ON u.employee_id = e.id 
                        LEFT JOIN `branches` as b ON u.branch_id = b.id """
        if search:
            where += """AND (so.code LIKE '%{0}%' OR b.name LIKE '%{0}%' 
                    OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                where += """AND (so.create_date >= '{0} 00:00:00' AND so.create_date <= '{1} 23:59:59') """.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            if data_filter['branch_id']:
                where += """AND so.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
            if data_filter['division_id']:
                where += """AND so.division_id IN ({0}) """.format(
                    ", ".join(str(x) for x in data_filter['division_id']))
        so_data = self.so_model.get_all_sales_order(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.so_model.get_count_all_sales_order(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.so_model.get_count_all_sales_order(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if so_data:
            for so in so_data:
                if so['packing_slip_code'] is not None and so['invoice_code'] is not None:
                    so['status'] = 'invoiced'
                elif so['packing_slip_code'] is not None and so['invoice_code'] is None:
                    so['status'] = 'Packing Slip'
                else:
                    so['status'] = 'Open Order'
                if so['product'] is not None:
                    so['product'] = json.loads(so['product'])
                if so['create_date'] is not None:
                    so['create_date'] = str(so['create_date'])
                if so['invoice_date'] is not None:
                    so['invoice_date'] = str(so['invoice_date'])
                if so['packing_slip_date'] is not None:
                    so['packing_slip_date'] = str(so['packing_slip_date'])
                if so['customer_code'] is not None:
                    try:
                        so['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, so['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        so['customer'] = {}
                else:
                    so['customer'] = {}
                if so['user_code'] is not None:
                    try:
                        so['user'] = self.user_model.get_user_by_username(self.cursor, so['user_code'],
                                                                          select="id, employee_id, branch_id, "
                                                                                 "division_id")[0]
                        if so['user']['employee_id'] is not None:
                            try:
                                so['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, so['user']['employee_id'], select="name")[0]['name']
                            except:
                                so['user']['employee_name'] = None
                        else:
                            so['user']['employee_name'] = None
                        if so['user']['branch_id'] is not None:
                            try:
                                so['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, so['user']['branch_id'], select="name")[0]['name']
                            except:
                                so['user']['branch_name'] = None
                        else:
                            so['user']['branch_name'] = None
                        if so['user']['division_id'] is not None:
                            try:
                                so['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, so['user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                so['user']['division_name'] = None
                        else:
                            so['user']['division_name'] = None
                    except:
                        so['user'] = {}
                else:
                    so['user'] = {}
                if so['branch_id'] is not None:
                    try:
                        so['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, so['branch_id'], select="name")[0]['name']
                    except:
                        so['branch_name'] = None
                else:
                    so['branch_name'] = None
                if so['division_id'] is not None:
                    try:
                        so['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, so['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        so['division_name'] = None
                else:
                    so['division_name'] = None
                data.append(so)
        sales_orders['data'] = data
        sales_orders['total'] = count
        sales_orders['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if sales_orders['total'] > page * limit:
            sales_orders['has_next'] = True
        else:
            sales_orders['has_next'] = False
        if limit <= page * count - count:
            sales_orders['has_prev'] = True
        else:
            sales_orders['has_prev'] = False
        return sales_orders

    def get_all_export_sales_order_data(
            self, page: int, limit: int, search: str, column: str, direction: str, branch_privilege: list,
            division_privilege: list, data_filter: list
    ):
        """
        Get List Of Sales Order
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :return:
            list Sales Orders Object
        """
        result_data = {}
        data = []
        start = page * limit - limit
        order = ''
        # Without Invoiced
        # where = """WHERE (so.invoice_code is NULL AND (so.status != "canceled" OR so.status is NULL))
        # AND (so.branch_id IN ({0}) AND so.division_id IN ({1})) """.format(
        #     ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        # )
        # With Invoiced
        where = """WHERE (so.status != "canceled" OR so.status is NULL) 
        AND (so.branch_id IN ({0}) AND so.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        where_original = where
        if column:
            if column == 'employee':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'customer':
                order = """ORDER BY c.name {0}""".format(direction)
            else:
                order = """ORDER BY so.{0} {1}""".format(column, direction)
        select = "so.*"
        select_count = "so.code"
        join = """as so LEFT JOIN `users` as u ON so.user_code = u.username 
                        LEFT JOIN `customer` as c ON so.customer_code = c.code
                        LEFT JOIN `employee` as e ON u.employee_id = e.id 
                        LEFT JOIN `branches` as b ON u.branch_id = b.id """
        if search:
            where += """AND (so.code LIKE '%{0}%' OR b.name LIKE '%{0}%' 
                    OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)
        if data_filter:
            tmp_data_filter = data_filter[0]
            if tmp_data_filter['start_date']:
                where += """AND (so.create_date >= '{0} 00:00:00' AND so.create_date <= '{1} 23:59:59') """.format(
                    tmp_data_filter['start_date'], tmp_data_filter['end_date']
                )
            if tmp_data_filter['branch_id']:
                where += """AND so.branch_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['branch_id']))
            if tmp_data_filter['division_id']:
                where += """AND so.division_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['division_id']))
        so_data = self.so_model.get_all_sales_order(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.so_model.get_count_all_sales_order(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.so_model.get_count_all_sales_order(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if so_data:
            for so in so_data:
                if so['packing_slip_code'] is not None and so['invoice_code'] is not None:
                    so['status'] = 'invoiced'
                elif so['packing_slip_code'] is not None and so['invoice_code'] is None:
                    so['status'] = 'Packing Slip'
                else:
                    so['status'] = 'Open Order'
                if so['product'] is not None:
                    so['product'] = json.loads(so['product'])
                if so['create_date'] is not None:
                    so['create_date'] = str(so['create_date'])
                if so['invoice_date'] is not None:
                    so['invoice_date'] = str(so['invoice_date'])
                if so['packing_slip_date'] is not None:
                    so['packing_slip_date'] = str(so['packing_slip_date'])
                if so['customer_code'] is not None:
                    try:
                        so['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, so['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        so['customer'] = {}
                else:
                    so['customer'] = {}
                if so['user_code'] is not None:
                    try:
                        so['user'] = self.user_model.get_user_by_username(self.cursor, so['user_code'],
                                                                          select="id, employee_id, branch_id, "
                                                                                 "division_id")[0]
                        if so['user']['employee_id'] is not None:
                            try:
                                so['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, so['user']['employee_id'], select="name")[0]['name']
                            except:
                                so['user']['employee_name'] = None
                        else:
                            so['user']['employee_name'] = None
                        if so['user']['branch_id'] is not None:
                            try:
                                so['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, so['user']['branch_id'], select="name")[0]['name']
                            except:
                                so['user']['branch_name'] = None
                        else:
                            so['user']['branch_name'] = None
                        if so['user']['division_id'] is not None:
                            try:
                                so['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, so['user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                so['user']['division_name'] = None
                        else:
                            so['user']['division_name'] = None
                    except:
                        so['user'] = {}
                else:
                    so['user'] = {}
                if so['branch_id'] is not None:
                    try:
                        so['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, so['branch_id'], select="name")[0]['name']
                    except:
                        so['branch_name'] = None
                else:
                    so['branch_name'] = None
                if so['division_id'] is not None:
                    try:
                        so['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, so['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        so['division_name'] = None
                else:
                    so['division_name'] = None
                data.append(so)
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Sales Order')
        merge_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter'
            }
        )
        # Header sheet
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                worksheet.merge_range(
                    'A1:F1',
                    'SALES ORDER (TANGGAL: {0} s/d {1})'.format(
                        data_filter['start_date'], data_filter['end_date']
                    ),
                    merge_format
                )
            else:
                worksheet.merge_range(
                    'A1:F1',
                    'SALES ORDER (TANGGAL: ALL)',
                    merge_format
                )
        else:
            worksheet.merge_range('A1:F1', 'SALES ORDER (TANGGAL: ALL)', merge_format)

        worksheet.write('A3', 'NO SALES ORDER', merge_format)
        worksheet.write('B3', 'TANGGAL', merge_format)
        worksheet.write('C3', 'BRANCH', merge_format)
        worksheet.write('D3', 'DIVISION', merge_format)
        worksheet.write('E3', 'CUSTOMER', merge_format)
        worksheet.write('F3', 'SALES REP', merge_format)
        worksheet.write('G3', 'STATUS', merge_format)

        data_rows = 3
        for rec in data:
            worksheet.write(data_rows, 0, rec['code'])
            worksheet.write(data_rows, 1, rec['create_date'])
            worksheet.write(data_rows, 2, rec['branch_name'])
            worksheet.write(data_rows, 3, rec['division_name'])
            worksheet.write(data_rows, 4, rec['customer_code'])
            worksheet.write(data_rows, 5, rec['user_code'])
            worksheet.write(data_rows, 6, rec['status'])
            data_rows += 1

        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_all_export_pdf_sales_order_data(
            self, page: int, limit: int, search: str, column: str, direction: str, branch_privilege: list,
            division_privilege: list, data_filter: list
    ):
        """
        Get List Of Sales Order
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :return:
            list Sales Orders Object
        """
        result_data = {}
        data = []
        start = page * limit - limit
        order = ''
        # Without Invoiced
        # where = """WHERE (so.invoice_code is NULL AND (so.status != "canceled" OR so.status is NULL))
        # AND (so.branch_id IN ({0}) AND so.division_id IN ({1})) """.format(
        #     ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        # )
        # With Invoiced
        where = """WHERE (so.status != "canceled" OR so.status is NULL) 
        AND (so.branch_id IN ({0}) AND so.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        where_original = where
        if column:
            if column == 'employee':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'customer':
                order = """ORDER BY c.name {0}""".format(direction)
            else:
                order = """ORDER BY so.{0} {1}""".format(column, direction)
        select = "so.*"
        select_count = "so.code"
        join = """as so LEFT JOIN `users` as u ON so.user_code = u.username 
                        LEFT JOIN `customer` as c ON so.customer_code = c.code
                        LEFT JOIN `employee` as e ON u.employee_id = e.id 
                        LEFT JOIN `branches` as b ON u.branch_id = b.id """
        if search:
            where += """AND (so.code LIKE '%{0}%' OR b.name LIKE '%{0}%' 
                    OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)
        if data_filter:
            tmp_data_filter = data_filter[0]
            if tmp_data_filter['start_date']:
                where += """AND (so.create_date >= '{0} 00:00:00' AND so.create_date <= '{1} 23:59:59') """.format(
                    tmp_data_filter['start_date'], tmp_data_filter['end_date']
                )
            if tmp_data_filter['branch_id']:
                where += """AND so.branch_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['branch_id']))
            if tmp_data_filter['division_id']:
                where += """AND so.division_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['division_id']))
        so_data = self.so_model.get_all_sales_order(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.so_model.get_count_all_sales_order(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.so_model.get_count_all_sales_order(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if so_data:
            for so in so_data:
                if so['packing_slip_code'] is not None and so['invoice_code'] is not None:
                    so['status'] = 'invoiced'
                elif so['packing_slip_code'] is not None and so['invoice_code'] is None:
                    so['status'] = 'Packing Slip'
                else:
                    so['status'] = 'Open Order'
                if so['product'] is not None:
                    so['product'] = json.loads(so['product'])
                if so['create_date'] is not None:
                    so['create_date'] = str(so['create_date'])
                if so['invoice_date'] is not None:
                    so['invoice_date'] = str(so['invoice_date'])
                if so['packing_slip_date'] is not None:
                    so['packing_slip_date'] = str(so['packing_slip_date'])
                if so['customer_code'] is not None:
                    try:
                        so['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, so['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        so['customer'] = {}
                else:
                    so['customer'] = {}
                if so['user_code'] is not None:
                    try:
                        so['user'] = self.user_model.get_user_by_username(self.cursor, so['user_code'],
                                                                          select="id, employee_id, branch_id, "
                                                                                 "division_id")[0]
                        if so['user']['employee_id'] is not None:
                            try:
                                so['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, so['user']['employee_id'], select="name")[0]['name']
                            except:
                                so['user']['employee_name'] = None
                        else:
                            so['user']['employee_name'] = None
                        if so['user']['branch_id'] is not None:
                            try:
                                so['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, so['user']['branch_id'], select="name")[0]['name']
                            except:
                                so['user']['branch_name'] = None
                        else:
                            so['user']['branch_name'] = None
                        if so['user']['division_id'] is not None:
                            try:
                                so['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, so['user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                so['user']['division_name'] = None
                        else:
                            so['user']['division_name'] = None
                    except:
                        so['user'] = {}
                else:
                    so['user'] = {}
                if so['branch_id'] is not None:
                    try:
                        so['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, so['branch_id'], select="name")[0]['name']
                    except:
                        so['branch_name'] = None
                else:
                    so['branch_name'] = None
                if so['division_id'] is not None:
                    try:
                        so['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, so['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        so['division_name'] = None
                else:
                    so['division_name'] = None
                data.append(so)

        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                head_title = 'SALES ORDER (TANGGAL: {0} s/d {1})'.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            else:
                head_title = 'SALES ORDER (TANGGAL: ALL)'
        else:
            head_title = 'SALES ORDER (TANGGAL: ALL)'

        head_table = OrderedDict()
        head_table['no'] = "NO SALES ORDER"
        head_table['tanggal'] = "TANGGAL"
        head_table['branch'] = "BRANCH"
        head_table['division'] = "DIVISION"
        head_table['customer'] = "CUSTOMER"
        head_table['sales'] = "SALES REP"
        head_table['status'] = "STATUS"
        body_table = []
        for rec in data:
            data_body = OrderedDict()
            data_body['no'] = rec['code']
            data_body['tanggal'] = rec['create_date']
            data_body['branch'] = rec['branch_name']
            data_body['division'] = rec['division_name']
            data_body['customer'] = rec['customer_code']
            data_body['sales'] = rec['user_code']
            data_body['status'] = rec['status']
            body_table.append(data_body)
        # rendered = render_template(
        #     'report_template.html', head_title=head_title, head_table=head_table,
        #     head_customer_table=head_customer_table, body_table=body_table, category="sales"
        # )
        rendered = render_template(
            'report_template.html', head_title=head_title, head_table=head_table, body_table=body_table
        )
        output = pdfkit.from_string(rendered, False)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_all_sales_order_by_list_customer(self, page: int, limit: int, customer: list, user_id: int, username: str):
        """
        Get List Of Sales Order
        :param: page: int
        :param: limit: int
        :param: customer: list
        :param: user_id: int
        :param: username: str
        :return:
            list Request Orders Object
        """
        # today = datetime.today()
        # today = today.strftime("%Y-%m-%d")
        today = "2018-06-04"

        result = {}
        data = []
        start = page * limit - limit

        # TODO: Get Sales Order
        # where = """WHERE `invoice_code` is NULL AND `customer_code` = '{0}'
        # AND `user_code` = '{1}'""".format(customer, username)
        where = """WHERE `invoice_code` is NULL AND `customer_code` IN ('{0}')""".format(
            "', '".join(x for x in customer))
        so_data = self.so_model.get_all_sales_order(self.cursor, where=where, start=start, limit=limit)
        count_so = self.so_model.get_count_all_sales_order(self.cursor, where=where)
        count_so_filter = count_so

        if so_data:
            for so in so_data:
                if so['packing_slip_code'] is not None and so['invoice_code'] is not None:
                    so['status'] = 'invoiced'
                elif so['packing_slip_code'] is not None and so['invoice_code'] is None:
                    so['status'] = 'Packing Slip'
                else:
                    so['status'] = 'Open Order'
                if so['product'] is not None:
                    so['product'] = json.loads(so['product'])
                if so['create_date'] is not None:
                    so['create_date'] = str(so['create_date'])
                if so['invoice_date'] is not None:
                    so['invoice_date'] = str(so['invoice_date'])
                if so['packing_slip_date'] is not None:
                    so['packing_slip_date'] = str(so['packing_slip_date'])
                if so['customer_code'] is not None:
                    try:
                        so['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, so['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        so['customer'] = {}
                else:
                    so['customer'] = {}
                if so['user_code'] is not None:
                    try:
                        so['user'] = self.user_model.get_user_by_username(self.cursor, so['user_code'],
                                                                          select="id, employee_id, branch_id, "
                                                                                 "division_id")[0]
                        if so['user']['employee_id'] is not None:
                            try:
                                so['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, so['user']['employee_id'], select="name")[0]['name']
                            except:
                                so['user']['employee_name'] = None
                        else:
                            so['user']['employee_name'] = None
                        if so['user']['branch_id'] is not None:
                            try:
                                so['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, so['user']['branch_id'], select="name")[0]['name']
                            except:
                                so['user']['branch_name'] = None
                        else:
                            so['user']['branch_name'] = None
                        if so['user']['division_id'] is not None:
                            try:
                                so['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, so['user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                so['user']['division_name'] = None
                        else:
                            so['user']['division_name'] = None
                    except:
                        so['user'] = {}
                else:
                    so['user'] = {}

                so['type'] = 'Sales Order'
                data.append(so)

        result['data'] = data
        result['total'] = count_so
        result['total_filter'] = count_so_filter

        # TODO: Check Has Next and Prev
        if result['total_filter'] > page * limit:
            result['has_next'] = True
        else:
            result['has_next'] = False
        if limit <= page * count_so_filter - count_so_filter:
            result['has_prev'] = True
        else:
            result['has_prev'] = False
        return result

    def get_sales_order_by_id(self, _id: int):
        """
        Get Sales Order Information Data

        :param _id: int
        :return:
            Sales Order Object
        """
        sales_order = self.so_model.get_sales_order_by_id(self.cursor, _id)

        if len(sales_order) == 0:
            raise BadRequest("This sales order not exist", 200, 1, data=[])
        else:
            sales_order = sales_order[0]
            if sales_order['product'] is not None:
                sales_order['product'] = json.loads(sales_order['product'])
            if sales_order['create_date'] is not None:
                sales_order['create_date'] = str(sales_order['create_date'])
            if sales_order['invoice_date'] is not None:
                sales_order['invoice_date'] = str(sales_order['invoice_date'])
            if sales_order['packing_slip_date'] is not None:
                sales_order['packing_slip_date'] = str(sales_order['packing_slip_date'])

            if sales_order['customer_code'] is not None:
                try:
                    sales_order['customer'] = self.customer_model.get_customer_by_id(
                        self.cursor, sales_order['customer_code'], select="code, name, address, lng, lat")[0]
                except:
                    sales_order['customer'] = {}
            else:
                sales_order['customer'] = {}
            if sales_order['user_code'] is not None:
                try:
                    sales_order['user'] = self.user_model.get_user_by_username(self.cursor, sales_order['user_code'],
                                                                               select="id, employee_id, branch_id, "
                                                                                      "division_id")[0]
                    if sales_order['user']['employee_id'] is not None:
                        try:
                            sales_order['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                self.cursor, sales_order['user']['employee_id'], select="name")[0]['name']
                        except:
                            sales_order['user']['employee_name'] = None
                    else:
                        sales_order['user']['employee_name'] = None
                    if sales_order['user']['branch_id'] is not None:
                        try:
                            sales_order['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, sales_order['user']['branch_id'], select="name")[0]['name']
                        except:
                            sales_order['user']['branch_name'] = None
                    else:
                        sales_order['user']['branch_name'] = None
                    if sales_order['user']['division_id'] is not None:
                        try:
                            sales_order['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, sales_order['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            sales_order['user']['division_name'] = None
                    else:
                        sales_order['user']['division_name'] = None
                except:
                    sales_order['user'] = {}
            else:
                sales_order['user'] = {}

        return sales_order

    def get_all_sales_order_import(self):
        """
        Get List Of Sales Order
        :return:
            list Sales Orders Object
        """
        import_file = {}
        data = []
        import_data = self.so_model.get_all_sales_order_import(self.cursor, where="""WHERE `status` = 0 
        AND `table_name` = 'sales_order'""")
        count = self.so_model.get_count_all_sales_order_import(self.cursor, key="id", where="""WHERE `status` = 0 
        AND `table_name` = 'sales_order'""")
        if import_data:
            for emp in import_data:
                data.append(emp)
        import_file['data'] = data
        import_file['total'] = count

        # TODO: Check Has Next and Prev
        import_file['has_next'] = False
        import_file['has_prev'] = False
        return import_file

    # TODO: Controllers for sales payment
    def create_payment_mobile(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create payment

        :param create_data: dict
        :param user_id: int
        :return:
            Request Order Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            create = self.spm_model.insert_into_db(
                self.cursor, visit_plan_id=create_data['visit_plan_id'], customer_code=create_data['customer_code'],
                invoice=create_data['invoice'], invoice_amount=create_data['invoice_amount'],
                payment_amount=create_data['payment_amount'], payment_date=today,
                # payment_method=create_data['payment_method'], payment_info=create_data['payment_info'],
                receipt_printed=create_data['receipt_printed'], create_by=user_id, create_date=today, update_date=today
            )
            mysql.connection.commit()
            # last_insert_id = mysql.connection.insert_id()
            last_insert_id = self.cursor.lastrowid
            print(last_insert_id)
            update_data = {
                "id": last_insert_id,
                "code": "PAY-{0:04}".format(last_insert_id),
                "receipt_code": "PAY-{0:04}".format(last_insert_id)
            }
            update = self.spm_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return last_insert_id

    def update_payment_reprint(self, update_data: 'dict', _id: 'int'):
        """
        Update division
        :param update_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.spm_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    # def import_sp(self, file, user_id: 'int'):
    #     """
    #     import sales payment
    #     :param file: file
    #     :param user_id: int
    #     :return:
    #     """
    #     headers = ["Invoice Code", "Invoice Date", "Customer Code", "Sales Order Code", "Sales Order Date",
    #                "Packing Slip", "Packing Slip Date", "Invoice Amount", "Payment Due Date", "Payment Date",
    #                "Payment Amount", "Notes", "Payment Status", "Branch Id", "Division Id", "Item Number",
    #                "Product Name", "Brand Name", "Quantity", "Unit Price", "Unit Discount", "Line Amount Gross",
    #                "Total Discount", "DPP", "PPN", "Net Amount"]
    #     batch_data = []
    #     today = datetime.today()
    #     today = today.strftime("%Y-%m-%d %H:%M:%S")
    #
    #     df = pd.read_excel(file, sheet_name=0, skiprows=0)
    #     for idx in df.columns:
    #         if idx not in headers:
    #             raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])
    #     # TODO: Get Parent Sales Payment
    #     df_parent = df[
    #         ['Invoice Code', 'Invoice Date', 'Customer Code', 'Payment Status', 'Notes', 'Packing Slip',
    #          'Packing Slip Date', 'Sales Order Date', 'Sales Order Code', 'Payment Due Date', 'Payment Date',
    #          'Invoice Amount', 'Payment Amount', 'Branch Id', 'Division Id']]
    #     df_parent.set_index("Invoice Code", inplace=True)
    #     df_parent = df_parent.groupby('Invoice Code').last()
    #     df_parent.columns = ['invoice_date', 'customer_code', 'status', 'notes', 'packing_slip_code',
    #                          'packing_slip_date', 'sales_order_date', 'sales_order_code', 'payment_due_date',
    #                          'payment_date', 'invoice_amount', 'payment_amount', 'branch_code', 'division_code']
    #     df_parent.index.names = ['code']
    #     # df_parent['branch_code'] = df_parent['site_id'].str[:2]
    #     # df_parent['division_code'] = df_parent['site_id'].str[2:]
    #     df_parent_json = df_parent.to_json(orient='index', date_format='iso')
    #     df_parent_json = json.loads(df_parent_json)
    #
    #     # TODO: Get Product from sales payment
    #     for idx in df_parent_json:
    #         df_product = df[['Item Number', 'Product Name', 'Brand Name', 'Branch Id', 'Division Id', 'Quantity',
    #                          'Unit Price', 'Line Amount Gross', 'Unit Discount', 'Total Discount', 'Net Amount',
    #                          'DPP', 'PPN']].loc[df['Invoice Code'] == idx]
    #         df_product.columns = ['item_number', 'product_name', 'brand_name', 'branch_code', 'division_code',
    #                               'quantity', 'unit_price', 'line_amount_gross', 'discount', 'total_discount',
    #                               'net_amount', 'dpp', 'dpn']
    #         df_product_list = df_product.to_dict('record')
    #         df_parent_json[idx]['product'] = df_product_list
    #
    #     for key, val in df_parent_json.items():
    #         value = val
    #         value['code'] = key
    #         if value['sales_order_date']:
    #             value['sales_order_date'] = dateutil.parser.parse(value['sales_order_date']).strftime("%Y-%m-%d %H:%M:%S")
    #         else:
    #             value['sales_order_date'] = None
    #         if value['invoice_date']:
    #             value['invoice_date'] = dateutil.parser.parse(value['invoice_date']).strftime("%Y-%m-%d %H:%M:%S")
    #         else:
    #             value['invoice_date'] = None
    #         if value['packing_slip_date']:
    #             value['packing_slip_date'] = dateutil.parser.parse(value['packing_slip_date']).strftime("%Y-%m-%d")
    #         else:
    #             value['packing_slip_date'] = None
    #         if value['payment_due_date']:
    #             value['payment_due_date'] = dateutil.parser.parse(value['payment_due_date']).strftime("%Y-%m-%d %H:%M:%S")
    #         else:
    #             value['payment_due_date'] = None
    #         value['import_date'] = today
    #         value['update_date'] = today
    #         value['import_by'] = user_id
    #         if value['payment_date']:
    #             value['payment_date'] = dateutil.parser.parse(value['payment_date']).strftime("%Y-%m-%d %H:%M:%S")
    #         if value['payment_amount'] is None:
    #             value['payment_amount'] = 0
    #         if value['invoice_amount'] != 0:
    #             if value['branch_code'] is not None:
    #                 try:
    #                     branch_id = self.branch_model.get_branches_by_code(self.cursor, code=value['branch_code'])[0]
    #                     value['branch_id'] = branch_id['id']
    #                 except:
    #                     value['branch_id'] = None
    #             else:
    #                 value['branch_id'] = None
    #             if value['division_code'] is not None:
    #                 try:
    #                     division_id = self.division_model.get_division_by_code(
    #                         self.cursor, code=value['division_code'], _id=None
    #                     )[0]
    #                     value['division_id'] = division_id['id']
    #                 except:
    #                     value['division_id'] = None
    #             else:
    #                 value['division_id'] = None
    #             del value['branch_code']
    #             del value['division_code']
    #             # del value['site_id']
    #             batch_data.append(value)
    #
    #     truncate = self.sp_model.delete_table(self.cursor)
    #
    #     for rec in batch_data:
    #         try:
    #             result = self.sp_model.import_insert(self.cursor, rec, 'code')
    #             mysql.connection.commit()
    #         except Exception as e:
    #             # raise BadRequest(e, 200, 1, data=[])
    #             pass
    #
    #     return True

    # TODO: controllers invoice new format
    def import_sp(self, file, user_id: 'int'):
        """
        import sales payment
        :param file: file
        :param user_id: int
        :return:
        """
        headers = ['CUSTKEY', 'TANGGAL_FAKTUR', 'JUMLAH_DPP', 'INVNO', 'KODE_OBJEK', 'NAMA', 'JUMLAH_BARANG',
                   'HARGA_SATUAN', 'HARGA_TOTAL', 'DISKON', 'DPP', 'PPN', 'BRANCH CODE', 'DIVISION CODE']
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_excel(file, sheet_name=0, skiprows=0)
        for idx in df.columns:
            if idx not in headers:
                raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])
        # TODO: Get Parent Sales Payment
        df_parent = df[
            [
                'INVNO', 'CUSTKEY', 'TANGGAL_FAKTUR', 'JUMLAH_DPP', 'BRANCH CODE', 'DIVISION CODE'
            ]
        ]
        df_parent.set_index('INVNO', inplace=True)
        df_parent = df_parent.groupby('INVNO').last()
        df_parent.columns = [
            'customer_code', 'invoice_date', 'payment_amount', 'branch_code', 'division_code'
        ]
        df_parent.index.names = ['code']
        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)

        # TODO: Get Product from sales payment
        for idx in df_parent_json:
            df_product = df[[
                'KODE_OBJEK', 'NAMA', 'JUMLAH_BARANG', 'HARGA_SATUAN', 'HARGA_TOTAL', 'DISKON', 'DPP', 'PPN'
            ]].loc[df['INVNO'] == idx]
            df_product.fillna(0, inplace=True)
            df_product.columns = ['item_number', 'product_name', 'quantity', 'unit_price', 'net_mount', 'discount',
                                  'dpp', 'dpn']
            df_product_list = df_product.to_dict('record')
            df_parent_json[idx]['product'] = df_product_list

        data_invoice = dict()
        for key, val in df_parent_json.items():
            data_invoice['code'] = key
            data_invoice['invoice_date'] = dateutil.parser.parse(val['invoice_date']).strftime("%Y-%m-%d %H:%M:%S")
            data_invoice['customer_code'] = val['customer_code']

            data_invoice['status'] = 'Not paid, not past due'
            data_invoice['notes'] = None
            data_invoice['invoice_due_date'] = None
            data_invoice['payment_date'] = None
            data_invoice['payment_due_date'] = None
            data_invoice['packing_slip_code'] = None
            data_invoice['packing_slip_date'] = None
            data_invoice['sales_order_code'] = None
            data_invoice['sales_order_date'] = None
            data_invoice['invoice_amount'] = val['payment_amount']
            data_invoice['product'] = val['product']
            if val['branch_code'] is not None:
                try:
                    branch_id = self.branch_model.get_branches_by_code(self.cursor, code=val['branch_code'])[0]
                    data_invoice['branch_id'] = branch_id['id']
                except:
                    data_invoice['branch_id'] = 1
            else:
                data_invoice['branch_id'] = 1
            if val['division_code'] is not None:
                try:
                    division_id = self.division_model.get_division_by_code(
                        self.cursor, code=val['division_code'], _id=None
                    )[0]
                    data_invoice['division_id'] = division_id['id']
                except:
                    data_invoice['division_id'] = 1
            else:
                data_invoice['division_id'] = 1
            data_invoice['import_date'] = today
            data_invoice['update_date'] = today
            data_invoice['import_by'] = user_id
            self.sp_model.import_insert(self.cursor, data_invoice, 'code')

        try:
            mysql.connection.commit()
        except Exception as e:
            pass

        return True

    def import_sp_file(self, filename: str, filename_origin: str, table: str, user_id: int):
        """

        :param filename:
        :param filename_origin:
        :param table:
        :param user_id:
        :return:
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.sp_model.import_insert_file(self.cursor, file_name=filename,
                                                      file_name_origin=filename_origin, table=table,
                                                      create_date=today, update_date=today, create_by=user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def get_all_sales_payment_data(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of Sales Payment
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :return:
            list Sales Payment Object
        """
        sales_payment = {}
        data = []
        start = page * limit - limit
        order_flag = False
        order = ''
        if column:
            if column == 'customer':
                order_flag = True
                order = """ORDER BY c.name {0}""".format(direction)
            elif column == 'branch':
                order_flag = True
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'employee':
                order_flag = True
                order = """ORDER BY e.name {0}""".format(direction)
            else:
                if search:
                    order = """ORDER BY sp.{0} {1}""".format(column, direction)
                else:
                    order = """ORDER BY {0} {1}""".format(column, direction)

        if search or order_flag:
            select = "sp.*"
            select_count = "sp.code"
            join = """as sp LEFT JOIN `customer` as c ON sp.customer_code = c.code 
            LEFT JOIN `sales_orders` as so ON sp.sales_order_code = so.code
            LEFT JOIN `users` as u ON so.user_code = u.username 
            LEFT JOIN `employee` as e ON u.employee_id = e.id 
            LEFT JOIN `branches` as b ON u.branch_id = b.id"""
            where = ''
            if search:
                where = """WHERE (c.name LIKE '%{0}%' OR e.name LIKE '%{0}%' 
                OR b.name LIKE '%{0}%' OR sp.code LIKE '%{0}%')""".format(search)
            sp_data = self.sp_model.get_all_sales_payment(self.cursor, select=select, join=join, where=where,
                                                          order=order, start=start, limit=limit)
            count_filter = self.sp_model.get_count_all_sales_payment(self.cursor, select=select_count, join=join,
                                                                     where=where)
            count = self.sp_model.get_count_all_sales_payment(self.cursor)
        else:
            sp_data = self.sp_model.get_all_sales_payment(self.cursor, start=start, limit=limit, order=order)
            count = self.sp_model.get_count_all_sales_payment(self.cursor)
            count_filter = count
        if sp_data:
            for sp in sp_data:
                if sp['product'] is not None:
                    sp['product'] = json.loads(sp['product'])
                if sp['invoice_date'] is not None:
                    sp['invoice_date'] = str(sp['invoice_date'])
                if sp['packing_slip_date'] is not None:
                    sp['packing_slip_date'] = str(sp['packing_slip_date'])
                if sp['payment_date'] is not None:
                    sp['payment_date'] = str(sp['payment_date'])
                if sp['payment_due_date'] is not None:
                    sp['payment_due_date'] = str(sp['payment_due_date'])
                if sp['invoice_amount'] == sp['payment_amount']:
                    sp['status'] = "Paid"
                else:
                    if sp['payment_amount'] == 0 or sp['payment_amount'] is None:
                        sp['status'] = 'Not Paid'
                    else:
                        sp['status'] = 'Partial Paid'

                if sp['customer_code'] is not None:
                    try:
                        sp['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, sp['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        sp['customer'] = {}
                else:
                    sp['customer'] = {}
                if sp['sales_order_code'] is not None:
                    try:
                        so_data = self.so_model.get_sales_order_by_id(
                            self.cursor, sp['sales_order_code'], select="user_code")[0]['user_code']
                        sp['user'] = self.user_model.get_user_by_username(
                            self.cursor, so_data, select="id, employee_id, branch_id")[0]
                        if sp['user']['employee_id'] is not None:
                            try:
                                sp['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, sp['user']['employee_id'], select="name")[0]['name']
                            except:
                                sp['user']['employee_name'] = None
                        else:
                            sp['user']['employee_name'] = None
                        if sp['user']['branch_id'] is not None:
                            try:
                                sp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, sp['user']['branch_id'], select="name")[0]['name']
                            except:
                                sp['user']['branch_name'] = None
                        else:
                            sp['user']['branch_name'] = None
                    except:
                        sp['user'] = {}
                else:
                    sp['user'] = {}
                data.append(sp)
        sales_payment['data'] = data
        sales_payment['total'] = count
        sales_payment['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if sales_payment['total'] > page * limit:
            sales_payment['has_next'] = True
        else:
            sales_payment['has_next'] = False
        if limit <= page * count - count:
            sales_payment['has_prev'] = True
        else:
            sales_payment['has_prev'] = False
        return sales_payment

    def get_all_payment_mobile_data(
            self, page: int, limit: int, search: str, column: str, direction: str, tipe: str, visit_plan_id: int,
            customer: str, branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of Sales Payment
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: tipe: str
        :param: visit_plan_id: int
        :param: customer: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            list Sales Payment Object
        """
        sales_payment = {}
        data = []
        start = page * limit - limit
        join = ''
        order = ''
        if tipe == "mobile":
            if customer:
                where = """WHERE `visit_plan_id` = {0} AND `customer_code` = '{1}' """.format(visit_plan_id, customer)
            else:
                where = """WHERE `visit_plan_id` = {0} """.format(visit_plan_id)
            select = '*'
            select_count = 'id'
        else:
            if column:
                if column == 'name':
                    order = """ORDER BY e.name {1}""".format(column, direction)
                elif column == 'branch':
                    order = """ORDER BY b.name {0}""".format(direction)
                else:
                    order = """ORDER BY spm.{0} {1}""".format(column, direction)
            where = "WHERE (e.job_function = 'sales' AND u.branch_id IN ({0}) AND u.division_id IN ({1})) ".format(
                ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
            join = """as spm LEFT JOIN `users` as u ON spm.create_by = u.id 
            LEFT JOIN `employee` as e ON u.employee_id = e.id 
            LEFT JOIN `branches` as b ON u.branch_id = b.id"""
            select = "spm.*"
            select_count = "spm.id"
            if search:
                where += """AND (spm.code LIKE '%{0}%' OR spm.customer_code LIKE '%{0}%' 
                OR e.name LIKE '%{0}%' OR b.name LIKE '%{0}%' OR spm.code LIKE '%{0}%') """.format(search)
            if data_filter:
                data_filter = data_filter[0]
                if data_filter['start_date']:
                    where += """AND (spm.payment_date >= '{0} 00:00:00' AND spm.payment_date <= '{1} 23:59:59') """.format(
                        data_filter['start_date'], data_filter['end_date']
                    )
                if data_filter['user_id']:
                    where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
                if data_filter['branch_id']:
                    where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
                if data_filter['division_id']:
                    where += """AND u.division_id IN ({0}) """.format(
                        ", ".join(str(x) for x in data_filter['division_id']))
        sp_data = self.spm_model.get_all_sales_payment(
            self.cursor, select=select, where=where, join=join, start=start, limit=limit, order=order
        )
        count = self.spm_model.get_count_all_sales_payment(self.cursor, select=select_count, where=where, join=join)
        count_filter = count

        if sp_data:
            for sp in sp_data:
                if sp['payment_date'] is not None:
                    sp['payment_date'] = str(sp['payment_date'])
                # set data json invoice to None (For index list payment)
                # to prevent loading large data image on frontend
                if tipe == 'web':
                    sp['invoice'] = None
                if sp['invoice'] is not None:
                    sp['invoice'] = json.loads(sp['invoice'])
                if sp['payment_info'] is not None:
                    sp['payment_info'] = json.loads(sp['payment_info'])
                if sp['is_canceled'] == 1:
                    sp['payment_status'] = "Canceled"
                elif sp['is_confirm'] == 1 and sp['is_canceled'] == 0:
                    sp['payment_status'] = "Confirmed"
                elif sp['is_confirm'] == 0 and sp['is_confirm_cancel'] == 1:
                    sp['payment_status'] = "Pending Cancelation"
                else:
                    sp['payment_status'] = "Pending"
                try:
                    sp['user'] = self.user_model.get_user_by_id(
                        self.cursor, sp['create_by'], select="id, employee_id, branch_id, division_id")[0]
                    if sp['user']['employee_id'] is not None:
                        try:
                            sp['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                self.cursor, sp['user']['employee_id'], select="name")[0]['name']
                        except:
                            sp['user']['employee_name'] = None
                    else:
                        sp['user']['employee_name'] = None
                    if sp['user']['branch_id'] is not None:
                        try:
                            sp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, sp['user']['branch_id'], select="name")[0]['name']
                        except:
                            sp['user']['branch_name'] = None
                    else:
                        sp['user']['branch_name'] = None

                    if sp['user']['division_id'] is not None:
                        try:
                            sp['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, sp['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            sp['user']['division_name'] = None
                    else:
                        sp['user']['division_name'] = None
                except Exception as e:
                    print(e)
                    sp['user'] = {}

                data.append(sp)
        sales_payment['data'] = data
        sales_payment['total'] = count
        sales_payment['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if sales_payment['total'] > page * limit:
            sales_payment['has_next'] = True
        else:
            sales_payment['has_next'] = False
        if limit <= page * count - count:
            sales_payment['has_prev'] = True
        else:
            sales_payment['has_prev'] = False
        return sales_payment

    def get_all_export_payment_mobile_data(
            self, page: int, limit: int, search: str, column: str, direction: str, tipe: str, visit_plan_id: int,
            customer: str, branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of Sales Payment
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: tipe: str
        :param: visit_plan_id: int
        :param: customer: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            list Sales Payment Object
        """
        result_data = {}
        data = []
        start = page * limit - limit
        join = ''
        order = ''
        if tipe == "mobile":
            if customer:
                where = """WHERE `visit_plan_id` = {0} AND `customer_code` = '{1}' """.format(visit_plan_id, customer)
            else:
                where = """WHERE `visit_plan_id` = {0} """.format(visit_plan_id)
            select = '*'
            select_count = 'id'
        else:
            if column:
                if column == 'name':
                    order = """ORDER BY e.name {1}""".format(column, direction)
                elif column == 'branch':
                    order = """ORDER BY b.name {0}""".format(direction)
                else:
                    order = """ORDER BY spm.{0} {1}""".format(column, direction)
            where = "WHERE (e.job_function = 'sales' AND u.branch_id IN ({0}) AND u.division_id IN ({1})) ".format(
                ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
            join = """as spm LEFT JOIN `users` as u ON spm.create_by = u.id 
            LEFT JOIN `employee` as e ON u.employee_id = e.id 
            LEFT JOIN `branches` as b ON u.branch_id = b.id"""
            select = "spm.*"
            select_count = "spm.id"
            if search:
                where += """AND (spm.code LIKE '%{0}%' OR spm.customer_code LIKE '%{0}%' 
                OR e.name LIKE '%{0}%' OR b.name LIKE '%{0}%' OR spm.code LIKE '%{0}%') """.format(search)
            if data_filter:
                tmp_data_filter = data_filter[0]
                if tmp_data_filter['start_date']:
                    where += """AND (spm.payment_date >= '{0} 00:00:00' AND spm.payment_date <= '{1} 23:59:59') """.format(
                        tmp_data_filter['start_date'], tmp_data_filter['end_date']
                    )
                if tmp_data_filter['user_id']:
                    where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['user_id']))
                if tmp_data_filter['branch_id']:
                    where += """AND u.branch_id IN ({0}) """.format(
                        ", ".join(str(x) for x in tmp_data_filter['branch_id']))
                if tmp_data_filter['division_id']:
                    where += """AND u.division_id IN ({0}) """.format(
                        ", ".join(str(x) for x in tmp_data_filter['division_id']))
        sp_data = self.spm_model.get_all_sales_payment(
            self.cursor, select=select, where=where, join=join, start=start, limit=limit, order=order
        )
        count = self.spm_model.get_count_all_sales_payment(self.cursor, select=select_count, where=where, join=join)
        count_filter = count

        if sp_data:
            for sp in sp_data:
                if sp['payment_date'] is not None:
                    sp['payment_date'] = str(sp['payment_date'])
                if sp['invoice'] is not None:
                    sp['invoice'] = json.loads(sp['invoice'])
                if sp['payment_info'] is not None:
                    sp['payment_info'] = json.loads(sp['payment_info'])
                if sp['is_canceled'] == 1:
                    sp['payment_status'] = "Canceled"
                elif sp['is_confirm'] == 1 and sp['is_canceled'] == 0:
                    sp['payment_status'] = "Confirmed"
                elif sp['is_confirm'] == 0 and sp['is_confirm_cancel'] == 1:
                    sp['payment_status'] = "Pending Cancelation"
                else:
                    sp['payment_status'] = "Pending"
                try:
                    sp['user'] = self.user_model.get_user_by_id(
                        self.cursor, sp['create_by'], select="id, employee_id, branch_id, division_id")[0]
                    if sp['user']['employee_id'] is not None:
                        try:
                            sp['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                self.cursor, sp['user']['employee_id'], select="name")[0]['name']
                        except:
                            sp['user']['employee_name'] = None
                    else:
                        sp['user']['employee_name'] = None
                    if sp['user']['branch_id'] is not None:
                        try:
                            sp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, sp['user']['branch_id'], select="name")[0]['name']
                        except:
                            sp['user']['branch_name'] = None
                    else:
                        sp['user']['branch_name'] = None

                    if sp['user']['division_id'] is not None:
                        try:
                            sp['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, sp['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            sp['user']['division_name'] = None
                    else:
                        sp['user']['division_name'] = None
                except Exception as e:
                    print(e)
                    sp['user'] = {}

                data.append(sp)
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Payment')
        merge_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter'
            }
        )
        # Header sheet
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date'] and not data_filter['user_id']:
                worksheet.merge_range(
                    'A1:J1',
                    'PAYMENT (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                        data_filter['start_date'], data_filter['end_date']
                    ),
                    merge_format
                )
            elif data_filter['user_id'] and not data_filter['start_date']:
                worksheet.merge_range(
                    'A1:J1',
                    'PAYMENT (USER: {0}, TANGGAL: ALL)'.format(", ".join(x for x in data_filter['username'])),
                    merge_format
                )
            else:
                worksheet.merge_range(
                    'A1:J1',
                    'PAYMENT (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                        ", ".join(x for x in data_filter['username']), data_filter['start_date'],
                        data_filter['end_date']
                    ),
                    merge_format
                )
        else:
            worksheet.merge_range('A1:J1', 'PAYMENT (USER: ALL, TANGGAL: ALL)', merge_format)

        worksheet.write('A3', 'NO PAYMENT', merge_format)
        worksheet.write('B3', 'TANGGAL', merge_format)
        worksheet.write('C3', 'BRANCH', merge_format)
        worksheet.write('D3', 'DIVISION', merge_format)
        worksheet.write('E3', 'CUSTOMER', merge_format)
        worksheet.write('F3', 'SALES REP', merge_format)
        worksheet.write('G3', 'INVOICE ID', merge_format)
        worksheet.write('H3', 'INVOICE AMOUNT', merge_format)
        worksheet.write('I3', 'PAYMENT AMOUNT', merge_format)
        worksheet.write('J3', 'STATUS', merge_format)

        data_rows = 3
        for rec in data:
            if rec['invoice']:
                list_id = []
                for rec_id in rec['invoice']:
                    list_id.append(rec_id['invoice_id'])
                string_id = ",".join(list_id)
            else:
                string_id = ""
            worksheet.write(data_rows, 0, rec['code'])
            worksheet.write(data_rows, 1, rec['payment_date'])
            worksheet.write(data_rows, 2, rec['user']['branch_name'])
            worksheet.write(data_rows, 3, rec['user']['division_name'])
            worksheet.write(data_rows, 4, rec['customer_code'])
            worksheet.write(data_rows, 5, rec['user']['employee_name'])
            worksheet.write(data_rows, 6, string_id)
            worksheet.write(data_rows, 7, rec['invoice_amount'])
            worksheet.write(data_rows, 8, rec['payment_amount'])
            worksheet.write(data_rows, 9, rec['payment_status'])
            data_rows += 1

        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_all_export_pdf_payment_mobile_data(
            self, page: int, limit: int, search: str, column: str, direction: str, tipe: str, visit_plan_id: int,
            customer: str, branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of Sales Payment
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: tipe: str
        :param: visit_plan_id: int
        :param: customer: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            list Sales Payment Object
        """
        result_data = {}
        data = []
        start = page * limit - limit
        join = ''
        order = ''
        if tipe == "mobile":
            if customer:
                where = """WHERE `visit_plan_id` = {0} AND `customer_code` = '{1}' """.format(visit_plan_id, customer)
            else:
                where = """WHERE `visit_plan_id` = {0} """.format(visit_plan_id)
            select = '*'
            select_count = 'id'
        else:
            if column:
                if column == 'name':
                    order = """ORDER BY e.name {1}""".format(column, direction)
                elif column == 'branch':
                    order = """ORDER BY b.name {0}""".format(direction)
                else:
                    order = """ORDER BY spm.{0} {1}""".format(column, direction)
            where = "WHERE (e.job_function = 'sales' AND u.branch_id IN ({0}) AND u.division_id IN ({1})) ".format(
                ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
            join = """as spm LEFT JOIN `users` as u ON spm.create_by = u.id 
            LEFT JOIN `employee` as e ON u.employee_id = e.id 
            LEFT JOIN `branches` as b ON u.branch_id = b.id"""
            select = "spm.*"
            select_count = "spm.id"
            if search:
                where += """AND (spm.code LIKE '%{0}%' OR spm.customer_code LIKE '%{0}%' 
                OR e.name LIKE '%{0}%' OR b.name LIKE '%{0}%' OR spm.code LIKE '%{0}%') """.format(search)
            if data_filter:
                tmp_data_filter = data_filter[0]
                if tmp_data_filter['start_date']:
                    where += """AND (spm.payment_date >= '{0} 00:00:00' AND spm.payment_date <= '{1} 23:59:59') """.format(
                        tmp_data_filter['start_date'], tmp_data_filter['end_date']
                    )
                if tmp_data_filter['user_id']:
                    where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['user_id']))
                if tmp_data_filter['branch_id']:
                    where += """AND u.branch_id IN ({0}) """.format(
                        ", ".join(str(x) for x in tmp_data_filter['branch_id']))
                if tmp_data_filter['division_id']:
                    where += """AND u.division_id IN ({0}) """.format(
                        ", ".join(str(x) for x in tmp_data_filter['division_id']))
        sp_data = self.spm_model.get_all_sales_payment(
            self.cursor, select=select, where=where, join=join, start=start, limit=limit, order=order
        )
        count = self.spm_model.get_count_all_sales_payment(self.cursor, select=select_count, where=where, join=join)
        count_filter = count

        if sp_data:
            for sp in sp_data:
                if sp['payment_date'] is not None:
                    sp['payment_date'] = str(sp['payment_date'])
                if sp['invoice'] is not None:
                    sp['invoice'] = json.loads(sp['invoice'])
                if sp['payment_info'] is not None:
                    sp['payment_info'] = json.loads(sp['payment_info'])
                if sp['is_canceled'] == 1:
                    sp['payment_status'] = "Canceled"
                elif sp['is_confirm'] == 1 and sp['is_canceled'] == 0:
                    sp['payment_status'] = "Confirmed"
                elif sp['is_confirm'] == 0 and sp['is_confirm_cancel'] == 1:
                    sp['payment_status'] = "Pending Cancelation"
                else:
                    sp['payment_status'] = "Pending"
                try:
                    sp['user'] = self.user_model.get_user_by_id(
                        self.cursor, sp['create_by'], select="id, employee_id, branch_id, division_id")[0]
                    if sp['user']['employee_id'] is not None:
                        try:
                            sp['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                self.cursor, sp['user']['employee_id'], select="name")[0]['name']
                        except:
                            sp['user']['employee_name'] = None
                    else:
                        sp['user']['employee_name'] = None
                    if sp['user']['branch_id'] is not None:
                        try:
                            sp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, sp['user']['branch_id'], select="name")[0]['name']
                        except:
                            sp['user']['branch_name'] = None
                    else:
                        sp['user']['branch_name'] = None

                    if sp['user']['division_id'] is not None:
                        try:
                            sp['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, sp['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            sp['user']['division_name'] = None
                    else:
                        sp['user']['division_name'] = None
                except Exception as e:
                    print(e)
                    sp['user'] = {}

                data.append(sp)

        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date'] and not data_filter['user_id']:
                head_title = 'PAYMENT (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            elif data_filter['user_id'] and not data_filter['start_date']:
                head_title = 'PAYMENT (USER: {0}, TANGGAL: ALL)'.format(
                    ", ".join(x for x in data_filter['username'])
                )
            else:
                head_title = 'PAYMENT (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                    ", ".join(x for x in data_filter['username']), data_filter['start_date'],
                    data_filter['end_date']
                )
        else:
            head_title = 'PAYMENT (USER: ALL, TANGGAL: ALL)'

        head_table = OrderedDict()
        head_table['no'] = "NO PAYMENT"
        head_table['tanggal'] = "TANGGAL"
        head_table['branch'] = "BRANCH"
        head_table['division'] = "DIVISION"
        head_table['customer'] = "CUSTOMER"
        head_table['sales'] = "SALES REP"
        head_table['invoice_id'] = "INVOICE ID"
        head_table['invoice_amount'] = "INVOICE AMOUNT"
        head_table['payment_amount'] = "PAYMENT AMOUNT"
        head_table['status'] = "STATUS"
        body_table = []
        for rec in data:
            data_body = OrderedDict()
            if rec['invoice']:
                list_id = []
                for rec_id in rec['invoice']:
                    list_id.append(rec_id['invoice_id'])
                string_id = ",".join(list_id)
            else:
                string_id = ""
            data_body['no'] = rec['code']
            data_body['tanggal'] = rec['payment_date']
            data_body['branch'] = rec['user']['branch_name']
            data_body['division'] = rec['user']['division_name']
            data_body['customer'] = rec['customer_code']
            data_body['sales'] = rec['user']['employee_name']
            data_body['invoice_id'] = string_id
            data_body['invoice_amount'] = rec['invoice_amount']
            data_body['payment_amount'] = rec['payment_amount']
            data_body['status'] = rec['payment_status']
            body_table.append(data_body)
        # rendered = render_template(
        #     'report_template.html', head_title=head_title, head_table=head_table,
        #     head_customer_table=head_customer_table, body_table=body_table, category="sales"
        # )
        rendered = render_template(
            'report_template.html', head_title=head_title, head_table=head_table, body_table=body_table
        )
        output = pdfkit.from_string(rendered, False)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_sales_payment_by_id(self, _id: int):
        """
        Get Sales Payment Information Data

        :param _id: int
        :return:
            Sales Payment Object
        """
        sales_payment = self.sp_model.get_sales_payment_by_id(self.cursor, _id)

        if len(sales_payment) == 0:
            raise BadRequest("This payment not exist", 200, 1, data=[])
        else:
            sales_payment = sales_payment[0]
            if sales_payment['product'] is not None:
                sales_payment['product'] = json.loads(sales_payment['product'])
            if sales_payment['invoice_date'] is not None:
                sales_payment['invoice_date'] = str(sales_payment['invoice_date'])
            if sales_payment['packing_slip_date'] is not None:
                sales_payment['packing_slip_date'] = str(sales_payment['packing_slip_date'])
            if sales_payment['payment_date'] is not None:
                sales_payment['payment_date'] = str(sales_payment['payment_date'])
            if sales_payment['payment_due_date'] is not None:
                sales_payment['payment_due_date'] = str(sales_payment['payment_due_date'])
            if sales_payment['invoice_amount'] == sales_payment['payment_amount']:
                sales_payment['status'] = "Paid"
            else:
                if sales_payment['payment_amount'] == 0 or sales_payment['payment_amount'] is None:
                    sales_payment['status'] = 'Not Paid'
                else:
                    sales_payment['status'] = 'Partial Paid'

            if sales_payment['customer_code'] is not None:
                try:
                    sales_payment['customer'] = self.customer_model.get_customer_by_id(
                        self.cursor, sales_payment['customer_code'], select="code, name, address, lng, lat")[0]
                except:
                    sales_payment['customer'] = {}
            else:
                sales_payment['customer'] = {}

            if sales_payment['sales_order_code'] is not None:
                try:
                    so_data = self.so_model.get_sales_order_by_id(
                        self.cursor, sales_payment['sales_order_code'], select="user_code")[0]['user_code']
                    sales_payment['user'] = self.user_model.get_user_by_username(
                        self.cursor, so_data, select="id, employee_id, branch_id, division_id")[0]
                    if sales_payment['user']['employee_id'] is not None:
                        try:
                            sales_payment['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                self.cursor, sales_payment['user']['employee_id'], select="name")[0]['name']
                        except:
                            sales_payment['user']['employee_name'] = None
                    else:
                        sales_payment['user']['employee_name'] = None
                    if sales_payment['user']['branch_id'] is not None:
                        try:
                            sales_payment['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, sales_payment['user']['branch_id'], select="name")[0]['name']
                        except:
                            sales_payment['user']['branch_name'] = None
                    else:
                        sales_payment['user']['branch_name'] = None

                    if sales_payment['user']['division_id'] is not None:
                        try:
                            sales_payment['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, sales_payment['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            sales_payment['user']['division_name'] = None
                    else:
                        sales_payment['user']['division_name'] = None
                except:
                    sales_payment['user'] = {}
            else:
                sales_payment['user'] = {}

        return sales_payment

    def get_sales_payment_mobile_by_id(self, _id: int):
        """
        Get Sales Payment Information Data

        :param _id: int
        :return:
            Sales Payment Object
        """
        sales_payment = self.spm_model.get_sales_payment_by_id(self.cursor, _id)

        if len(sales_payment) == 0:
            raise BadRequest("This payment not exist", 200, 1, data=[])
        else:
            sales_payment = sales_payment[0]
            if sales_payment['payment_date'] is not None:
                sales_payment['payment_date'] = str(sales_payment['payment_date'])
            if sales_payment['invoice'] is not None:
                sales_payment['invoice'] = json.loads(sales_payment['invoice'])
            if sales_payment['payment_info'] is not None:
                sales_payment['payment_info'] = json.loads(sales_payment['payment_info'])
            if sales_payment['is_canceled'] == 1:
                sales_payment['payment_status'] = "Canceled"
            elif sales_payment['is_confirm'] == 1 and sales_payment['is_canceled'] == 0:
                sales_payment['payment_status'] = "Confirmed"
            elif sales_payment['is_confirm'] == 0 and sales_payment['is_confirm_cancel'] == 1:
                sales_payment['payment_status'] = "Pending Cancelation"
            else:
                sales_payment['payment_status'] = "Pending"
            try:
                sales_payment['user'] = self.user_model.get_user_by_id(
                    self.cursor, sales_payment['create_by'], select="id, employee_id, branch_id, division_id")[0]
                if sales_payment['user']['employee_id'] is not None:
                    try:
                        sales_payment['user']['employee_name'] = self.employee_model.get_employee_by_id(
                            self.cursor, sales_payment['user']['employee_id'], select="name")[0]['name']
                    except:
                        sales_payment['user']['employee_name'] = None
                else:
                    sales_payment['user']['employee_name'] = None
                if sales_payment['user']['branch_id'] is not None:
                    try:
                        sales_payment['user']['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, sales_payment['user']['branch_id'], select="name")[0]['name']
                    except:
                        sales_payment['user']['branch_name'] = None
                else:
                    sales_payment['user']['branch_name'] = None

                if sales_payment['user']['division_id'] is not None:
                    try:
                        sales_payment['user']['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, sales_payment['user']['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        sales_payment['user']['division_name'] = None
                else:
                    sales_payment['user']['division_name'] = None
            except:
                sales_payment['user'] = {}

        return sales_payment

    def get_all_sales_payment_import(self):
        """
        Get List Of Sales Payment Import
        :return:
            list Import Sales Payment Object
        """
        import_file = {}
        data = []
        import_data = self.sp_model.get_all_sales_payment_import(self.cursor, where="""WHERE `status` = 0 
        AND `table_name` = 'sales_payment'""")
        count = self.sp_model.get_count_all_sales_payment_import(self.cursor, key="id", where="""WHERE `status` = 0 
        AND `table_name` = 'sales_payment'""")
        if import_data:
            for emp in import_data:
                data.append(emp)
        import_file['data'] = data
        import_file['total'] = count

        # TODO: Check Has Next and Prev
        import_file['has_next'] = False
        import_file['has_prev'] = False
        return import_file

    # TODO: using for general purpose
    def get_import_file(self, _id: int, cat: str):
        """
        Get area Information Data

        :param _id: int
        :param cat: int
        :return:
            area Object
        """
        if cat == 'so':
            import_file = self.so_model.get_import_by_id(self.cursor, _id)
        elif cat == 'sp':
            import_file = self.sp_model.get_import_by_id(self.cursor, _id)
        else:
            import_file = []

        if len(import_file) == 0:
            raise BadRequest("This import file not exist", 200, 1, data=[])
        else:
            import_file = import_file[0]

        return import_file

    def update_import_file(self, _id: int, user_id: int, cat: str):
        """
        Get area Information Data

        :param _id: int
        :param user_id: int
        :param cat: str
        :return:
            area Object
        """
        try:
            if cat == 'so':
                result = self.so_model.update_import_by_id(self.cursor, _id, user_id)
                mysql.connection.commit()
            elif cat == 'sp':
                result = self.sp_model.update_import_by_id(self.cursor, _id, user_id)
                mysql.connection.commit()
            else:
                return True
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    # TODO: controllers for invoice
    def get_all_sales_invoice_data(
            self, page: int, limit: int, search: str, column: str, direction: str, dropdown: bool, division: int,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of Invoice
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: dropdown: bool
        :param: division: int
        :param: branch_privilege: list
        :param: division_privilege: list
        :return:
            list Invoice Object
        """

        invoice = {}
        data = []
        start = page * limit - limit
        order_flag = False
        order = ''
        # where = 'WHERE (`packing_slip_date` IS NOT NULL AND `invoice_code` IS NOT NULL)'
        if dropdown:
            where = """WHERE (sp.invoice_amount > sp.payment_amount) AND sp.branch_id IN ({0}) 
            AND sp.division_id = {1}""".format(", ".join(str(x) for x in branch_privilege), division)
        else:
            where = """WHERE (sp.invoice_amount > sp.payment_amount) 
            AND (sp.branch_id IN ({0}) AND sp.division_id IN ({1})) """.format(
                ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
        where_original = where
        if column:
            if column == 'customer_code':
                order_flag = True
                order = """ORDER BY c.code {0}""".format(direction)
            elif column == 'customer':
                order_flag = True
                order = """ORDER BY c.name {0}""".format(direction)
            elif column == 'branch':
                # order_flag = True
                # order = """ORDER BY b.name {0}""".format(direction)
                pass
            elif column == 'employee':
                # order_flag = True
                # order = """ORDER BY e.name {0}""".format(direction)
                pass
            else:
                order = """ORDER BY sp.{0} {1}""".format(column, direction)

        select = "sp.*"
        select_count = "sp.code"
        join = """as sp LEFT JOIN `customer` as c ON sp.customer_code = c.code"""
        # join = """as sp LEFT JOIN `customer` as c ON sp.customer_code = c.code
        # LEFT JOIN `users` as u ON sp.user_code = u.username
        # LEFT JOIN `employee` as e ON u.employee_id = e.id
        # LEFT JOIN `branches` as b ON u.branch_id = b.id"""
        if search:
            where += """AND (c.code LIKE '%{0}%' OR c.name LIKE '%{0}%' 
            OR sp.code LIKE '%{0}%' OR sp.sales_order_code LIKE '%{0}%') """.format(search)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                where += """AND (sp.invoice_date >= '{0} 00:00:00' AND sp.invoice_date <= '{1} 23:59:59') """.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            if data_filter['branch_id']:
                where += """AND sp.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
            if data_filter['division_id']:
                where += """AND sp.division_id IN ({0}) """.format(
                    ", ".join(str(x) for x in data_filter['division_id']))
        sp_data = self.sp_model.get_all_sales_payment(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.sp_model.get_count_all_sales_payment(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.sp_model.get_count_all_sales_payment(
            self.cursor, select=select_count, join=join, where=where_original
        )
        #     # sp_data = self.so_model.get_all_sales_order(self.cursor, select=select, join=join, where=where,
        #     #                                             order=order, start=start, limit=limit)
        #     # count_filter = self.so_model.get_count_all_sales_order(self.cursor, select=select_count, join=join,
        #     #                                                          where=where)
        #     # count = self.so_model.get_count_all_sales_order(self.cursor)
        # else:
        #     sp_data = self.sp_model.get_all_sales_payment(self.cursor, where=where, start=start, limit=limit, order=order)
        #     count = self.sp_model.get_count_all_sales_payment(self.cursor, where=where)
        #     # sp_data = self.so_model.get_all_sales_order(self.cursor, where=where, start=start, limit=limit, order=order)
        #     # count = self.so_model.get_count_all_sales_order(self.cursor, where=where)
        #     count_filter = count

        if sp_data:
            for sp in sp_data:
                invoice_data = dict()
                if sp['product'] is not None:
                    sp['product'] = json.loads(sp['product'])
                if sp['invoice_date'] is not None:
                    sp['invoice_date'] = str(sp['invoice_date'])
                if sp['packing_slip_date'] is not None:
                    sp['packing_slip_date'] = str(sp['packing_slip_date'])
                if sp['sales_order_date'] is not None:
                    sp['sales_order_date'] = str(sp['sales_order_date'])
                if sp['payment_date'] is not None:
                    sp['payment_date'] = str(sp['payment_date'])
                if sp['payment_due_date'] is not None:
                    sp['payment_due_date'] = str(sp['payment_due_date'])

                if sp['customer_code'] is not None:
                    try:
                        sp['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, sp['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        sp['customer'] = {}
                else:
                    sp['customer'] = {}

                # if sp['user_code'] is not None:
                #     try:
                #         sp['user'] = self.user_model.get_user_by_username(
                #             self.cursor, sp['user_code'], select="id, employee_id, branch_id")[0]
                #         if sp['user']['employee_id'] is not None:
                #             try:
                #                 sp['user']['employee_name'] = self.employee_model.get_employee_by_id(
                #                     self.cursor, sp['user']['employee_id'], select="name")[0]['name']
                #             except:
                #                 sp['user']['employee_name'] = None
                #         else:
                #             sp['user']['employee_name'] = None
                #         if sp['user']['branch_id'] is not None:
                #             try:
                #                 sp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                #                     self.cursor, sp['user']['branch_id'], select="name")[0]['name']
                #             except:
                #                 sp['user']['branch_name'] = None
                #         else:
                #             sp['user']['branch_name'] = None
                #     except:
                #         sp['user'] = {}
                # else:
                #     sp['user'] = {}
                # if sp['sales_order_code'] is not None:
                #     try:
                #         so_data = self.so_model.get_sales_order_by_id(
                #             self.cursor, sp['sales_order_code'], select="user_code")[0]['user_code']
                #         sp['user'] = self.user_model.get_user_by_username(
                #             self.cursor, so_data, select="id, employee_id, branch_id")[0]
                #         if sp['user']['employee_id'] is not None:
                #             try:
                #                 sp['user']['employee_name'] = self.employee_model.get_employee_by_id(
                #                     self.cursor, sp['user']['employee_id'], select="name")[0]['name']
                #             except:
                #                 sp['user']['employee_name'] = None
                #         else:
                #             sp['user']['employee_name'] = None
                #         if sp['user']['branch_id'] is not None:
                #             try:
                #                 sp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                #                     self.cursor, sp['user']['branch_id'], select="name")[0]['name']
                #             except:
                #                 sp['user']['branch_name'] = None
                #         else:
                #             sp['user']['branch_name'] = None
                #     except:
                #         sp['user'] = {}
                # else:
                #     sp['user'] = {}

                invoice_data['code'] = sp['code']
                # invoice_data['invoice_code'] = sp['invoice_code']
                invoice_data['invoice_date'] = sp['invoice_date']
                invoice_data['customer_code'] = sp['customer_code']
                invoice_data['customer'] = sp['customer']
                invoice_data['packing_slip_code'] = sp['packing_slip_code']
                invoice_data['packing_slip_date'] = sp['packing_slip_date']
                invoice_data['sales_order_code'] = sp['sales_order_code']
                invoice_data['sales_order_date'] = sp['sales_order_date']
                invoice_data['payment_due_date'] = sp['payment_due_date']
                invoice_data['invoice_amount'] = sp['invoice_amount']
                invoice_data['branch_id'] = sp['branch_id']
                if sp['branch_id'] is not None:
                    try:
                        invoice_data['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, sp['branch_id'], select="name")[0]['name']
                    except:
                        invoice_data['branch_name'] = None
                else:
                    invoice_data['branch_name'] = None
                invoice_data['division_id'] = sp['division_id']

                if sp['division_id'] is not None:
                    try:
                        invoice_data['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, sp['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        invoice_data['division_name'] = None
                else:
                    invoice_data['division_name'] = None
                # invoice_data['user'] = sp['user']
                invoice_data['product'] = sp['product']

                try:
                    visit_plan = self.visit_plan_model.get_all_visit_plan(
                        self.cursor, select="user_id",
                        where="WHERE JSON_CONTAINS(`invoice_id`, '{{\"id_invoice\": \"{0}\"}}')".format(sp['code'])
                    )[0]
                    sp['user_code'] = visit_plan['user_id']
                    if sp['user_code'] is not None:
                        try:
                            sp['user'] = self.user_model.get_user_by_id(
                                self.cursor, sp['user_code'], select="id, employee_id, branch_id, division_id")[0]
                            if sp['user']['employee_id'] is not None:
                                try:
                                    sp['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                        self.cursor, sp['user']['employee_id'], select="name")[0]['name']
                                except:
                                    sp['user']['employee_name'] = None
                            else:
                                sp['user']['employee_name'] = None
                            if sp['user']['branch_id'] is not None:
                                try:
                                    sp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                        self.cursor, sp['user']['branch_id'], select="name")[0]['name']
                                except:
                                    sp['user']['branch_name'] = None
                            else:
                                sp['user']['branch_name'] = None
                            if sp['user']['division_id'] is not None:
                                try:
                                    sp['user']['division_name'] = self.division_model.get_division_by_id(
                                        self.cursor, sp['user']['division_id'], select="division_name")[0][
                                        'division_name']
                                except:
                                    sp['user']['division_name'] = None
                            else:
                                sp['user']['division_name'] = None
                        except:
                            sp['user'] = {}
                    else:
                        sp['user'] = {}

                except:
                    sp['user_code'] = None
                    sp['user'] = {}
                invoice_data['user'] = sp['user']
                invoice_data['user_code'] = sp['user_code']

                if (sp['invoice_amount'] - sp['payment_amount']) > 0:
                    if sp['payment_amount'] > 0:
                        invoice_data['status'] = 'Partialy Paid'
                    else:
                        invoice_data['status'] = 'Not Paid'
                    try:
                        payment_mobile = self.spm_model.get_all_sales_payment(
                            self.cursor, select="invoice", order="ORDER BY payment_date DESC",
                            where="WHERE JSON_CONTAINS(`invoice`, '{{\"invoice_id\": \"{0}\"}}') AND is_confirm = 1".format(
                                sp['code'])
                        )
                        if payment_mobile:
                            for pay in payment_mobile:
                                amount_payment = json.loads(pay['invoice'])
                                if amount_payment:
                                    for rec in amount_payment:
                                        if rec['invoice_id'] == sp['code']:
                                            sp['payment_amount'] += rec['payment_amount']
                                            if (sp['invoice_amount'] - sp['payment_amount']) > 0:
                                                if rec['payment_amount'] > 0:
                                                    invoice_data['status'] = 'Partialy Paid'
                                                else:
                                                    invoice_data['status'] = 'Not Paid'
                                            else:
                                                invoice_data['status'] = 'Paid'
                    except Exception as e:
                        pass
                        print("tidak ada payment")
                else:
                    invoice_data['status'] = 'Paid'
                invoice_data['payment_amount'] = sp['payment_amount']
                if dropdown:
                    if invoice_data['status'] != 'Paid':
                        data.append(invoice_data)
                else:
                    data.append(invoice_data)

        invoice['data'] = data
        invoice['total'] = count
        invoice['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if invoice['total'] > page * limit:
            invoice['has_next'] = True
        else:
            invoice['has_next'] = False
        if limit <= page * count - count:
            invoice['has_prev'] = True
        else:
            invoice['has_prev'] = False
        return invoice

    def get_all_export_sales_invoice_data(
            self, page: int, limit: int, search: str, column: str, direction: str, dropdown: bool, division: int,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of Invoice
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: dropdown: bool
        :param: division: int
        :param: branch_privilege: list
        :param: division_privilege: list
        :return:
            list Invoice Object
        """

        result_data = {}
        data = []
        start = page * limit - limit
        order_flag = False
        order = ''
        # where = 'WHERE (`packing_slip_date` IS NOT NULL AND `invoice_code` IS NOT NULL)'
        if dropdown:
            where = """WHERE (sp.invoice_amount > sp.payment_amount) AND sp.branch_id IN ({0}) 
            AND sp.division_id = {1}""".format(", ".join(str(x) for x in branch_privilege), division)
        else:
            where = """WHERE (sp.invoice_amount > sp.payment_amount) 
            AND (sp.branch_id IN ({0}) AND sp.division_id IN ({1})) """.format(
                ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
        where_original = where
        if column:
            if column == 'customer_code':
                order_flag = True
                order = """ORDER BY c.code {0}""".format(direction)
            elif column == 'customer':
                order_flag = True
                order = """ORDER BY c.name {0}""".format(direction)
            elif column == 'branch':
                # order_flag = True
                # order = """ORDER BY b.name {0}""".format(direction)
                pass
            elif column == 'employee':
                # order_flag = True
                # order = """ORDER BY e.name {0}""".format(direction)
                pass
            else:
                order = """ORDER BY sp.{0} {1}""".format(column, direction)

        select = "sp.*"
        select_count = "sp.code"
        join = """as sp LEFT JOIN `customer` as c ON sp.customer_code = c.code"""
        if search:
            where += """AND (c.code LIKE '%{0}%' OR c.name LIKE '%{0}%' 
            OR sp.code LIKE '%{0}%' OR sp.sales_order_code LIKE '%{0}%') """.format(search)
        if data_filter:
            tmp_data_filter = data_filter[0]
            if tmp_data_filter['start_date']:
                where += """AND (sp.invoice_date >= '{0} 00:00:00' AND sp.invoice_date <= '{1} 23:59:59') """.format(
                    tmp_data_filter['start_date'], tmp_data_filter['end_date']
                )
            if tmp_data_filter['branch_id']:
                where += """AND sp.branch_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['branch_id']))
            if tmp_data_filter['division_id']:
                where += """AND sp.division_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['division_id']))
        sp_data = self.sp_model.get_all_sales_payment(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.sp_model.get_count_all_sales_payment(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.sp_model.get_count_all_sales_payment(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if sp_data:
            for sp in sp_data:
                invoice_data = dict()
                if sp['product'] is not None:
                    sp['product'] = json.loads(sp['product'])
                if sp['invoice_date'] is not None:
                    sp['invoice_date'] = str(sp['invoice_date'])
                if sp['packing_slip_date'] is not None:
                    sp['packing_slip_date'] = str(sp['packing_slip_date'])
                if sp['sales_order_date'] is not None:
                    sp['sales_order_date'] = str(sp['sales_order_date'])
                if sp['payment_date'] is not None:
                    sp['payment_date'] = str(sp['payment_date'])
                if sp['payment_due_date'] is not None:
                    sp['payment_due_date'] = str(sp['payment_due_date'])

                if sp['customer_code'] is not None:
                    try:
                        sp['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, sp['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        sp['customer'] = {}
                else:
                    sp['customer'] = {}

                invoice_data['code'] = sp['code']
                # invoice_data['invoice_code'] = sp['invoice_code']
                invoice_data['invoice_date'] = sp['invoice_date']
                invoice_data['customer_code'] = sp['customer_code']
                invoice_data['customer'] = sp['customer']
                invoice_data['packing_slip_code'] = sp['packing_slip_code']
                invoice_data['packing_slip_date'] = sp['packing_slip_date']
                invoice_data['sales_order_code'] = sp['sales_order_code']
                invoice_data['sales_order_date'] = sp['sales_order_date']
                invoice_data['payment_due_date'] = sp['payment_due_date']
                invoice_data['invoice_amount'] = sp['invoice_amount']
                invoice_data['branch_id'] = sp['branch_id']
                if sp['branch_id'] is not None:
                    try:
                        invoice_data['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, sp['branch_id'], select="name")[0]['name']
                    except:
                        invoice_data['branch_name'] = None
                else:
                    invoice_data['branch_name'] = None
                invoice_data['division_id'] = sp['division_id']

                if sp['division_id'] is not None:
                    try:
                        invoice_data['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, sp['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        invoice_data['division_name'] = None
                else:
                    invoice_data['division_name'] = None
                # invoice_data['user'] = sp['user']
                invoice_data['product'] = sp['product']

                try:
                    visit_plan = self.visit_plan_model.get_all_visit_plan(
                        self.cursor, select="user_id",
                        where="WHERE JSON_CONTAINS(`invoice_id`, '{{\"id_invoice\": \"{0}\"}}')".format(sp['code'])
                    )[0]
                    sp['user_code'] = visit_plan['user_id']
                    if sp['user_code'] is not None:
                        try:
                            sp['user'] = self.user_model.get_user_by_id(
                                self.cursor, sp['user_code'], select="id, employee_id, branch_id, division_id")[0]
                            if sp['user']['employee_id'] is not None:
                                try:
                                    sp['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                        self.cursor, sp['user']['employee_id'], select="name")[0]['name']
                                except:
                                    sp['user']['employee_name'] = None
                            else:
                                sp['user']['employee_name'] = None
                            if sp['user']['branch_id'] is not None:
                                try:
                                    sp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                        self.cursor, sp['user']['branch_id'], select="name")[0]['name']
                                except:
                                    sp['user']['branch_name'] = None
                            else:
                                sp['user']['branch_name'] = None
                            if sp['user']['division_id'] is not None:
                                try:
                                    sp['user']['division_name'] = self.division_model.get_division_by_id(
                                        self.cursor, sp['user']['division_id'], select="division_name")[0][
                                        'division_name']
                                except:
                                    sp['user']['division_name'] = None
                            else:
                                sp['user']['division_name'] = None
                        except:
                            sp['user'] = {}
                    else:
                        sp['user'] = {}

                except:
                    sp['user_code'] = None
                    sp['user'] = {}
                invoice_data['user'] = sp['user']
                invoice_data['user_code'] = sp['user_code']

                if (sp['invoice_amount'] - sp['payment_amount']) > 0:
                    if sp['payment_amount'] > 0:
                        invoice_data['status'] = 'Partialy Paid'
                    else:
                        invoice_data['status'] = 'Not Paid'
                    try:
                        payment_mobile = self.spm_model.get_all_sales_payment(
                            self.cursor, select="invoice", order="ORDER BY payment_date DESC",
                            where="WHERE JSON_CONTAINS(`invoice`, '{{\"invoice_id\": \"{0}\"}}') AND is_confirm = 1".format(
                                sp['code'])
                        )
                        if payment_mobile:
                            for pay in payment_mobile:
                                amount_payment = json.loads(pay['invoice'])
                                if amount_payment:
                                    for rec in amount_payment:
                                        if rec['invoice_id'] == sp['code']:
                                            sp['payment_amount'] += rec['payment_amount']
                                            if (sp['invoice_amount'] - sp['payment_amount']) > 0:
                                                if rec['payment_amount'] > 0:
                                                    invoice_data['status'] = 'Partialy Paid'
                                                else:
                                                    invoice_data['status'] = 'Not Paid'
                                            else:
                                                invoice_data['status'] = 'Paid'
                    except Exception as e:
                        pass
                        print("tidak ada payment")
                else:
                    invoice_data['status'] = 'Paid'
                invoice_data['payment_amount'] = sp['payment_amount']
                if dropdown:
                    if invoice_data['status'] != 'Paid':
                        data.append(invoice_data)
                else:
                    data.append(invoice_data)
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Invoice')
        merge_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter'
            }
        )
        # Header sheet
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                worksheet.merge_range(
                    'A1:F1',
                    'INVOICE (TANGGAL: {0} s/d {1})'.format(
                        data_filter['start_date'], data_filter['end_date']
                    ),
                    merge_format
                )
            else:
                worksheet.merge_range(
                    'A1:F1',
                    'INVOICE (TANGGAL: ALL)',
                    merge_format
                )
        else:
            worksheet.merge_range('A1:F1', 'INVOICE (TANGGAL: ALL)', merge_format)

        worksheet.write('A3', 'NO INVOICE')
        worksheet.write('B3', 'NO SALES ORDER')
        worksheet.write('C3', 'TANGGAL')
        worksheet.write('D3', 'DUE DATE')
        worksheet.write('E3', 'BRANCH')
        worksheet.write('F3', 'DIVISION')
        worksheet.write('G3', 'CUSTOMER')
        worksheet.write('H3', 'SALES REP')
        worksheet.write('I3', 'STATUS')

        data_rows = 3
        for rec in data:
            worksheet.write(data_rows, 0, rec['code'])
            worksheet.write(data_rows, 1, rec['sales_order_code'])
            worksheet.write(data_rows, 2, rec['invoice_date'])
            worksheet.write(data_rows, 3, rec['payment_due_date'])
            worksheet.write(data_rows, 4, rec['branch_name'])
            worksheet.write(data_rows, 5, rec['division_name'])
            worksheet.write(data_rows, 6, rec['customer_code'])
            worksheet.write(data_rows, 7, rec['user_code'])
            worksheet.write(data_rows, 8, rec['status'])
            data_rows += 1

        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_all_export_pdf_sales_invoice_data(
            self, page: int, limit: int, search: str, column: str, direction: str, dropdown: bool, division: int,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of Invoice
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: dropdown: bool
        :param: division: int
        :param: branch_privilege: list
        :param: division_privilege: list
        :return:
            list Invoice Object
        """

        result_data = {}
        data = []
        start = page * limit - limit
        order_flag = False
        order = ''
        # where = 'WHERE (`packing_slip_date` IS NOT NULL AND `invoice_code` IS NOT NULL)'
        if dropdown:
            where = """WHERE (sp.invoice_amount > sp.payment_amount) AND sp.branch_id IN ({0}) 
            AND sp.division_id = {1}""".format(", ".join(str(x) for x in branch_privilege), division)
        else:
            where = """WHERE (sp.invoice_amount > sp.payment_amount) 
            AND (sp.branch_id IN ({0}) AND sp.division_id IN ({1})) """.format(
                ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
        where_original = where
        if column:
            if column == 'customer_code':
                order_flag = True
                order = """ORDER BY c.code {0}""".format(direction)
            elif column == 'customer':
                order_flag = True
                order = """ORDER BY c.name {0}""".format(direction)
            elif column == 'branch':
                # order_flag = True
                # order = """ORDER BY b.name {0}""".format(direction)
                pass
            elif column == 'employee':
                # order_flag = True
                # order = """ORDER BY e.name {0}""".format(direction)
                pass
            else:
                order = """ORDER BY sp.{0} {1}""".format(column, direction)

        select = "sp.*"
        select_count = "sp.code"
        join = """as sp LEFT JOIN `customer` as c ON sp.customer_code = c.code"""
        if search:
            where += """AND (c.code LIKE '%{0}%' OR c.name LIKE '%{0}%' 
            OR sp.code LIKE '%{0}%' OR sp.sales_order_code LIKE '%{0}%') """.format(search)
        if data_filter:
            tmp_data_filter = data_filter[0]
            if tmp_data_filter['start_date']:
                where += """AND (sp.invoice_date >= '{0} 00:00:00' AND sp.invoice_date <= '{1} 23:59:59') """.format(
                    tmp_data_filter['start_date'], tmp_data_filter['end_date']
                )
            if tmp_data_filter['branch_id']:
                where += """AND sp.branch_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['branch_id']))
            if tmp_data_filter['division_id']:
                where += """AND sp.division_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['division_id']))
        sp_data = self.sp_model.get_all_sales_payment(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.sp_model.get_count_all_sales_payment(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.sp_model.get_count_all_sales_payment(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if sp_data:
            for sp in sp_data:
                invoice_data = dict()
                if sp['product'] is not None:
                    sp['product'] = json.loads(sp['product'])
                if sp['invoice_date'] is not None:
                    sp['invoice_date'] = str(sp['invoice_date'])
                if sp['packing_slip_date'] is not None:
                    sp['packing_slip_date'] = str(sp['packing_slip_date'])
                if sp['sales_order_date'] is not None:
                    sp['sales_order_date'] = str(sp['sales_order_date'])
                if sp['payment_date'] is not None:
                    sp['payment_date'] = str(sp['payment_date'])
                if sp['payment_due_date'] is not None:
                    sp['payment_due_date'] = str(sp['payment_due_date'])

                if sp['customer_code'] is not None:
                    try:
                        sp['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, sp['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        sp['customer'] = {}
                else:
                    sp['customer'] = {}

                invoice_data['code'] = sp['code']
                # invoice_data['invoice_code'] = sp['invoice_code']
                invoice_data['invoice_date'] = sp['invoice_date']
                invoice_data['customer_code'] = sp['customer_code']
                invoice_data['customer'] = sp['customer']
                invoice_data['packing_slip_code'] = sp['packing_slip_code']
                invoice_data['packing_slip_date'] = sp['packing_slip_date']
                invoice_data['sales_order_code'] = sp['sales_order_code']
                invoice_data['sales_order_date'] = sp['sales_order_date']
                invoice_data['payment_due_date'] = sp['payment_due_date']
                invoice_data['invoice_amount'] = sp['invoice_amount']
                invoice_data['branch_id'] = sp['branch_id']
                if sp['branch_id'] is not None:
                    try:
                        invoice_data['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, sp['branch_id'], select="name")[0]['name']
                    except:
                        invoice_data['branch_name'] = None
                else:
                    invoice_data['branch_name'] = None
                invoice_data['division_id'] = sp['division_id']

                if sp['division_id'] is not None:
                    try:
                        invoice_data['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, sp['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        invoice_data['division_name'] = None
                else:
                    invoice_data['division_name'] = None
                # invoice_data['user'] = sp['user']
                invoice_data['product'] = sp['product']

                try:
                    visit_plan = self.visit_plan_model.get_all_visit_plan(
                        self.cursor, select="user_id",
                        where="WHERE JSON_CONTAINS(`invoice_id`, '{{\"id_invoice\": \"{0}\"}}')".format(sp['code'])
                    )[0]
                    sp['user_code'] = visit_plan['user_id']
                    if sp['user_code'] is not None:
                        try:
                            sp['user'] = self.user_model.get_user_by_id(
                                self.cursor, sp['user_code'], select="id, employee_id, branch_id, division_id")[0]
                            if sp['user']['employee_id'] is not None:
                                try:
                                    sp['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                        self.cursor, sp['user']['employee_id'], select="name")[0]['name']
                                except:
                                    sp['user']['employee_name'] = None
                            else:
                                sp['user']['employee_name'] = None
                            if sp['user']['branch_id'] is not None:
                                try:
                                    sp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                        self.cursor, sp['user']['branch_id'], select="name")[0]['name']
                                except:
                                    sp['user']['branch_name'] = None
                            else:
                                sp['user']['branch_name'] = None
                            if sp['user']['division_id'] is not None:
                                try:
                                    sp['user']['division_name'] = self.division_model.get_division_by_id(
                                        self.cursor, sp['user']['division_id'], select="division_name")[0][
                                        'division_name']
                                except:
                                    sp['user']['division_name'] = None
                            else:
                                sp['user']['division_name'] = None
                        except:
                            sp['user'] = {}
                    else:
                        sp['user'] = {}

                except:
                    sp['user_code'] = None
                    sp['user'] = {}
                invoice_data['user'] = sp['user']
                invoice_data['user_code'] = sp['user_code']

                if (sp['invoice_amount'] - sp['payment_amount']) > 0:
                    if sp['payment_amount'] > 0:
                        invoice_data['status'] = 'Partialy Paid'
                    else:
                        invoice_data['status'] = 'Not Paid'
                    try:
                        payment_mobile = self.spm_model.get_all_sales_payment(
                            self.cursor, select="invoice", order="ORDER BY payment_date DESC",
                            where="WHERE JSON_CONTAINS(`invoice`, '{{\"invoice_id\": \"{0}\"}}') AND is_confirm = 1".format(
                                sp['code'])
                        )
                        if payment_mobile:
                            for pay in payment_mobile:
                                amount_payment = json.loads(pay['invoice'])
                                if amount_payment:
                                    for rec in amount_payment:
                                        if rec['invoice_id'] == sp['code']:
                                            sp['payment_amount'] += rec['payment_amount']
                                            if (sp['invoice_amount'] - sp['payment_amount']) > 0:
                                                if rec['payment_amount'] > 0:
                                                    invoice_data['status'] = 'Partialy Paid'
                                                else:
                                                    invoice_data['status'] = 'Not Paid'
                                            else:
                                                invoice_data['status'] = 'Paid'
                    except Exception as e:
                        pass
                        print("tidak ada payment")
                else:
                    invoice_data['status'] = 'Paid'
                invoice_data['payment_amount'] = sp['payment_amount']
                if dropdown:
                    if invoice_data['status'] != 'Paid':
                        data.append(invoice_data)
                else:
                    data.append(invoice_data)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                head_title = 'INVOICE (TANGGAL: {0} s/d {1})'.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            else:
                head_title = 'INVOICE (TANGGAL: ALL)'
        else:
            head_title = 'INVOICE (TANGGAL: ALL)'

        head_table = OrderedDict()
        head_table['no'] = "NO INVOICE"
        head_table['no_sales'] = "NO SALES ORDER"
        head_table['tanggal'] = "TANGGAL"
        head_table['due_date'] = "DUE DATE"
        head_table['branch'] = "BRANCH"
        head_table['division'] = "DIVISION"
        head_table['customer'] = "CUSTOMER"
        head_table['sales'] = "SALES REP"
        head_table['status'] = "STATUS"
        body_table = []
        for rec in data:
            data_body = OrderedDict()
            data_body['no'] = rec['code']
            data_body['no_sales'] = rec['sales_order_code']
            data_body['tanggal'] = rec['invoice_date']
            data_body['due_date'] = rec['payment_due_date']
            data_body['branch'] = rec['branch_name']
            data_body['division'] = rec['division_name']
            data_body['customer'] = rec['customer_code']
            data_body['sales'] = rec['user_code']
            data_body['status'] = rec['status']
            body_table.append(data_body)
        # rendered = render_template(
        #     'report_template.html', head_title=head_title, head_table=head_table,
        #     head_customer_table=head_customer_table, body_table=body_table, category="sales"
        # )
        rendered = render_template(
            'report_template.html', head_title=head_title, head_table=head_table, body_table=body_table
        )
        output = pdfkit.from_string(rendered, False)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_all_sales_invoice_data_by_customer(
            self, page: int, limit: int, search: str, column: str, direction: str, customer_code: list, division: int
    ):
        """
        Get List Of Invoice
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilege: list
        :return:
            list Invoice Object
        """

        invoice = {}
        data = []
        start = page * limit - limit
        order_flag = False
        order = ''
        where = """WHERE (sp.invoice_amount > sp.payment_amount) 
        AND (sp.customer_code IN ('{0}') AND sp.division_id = {1}) """.format(
            "', '".join(str(x) for x in customer_code), division
        )
        where_original = where
        if column:
            if column == 'customer_code':
                order = """ORDER BY c.code {0}""".format(direction)
            elif column == 'customer':
                order = """ORDER BY c.name {0}""".format(direction)
            elif column == 'branch':
                pass
            elif column == 'employee':
                pass
            else:
                order = """ORDER BY sp.{0} {1}""".format(column, direction)

        select = "sp.*"
        select_count = "sp.code"
        join = """as sp LEFT JOIN `customer` as c ON sp.customer_code = c.code"""
        if search:
            where += """AND (c.code LIKE '%{0}%' OR c.name LIKE '%{0}%' 
            OR sp.code LIKE '%{0}%' OR sp.sales_order_code LIKE '%{0}%') """.format(search)
        sp_data = self.sp_model.get_all_sales_payment(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.sp_model.get_count_all_sales_payment(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.sp_model.get_count_all_sales_payment(
            self.cursor, select=select_count, join=join, where=where_original
        )

        if sp_data:
            for sp in sp_data:
                invoice_data = dict()
                if sp['product'] is not None:
                    sp['product'] = json.loads(sp['product'])
                if sp['invoice_date'] is not None:
                    sp['invoice_date'] = str(sp['invoice_date'])
                if sp['packing_slip_date'] is not None:
                    sp['packing_slip_date'] = str(sp['packing_slip_date'])
                if sp['sales_order_date'] is not None:
                    sp['sales_order_date'] = str(sp['sales_order_date'])
                if sp['payment_date'] is not None:
                    sp['payment_date'] = str(sp['payment_date'])
                if sp['payment_due_date'] is not None:
                    sp['payment_due_date'] = str(sp['payment_due_date'])

                if sp['customer_code'] is not None:
                    try:
                        sp['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, sp['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        sp['customer'] = {}
                else:
                    sp['customer'] = {}

                invoice_data['code'] = sp['code']
                invoice_data['invoice_date'] = sp['invoice_date']
                invoice_data['customer_code'] = sp['customer_code']
                invoice_data['customer'] = sp['customer']
                invoice_data['packing_slip_code'] = sp['packing_slip_code']
                invoice_data['packing_slip_date'] = sp['packing_slip_date']
                invoice_data['sales_order_code'] = sp['sales_order_code']
                invoice_data['sales_order_date'] = sp['sales_order_date']
                invoice_data['payment_due_date'] = sp['payment_due_date']
                invoice_data['invoice_amount'] = sp['invoice_amount']
                invoice_data['branch_id'] = sp['branch_id']
                if sp['branch_id'] is not None:
                    try:
                        invoice_data['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, sp['branch_id'], select="name")[0]['name']
                    except:
                        invoice_data['branch_name'] = None
                else:
                    invoice_data['branch_name'] = None
                invoice_data['division_id'] = sp['division_id']

                if sp['division_id'] is not None:
                    try:
                        invoice_data['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, sp['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        invoice_data['division_name'] = None
                else:
                    invoice_data['division_name'] = None
                invoice_data['product'] = sp['product']

                try:
                    visit_plan = self.visit_plan_model.get_all_visit_plan(
                        self.cursor, select="user_id",
                        where="WHERE JSON_CONTAINS(`invoice_id`, '{{\"id_invoice\": \"{0}\"}}')".format(sp['code'])
                    )[0]
                    sp['user_code'] = visit_plan['user_id']
                    if sp['user_code'] is not None:
                        try:
                            sp['user'] = self.user_model.get_user_by_id(
                                self.cursor, sp['user_code'], select="id, employee_id, branch_id, division_id")[0]
                            if sp['user']['employee_id'] is not None:
                                try:
                                    sp['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                        self.cursor, sp['user']['employee_id'], select="name")[0]['name']
                                except:
                                    sp['user']['employee_name'] = None
                            else:
                                sp['user']['employee_name'] = None
                            if sp['user']['branch_id'] is not None:
                                try:
                                    sp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                        self.cursor, sp['user']['branch_id'], select="name")[0]['name']
                                except:
                                    sp['user']['branch_name'] = None
                            else:
                                sp['user']['branch_name'] = None
                            if sp['user']['division_id'] is not None:
                                try:
                                    sp['user']['division_name'] = self.division_model.get_division_by_id(
                                        self.cursor, sp['user']['division_id'], select="division_name")[0][
                                        'division_name']
                                except:
                                    sp['user']['division_name'] = None
                            else:
                                sp['user']['division_name'] = None
                        except:
                            sp['user'] = {}
                    else:
                        sp['user'] = {}

                except:
                    sp['user_code'] = None
                    sp['user'] = {}
                invoice_data['user'] = sp['user']
                invoice_data['user_code'] = sp['user_code']

                if (sp['invoice_amount'] - sp['payment_amount']) > 0:
                    if sp['payment_amount'] > 0:
                        invoice_data['status'] = 'Partialy Paid'
                    else:
                        invoice_data['status'] = 'Not Paid'
                    try:
                        payment_mobile = self.spm_model.get_all_sales_payment(
                            self.cursor, select="invoice", order="ORDER BY payment_date DESC",
                            where="WHERE JSON_CONTAINS(`invoice`, '{{\"invoice_id\": \"{0}\"}}') AND is_confirm = 1".format(
                                sp['code'])
                        )
                        if payment_mobile:
                            for pay in payment_mobile:
                                amount_payment = json.loads(pay['invoice'])
                                if amount_payment:
                                    for rec in amount_payment:
                                        if rec['invoice_id'] == sp['code']:
                                            sp['payment_amount'] += rec['payment_amount']
                                            if (sp['invoice_amount'] - sp['payment_amount']) > 0:
                                                if rec['payment_amount'] > 0:
                                                    invoice_data['status'] = 'Partialy Paid'
                                                else:
                                                    invoice_data['status'] = 'Not Paid'
                                            else:
                                                invoice_data['status'] = 'Paid'
                    except Exception as e:
                        pass
                        print("tidak ada payment")
                else:
                    invoice_data['status'] = 'Paid'
                invoice_data['payment_amount'] = sp['payment_amount']
                if invoice_data['status'] != 'Paid':
                    data.append(invoice_data)
                # if dropdown:
                #
                # else:
                #     data.append(invoice_data)

        invoice['data'] = data
        invoice['total'] = count
        invoice['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if invoice['total'] > page * limit:
            invoice['has_next'] = True
        else:
            invoice['has_next'] = False
        if limit <= page * count - count:
            invoice['has_prev'] = True
        else:
            invoice['has_prev'] = False
        return invoice

    def get_sales_invoice_by_id(self, _id: int):
        """
        Get Invoice Information Data

        :param _id: int
        :return:
            Invoice Object
        """
        result = self.sp_model.get_sales_payment_by_id(self.cursor, _id)
        # result = self.so_model.get_sales_order_by_id(self.cursor, _id)

        if len(result) == 0:
            raise BadRequest("This invoice not exist", 200, 1, data=[])
        else:
            result = result[0]
            if result['product'] is not None:
                result['product'] = json.loads(result['product'])
            if result['invoice_date'] is not None:
                result['invoice_date'] = str(result['invoice_date'])
            if result['sales_order_date'] is not None:
                result['sales_order_date'] = str(result['sales_order_date'])
            if result['packing_slip_date'] is not None:
                result['packing_slip_date'] = str(result['packing_slip_date'])
            # if result['payment_date'] is not None:
            #     result['payment_date'] = str(result['payment_date'])
            if result['payment_due_date'] is not None:
                result['payment_due_date'] = str(result['payment_due_date'])

            if result['customer_code'] is not None:
                try:
                    result['customer'] = self.customer_model.get_customer_by_id(
                        self.cursor, result['customer_code'], select="code, name, contacts, address, lng, lat")[0]
                    if result['customer']['contacts'] is not None:
                        result['customer']['contacts'] = json.loads(result['customer']['contacts'])
                    else:
                        result['customer']['contacts'] = []
                except:
                    result['customer'] = {}
            else:
                result['customer'] = {}

            # if result['user_code'] is not None:
            #     try:
            #         result['user'] = self.user_model.get_user_by_username(
            #             self.cursor, result['user_code'], select="id, employee_id, branch_id")[0]
            #         if result['user']['employee_id'] is not None:
            #             try:
            #                 result['user']['employee_name'] = self.employee_model.get_employee_by_id(
            #                     self.cursor, result['user']['employee_id'], select="name")[0]['name']
            #             except:
            #                 result['user']['employee_name'] = None
            #         else:
            #             result['user']['employee_name'] = None
            #         if result['user']['branch_id'] is not None:
            #             try:
            #                 result['user']['branch_name'] = self.branch_model.get_branches_by_id(
            #                     self.cursor, result['user']['branch_id'], select="name")[0]['name']
            #             except:
            #                 result['user']['branch_name'] = None
            #         else:
            #             result['user']['branch_name'] = None
            #     except:
            #         result['user'] = {}
            # else:
            #     result['user'] = {}
            # if result['sales_order_code'] is not None:
            #     try:
            #         so_data = self.so_model.get_sales_order_by_id(
            #             self.cursor, result['sales_order_code'], select="user_code")[0]['user_code']
            #         result['user'] = self.user_model.get_user_by_username(
            #             self.cursor, so_data, select="id, employee_id, branch_id")[0]
            #         if result['user']['employee_id'] is not None:
            #             try:
            #                 result['user']['employee_name'] = self.employee_model.get_employee_by_id(
            #                     self.cursor, result['user']['employee_id'], select="name")[0]['name']
            #             except:
            #                 result['user']['employee_name'] = None
            #         else:
            #             result['user']['employee_name'] = None
            #         if result['user']['branch_id'] is not None:
            #             try:
            #                 result['user']['branch_name'] = self.branch_model.get_branches_by_id(
            #                     self.cursor, result['user']['branch_id'], select="name")[0]['name']
            #             except:
            #                 result['user']['branch_name'] = None
            #         else:
            #             result['user']['branch_name'] = None
            #         if result['user']['division_id'] is not None:
            #             try:
            #                 result['user']['division_name'] = self.division_model.get_division_by_id(
            #                     self.cursor, result['user']['division_id'], select="division_name")[0]['division_name']
            #             except:
            #                 result['user']['division_name'] = None
            #         else:
            #             result['user']['division_name'] = None
            #     except:
            #         result['user'] = {}
            # else:
            #     result['user'] = {}
            invoice_data = dict()
            invoice_data['code'] = result['code']
            # invoice_data['invoice_code'] = result['invoice_code']
            invoice_data['invoice_date'] = result['invoice_date']
            invoice_data['customer_code'] = result['customer_code']
            invoice_data['customer'] = result['customer']
            invoice_data['packing_slip_code'] = result['packing_slip_code']
            invoice_data['packing_slip_date'] = result['packing_slip_date']
            invoice_data['sales_order_date'] = result['sales_order_date']
            invoice_data['sales_order_code'] = result['sales_order_code']
            invoice_data['payment_due_date'] = result['payment_due_date']
            invoice_data['invoice_amount'] = result['invoice_amount']
            invoice_data['branch_id'] = result['branch_id']
            if result['branch_id'] is not None:
                try:
                    result['branch_name'] = self.branch_model.get_branches_by_id(
                        self.cursor, result['branch_id'], select="name")[0]['name']
                except:
                    result['branch_name'] = None
            else:
                result['branch_name'] = None
            invoice_data['division_id'] = result['division_id']

            if result['division_id'] is not None:
                try:
                    result['division_name'] = self.division_model.get_division_by_id(
                        self.cursor, result['division_id'], select="division_name")[0][
                        'division_name']
                except:
                    result['division_name'] = None
            else:
                result['division_name'] = None
            # invoice_data['user'] = result['user']
            invoice_data['product'] = result['product']
            # try:
            #     delivery_status = self.delivery_model.get_delivery_by_slip_code(
            #         self.cursor, result['packing_slip_code'])[0]['delivery_date']
            #     if delivery_status:
            #         invoice_data['status'] = 'Packing Slip'
            #     else:
            #         invoice_data['status'] = 'Open Order'
            # except:
            if (result['invoice_amount'] - result['payment_amount']) > 0:
                if result['payment_amount'] > 0:
                    invoice_data['status'] = 'Partialy Paid'
                else:
                    invoice_data['status'] = 'Not Paid'
                try:
                    payment_mobile = self.spm_model.get_all_sales_payment(
                        self.cursor, select="invoice",
                        where="""WHERE JSON_CONTAINS(`invoice`, '{{\"invoice_id\": \"{0}\"}}') 
                              AND is_confirm = 1 """.format(result['code'])
                    )
                    if payment_mobile:
                        for pay in payment_mobile:
                            amount_payment = json.loads(pay['invoice'])
                            if amount_payment:
                                for rec in amount_payment:
                                    if rec['invoice_id'] == result['code']:
                                        result['payment_amount'] += rec['payment_amount']
                                        if (result['invoice_amount'] - rec['payment_amount']) > 0:
                                            if rec['payment_amount'] > 0:
                                                invoice_data['status'] = 'Partialy Paid'
                                            else:
                                                invoice_data['status'] = 'Not Paid'
                                        else:
                                            invoice_data['status'] = 'Paid'
                except:
                    pass
                    print("tidak ada payment")
            else:
                invoice_data['status'] = 'Paid'
            # try:
            #     delivery_status = self.delivery_model.get_delivery_by_slip_code(
            #         self.cursor, sp['packing_slip_code'])[0]['delivery_date']
            #     if delivery_status:
            #         invoice_data['status'] = 'Packing Slip'
            #     else:
            #         invoice_data['status'] = 'Open Order'
            # except:
            #     invoice_data['status'] = 'Open Order'
            try:
                visit_plan = self.visit_plan_model.get_all_visit_plan(
                    self.cursor, select="user_id",
                    where="WHERE JSON_CONTAINS(`invoice_id`, '{{\"id_invoice\": \"{0}\"}}')".format(result['code'])
                )[0]
                result['user_code'] = visit_plan['user_id']
                if result['user_code'] is not None:
                    try:
                        result['user'] = self.user_model.get_user_by_id(
                            self.cursor, result['user_code'], select="id, employee_id, branch_id, division_id")[0]
                        if result['user']['employee_id'] is not None:
                            try:
                                result['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, result['user']['employee_id'], select="name")[0]['name']
                            except:
                                result['user']['employee_name'] = None
                        else:
                            result['user']['employee_name'] = None
                        if result['user']['branch_id'] is not None:
                            try:
                                result['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, result['user']['branch_id'], select="name")[0]['name']
                            except:
                                result['user']['branch_name'] = None
                        else:
                            result['user']['branch_name'] = None
                        if result['user']['division_id'] is not None:
                            try:
                                result['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, result['user']['division_id'], select="division_name")[0][
                                    'division_name']
                            except:
                                result['user']['division_name'] = None
                        else:
                            result['user']['division_name'] = None
                    except:
                        result['user'] = {}
                else:
                    result['user'] = {}

            except Exception as e:
                result['user_code'] = None
                result['user'] = {}
            invoice_data['division_name'] = result['division_name']
            invoice_data['branch_name'] = result['branch_name']
            invoice_data['user'] = result['user']
            invoice_data['user_code'] = result['user_code']
            invoice_data['payment_amount'] = result['payment_amount']

        return invoice_data
