import re
import json
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
from rest.models import PackingSlipModel, SalesOrderModel, CustomerModel, UserModel, EmployeeModel, BranchesModel, \
    DivisionModel, DeliveryModel, DeliveryPlanModel

__author__ = 'Junior'


class LogisticController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.so_model = SalesOrderModel()
        self.packing_slip_model = PackingSlipModel()
        self.customer_model = CustomerModel()
        self.user_model = UserModel()
        self.employee_model = EmployeeModel()
        self.branch_model = BranchesModel()
        self.division_model = DivisionModel()
        self.delivery_model = DeliveryModel()
        self.delivery_plan_model = DeliveryPlanModel()

    # # TODO: controllers packing slip
    # def import_packing_slip(self, file, user_id: 'int'):
    #     """
    #     import packing slip
    #     :param file: file
    #     :param user_id: int
    #     :return:
    #     """
    #     headers = ['Created date and time', 'Packing slip', 'Customer code', 'Item number',
    #                'Product name', 'Brand name', 'Branch code', 'Division code', 'Quantity', 'Notes']
    #     batch_data = []
    #     today = datetime.today()
    #     today = today.strftime("%Y-%m-%d %H:%M:%S")
    #
    #     df = pd.read_excel(file, sheet_name=0, skiprows=0)
    #     for idx in df.columns:
    #         if idx not in headers:
    #             raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])
    #     # TODO: Get Parent Sales Order
    #     # df_parent = df[
    #     #     ['Sales order', 'Created date and time', 'Customer account', 'Line status', '(C) No bukti / keterangan',
    #     #      'Packing slip', 'PS date', 'Invoice', 'Inv date', 'Sales group']]
    #     df_parent = df[
    #         ['Created date and time', 'Customer code', 'Notes',
    #          'Packing slip', 'Branch code', 'Division code']]
    #     df_parent.set_index("Packing slip", inplace=True)
    #     df_parent = df_parent.groupby('Packing slip').last()
    #     # df_parent.columns = ['create_date', 'customer_code', 'status', 'notes', 'packing_slip_code',
    #     #                      'packing_slip_date', 'invoice_code', 'invoice_date', 'sales_group']
    #     df_parent.columns = ['date', 'customer_code', 'notes', 'branch_code', 'division_code']
    #     df_parent.index.names = ['code']
    #     # df_parent['branch_code'] = df_parent['site_id'].str[:2]
    #     # df_parent['division_code'] = df_parent['site_id'].str[2:]
    #     # df_parent['division_code'] = df_parent['sales_group'].str.split('-').str[0]
    #     # df_parent['user_code'] = df_parent['sales_group'].str.split('-').str[1]
    #     # df_parent['cycle_number'] = df_parent['sales_group'].str.split('-').str[2]
    #
    #     df_parent_json = df_parent.to_json(orient='index', date_format='iso')
    #     df_parent_json = json.loads(df_parent_json)
    #
    #     # # TODO: Get Product from sales order
    #     for idx in df_parent_json:
    #         df_product = \
    #         df[['Item number', 'Product name', 'Brand name', 'Branch code', 'Division code', 'Quantity']].loc[
    #             df['Packing slip'] == idx]
    #         df_product.columns = ['item_number', 'product_name', 'brand_name', 'branch_code', 'division_code',
    #                               'quantity']
    #         # df_product = df_product[['Item number', 'Product name']]
    #         df_product_list = df_product.to_dict('record')
    #         df_parent_json[idx]['product'] = df_product_list
    #         # df_parent_json[idx]['invoice_amount'] = 0
    #         # for prod in df_product_list:
    #         #     df_parent_json[idx]['invoice_amount'] += int(prod['net_amount'])
    #
    #     for key, val in df_parent_json.items():
    #         value = val
    #         value['code'] = key
    #         if value['date']:
    #             value['date'] = dateutil.parser.parse(value['date']).strftime("%Y-%m-%d %H:%M:%S")
    #         else:
    #             value['date'] = None
    #         # if value['packing_slip_date']:
    #         #     value['packing_slip_date'] = dateutil.parser.parse(value['packing_slip_date']).strftime("%Y-%m-%d")
    #         # else:
    #         #     value['packing_slip_date'] = None
    #         # if value['invoice_date']:
    #         #     value['invoice_date'] = dateutil.parser.parse(value['invoice_date']).strftime("%Y-%m-%d")
    #         # else:
    #         #     value['invoice_date'] = None
    #         value['import_date'] = today
    #         value['update_date'] = today
    #         value['import_by'] = user_id
    #         if value['branch_code'] is not None:
    #             try:
    #                 branch_id = self.branch_model.get_branches_by_code(self.cursor, code=value['branch_code'])[0]
    #                 value['branch_id'] = branch_id['id']
    #             except:
    #                 value['branch_id'] = None
    #         else:
    #             value['branch_id'] = None
    #         if value['division_code'] is not None:
    #             try:
    #                 division_id = self.division_model.get_division_by_code(
    #                     self.cursor, code=value['division_code'], _id=None
    #                 )[0]
    #                 value['division_id'] = division_id['id']
    #             except:
    #                 value['division_id'] = None
    #         else:
    #             value['division_id'] = None
    #         del value['branch_code']
    #         del value['division_code']
    #         batch_data.append(value)
    #
    #     truncate = self.packing_slip_model.delete_table(self.cursor)
    #
    #     for rec in batch_data:
    #         try:
    #             result = self.packing_slip_model.import_insert(self.cursor, rec, 'code')
    #             mysql.connection.commit()
    #         except Exception as e:
    #             # raise BadRequest(e, 200, 1, data=[])
    #             pass
    #
    #     return True

    # TODO: controllers packing slip new format
    def import_packing_slip(self, file, user_id: 'int'):
        """
        import packing slip
        :param file: file
        :param user_id: int
        :return:
        """
        headers = ['INVNO', 'DOCUMENTNUMBER', 'CUSTOMERKEY', 'ITEMKEY', 'ITEMDESCRIPTION', 'QTYSHIPPED', 'SHIPDATE',
                   'BRANCH CODE', 'DIVISION CODE']
        batch_data = []
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_excel(file, sheet_name=0, skiprows=0, usecols=13)
        for idx in df.columns:
            if idx not in headers:
                raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])

        # TODO: Get Parent Sales Order
        df_parent = df[['DOCUMENTNUMBER', 'CUSTOMERKEY', 'SHIPDATE', 'BRANCH CODE', 'DIVISION CODE']]
        df_parent.set_index("DOCUMENTNUMBER", inplace=True)
        df_parent = df_parent.groupby('DOCUMENTNUMBER').last()
        df_parent.columns = ['customer_code', 'date', 'branch_id', 'division_id']
        df_parent.index.names = ['code']

        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)

        for idx in df_parent_json:
            df_product = df[['ITEMKEY', 'ITEMDESCRIPTION', 'QTYSHIPPED']].loc[df['DOCUMENTNUMBER'] == idx]
            df_product.columns = ['item_number', 'product_name', 'quantity']
            df_product['brand_code'] = idx  # isi brand_code dengan packing_slip id
            df_product['brand_name'] = ""
            df_product['division_code'] = ""
            df_product_list = df_product.to_dict('record')
            df_parent_json[idx]['product'] = df_product_list

        for key, val in df_parent_json.items():
            value = val
            value['code'] = key
            if value['date']:
                value['date'] = dateutil.parser.parse(value['date']).strftime("%Y-%m-%d %H:%M:%S")
            else:
                value['date'] = None
            value['import_date'] = today
            value['update_date'] = today
            value['import_by'] = user_id
            if value['branch_id'] is not None:
                try:
                    branch_id = self.branch_model.get_branches_by_code(self.cursor, code=value['branch_id'])[0]
                    value['branch_id'] = branch_id['id']
                except:
                    value['branch_id'] = 1
            else:
                value['branch_id'] = 1
            if value['branch_id'] is not None:
                try:
                    division_id = self.division_model.get_division_by_code(
                        self.cursor, code=value['branch_id'], _id=None
                    )[0]
                    value['division_id'] = division_id['id']
                except:
                    value['division_id'] = 1
            else:
                value['division_id'] = 1

            batch_data.append(value)

        for rec in batch_data:
            try:
                result = self.packing_slip_model.import_insert(self.cursor, rec, 'code')
                mysql.connection.commit()
            except Exception as e:
                pass

        return True

    def import_packing_slip_file(self, filename: str, filename_origin: str, table: str, user_id: int):
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
            result = self.packing_slip_model.import_insert_file(
                self.cursor, file_name=filename, file_name_origin=filename_origin, table=table,
                create_date=today, update_date=today, create_by=user_id
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def accept_packing_slip(self, create_data: dict, user_id: int, packing_id: str):
        """

        :param create_data: dict
        :param user_id: int
        :param packing_id: str
        :return:
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.delivery_model.insert_into_db(
                self.cursor, packing_slip_code=packing_id, delivery_date=today, user_id=user_id,
                customer_code=create_data['customer_code'], delivery_plan_id=create_data['delivery_plan_id'],
                product=create_data['product'], is_accepted=True, accepted_by=create_data['accepted_by'],
                is_rejected=False, rejected_by=None, reason_reject=None, create_date=today, update_date=today
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return last_insert_id

    def reject_packing_slip(self, create_data: dict, user_id: int, packing_id: str):
        """

        :param create_data: dict
        :param user_id: int
        :param packing_id: str
        :return:
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.delivery_model.insert_into_db(
                self.cursor, packing_slip_code=packing_id, delivery_date=today, user_id=user_id,
                customer_code=create_data['customer_code'], delivery_plan_id=create_data['delivery_plan_id'],
                product=create_data['product'], is_accepted=False, accepted_by=None,
                is_rejected=True, rejected_by=create_data['rejected_by'], reason_reject=create_data['reason_reject'],
                create_date=today, update_date=today
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return last_insert_id

    def get_all_packing_slip_data(
            self, page: int, limit: int, search: str, column: str, direction: str,
            dropdown: bool, branch_privilege: list, data_filter: list
    ):
        """
        Get List Of Sales Order
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: dropdown: bool
        :param: branch_privilege: list
        :return:
            list Sales Orders Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        # today = '2018-06-29'

        packing_slip = {}
        data = []
        start = page * limit - limit
        order = ''
        if column:
            if column == 'employee':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'customer':
                order = """ORDER BY c.name {0}""".format(direction)
            else:
                order = """ORDER BY ps.{0} {1}""".format(column, direction)

        if dropdown:
            where = "WHERE (ps.branch_id IN ({0})) ".format(
                ", ".join(str(x) for x in branch_privilege)
            )
        else:
            where = "WHERE (ps.branch_id IN ({0})) ".format(
                ", ".join(str(x) for x in branch_privilege)
            )
        where_origin = where

        select = "ps.*"
        select_count = "ps.code"
        join = """as ps LEFT JOIN `sales_orders` as so ON ps.sales_order_code = so.code
                        LEFT JOIN `users` as u ON so.user_code = u.username 
                        LEFT JOIN `customer` as c ON ps.customer_code = c.code
                        LEFT JOIN `employee` as e ON u.employee_id = e.id 
                        LEFT JOIN `branches` as b ON u.branch_id = b.id """
        if search:
            if dropdown:
                where += """AND (ps.sales_order_code LIKE '%{0}%' OR ps.code LIKE '%{0}%' OR b.name LIKE '%{0}%' 
                        OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%' OR ps.customer_code LIKE '%{0}%')""".format(search)
            else:
                where += """AND (ps.sales_order_code LIKE '%{0}%' OR ps.code LIKE '%{0}%' OR b.name LIKE '%{0}%' 
                        OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%' OR ps.customer_code LIKE '%{0}%')""".format(search)

        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                where += """AND (ps.date >= '{0} 00:00:00' AND ps.date <= '{1} 23:59:59') """.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            if data_filter['branch_id']:
                where += """AND ps.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
        ps_data = self.packing_slip_model.get_all_packing_slip(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.packing_slip_model.get_count_all_packing_slip(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.packing_slip_model.get_count_all_packing_slip(
            self.cursor, select=select_count, join=join, where=where_origin
        )
        if ps_data:
            for ps in ps_data:
                if ps['sales_order_code'] is not None:
                    try:
                        ps['sales_order'] = self.so_model.get_sales_order_by_id(
                            self.cursor, ps['sales_order_code'], select='product, user_code'
                        )[0]
                        if ps['sales_order']['product'] is not None:
                            ps['sales_order']['product'] = json.loads(ps['sales_order']['product'])
                        if ps['sales_order']['user_code'] is not None:
                            try:
                                ps['sales_order']['user'] = self.user_model.get_user_by_username(
                                    self.cursor, ps['sales_order']['user_code'],
                                    select="id, employee_id, branch_id, division_id"
                                )[0]
                                if ps['sales_order']['user']['employee_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['employee_name'] = \
                                            self.employee_model.get_employee_by_id(
                                                self.cursor, ps['sales_order']['user']['employee_id'], select="name")[
                                                0][
                                                'name']
                                    except:
                                        ps['sales_order']['user']['employee_name'] = None
                                else:
                                    ps['sales_order']['user']['employee_name'] = None
                                if ps['sales_order']['user']['branch_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ps['sales_order']['user']['branch_id'], select="name")[0][
                                            'name']
                                    except:
                                        ps['sales_order']['user']['branch_name'] = None
                                else:
                                    ps['sales_order']['user']['branch_name'] = None
                                if ps['sales_order']['user']['division_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['division_name'] = \
                                            self.division_model.get_division_by_id(
                                                self.cursor, ps['sales_order']['user']['division_id'],
                                                select="division_name")[0][
                                                'division_name']
                                    except:
                                        ps['sales_order']['user']['division_name'] = None
                                else:
                                    ps['sales_order']['user']['division_name'] = None
                            except:
                                ps['sales_order']['user'] = {}
                        else:
                            ps['sales_order']['user'] = {}
                    except:
                        ps['sales_order'] = {}
                else:
                    ps['sales_order'] = {}
                if ps['branch_id'] is not None:
                    try:
                        ps['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, ps['branch_id'], select="name")[0]['name']
                    except:
                        ps['branch_name'] = None
                else:
                    ps['branch_name'] = None

                if ps['division_id'] is not None:
                    try:
                        ps['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, ps['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        ps['division_name'] = None
                else:
                    ps['division_name'] = None
                try:
                    delivery_plan = self.delivery_plan_model.get_all_delivery_plan(
                        self.cursor, select="user_id",
                        where="WHERE JSON_CONTAINS(`packing_slip_id`, '{{\"id_packing_slip\": \"{0}\"}}')".format(
                            ps['code'])
                    )[0]
                    ps['user_id'] = delivery_plan['user_id']
                    if ps['user_id'] is not None:
                        try:
                            ps['user'] = self.user_model.get_user_by_id(
                                self.cursor, ps['user_id'], select="id, username, employee_id, branch_id, division_id")[
                                0]
                            ps['user_code'] = ps['user']['username']
                            if ps['user']['employee_id'] is not None:
                                try:
                                    ps['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                        self.cursor, ps['user']['employee_id'], select="name")[0]['name']
                                except:
                                    ps['user']['employee_name'] = None
                            else:
                                ps['user']['employee_name'] = None
                            if ps['user']['branch_id'] is not None:
                                try:
                                    ps['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                        self.cursor, ps['user']['branch_id'], select="name")[0]['name']
                                except:
                                    ps['user']['branch_name'] = None
                            else:
                                ps['user']['branch_name'] = None
                        except:
                            ps['user_code'] = None
                            ps['user'] = {}
                    else:
                        ps['user_code'] = None
                        ps['user'] = {}
                except:
                    ps['user_code'] = None
                    ps['user'] = {}
                if ps['date'] is not None:
                    ps['date'] = str(ps['date'])
                    # today = datetime.today()
                    # today = today.strftime("%Y-%m-%d")
                    # if datetime.strptime(ps['date'], "%Y-%m-%d %H:%M:%S") < datetime.strptime(today, "%Y-%m-%d"):
                    #     ps['status'] = 'Delivered'
                    # else:
                    #     try:
                    #         delivery_status = self.delivery_model.get_delivery_by_slip_code(
                    #             self.cursor, ps['code'])[0]['delivery_date']
                    #         if delivery_status:
                    #             ps['status'] = 'Delivered'
                    #     except:
                    #         ps['status'] = 'Ready'
                    try:
                        delivery_status = self.delivery_model.get_delivery_by_slip_code(
                            self.cursor, ps['code'])[0]['delivery_date']
                        if delivery_status:
                            ps['status'] = 'Delivered'
                    except:
                        ps['status'] = 'Ready'
                if ps['customer_code'] is not None:
                    try:
                        ps['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, ps['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        ps['customer'] = {}
                else:
                    ps['customer'] = {}
                if dropdown:
                    if ps['status'] != 'Delivered':
                        data.append(ps)
                    else:
                        count -= 1
                else:
                    data.append(ps)
        packing_slip['data'] = data
        packing_slip['total'] = count
        packing_slip['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if packing_slip['total'] > page * limit:
            packing_slip['has_next'] = True
        else:
            packing_slip['has_next'] = False
        if limit <= page * count - count:
            packing_slip['has_prev'] = True
        else:
            packing_slip['has_prev'] = False
        return packing_slip

    def get_all_packing_slip_data_by_customer(
            self, page: int, limit: int, search: str, column: str, direction: str, customer_code: list,
            branch_privilege: list
    ):
        """
        Get List Of Sales Order
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: customer_code: list
        :param: branch_privilege: list
        :return:
            list Sales Orders Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        # today = '2018-06-29'

        packing_slip = {}
        data = []
        start = page * limit - limit
        order = ''
        if column:
            if column == 'employee':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'customer':
                order = """ORDER BY c.name {0}""".format(direction)
            else:
                order = """ORDER BY ps.{0} {1}""".format(column, direction)
        where = "WHERE (ps.branch_id IN ({0}) AND ps.customer_code IN ('{1}')) ".format(
            ", ".join(str(x) for x in branch_privilege), "', '".join(str(x) for x in customer_code)
        )
        where_origin = where

        select = "ps.*"
        select_count = "ps.code"
        join = """as ps LEFT JOIN `sales_orders` as so ON ps.sales_order_code = so.code
                        LEFT JOIN `users` as u ON so.user_code = u.username 
                        LEFT JOIN `customer` as c ON ps.customer_code = c.code
                        LEFT JOIN `employee` as e ON u.employee_id = e.id 
                        LEFT JOIN `branches` as b ON u.branch_id = b.id """
        if search:
            where += """AND (ps.sales_order_code LIKE '%{0}%' OR ps.code LIKE '%{0}%' OR b.name LIKE '%{0}%' 
                        OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)

        ps_data = self.packing_slip_model.get_all_packing_slip(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.packing_slip_model.get_count_all_packing_slip(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.packing_slip_model.get_count_all_packing_slip(
            self.cursor, select=select_count, join=join, where=where_origin
        )
        if ps_data:
            for ps in ps_data:
                if ps['sales_order_code'] is not None:
                    try:
                        ps['sales_order'] = self.so_model.get_sales_order_by_id(
                            self.cursor, ps['sales_order_code'], select='product, user_code'
                        )[0]
                        if ps['sales_order']['product'] is not None:
                            ps['sales_order']['product'] = json.loads(ps['sales_order']['product'])
                        if ps['sales_order']['user_code'] is not None:
                            try:
                                ps['sales_order']['user'] = self.user_model.get_user_by_username(
                                    self.cursor, ps['sales_order']['user_code'],
                                    select="id, employee_id, branch_id, division_id"
                                )[0]
                                if ps['sales_order']['user']['employee_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['employee_name'] = \
                                            self.employee_model.get_employee_by_id(
                                                self.cursor, ps['sales_order']['user']['employee_id'], select="name")[
                                                0][
                                                'name']
                                    except:
                                        ps['sales_order']['user']['employee_name'] = None
                                else:
                                    ps['sales_order']['user']['employee_name'] = None
                                if ps['sales_order']['user']['branch_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ps['sales_order']['user']['branch_id'], select="name")[0][
                                            'name']
                                    except:
                                        ps['sales_order']['user']['branch_name'] = None
                                else:
                                    ps['sales_order']['user']['branch_name'] = None
                                if ps['sales_order']['user']['division_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['division_name'] = \
                                            self.division_model.get_division_by_id(
                                                self.cursor, ps['sales_order']['user']['division_id'],
                                                select="division_name")[0][
                                                'division_name']
                                    except:
                                        ps['sales_order']['user']['division_name'] = None
                                else:
                                    ps['sales_order']['user']['division_name'] = None
                            except:
                                ps['sales_order']['user'] = {}
                        else:
                            ps['sales_order']['user'] = {}
                    except:
                        ps['sales_order'] = {}
                else:
                    ps['sales_order'] = {}
                if ps['branch_id'] is not None:
                    try:
                        ps['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, ps['branch_id'], select="name")[0]['name']
                    except:
                        ps['branch_name'] = None
                else:
                    ps['branch_name'] = None

                if ps['division_id'] is not None:
                    try:
                        ps['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, ps['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        ps['division_name'] = None
                else:
                    ps['division_name'] = None
                try:
                    delivery_plan = self.delivery_plan_model.get_all_delivery_plan(
                        self.cursor, select="user_id",
                        where="WHERE JSON_CONTAINS(`packing_slip_id`, '{{\"id_packing_slip\": \"{0}\"}}')".format(
                            ps['code'])
                    )[0]
                    ps['user_id'] = delivery_plan['user_id']
                    if ps['user_id'] is not None:
                        try:
                            ps['user'] = self.user_model.get_user_by_id(
                                self.cursor, ps['user_id'], select="id, username, employee_id, branch_id, division_id")[
                                0]
                            ps['user_code'] = ps['user']['username']
                            if ps['user']['employee_id'] is not None:
                                try:
                                    ps['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                        self.cursor, ps['user']['employee_id'], select="name")[0]['name']
                                except:
                                    ps['user']['employee_name'] = None
                            else:
                                ps['user']['employee_name'] = None
                            if ps['user']['branch_id'] is not None:
                                try:
                                    ps['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                        self.cursor, ps['user']['branch_id'], select="name")[0]['name']
                                except:
                                    ps['user']['branch_name'] = None
                            else:
                                ps['user']['branch_name'] = None
                        except:
                            ps['user_code'] = None
                            ps['user'] = {}
                    else:
                        ps['user_code'] = None
                        ps['user'] = {}
                except:
                    ps['user_code'] = None
                    ps['user'] = {}
                if ps['date'] is not None:
                    ps['date'] = str(ps['date'])
                    # today = datetime.today()
                    # today = today.strftime("%Y-%m-%d")
                    # if datetime.strptime(ps['date'], "%Y-%m-%d %H:%M:%S") < datetime.strptime(today, "%Y-%m-%d"):
                    #     ps['status'] = 'Delivered'
                    # else:
                    #     try:
                    #         delivery_status = self.delivery_model.get_delivery_by_slip_code(
                    #             self.cursor, ps['code'])[0]['delivery_date']
                    #         if delivery_status:
                    #             ps['status'] = 'Delivered'
                    #     except:
                    #         ps['status'] = 'Ready'
                    try:
                        delivery_status = self.delivery_model.get_delivery_by_slip_code(
                            self.cursor, ps['code'])[0]['delivery_date']
                        if delivery_status:
                            ps['status'] = 'Delivered'
                    except:
                        ps['status'] = 'Ready'
                if ps['customer_code'] is not None:
                    try:
                        ps['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, ps['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        ps['customer'] = {}
                else:
                    ps['customer'] = {}
                if ps['status'] != 'Delivered':
                    data.append(ps)
                else:
                    count -= 1
        packing_slip['data'] = data
        packing_slip['total'] = count
        packing_slip['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if packing_slip['total'] > page * limit:
            packing_slip['has_next'] = True
        else:
            packing_slip['has_next'] = False
        if limit <= page * count - count:
            packing_slip['has_prev'] = True
        else:
            packing_slip['has_prev'] = False
        return packing_slip

    def get_all_export_packing_slip_data(
            self, page: int, limit: int, search: str, column: str, direction: str,
            dropdown: bool, branch_privilege: list, data_filter: list
    ):
        """
        Get List Of Sales Order
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: dropdown: bool
        :param: branch_privilege: list
        :return:
            list Sales Orders Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        # today = '2018-06-29'

        result_data = {}
        data = []
        start = page * limit - limit
        order = ''
        if column:
            if column == 'employee':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'customer':
                order = """ORDER BY c.name {0}""".format(direction)
            else:
                order = """ORDER BY ps.{0} {1}""".format(column, direction)

        if dropdown:
            where = "WHERE (ps.branch_id IN ({0})) ".format(
                ", ".join(str(x) for x in branch_privilege)
            )
        else:
            where = "WHERE (ps.branch_id IN ({0})) ".format(
                ", ".join(str(x) for x in branch_privilege)
            )
        where_origin = where

        select = "ps.*"
        select_count = "ps.code"
        join = """as ps LEFT JOIN `sales_orders` as so ON ps.sales_order_code = so.code
                        LEFT JOIN `users` as u ON so.user_code = u.username 
                        LEFT JOIN `customer` as c ON so.customer_code = c.code
                        LEFT JOIN `employee` as e ON u.employee_id = e.id 
                        LEFT JOIN `branches` as b ON u.branch_id = b.id """
        if search:
            if dropdown:
                where += """AND (ps.sales_order_code LIKE '%{0}%' OR ps.code LIKE '%{0}%' OR b.name LIKE '%{0}%' 
                        OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)
            else:
                where += """AND (ps.sales_order_code LIKE '%{0}%' OR ps.code LIKE '%{0}%' OR b.name LIKE '%{0}%' 
                        OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)

        if data_filter:
            tmp_data_filter = data_filter[0]
            if tmp_data_filter['start_date']:
                where += """AND (ps.date >= '{0} 00:00:00' AND ps.date <= '{1} 23:59:59') """.format(
                    tmp_data_filter['start_date'], tmp_data_filter['end_date']
                )
            if tmp_data_filter['branch_id']:
                where += """AND ps.branch_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['branch_id']))
        ps_data = self.packing_slip_model.get_all_packing_slip(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.packing_slip_model.get_count_all_packing_slip(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.packing_slip_model.get_count_all_packing_slip(
            self.cursor, select=select_count, join=join, where=where_origin
        )
        if ps_data:
            for ps in ps_data:
                if ps['sales_order_code'] is not None:
                    try:
                        ps['sales_order'] = self.so_model.get_sales_order_by_id(
                            self.cursor, ps['sales_order_code'], select='product, user_code'
                        )[0]
                        if ps['sales_order']['product'] is not None:
                            ps['sales_order']['product'] = json.loads(ps['sales_order']['product'])
                        if ps['sales_order']['user_code'] is not None:
                            try:
                                ps['sales_order']['user'] = self.user_model.get_user_by_username(
                                    self.cursor, ps['sales_order']['user_code'],
                                    select="id, employee_id, branch_id, division_id"
                                )[0]
                                if ps['sales_order']['user']['employee_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['employee_name'] = \
                                            self.employee_model.get_employee_by_id(
                                                self.cursor, ps['sales_order']['user']['employee_id'], select="name")[
                                                0][
                                                'name']
                                    except:
                                        ps['sales_order']['user']['employee_name'] = None
                                else:
                                    ps['sales_order']['user']['employee_name'] = None
                                if ps['sales_order']['user']['branch_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ps['sales_order']['user']['branch_id'], select="name")[0][
                                            'name']
                                    except:
                                        ps['sales_order']['user']['branch_name'] = None
                                else:
                                    ps['sales_order']['user']['branch_name'] = None
                                if ps['sales_order']['user']['division_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['division_name'] = \
                                            self.division_model.get_division_by_id(
                                                self.cursor, ps['sales_order']['user']['division_id'],
                                                select="division_name")[0][
                                                'division_name']
                                    except:
                                        ps['sales_order']['user']['division_name'] = None
                                else:
                                    ps['sales_order']['user']['division_name'] = None
                            except:
                                ps['sales_order']['user'] = {}
                        else:
                            ps['sales_order']['user'] = {}
                    except:
                        ps['sales_order'] = {}
                else:
                    ps['sales_order'] = {}
                if ps['branch_id'] is not None:
                    try:
                        ps['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, ps['branch_id'], select="name")[0]['name']
                    except:
                        ps['branch_name'] = None
                else:
                    ps['branch_name'] = None

                if ps['division_id'] is not None:
                    try:
                        ps['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, ps['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        ps['division_name'] = None
                else:
                    ps['division_name'] = None
                try:
                    delivery_plan = self.delivery_plan_model.get_all_delivery_plan(
                        self.cursor, select="user_id",
                        where="WHERE JSON_CONTAINS(`packing_slip_id`, '{{\"id_packing_slip\": \"{0}\"}}')".format(
                            ps['code'])
                    )[0]
                    ps['user_id'] = delivery_plan['user_id']
                    if ps['user_id'] is not None:
                        try:
                            ps['user'] = self.user_model.get_user_by_id(
                                self.cursor, ps['user_id'], select="id, username, employee_id, branch_id, division_id")[
                                0]
                            ps['user_code'] = ps['user']['username']
                            if ps['user']['employee_id'] is not None:
                                try:
                                    ps['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                        self.cursor, ps['user']['employee_id'], select="name")[0]['name']
                                except:
                                    ps['user']['employee_name'] = None
                            else:
                                ps['user']['employee_name'] = None
                            if ps['user']['branch_id'] is not None:
                                try:
                                    ps['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                        self.cursor, ps['user']['branch_id'], select="name")[0]['name']
                                except:
                                    ps['user']['branch_name'] = None
                            else:
                                ps['user']['branch_name'] = None
                        except:
                            ps['user_code'] = None
                            ps['user'] = {}
                    else:
                        ps['user_code'] = None
                        ps['user'] = {}
                except:
                    ps['user_code'] = None
                    ps['user'] = {}
                if ps['date'] is not None:
                    ps['date'] = str(ps['date'])
                    # today = datetime.today()
                    # today = today.strftime("%Y-%m-%d")
                    # if datetime.strptime(ps['date'], "%Y-%m-%d %H:%M:%S") < datetime.strptime(today, "%Y-%m-%d"):
                    #     ps['status'] = 'Delivered'
                    # else:
                    #     try:
                    #         delivery_status = self.delivery_model.get_delivery_by_slip_code(
                    #             self.cursor, ps['code'])[0]['delivery_date']
                    #         if delivery_status:
                    #             ps['status'] = 'Delivered'
                    #     except:
                    #         ps['status'] = 'Ready'
                    try:
                        delivery_status = self.delivery_model.get_delivery_by_slip_code(
                            self.cursor, ps['code'])[0]['delivery_date']
                        if delivery_status:
                            ps['status'] = 'Delivered'
                    except:
                        ps['status'] = 'Ready'
                if ps['customer_code'] is not None:
                    try:
                        ps['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, ps['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        ps['customer'] = {}
                else:
                    ps['customer'] = {}
                if dropdown:
                    if ps['status'] != 'Delivered':
                        data.append(ps)
                    else:
                        count -= 1
                else:
                    data.append(ps)
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Packing Slip')
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
                    'PACKING SLIP (TANGGAL: {0} s/d {1})'.format(
                        data_filter['start_date'], data_filter['end_date']
                    ),
                    merge_format
                )
            else:
                worksheet.merge_range(
                    'A1:F1',
                    'PACKING SLIP (TANGGAL: ALL)',
                    merge_format
                )
        else:
            worksheet.merge_range('A1:F1', 'PACKING SLIP (TANGGAL: ALL)', merge_format)

        worksheet.write('A3', 'NO PACKING SLIP')
        worksheet.write('B3', 'NO SALES ORDER')
        worksheet.write('C3', 'TANGGAL')
        worksheet.write('D3', 'BRANCH')
        worksheet.write('E3', 'CUSTOMER')
        worksheet.write('F3', 'DRIVER')
        worksheet.write('G3', 'STATUS')

        data_rows = 3
        for rec in data:
            worksheet.write(data_rows, 0, rec['code'])
            worksheet.write(data_rows, 1, rec['sales_order_code'])
            worksheet.write(data_rows, 2, rec['date'])
            worksheet.write(data_rows, 3, rec['branch_name'])
            worksheet.write(data_rows, 4, rec['customer_code'])
            worksheet.write(data_rows, 5, rec['user_code'])
            worksheet.write(data_rows, 6, rec['status'])
            data_rows += 1

        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_all_export_pdf_packing_slip_data(
            self, page: int, limit: int, search: str, column: str, direction: str,
            dropdown: bool, branch_privilege: list, data_filter: list
    ):
        """
        Get List Of Sales Order
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: dropdown: bool
        :param: branch_privilege: list
        :return:
            list Sales Orders Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        # today = '2018-06-29'

        result_data = {}
        data = []
        start = page * limit - limit
        order = ''
        if column:
            if column == 'employee':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'customer':
                order = """ORDER BY c.name {0}""".format(direction)
            else:
                order = """ORDER BY ps.{0} {1}""".format(column, direction)

        if dropdown:
            where = "WHERE (ps.branch_id IN ({0})) ".format(
                ", ".join(str(x) for x in branch_privilege)
            )
        else:
            where = "WHERE (ps.branch_id IN ({0})) ".format(
                ", ".join(str(x) for x in branch_privilege)
            )
        where_origin = where

        select = "ps.*"
        select_count = "ps.code"
        join = """as ps LEFT JOIN `sales_orders` as so ON ps.sales_order_code = so.code
                        LEFT JOIN `users` as u ON so.user_code = u.username 
                        LEFT JOIN `customer` as c ON so.customer_code = c.code
                        LEFT JOIN `employee` as e ON u.employee_id = e.id 
                        LEFT JOIN `branches` as b ON u.branch_id = b.id """
        if search:
            if dropdown:
                where += """AND (ps.sales_order_code LIKE '%{0}%' OR ps.code LIKE '%{0}%' OR b.name LIKE '%{0}%' 
                        OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)
            else:
                where += """AND (ps.sales_order_code LIKE '%{0}%' OR ps.code LIKE '%{0}%' OR b.name LIKE '%{0}%' 
                        OR e.name LIKE '%{0}%' OR c.name LIKE '%{0}%')""".format(search)

        if data_filter:
            tmp_data_filter = data_filter[0]
            if tmp_data_filter['start_date']:
                where += """AND (ps.date >= '{0} 00:00:00' AND ps.date <= '{1} 23:59:59') """.format(
                    tmp_data_filter['start_date'], tmp_data_filter['end_date']
                )
            if tmp_data_filter['branch_id']:
                where += """AND ps.branch_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['branch_id']))
        ps_data = self.packing_slip_model.get_all_packing_slip(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.packing_slip_model.get_count_all_packing_slip(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.packing_slip_model.get_count_all_packing_slip(
            self.cursor, select=select_count, join=join, where=where_origin
        )
        if ps_data:
            for ps in ps_data:
                if ps['sales_order_code'] is not None:
                    try:
                        ps['sales_order'] = self.so_model.get_sales_order_by_id(
                            self.cursor, ps['sales_order_code'], select='product, user_code'
                        )[0]
                        if ps['sales_order']['product'] is not None:
                            ps['sales_order']['product'] = json.loads(ps['sales_order']['product'])
                        if ps['sales_order']['user_code'] is not None:
                            try:
                                ps['sales_order']['user'] = self.user_model.get_user_by_username(
                                    self.cursor, ps['sales_order']['user_code'],
                                    select="id, employee_id, branch_id, division_id"
                                )[0]
                                if ps['sales_order']['user']['employee_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['employee_name'] = \
                                            self.employee_model.get_employee_by_id(
                                                self.cursor, ps['sales_order']['user']['employee_id'], select="name")[
                                                0][
                                                'name']
                                    except:
                                        ps['sales_order']['user']['employee_name'] = None
                                else:
                                    ps['sales_order']['user']['employee_name'] = None
                                if ps['sales_order']['user']['branch_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ps['sales_order']['user']['branch_id'], select="name")[0][
                                            'name']
                                    except:
                                        ps['sales_order']['user']['branch_name'] = None
                                else:
                                    ps['sales_order']['user']['branch_name'] = None
                                if ps['sales_order']['user']['division_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['division_name'] = \
                                            self.division_model.get_division_by_id(
                                                self.cursor, ps['sales_order']['user']['division_id'],
                                                select="division_name")[0][
                                                'division_name']
                                    except:
                                        ps['sales_order']['user']['division_name'] = None
                                else:
                                    ps['sales_order']['user']['division_name'] = None
                            except:
                                ps['sales_order']['user'] = {}
                        else:
                            ps['sales_order']['user'] = {}
                    except:
                        ps['sales_order'] = {}
                else:
                    ps['sales_order'] = {}
                if ps['branch_id'] is not None:
                    try:
                        ps['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, ps['branch_id'], select="name")[0]['name']
                    except:
                        ps['branch_name'] = None
                else:
                    ps['branch_name'] = None

                if ps['division_id'] is not None:
                    try:
                        ps['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, ps['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        ps['division_name'] = None
                else:
                    ps['division_name'] = None
                try:
                    delivery_plan = self.delivery_plan_model.get_all_delivery_plan(
                        self.cursor, select="user_id",
                        where="WHERE JSON_CONTAINS(`packing_slip_id`, '{{\"id_packing_slip\": \"{0}\"}}')".format(
                            ps['code'])
                    )[0]
                    ps['user_id'] = delivery_plan['user_id']
                    if ps['user_id'] is not None:
                        try:
                            ps['user'] = self.user_model.get_user_by_id(
                                self.cursor, ps['user_id'], select="id, username, employee_id, branch_id, division_id")[
                                0]
                            ps['user_code'] = ps['user']['username']
                            if ps['user']['employee_id'] is not None:
                                try:
                                    ps['user']['employee_name'] = self.employee_model.get_employee_by_id(
                                        self.cursor, ps['user']['employee_id'], select="name")[0]['name']
                                except:
                                    ps['user']['employee_name'] = None
                            else:
                                ps['user']['employee_name'] = None
                            if ps['user']['branch_id'] is not None:
                                try:
                                    ps['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                        self.cursor, ps['user']['branch_id'], select="name")[0]['name']
                                except:
                                    ps['user']['branch_name'] = None
                            else:
                                ps['user']['branch_name'] = None
                        except:
                            ps['user_code'] = None
                            ps['user'] = {}
                    else:
                        ps['user_code'] = None
                        ps['user'] = {}
                except:
                    ps['user_code'] = None
                    ps['user'] = {}
                if ps['date'] is not None:
                    ps['date'] = str(ps['date'])
                    # today = datetime.today()
                    # today = today.strftime("%Y-%m-%d")
                    # if datetime.strptime(ps['date'], "%Y-%m-%d %H:%M:%S") < datetime.strptime(today, "%Y-%m-%d"):
                    #     ps['status'] = 'Delivered'
                    # else:
                    #     try:
                    #         delivery_status = self.delivery_model.get_delivery_by_slip_code(
                    #             self.cursor, ps['code'])[0]['delivery_date']
                    #         if delivery_status:
                    #             ps['status'] = 'Delivered'
                    #     except:
                    #         ps['status'] = 'Ready'
                    try:
                        delivery_status = self.delivery_model.get_delivery_by_slip_code(
                            self.cursor, ps['code'])[0]['delivery_date']
                        if delivery_status:
                            ps['status'] = 'Delivered'
                    except:
                        ps['status'] = 'Ready'
                if ps['customer_code'] is not None:
                    try:
                        ps['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, ps['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        ps['customer'] = {}
                else:
                    ps['customer'] = {}
                if dropdown:
                    if ps['status'] != 'Delivered':
                        data.append(ps)
                    else:
                        count -= 1
                else:
                    data.append(ps)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                head_title = 'PACKING SLIP (TANGGAL: {0} s/d {1})'.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            else:
                head_title = 'PACKING SLIP (TANGGAL: ALL)'
        else:
            head_title = 'PACKING SLIP (TANGGAL: ALL)'

        head_table = OrderedDict()
        head_table['no'] = "NO PACKING SLIP"
        head_table['no_sales'] = "NO SALES ORDER"
        head_table['tanggal'] = "TANGGAL"
        head_table['branch'] = "BRANCH"
        head_table['customer'] = "CUSTOMER"
        head_table['driver'] = "DRIVER"
        head_table['status'] = "STATUS"
        body_table = []
        for rec in data:
            data_body = OrderedDict()
            data_body['no'] = rec['code']
            data_body['no_sales'] = rec['sales_order_code']
            data_body['tanggal'] = rec['date']
            data_body['branch'] = rec['branch_name']
            data_body['customer'] = rec['customer_code']
            data_body['driver'] = rec['user_code']
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

    def get_all_packing_slip_by_list_customer(self, page: int, limit: int, customer: list, user_id: int, username: str):
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
        where = """WHERE `customer_code` IN ('{0}')""".format("', '".join(x for x in customer))
        ps_data = self.packing_slip_model.get_all_packing_slip(self.cursor, where=where, start=start, limit=limit)
        count_so = self.packing_slip_model.get_count_all_packing_slip(self.cursor, where=where)
        count_so_filter = count_so

        if ps_data:
            for ps in ps_data:
                if ps['sales_order_code'] is not None:
                    try:
                        ps['sales_order'] = self.so_model.get_sales_order_by_id(
                            self.cursor, ps['sales_order_code'], select='product, user_code'
                        )[0]
                        if ps['sales_order']['product'] is not None:
                            ps['sales_order']['product'] = json.loads(ps['sales_order']['product'])
                        if ps['sales_order']['user_code'] is not None:
                            try:
                                ps['sales_order']['user'] = self.user_model.get_user_by_username(
                                    self.cursor, ps['sales_order']['user_code'],
                                    select="id, employee_id, branch_id, division_id"
                                )[0]
                                if ps['sales_order']['user']['employee_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['employee_name'] = \
                                            self.employee_model.get_employee_by_id(
                                                self.cursor, ps['sales_order']['user']['employee_id'], select="name")[
                                                0][
                                                'name']
                                    except:
                                        ps['sales_order']['user']['employee_name'] = None
                                else:
                                    ps['sales_order']['user']['employee_name'] = None
                                if ps['sales_order']['user']['branch_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ps['sales_order']['user']['branch_id'], select="name")[0][
                                            'name']
                                    except:
                                        ps['sales_order']['user']['branch_name'] = None
                                else:
                                    ps['sales_order']['user']['branch_name'] = None
                                if ps['sales_order']['user']['division_id'] is not None:
                                    try:
                                        ps['sales_order']['user']['division_name'] = \
                                            self.division_model.get_division_by_id(
                                                self.cursor, ps['sales_order']['user']['division_id'],
                                                select="division_name")[0][
                                                'division_name']
                                    except:
                                        ps['sales_order']['user']['division_name'] = None
                                else:
                                    ps['sales_order']['user']['division_name'] = None
                            except:
                                ps['sales_order']['user'] = {}
                        else:
                            ps['sales_order']['user'] = {}
                    except:
                        ps['sales_order'] = {}
                else:
                    ps['sales_order'] = {}
                if ps['date'] is not None:
                    ps['date'] = str(ps['date'])
                if ps['customer_code'] is not None:
                    try:
                        ps['customer'] = self.customer_model.get_customer_by_id(
                            self.cursor, ps['customer_code'], select="code, name, address, lng, lat")[0]
                    except:
                        ps['customer'] = {}
                else:
                    ps['customer'] = {}

                data.append(ps)

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

    def get_packing_slip_by_id(self, _id: int):
        """
        Get Sales Order Information Data

        :param _id: int
        :return:
            Sales Order Object
        """
        packing_slip = self.packing_slip_model.get_packing_slip_by_id(self.cursor, _id)

        if len(packing_slip) == 0:
            raise BadRequest("This packing slip not exist", 200, 1, data=[])
        else:
            packing_slip = packing_slip[0]
            if packing_slip['product'] is not None:
                packing_slip['product'] = json.loads(packing_slip['product'])
            if packing_slip['sales_order_code'] is not None:
                try:
                    packing_slip['sales_order'] = self.so_model.get_sales_order_by_id(
                        self.cursor, packing_slip['sales_order_code'], select='product, user_code'
                    )[0]
                    if packing_slip['sales_order']['product'] is not None:
                        packing_slip['sales_order']['product'] = json.loads(packing_slip['sales_order']['product'])
                    if packing_slip['sales_order']['user_code'] is not None:
                        try:
                            packing_slip['sales_order']['user'] = self.user_model.get_user_by_username(
                                self.cursor, packing_slip['sales_order']['user_code'],
                                select="id, employee_id, branch_id, division_id"
                            )[0]
                            if packing_slip['sales_order']['user']['employee_id'] is not None:
                                try:
                                    packing_slip['sales_order']['user']['employee_name'] = \
                                        self.employee_model.get_employee_by_id(
                                            self.cursor, packing_slip['sales_order']['user']['employee_id'],
                                            select="name")[
                                            0]['name']
                                except:
                                    packing_slip['sales_order']['user']['employee_name'] = None
                            else:
                                packing_slip['sales_order']['user']['employee_name'] = None
                            if packing_slip['sales_order']['user']['branch_id'] is not None:
                                try:
                                    packing_slip['sales_order']['user']['branch_name'] = \
                                        self.branch_model.get_branches_by_id(
                                            self.cursor, packing_slip['sales_order']['user']['branch_id'],
                                            select="name")[
                                            0]['name']
                                except:
                                    packing_slip['sales_order']['user']['branch_name'] = None
                            else:
                                packing_slip['sales_order']['user']['branch_name'] = None
                            if packing_slip['sales_order']['user']['division_id'] is not None:
                                try:
                                    packing_slip['sales_order']['user']['division_name'] = \
                                        self.division_model.get_division_by_id(
                                            self.cursor, packing_slip['sales_order']['user']['division_id'],
                                            select="division_name")[
                                            0][
                                            'division_name']
                                except:
                                    packing_slip['sales_order']['user']['division_name'] = None
                            else:
                                packing_slip['sales_order']['user']['division_name'] = None
                        except:
                            packing_slip['sales_order']['user'] = {}
                    else:
                        packing_slip['sales_order']['user'] = {}
                except:
                    packing_slip['sales_order'] = {}
            else:
                packing_slip['sales_order'] = {}
            if packing_slip['date'] is not None:
                packing_slip['date'] = str(packing_slip['date'])
            if packing_slip['customer_code'] is not None:
                try:
                    packing_slip['customer'] = self.customer_model.get_customer_by_id(
                        self.cursor, packing_slip['customer_code'], select="code, name, address, lng, lat")[0]
                except:
                    packing_slip['customer'] = {}
            else:
                packing_slip['customer'] = {}

        return packing_slip

    def get_all_packing_slip_import(self):
        """
        Get List Of Sales Order
        :return:
            list Sales Orders Object
        """
        import_file = {}
        data = []
        import_data = self.packing_slip_model.get_all_packing_slip_import(self.cursor, where="""WHERE `status` = 0 
        AND `table_name` = 'packing_slip'""")
        count = self.packing_slip_model.get_count_all_packing_slip_import(self.cursor, key="id", where="""WHERE `status` = 0 
        AND `table_name` = 'packing_slip'""")
        if import_data:
            for emp in import_data:
                data.append(emp)
        import_file['data'] = data
        import_file['total'] = count

        # TODO: Check Has Next and Prev
        import_file['has_next'] = False
        import_file['has_prev'] = False
        return import_file
