import re
import json
import time
import pandas as pd
import dateutil.parser

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql, date_range
from rest.models import VisitEyeCustomerModel, VisitEyeUserModel

__author__ = 'Junior'


class VisitEyeController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.customer_model = VisitEyeCustomerModel()
        self.user_model = VisitEyeUserModel()

    def get_all_user_data(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of User
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :return:
            list User Object
        """
        user = {}
        data = []
        start = page * limit - limit
        where = ""
        order = ''
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        select = "*"
        select_count = "username"
        join = """"""
        if search:
            where += """WHERE (username LIKE '%{0}%')""".format(search)
        user_data = self.user_model.get_all_user(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.user_model.get_count_all_user(self.cursor, select=select_count, join=join, where=where)
        count = self.user_model.get_count_all_user(self.cursor, select=select_count, join=join, where=where)

        if user_data:
            for u in user_data:
                if u['customer_id'] is not None:
                    u['customer_id'] = json.loads(u['customer_id'])
                data.append(u)
        user['data'] = data
        user['total'] = count
        user['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if user['total'] > page * limit:
            user['has_next'] = True
        else:
            user['has_next'] = False
        if limit <= page * count - count:
            user['has_prev'] = True
        else:
            user['has_prev'] = False
        return user

    def get_customer_from_user_id(self, user_id):
        """

        :param branch_privilege: list
        :param division_privilege: list
        :param category: str
        :return:
        """
        list_customer = []

        select = "customer_id"
        join = ""
        where = """WHERE username IN ({0}) """.format(", ".join(repr(x) for x in user_id))
        all_customer = self.user_model.get_all_user(
            self.cursor, select=select, where=where, join=join
        )
        for rec in all_customer:
            if rec['customer_id']:
                cust = json.loads(rec['customer_id'])
                for c in cust:
                    list_customer.append(c)
        unique_customer = set(list_customer)

        return unique_customer

    def check_customer_by_code(self, code: str, _id: str):
        """
        Check for name division

        :param code: str
        :param _id: str
        :return:
            division Object
        """
        customer = self.customer_model.get_customer_by_code(self.cursor, code, _id)

        if len(customer) == 0:
            return False
        else:
            return True

    def get_customer_by_id(self, _id: int):
        """
        Get division Information Data

        :param _id: int
        :return:
            division Object
        """
        customer = self.customer_model.get_customer_by_id(self.cursor, _id)

        if len(customer) == 0:
            raise BadRequest("This customer not exist", 500, 1, data=[])
        else:
            customer = customer[0]
            if customer['contacts'] is not None:
                customer['contacts'] = json.loads(customer['contacts'])
                for rec in customer['contacts']:
                    customer['list_contacts'].append({
                        "name": rec['name'],
                        "email": rec['email'],
                        "mobile": rec['mobile'],
                        "phone": rec['phone']
                    })

        return customer

    def get_all_customer_data(
            self, page: int, limit: int, search: str, column: str, direction: str, list_customer: list
    ):
        """
        Get List Of cutomer
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: list_customer: list
        :param: dropdown: bool
        :return:
            list customer Object
        """
        customer = {}
        data = []
        where = ""
        start = page * limit - limit
        order = ''
        join = ''
        if list_customer:
            where = "WHERE code IN ('{0}')".format(
                "', '".join(x for x in list_customer)
            )
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            if list_customer:
                where += """AND (code LIKE '%{0}%' OR name LIKE '%{0}%' OR address LIKE '%{0}%')""".format(search)
            else:
                where += """WHERE (code LIKE '%{0}%' OR name LIKE '%{0}%' OR address LIKE '%{0}%')""".format(search)
        customer_data = self.customer_model.get_all_customer(
            self.cursor, where=where, order=order, join=join, start=start, limit=limit
        )
        count_filter = self.customer_model.get_count_all_customer(self.cursor, where=where, join=join)
        count = self.customer_model.get_count_all_customer(self.cursor)
        if customer_data:
            for emp in customer_data:
                if emp['contacts'] is not None:
                    emp['contacts'] = json.loads(emp['contacts'])
                data.append(emp)
        customer['data'] = data
        customer['total'] = count
        customer['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if customer['total'] > page * limit:
            customer['has_next'] = True
        else:
            customer['has_next'] = False
        if limit <= page * count - count:
            customer['has_prev'] = True
        else:
            customer['has_prev'] = False
        return customer

    def get_all_customer_by_area(self, polygon_list: list):
        """
        Get List Of cutomer
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: lng: str
        :param: lat: str
        :param: list_customer: list
        :return:
            list customer Object
        """
        customer = {}
        data = []
        select = """code"""
        where = "WHERE ST_CONTAINS(ST_GEOMFROMTEXT('MULTIPOLYGON({0})'), POINT(lat, lng))".format(
            ", ".join(x for x in polygon_list)
        )
        customer_data = self.customer_model.get_all_customer(
            self.cursor, select=select, where=where, start=0, limit=10000
        )
        if customer_data:
            for emp in customer_data:
                data.append(emp['code'])
        return data

    def get_all_customer_report(
            self, list_customer: list, data_filter: dict, search: str
    ):
        """
        Get List Of cutomer report
        :param: list_customer: list
        :param: data_filter: dict
        :param: job_function: str
        :param: search: str
        :return:
            list customer Object
        """
        customer = {}
        data = []
        where = "WHERE code IN ('{0}') ".format(
            "', '".join(x for x in list_customer)
        )
        if search:
            where += """AND (code LIKE '%{0}%' OR name LIKE '%{0}%') """.format(search)
        customer_data = self.customer_model.get_all_customer(
            self.cursor, where=where, start=0, limit=100000
        )
        count = self.customer_model.get_count_all_customer(
            self.cursor, where=where
        )
        if customer_data:
            for emp in customer_data:
                if emp['contacts'] is not None:
                    emp['contacts'] = json.loads(emp['contacts'])

                data.append(emp)
        customer['data'] = data
        customer['total'] = count

        # TODO: Check Has Next and Prev
        customer['has_next'] = False
        customer['has_prev'] = False

        return customer

    def import_customer_new_format(self):
        """
        import customer
        :return:
        """

        # TODO
        # insert customer
        # insert user, get customer_code, get_employee_id

        file_cust = "rest/file_import/locations.csv"
        file_cust_contact = "rest/file_import/locationContacts.csv"
        file_territory = "rest/file_import/territory.csv"
        file_user = "rest/file_import/beton_user.csv"
        file_employee = "rest/file_import/beton_employee.csv"

        # proses file Customer Contact <file_cust_contact>
        df_cust_contact = pd.read_csv(file_cust_contact, skiprows=0)
        df_parent = df_cust_contact[
            ['no', 'locationCode', 'email', 'name', 'position', 'telephone']
        ]
        df_parent.set_index("no", inplace=True)
        df_parent = df_parent.groupby('no').last()
        df_parent.index.names = ['no']
        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)
        data_customer_contact = []
        for key, val in df_parent_json.items():
            contact = dict()
            contact['locationCode'] = val['locationCode']
            contact['email'] = val['email']
            contact['name'] = val['name']
            contact['position'] = val['position']
            contact['telephone'] = val['telephone']
            data_customer_contact.append(contact)
        print("length data_customer_contact {0}".format(len(data_customer_contact)))

        # Proses file Customer <file_cust>
        headers = ['no', 'code', 'active', 'city', 'country', 'latitude', 'locationCode', 'locationName', 'longitude',
                   'postCode', 'state', 'street1', 'street2', 'street3', 'street4', 'street5']
        data_customer = []
        dump_data_customer = []
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        df_cust = pd.read_csv(file_cust, skiprows=0)
        df_parent = df_cust[
            ['no', 'code', 'active', 'city', 'country', 'latitude', 'locationCode', 'locationName', 'longitude',
             'postCode', 'state', 'street1', 'street2', 'street3', 'street4', 'street5']
        ]
        df_parent.set_index("no", inplace=True)
        df_parent = df_parent.groupby('no').last()
        df_parent.index.names = ['no']
        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)
        for key, val in df_parent_json.items():
            value = dict()
            dump_value = val
            value['code'] = val['code']
            value['name'] = val['locationName']
            address = ""
            if val['street1'] is not None:
                address += val['street1']
            if val['street2'] is not None:
                address += ", "
                address += val['street2']
            if val['street3'] is not None:
                address += ", "
                address += val['street3']
            if val['street4'] is not None:
                address += ", "
                address += val['street4']
            if val['street5'] is not None:
                address += ", "
                address += val['street5']
            value['address'] = address
            value['lng'] = val['longitude']
            value['lat'] = val['latitude']

            # Check Contact from variable: data_cust_contact
            value['contacts'] = []
            for rec in data_customer_contact:
                if rec['locationCode'] == val['locationCode']:
                    value['contacts'].append(
                        {
                            "name": rec['name'],
                            "note": None,
                            "email": rec['email'],
                            "phone": rec['telephone'],
                            "mobile": None,
                            "job_position": rec['position'],
                            "notifications": {
                                "nfc_not_read": None,
                                "invoice_reminder": None,
                                "payment_received": None,
                                "delivery_received": None,
                                "delivery_rejected": None,
                                "sales_order_return": None,
                                "visit_plan_reminder": None,
                                "payment_confirmation": None,
                                "request_order_create": None,
                                "payment_receipt_not_read": None,
                                "sales_order_status_changed": None
                            }
                        }
                    )

            if len(value['contacts']) == 0:
                value['contacts'].append(
                    {
                        "name": value['name'],
                        "note": None,
                        "email": None,
                        "phone": None,
                        "mobile": None,
                        "job_position": "PIC",
                        "notifications": {
                            "nfc_not_read": None,
                            "invoice_reminder": None,
                            "payment_received": None,
                            "delivery_received": None,
                            "delivery_rejected": None,
                            "sales_order_return": None,
                            "visit_plan_reminder": None,
                            "payment_confirmation": None,
                            "request_order_create": None,
                            "payment_receipt_not_read": None,
                            "sales_order_status_changed": None
                        }
                    }
                )

            data_customer.append(value)
            dump_data_customer.append(dump_value)

        print("length of data_customer {0}".format(len(data_customer)))
        print("length of dump_data_customer {0}".format(len(dump_data_customer)))
        print("Process insert data customer...")
        for rec in data_customer:
            try:
                result = self.customer_model.import_insert(self.cursor, rec, 'code')
                mysql.connection.commit()
            except Exception as e:
                pass

        # Proses File Territory <file_territory>
        data_territory = []
        df_territory = pd.read_csv(file_territory, skiprows=0)
        df_parent = df_territory[['no', 'locationCode', 'nickname']]
        df_parent.set_index("no", inplace=True)
        df_parent = df_parent.groupby('no').last()
        df_parent.index.names = ['no']
        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)
        for key, val in df_parent_json.items():
            data_territory.append(val)
        print("length of data_territory {0}".format(len(data_territory)))

        # Proses File User-Employee <file_user>
        data_user = []
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        df_user = pd.read_csv(file_user, skiprows=0)
        df_parent = df_user[['no', 'name']]
        df_parent.set_index("no", inplace=True)
        df_parent = df_parent.groupby('no').last()
        df_parent.index.names = ['no']
        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)
        for key, val in df_parent_json.items():
            value = dict()
            value['username'] = val['name']

            # Get customer by locationCode
            value['customer_id'] = []
            for rec in data_territory:
                if val['name'] == rec['nickname']:
                    locationCode = rec['locationCode']
                    for cust in dump_data_customer:
                        if locationCode == cust['locationCode']:
                            value['customer_id'].append(cust['code'])

            data_user.append(value)
        print("length of data_user {0}".format(len(data_user)))
        print("Process insert data User...")
        for rec in data_user:
            try:
                result = self.user_model.import_insert(self.cursor, rec, 'username')
                mysql.connection.commit()
            except Exception as e:
                pass

        return True
