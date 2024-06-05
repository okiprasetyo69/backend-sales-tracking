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
from rest.helpers.validator import safe_format, safe_invalid_format_message
from rest.models import CustomerModel, UserModel, VisitPlanSummaryModel, SalesActivityModel, LogisticActivityModel, \
    EmployeeModel

# from rest.models import ContactModel

__author__ = 'Junior'


class CustomerController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.customer_model = CustomerModel()
        self.user_model = UserModel()
        self.visit_plan_summary_model = VisitPlanSummaryModel()
        self.sales_activity_model = SalesActivityModel()
        self.logistic_activity_model = LogisticActivityModel()
        self.employee_model = EmployeeModel()
        # self.contact_model = ContactModel()

    def import_customer(self, file, user_id: 'int'):
        """
        import customer
        :param file: file
        :param user_id: int
        :return:
        """
        headers = ['Customer account', 'Name', 'Telephone', 'Contact Name', 'Contact Email', 'Contact Job',
                   'Contact Phone', 'Contact Mobile', 'Contact Notes', 'Address', 'Longitude', 'Latitude',
                   'Parent Customer Account']
        batch_data = []
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_excel(file, sheet_name=0, skiprows=0)
        for idx in df.columns:
            if idx not in headers:
                raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])

        df_parent = df[['Customer account', 'Name', 'Telephone', 'Contact Name', 'Contact Email', 'Contact Job',
                        'Contact Phone', 'Contact Mobile', 'Contact Notes', 'Address', 'Longitude', 'Latitude',
                        'Parent Customer Account']]
        df_parent.set_index("Customer account", inplace=True)
        df_parent = df_parent.groupby('Customer account').last()
        df_parent.columns = ['name', 'phone', 'contact_name', 'contact_email', 'contact_job', 'contact_phone',
                             'contact_mobile', 'contact_notes', 'address', 'lng', 'lat', 'parent_code']
        df_parent.index.names = ['code']
        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)

        for key, val in df_parent_json.items():
            value = val
            if safe_format(value['name']):
                value['code'] = key
                value['nfcid'] = key
                value['import_date'] = today
                value['update_date'] = today
                if value['parent_code']:
                    value['is_branch'] = True
                else:
                    value['is_branch'] = False
                value['import_by'] = user_id
                value['is_approval'] = True
                value['approval_by'] = user_id
                value['contacts'] = []
                value['contacts'].append(
                    {
                        "name": value['contact_name'],
                        "note": value['contact_notes'],
                        "email": value['contact_email'],
                        "phone": value['contact_phone'],
                        "mobile": value['contact_mobile'],
                        "job_position": value['contact_job'],
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
                del value['contact_name'], value['contact_notes'], value['contact_email'], value['contact_phone'], \
                    value['contact_mobile'], value['contact_job']
                batch_data.append(value)
            else:
                raise BadRequest(
                    "Customer Name " + value['name'] + " is not valid, don't include " + safe_invalid_format_message,
                    422, 1,
                    data=[])
        print(batch_data)
        # truncate = self.so_model.delete_table(self.cursor)

        for rec in batch_data:
            try:
                result = self.customer_model.import_insert(self.cursor, rec, 'code')
                mysql.connection.commit()
            except Exception as e:
                # raise BadRequest(e, 200, 1, data=[])
                pass

        return True

    def import_customer_file(self, filename: str, filename_origin: str, table: str, user_id: int):
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
            result = self.customer_model.import_insert_file(self.cursor, file_name=filename,
                                                            file_name_origin=filename_origin,
                                                            table=table, create_date=today,
                                                            update_date=today, create_by=user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def get_all_customer_import(self):
        """
        Get List Of Sales Order
        :return:
            list Sales Orders Object
        """
        import_file = {}
        data = []
        import_data = self.customer_model.get_all_customer_import(self.cursor, where="""WHERE `status` = 0 
        AND `table_name` = 'customer'""")
        count = self.customer_model.get_count_all_customer_import(self.cursor, key="id", where="""WHERE `status` = 0 
        AND `table_name` = 'customer'""")
        if import_data:
            for emp in import_data:
                data.append(emp)
        import_file['data'] = data
        import_file['total'] = count

        # TODO: Check Has Next and Prev
        import_file['has_next'] = False
        import_file['has_prev'] = False
        return import_file

    def get_import_file(self, _id: int):
        """
        Get import by id

        :param _id: int
        :return:
            area Object
        """
        import_file = self.customer_model.get_import_by_id(self.cursor, _id)

        if len(import_file) == 0:
            raise BadRequest("This import file not exist", 200, 1, data=[])
        else:
            import_file = import_file[0]

        return import_file

    def update_import_file(self, _id: int, user_id: int):
        """
        Get area Information Data

        :param _id: int
        :param user_id: int
        :return:
            area Object
        """
        try:
            result = self.customer_model.update_import_by_id(self.cursor, _id, user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def create(self, customer_data: 'dict', user_id: 'int'):
        """
        Function for create new customer

        :param customer_data: dict
        :param user_id: int
        :return:
            Division Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        if customer_data['password']:
            password = self.user_model.hash(customer_data['password'])
        else:
            password = None
        try:
            result = self.customer_model.insert_into_db(self.cursor, code=customer_data['code'],
                                                        name=customer_data['name'], email=customer_data['email'],
                                                        phone=customer_data['phone'], address=customer_data['address'],
                                                        lng=customer_data['lng'], lat=customer_data['lat'],
                                                        username=customer_data['username'],
                                                        password=password,
                                                        nfcid=customer_data['nfcid'],
                                                        contacts=customer_data['contacts'],
                                                        business_activity=customer_data['business_activity'],
                                                        is_branch=customer_data['is_branch'],
                                                        parent_code=(customer_data['parent_code'] if (
                                                                'parent_code' in customer_data) else ""),
                                                        create_date=today, update_date=today,
                                                        is_approval=customer_data['is_approval'],
                                                        approval_by=customer_data['approval_by'], create_by=user_id)
            mysql.connection.commit()
            last_insert_id = customer_data['code']
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id

    def check_customer_by_username(self, username: str, _id: str):
        """
        Check for name division

        :param username: str
        :param _id: str
        :return:
            division Object
        """
        customer = self.customer_model.get_customer_by_username(self.cursor, username, _id)

        if len(customer) == 0:
            return False
        else:
            return True

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

    def check_customer_by_nfcid(self, nfcid: str, _id: str):
        """
        Check for name division

        :param nfcid: str
        :param _id: str
        :return:
            division Object
        """
        customer = self.customer_model.get_customer_by_nfcid(self.cursor, nfcid, _id)

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
            customer['branch'] = []
            customer['list_address'] = []
            customer['list_contacts'] = []
            if customer['address'] is not None:
                customer['list_address'].append(customer['address'])
            if customer['contacts'] is not None:
                customer['contacts'] = json.loads(customer['contacts'])
                for rec in customer['contacts']:
                    customer['list_contacts'].append({
                        "name": rec['name'],
                        "email": rec['email'],
                        "mobile": rec['mobile'],
                        "phone": rec['phone']
                    })
            if customer['parent_code'] is None:
                where = """WHERE `parent_code` = '{}' AND `is_approval` = 1 AND `is_deleted` = 0""".format(
                    customer['code'])
                customer_data = self.customer_model.get_all_customer(self.cursor, where=where)
                if customer_data:
                    for emp in customer_data:
                        if emp['edit_data'] is not None:
                            emp['edit_data'] = json.loads(emp['edit_data'])
                        if emp['contacts'] is not None:
                            emp['contacts'] = json.loads(emp['contacts'])
                            for rec in emp['contacts']:
                                customer['list_contacts'].append({
                                    "name": rec['name'],
                                    "email": rec['email'],
                                    "mobile": rec['mobile'],
                                    "phone": rec['phone']
                                })
                        if emp['business_activity'] is not None:
                            emp['business_activity'] = json.loads(emp['business_activity'])
                        customer['branch'].append(emp)
                        customer['list_address'].append(emp['address'])
            if customer['edit_data'] is not None:
                customer['edit_data'] = json.loads(customer['edit_data'])
            if customer['business_activity'] is not None:
                customer['business_activity'] = json.loads(customer['business_activity'])

            # get last competitor product by customer code
            customer['competitor_images'] = None
            customer_competitor_product = self.visit_plan_summary_model.get_lastest_competitor_product_by_customer_code(
                self.cursor, customer['code'])
            if customer_competitor_product:
                for rec in customer_competitor_product:
                    if rec['competitor_images'] is not None:
                        competitor_images_temporary = []
                        for image in json.loads(rec['competitor_images']):
                            competitor_image = image
                            competitor_image.update({'create_date': rec['create_date'].strftime("%d-%m-%Y")})
                            competitor_images_temporary.append(competitor_image)
                    customer['competitor_images'] = competitor_images_temporary

        return customer

    def get_all_customer_data(
            self, page: int, limit: int, search: str, column: str, direction: str, list_customer: list, dropdown: bool
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
        where_user = ""
        start = page * limit - limit
        order = ''
        join = ''
        if dropdown:
            where = "WHERE is_deleted = 0 AND is_approval = 1 AND `is_deleted` = 0 AND code IN ('{0}')".format(
                "', '".join(x for x in list_customer)
            )
        else:
            where = "WHERE is_deleted = 0 AND is_approval = 1 AND `is_deleted` = 0 "
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (code LIKE '%{0}%' OR name LIKE '%{0}%' OR address LIKE '%{0}%' 
            OR phone LIKE '%{0}%' OR email LIKE '%{0}%')""".format(search)
        customer_data = self.customer_model.get_all_customer(self.cursor, where=where, order=order, join=join,
                                                             start=start, limit=limit)
        count_filter = self.customer_model.get_count_all_customer(self.cursor, where=where, join=join)
        count = self.customer_model.get_count_all_customer(self.cursor)
        if customer_data:
            for emp in customer_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                if emp['contacts'] is not None:
                    emp['contacts'] = json.loads(emp['contacts'])
                if emp['business_activity'] is not None:
                    emp['business_activity'] = json.loads(emp['business_activity'])
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

    def get_all_customer_parent(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of cutomer
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :return:
            list division Object
        """
        customer = {}
        data = []
        start = page * limit - limit
        order = ''
        where = 'WHERE parent_code IS NULL'
        customer_data = self.customer_model.get_all_customer(self.cursor, where=where, order=order,
                                                             start=start, limit=limit)
        count = self.customer_model.get_count_all_customer(self.cursor, where=where)
        if customer_data:
            for emp in customer_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                data.append(emp)
        customer['data'] = data
        customer['total'] = count

        # TODO: Check Has Next and Prev
        customer['has_next'] = False
        customer['has_prev'] = False
        return customer

    def get_all_customer_nearby_data(
            self, page: int, limit: int, search: str, distance: int, lng: str, lat: str, list_customer: list
    ):
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
        where_user = ""
        start = page * limit - limit
        select = """*"""
        select_nearby = """(6371 * acos(cos(radians({0})) 
        * cos(radians(lat)) * cos(radians(lng) 
        - radians({1})) + sin (radians({0})) 
        * sin(radians(lat)))) AS distance""".format(lat, lng)
        order = 'ORDER BY distance'
        where = "WHERE is_deleted = 0 AND is_approval = 1 AND `is_deleted` = 0 "
        if list_customer:
            where += "AND `code` IN ('{0}') ".format(
                "', '".join(x for x in list_customer)
            )
        where_original = where
        if search:
            where += """AND (code LIKE '%{0}%' OR name LIKE '%{0}%' OR address LIKE '%{0}%' 
            OR phone LIKE '%{0}%' OR email LIKE '%{0}%') """.format(search)
        having = "HAVING distance < {} ".format(distance)
        customer_data = self.customer_model.get_all_customer(
            self.cursor, select=select + ', ' + select_nearby, where=where + having, order=order, start=start,
            limit=limit
        )
        count_filter = self.customer_model.get_count_all_customer_nearby(
            self.cursor,
            select_nearby='(SELECT ' + select + ', ' + select_nearby + ' FROM customer ' + where + having + ') AS customer'
        )
        count = self.customer_model.get_count_all_customer_nearby(
            self.cursor,
            select_nearby='(SELECT ' + select + ', ' + select_nearby + ' FROM customer ' + where_original + having + ') AS customer'
        )
        if customer_data:
            for emp in customer_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                if emp['contacts'] is not None:
                    emp['contacts'] = json.loads(emp['contacts'])
                if emp['business_activity'] is not None:
                    emp['business_activity'] = json.loads(emp['business_activity'])
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

    def get_all_customer_by_area(self, polygon_list: list, job_function: list, data_filter: str):
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
        limit = 100000
        customer = {}
        data = []
        select = """customer.code"""
        if job_function == 'sales':
            if data_filter['user_id'] is not '':  # Jika array user_id lebih dari 0
                data_filter_user_id = data_filter['user_id']
                where = "LEFT JOIN sales_activity ON (sales_activity.nfc_code = customer.code) "
                where += "WHERE ST_CONTAINS(ST_GEOMFROMTEXT('MULTIPOLYGON({0})'), POINT(lat, lng)) ".format(
                    ", ".join(x for x in polygon_list)
                )
                where += "AND sales_activity.user_id IN ({0}) ".format(
                    data_filter_user_id
                )
                where += "AND customer.is_branch = 0 "
                where += "GROUP BY customer.code"
            else:
                where = "LEFT JOIN sales_activity ON (sales_activity.nfc_code = customer.code) "
                where += "WHERE ST_CONTAINS(ST_GEOMFROMTEXT('MULTIPOLYGON({0})'), POINT(lat, lng)) ".format(
                    ", ".join(x for x in polygon_list)
                )
                where += "AND customer.is_branch = 0 "
                where += "GROUP BY customer.code"
        else:
            if data_filter['user_id'] is not '':  # Jika array user_id lebih dari 0
                data_filter_user_id = data_filter['user_id']
                where = "LEFT JOIN logistic_activity ON (logistic_activity.nfc_code = customer.code) "
                where += "WHERE ST_CONTAINS(ST_GEOMFROMTEXT('MULTIPOLYGON({0})'), POINT(lat, lng)) ".format(
                    ", ".join(x for x in polygon_list)
                )
                where += "AND logistic_activity.user_id IN ({0}) ".format(
                    data_filter_user_id
                )
                where += "AND customer.is_branch = 0 "
                where += "GROUP BY customer.code"
            else:
                where = "LEFT JOIN logistic_activity ON (logistic_activity.nfc_code = customer.code) "
                where += "WHERE ST_CONTAINS(ST_GEOMFROMTEXT('MULTIPOLYGON({0})'), POINT(lat, lng)) ".format(
                    ", ".join(x for x in polygon_list)
                )
                where += "AND customer.is_branch = 0 "
                where += "GROUP BY customer.code"
        customer_data = self.customer_model.get_all_customer(
            self.cursor, select=select, where=where, start=0, limit=limit
        )
        if customer_data:
            for emp in customer_data:
                data.append(emp['code'])
        return data

    def get_all_customer_report(
            self, list_customer: list, data_filter: dict, job_function: str, search: str
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
        limit = 100000
        customer = {}
        data = []
        data_gantt = []
        where = "WHERE is_deleted = 0 AND is_approval = 1 AND `is_deleted` = 0 AND `is_branch` = 0 AND code IN ('{0}') ".format(
            "', '".join(x for x in list_customer)
        )
        if search:
            where += """AND (code LIKE '%{0}%' OR name LIKE '%{0}%') """.format(search)
        customer_data = self.customer_model.get_all_customer(
            self.cursor, where=where, start=0, limit=limit
        )
        count = self.customer_model.get_count_all_customer(
            self.cursor, where=where
        )
        if customer_data:
            for emp in customer_data:
                cust = {}
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                if emp['contacts'] is not None:
                    emp['contacts'] = json.loads(emp['contacts'])
                if emp['business_activity'] is not None:
                    emp['business_activity'] = json.loads(emp['business_activity'])

                # Start For Sales
                if job_function == "sales":
                    # TODO: Get Child data statistic
                    where_child = """WHERE is_deleted = 0 AND is_approval = 1 AND `is_deleted` = 0 
                    AND `is_branch` = 1 AND parent_code = '{0}' """.format(emp['code'])
                    customer_child_data = self.customer_model.get_all_customer(
                        self.cursor, where=where_child, start=0, limit=limit
                    )
                    temp_child_statistic = {}
                    for cust_child in customer_child_data:
                        s_date = datetime.strptime(data_filter['start_date'], "%Y-%m-%d")
                        e_date = datetime.strptime(data_filter['end_date'], "%Y-%m-%d")
                        # for single_date in date_range(s_date, e_date):
                        #     temp_child_statistic[single_date.strftime("%Y-%m-%d")] = 0
                        try:
                            select = "DATE(sa.tap_nfc_date) AS date, "
                            select_count = "COUNT(sa.id) AS total "

                            if data_filter['user_id'] is not '':
                                select_from = """(SELECT la.* FROM sales_activity AS la INNER JOIN visit_plan AS dp on la.visit_plan_id = dp.id WHERE la.user_id IN ({3}) AND la.tap_nfc_type = 'IN' AND dp.is_deleted = 0 AND (DATE(la.tap_nfc_date) BETWEEN '{0}' AND '{1}') AND la.nfc_code = '{2}' GROUP BY la.visit_plan_id, la.nfc_code, la.tap_nfc_type) as sa""".format(
                                    data_filter['start_date'], data_filter['end_date'], cust_child['code'],
                                    data_filter['user_id']
                                )
                            else:
                                select_from = """(SELECT la.* FROM sales_activity AS la INNER JOIN visit_plan AS dp on la.visit_plan_id = dp.id WHERE la.tap_nfc_type = 'IN' AND dp.is_deleted = 0 AND (DATE(la.tap_nfc_date) BETWEEN '{0}' AND '{1}') AND la.nfc_code = '{2}' GROUP BY la.visit_plan_id, la.nfc_code, la.tap_nfc_type) as sa""".format(
                                    data_filter['start_date'], data_filter['end_date'], cust_child['code']
                                )
                            group = " GROUP BY date"
                            sales_child_statistic = self.sales_activity_model.get_count_all_activity_statistic(
                                self.cursor, select=select, select_count=select_count, select_from=select_from,
                                group=group
                            )
                            # if sales_child_statistic:
                            for single_date in date_range(s_date, e_date):
                                for rec in sales_child_statistic:
                                    if rec['date'].strftime("%Y-%m-%d") == single_date.strftime("%Y-%m-%d"):
                                        temp_child_statistic[single_date.strftime("%Y-%m-%d")] = int(rec['total'])
                        except Exception as e:
                            pass
                    # TODO: Get data statistic sales
                    s_date = datetime.strptime(data_filter['start_date'], "%Y-%m-%d")
                    e_date = datetime.strptime(data_filter['end_date'], "%Y-%m-%d")
                    temp_statistic = {}
                    for single_date in date_range(s_date, e_date):
                        temp_statistic[single_date.strftime("%Y-%m-%d")] = 0
                    try:
                        data_statistic = []
                        data_statistic_gantt = []
                        select = "DATE(sa.tap_nfc_date) AS date, "
                        select_count = "COUNT(sa.id) AS total "

                        if data_filter['user_id'] is not '':
                            select_from = """(SELECT la.* FROM sales_activity AS la INNER JOIN visit_plan AS dp on la.visit_plan_id = dp.id WHERE la.user_id IN ({3}) AND la.tap_nfc_type = 'IN' AND dp.is_deleted = 0 AND (DATE(la.tap_nfc_date) BETWEEN '{0}' AND '{1}') AND la.nfc_code = '{2}' GROUP BY la.visit_plan_id, la.nfc_code, la.tap_nfc_type) as sa""".format(
                                data_filter['start_date'], data_filter['end_date'], emp['code'], data_filter['user_id']
                            )
                        else:
                            select_from = """(SELECT la.* FROM sales_activity AS la INNER JOIN visit_plan AS dp on la.visit_plan_id = dp.id WHERE la.tap_nfc_type = 'IN' AND dp.is_deleted = 0 AND (DATE(la.tap_nfc_date) BETWEEN '{0}' AND '{1}') AND la.nfc_code = '{2}' GROUP BY la.visit_plan_id, la.nfc_code, la.tap_nfc_type) as sa""".format(
                                data_filter['start_date'], data_filter['end_date'], emp['code']
                            )
                        group = " GROUP BY date"
                        sales_statistic = self.sales_activity_model.get_count_all_activity_statistic(
                            self.cursor, select=select, select_count=select_count, select_from=select_from, group=group
                        )
                        if sales_statistic:
                            for rec in sales_statistic:
                                child_data_total = 0
                                if temp_child_statistic:
                                    if temp_child_statistic.get(rec['date'].strftime("%Y-%m-%d")):
                                        child_data_total += temp_child_statistic[rec['date'].strftime("%Y-%m-%d")]
                                temp_statistic[rec['date'].strftime("%Y-%m-%d")] = int(rec['total']) + child_data_total
                                data_statistic_gantt.append({
                                    "from": "/Date('{0}')/".format(rec['date'].strftime("%Y-%m-%d")),
                                    "to": "/Date('{0}')/".format(rec['date'].strftime("%Y-%m-%d")),
                                    "label": int(rec['total']) + child_data_total,
                                    "desc": "{0} Visit".format(int(rec['total']) + child_data_total),
                                })

                        for key, value in temp_statistic.items():
                            data_statistic.append({
                                'date': key,
                                'total': value
                            })

                        # emp['data_statistic'] = data_statistic
                        total = 0
                        for rc in data_statistic:
                            total += rc['total']
                        emp['data_statistic_total'] = total
                    except Exception as e:
                        data_statistic = []
                        data_statistic_gantt = []
                        for key, value in temp_statistic.items():
                            data_statistic.append({
                                'date': key,
                                'total': value
                            })
                        # emp['data_statistic'] = data_statistic
                        emp['data_statistic_total'] = 0
                # Start For Logistic
                else:  # Start Logistic
                    # TODO: Get Child data statistic
                    where_child = """WHERE is_deleted = 0 AND is_approval = 1 AND `is_deleted` = 0 
                                        AND `is_branch` = 1 AND parent_code = '{0}' """.format(emp['code'])
                    customer_child_data = self.customer_model.get_all_customer(
                        self.cursor, where=where_child, start=0, limit=limit
                    )
                    temp_child_statistic = {}
                    if customer_child_data:
                        for cust_child in customer_child_data:
                            s_date = datetime.strptime(data_filter['start_date'], "%Y-%m-%d")
                            e_date = datetime.strptime(data_filter['end_date'], "%Y-%m-%d")
                            try:
                                select = "DATE(sa.tap_nfc_date) AS date, "
                                select_count = "COUNT(sa.id) AS total "

                                if data_filter['user_id'] is not '':
                                    select_from = """(SELECT la.* FROM logistic_activity AS la INNER JOIN delivery_plan AS dp on la.delivery_plan_id = dp.id WHERE la.user_id IN ({3}) AND la.tap_nfc_type = 'IN' AND dp.is_deleted = 0 AND (DATE(la.tap_nfc_date) BETWEEN '{0}' AND '{1}') AND la.nfc_code = '{2}' GROUP BY la.delivery_plan_id, la.nfc_code, la.tap_nfc_type) as sa""".format(
                                        data_filter['start_date'], data_filter['end_date'], cust_child['code'],
                                        data_filter['user_id']
                                    )
                                else:
                                    select_from = """(SELECT la.* FROM logistic_activity AS la INNER JOIN delivery_plan AS dp on la.delivery_plan_id = dp.id WHERE la.tap_nfc_type = 'IN' AND dp.is_deleted = 0 AND (DATE(la.tap_nfc_date) BETWEEN '{0}' AND '{1}') AND la.nfc_code = '{2}' GROUP BY la.delivery_plan_id, la.nfc_code, la.tap_nfc_type) as sa""".format(
                                        data_filter['start_date'], data_filter['end_date'], cust_child['code']
                                    )
                                group = " GROUP BY date"
                                logistic_child_statistic = self.logistic_activity_model.get_count_all_activity_statistic(
                                    self.cursor, select=select, select_count=select_count, select_from=select_from,
                                    group=group
                                )
                                # if logistic_child_statistic:
                                for single_date in date_range(s_date, e_date):
                                    for rec in logistic_child_statistic:
                                        if rec['date'].strftime("%Y-%m-%d") == single_date.strftime("%Y-%m-%d"):
                                            temp_child_statistic[single_date.strftime("%Y-%m-%d")] = int(rec['total'])
                            except Exception as e:
                                pass
                    # TODO: Get data statistic logistic
                    s_date = datetime.strptime(data_filter['start_date'], "%Y-%m-%d")
                    e_date = datetime.strptime(data_filter['end_date'], "%Y-%m-%d")
                    temp_statistic = {}
                    for single_date in date_range(s_date, e_date):
                        temp_statistic[single_date.strftime("%Y-%m-%d")] = 0
                    try:
                        data_statistic = []
                        data_statistic_gantt = []

                        select = "DATE(sa.tap_nfc_date) AS date, "
                        select_count = "COUNT(sa.id) AS total "

                        if data_filter['user_id'] is not '':
                            select_from = """(SELECT la.* FROM logistic_activity AS la INNER JOIN delivery_plan AS dp on la.delivery_plan_id = dp.id WHERE la.user_id IN ({3}) AND la.tap_nfc_type = 'IN' AND dp.is_deleted = 0 AND (DATE(la.tap_nfc_date) BETWEEN '{0}' AND '{1}') AND la.nfc_code = '{2}' GROUP BY la.delivery_plan_id, la.nfc_code, la.tap_nfc_type) as sa""".format(
                                data_filter['start_date'], data_filter['end_date'], emp['code'], data_filter['user_id']
                            )
                        else:
                            select_from = """(SELECT la.* FROM logistic_activity AS la INNER JOIN delivery_plan AS dp on la.delivery_plan_id = dp.id WHERE la.tap_nfc_type = 'IN' AND dp.is_deleted = 0 AND (DATE(la.tap_nfc_date) BETWEEN '{0}' AND '{1}') AND la.nfc_code = '{2}' GROUP BY la.delivery_plan_id, la.nfc_code, la.tap_nfc_type) as sa""".format(
                                data_filter['start_date'], data_filter['end_date'], emp['code']
                            )
                        group = " GROUP BY date"
                        logistic_statistic = self.logistic_activity_model.get_count_all_activity_statistic(
                            self.cursor, select=select, select_count=select_count, select_from=select_from, group=group
                        )
                        if logistic_statistic:
                            for rec in logistic_statistic:
                                child_data_total = 0
                                if temp_child_statistic:
                                    if temp_child_statistic.get(rec['date'].strftime("%Y-%m-%d")):
                                        child_data_total += temp_child_statistic[rec['date'].strftime("%Y-%m-%d")]
                                temp_statistic[rec['date'].strftime("%Y-%m-%d")] = int(rec['total']) + child_data_total
                                data_statistic_gantt.append({
                                    "from": "/Date('{0}')/".format(rec['date'].strftime("%Y-%m-%d")),
                                    "to": "/Date('{0}')/".format(rec['date'].strftime("%Y-%m-%d")),
                                    "label": int(rec['total']) + child_data_total,
                                    "desc": "{0} Delivery".format(int(rec['total']) + child_data_total),
                                })

                        for key, value in temp_statistic.items():
                            data_statistic.append({
                                'date': key,
                                'total': value
                            })
                        # emp['data_statistic'] = data_statistic
                        total = 0
                        for rc in data_statistic:
                            total += rc['total']
                        emp['data_statistic_total'] = total
                    except Exception as e:
                        data_statistic = []
                        data_statistic_gantt = []
                        for key, value in temp_statistic.items():
                            data_statistic.append({
                                'date': key,
                                'total': value
                            })
                        # emp['data_statistic'] = data_statistic
                        emp['data_statistic_total'] = 0

                cust['name'] = emp['name']
                cust['desc'] = emp['code']
                cust['values'] = data_statistic_gantt

                data.append(emp)
                data_gantt.append(cust)

        customer['data'] = {
            'customer': data,
            'customer_gantt': data_gantt
        }
        customer['total'] = count

        # TODO: Check Has Next and Prev
        customer['has_next'] = False
        customer['has_prev'] = False

        return customer

    def update_customer(self, customer_data: 'dict', _id: 'int'):
        """
        Update division
        :param customer_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.customer_model.update_by_id(self.cursor, customer_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_customer_delete_count(self, code: 'str'):
        """
        Get delete count customer
        :param code: str
        :return:
            Message Boolean Success or Failure
        """
        try:
            select = "is_delete_count"
            where = "WHERE `code` = '{}' AND `is_deleted` = 1".format(code)
            order = "ORDER BY is_delete_count DESC"
            count = self.customer_model.get_all_customer(
                self.cursor, select=select, where=where, order=order, start=0, limit=1000)[0]
        except Exception as e:
            count = {
                "is_delete_count": 0
            }

        return count['is_delete_count']

    def rollback_insert(self, _id: 'int'):
        """
        Rollback insert branches
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `customer` WHERE id = {}".format(_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result
