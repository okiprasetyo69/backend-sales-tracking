import re
import json
import pandas as pd
import requests

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql, get_cycle_data, date_range, convert_date_name
from rest.models import DeliveryCycleModel, DeliveryPlanModel, DeliveryPlanSummaryModel, GeneralModel, UserModel, \
    BranchesModel, EmployeeModel, CustomerModel, SalesOrderModel, PackingSlipModel, DeliveryModel, DivisionModel, \
    LogisticActivityModel, PermissionsModel, AssetModel

__author__ = 'Junior'


class DeliveryController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.delivery_cycle_model = DeliveryCycleModel()
        self.delivery_plan_model = DeliveryPlanModel()
        self.delivery_plan_summary_model = DeliveryPlanSummaryModel()
        self.delivery_model = DeliveryModel()
        self.general_model = GeneralModel()
        self.user_model = UserModel()
        self.branch_model = BranchesModel()
        self.division_model = DivisionModel()
        self.employee_model = EmployeeModel()
        self.customer_model = CustomerModel()
        self.asset_model = AssetModel()
        self.so_model = SalesOrderModel()
        self.packing_slip_model = PackingSlipModel()
        self.permissions_model = PermissionsModel()
        self.logistic_activity_model = LogisticActivityModel()

    # TODO: Controller for delivery cycle
    def create(self, delivery_cycle_data: 'dict', user_id: 'int'):
        """
        Function for create new delivery cycle

        :param visit_cycle_data: dict
        :param user_id: int
        :return:
            Visit Cycle Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.delivery_cycle_model.insert_into_db(
                self.cursor, user_id=delivery_cycle_data['user_id'], asset_id=delivery_cycle_data['asset_id'],
                cycle_number=delivery_cycle_data['cycle_number'],
                cycle_monday=json.dumps(delivery_cycle_data['cycle_monday']),
                cycle_tuesday=json.dumps(delivery_cycle_data['cycle_tuesday']),
                cycle_wednesday=json.dumps(delivery_cycle_data['cycle_wednesday']),
                cycle_thursday=json.dumps(delivery_cycle_data['cycle_thursday']),
                cycle_friday=json.dumps(delivery_cycle_data['cycle_friday']),
                cycle_saturday=json.dumps(delivery_cycle_data['cycle_saturday']),
                cycle_sunday=json.dumps(delivery_cycle_data['cycle_sunday']),
                create_date=today, update_date=today,
                is_approval=delivery_cycle_data['is_approval'],
                approval_by=delivery_cycle_data['approval_by'], create_by=user_id
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id

    def import_delivery_cycle(self, file, user_id: 'int'):
        """
        import sales payment
        :param file: file
        :param user_id: int
        :return:
        """
        headers = ['User', 'Cycle No', 'Day', 'Customer', 'Start Branch', 'End Branch']
        batch_data = []
        batch_data_customer = []
        list_day = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_excel(file, sheet_name=0, skiprows=0)
        for idx in df.columns:
            if idx not in headers:
                raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])

        # TODO: Get Parent User
        df_parent_user = df[['User']]
        df_parent_user.set_index("User", inplace=True)
        df_parent_user = df_parent_user.groupby(['User']).last()
        df_parent_user.index.names = ['username']
        df_parent_user_json = df_parent_user.to_json(orient='index', date_format='iso')
        df_parent_user_json = json.loads(df_parent_user_json)

        delete_user_not_found = []
        # TODO: Get Customer
        for idx in df_parent_user_json:
            user = self.user_model.get_user_by_username(self.cursor, idx)
            if len(user) == 0:
                delete_user_not_found.append(idx)
            else:
                user = user[0]
                df_destination = df[['Cycle No', 'Day', 'Customer', 'Start Branch', 'End Branch']].loc[
                    df['User'] == idx]
                df_destination.columns = ['cycle_no', 'day', 'customer_code', 'start_branch', 'end_branch']
                # get all cycle no
                df_cycle = df_destination[['cycle_no']]
                df_cycle.set_index("cycle_no", inplace=True)
                df_cycle = df_cycle.groupby(['cycle_no']).last()
                df_cycle = df_cycle.to_json(orient='index')
                df_cycle = json.loads(df_cycle)
                # get all customer per user
                df_customer = df_destination[['customer_code']]
                df_customer.set_index("customer_code", inplace=True)
                df_customer = df_customer.groupby(['customer_code']).last()
                df_customer = df_customer.to_json(orient='index')
                df_customer = json.loads(df_customer)
                # print("=======Unique Customer========")
                df_parent_user_json[idx]['customer'] = []
                for cus in df_customer:
                    customer = self.customer_model.get_customer_by_code(self.cursor, cus, None)
                    print("====debug cust: {}".format(cus))
                    print(customer)
                    if len(customer) != 0:
                        df_parent_user_json[idx]['customer'].append(cus)
                df_parent_user_json[idx]['cycle'] = []
                for cno in df_cycle:
                    delivery_cycle = self.delivery_cycle_model.get_delivery_cycle_by_user_cycle(
                        self.cursor, user['id'], cno, None
                    )
                    if len(delivery_cycle) == 0:
                        delivery_cycle = False
                    else:
                        delivery_cycle = delivery_cycle[0]
                        if delivery_cycle['cycle_monday'] is not None:
                            delivery_cycle['cycle_monday'] = json.loads(delivery_cycle['cycle_monday'])
                        if delivery_cycle['cycle_tuesday'] is not None:
                            delivery_cycle['cycle_tuesday'] = json.loads(delivery_cycle['cycle_tuesday'])
                        if delivery_cycle['cycle_wednesday'] is not None:
                            delivery_cycle['cycle_wednesday'] = json.loads(delivery_cycle['cycle_wednesday'])
                        if delivery_cycle['cycle_thursday'] is not None:
                            delivery_cycle['cycle_thursday'] = json.loads(delivery_cycle['cycle_thursday'])
                        if delivery_cycle['cycle_friday'] is not None:
                            delivery_cycle['cycle_friday'] = json.loads(delivery_cycle['cycle_friday'])
                        if delivery_cycle['cycle_saturday'] is not None:
                            delivery_cycle['cycle_saturday'] = json.loads(delivery_cycle['cycle_saturday'])
                        if delivery_cycle['cycle_sunday'] is not None:
                            delivery_cycle['cycle_sunday'] = json.loads(delivery_cycle['cycle_sunday'])
                    df_destination_cycle = df_destination[['day', 'customer_code', 'start_branch', 'end_branch']].loc[
                        df_destination['cycle_no'] == int(cno)]
                    destination_per_cycle = []
                    data = dict()
                    data['cycle_monday'] = None
                    data['cycle_tuesday'] = None
                    data['cycle_wednesday'] = None
                    data['cycle_thursday'] = None
                    data['cycle_friday'] = None
                    data['cycle_saturday'] = None
                    data['cycle_sunday'] = None
                    for day_idx in list_day:
                        df_destination_day = df_destination_cycle[['customer_code', 'start_branch', 'end_branch']].loc[
                            df_destination_cycle['day'] == (list_day.index(day_idx) + 1)]
                        df_destination_day = df_destination_day.groupby(['customer_code'], as_index=False).last()
                        if not df_destination_day.empty:
                            start_branch_code = df_destination_day.iat[0, 1]
                            end_branch_code = df_destination_day.iat[0, 2]
                            df_destination_day = df_destination_day[['customer_code']].to_dict('record')
                            destination = []
                            destination_for_cycle = []
                            for cust in df_destination_day:
                                customer = self.customer_model.get_customer_by_code(self.cursor, cust['customer_code'], None)
                                if len(customer) == 0:
                                    pass
                                else:
                                    customer = customer[0]
                                    if customer['lat'] is not None and customer['lng'] is not None:
                                        destination.append({"customer": cust['customer_code'], "order_route": None})
                                        destination_for_cycle.append(
                                            {
                                                "customer_code": cust['customer_code'],
                                                "customer_name": customer['name'],
                                                "address": customer['address'],
                                                "order_route": None,
                                            }
                                        )
                                    else:
                                        pass
                            start_branch = self.branch_model.get_branches_by_code(self.cursor, start_branch_code, None)
                            end_branch = self.branch_model.get_branches_by_code(self.cursor, end_branch_code, None)
                            if len(start_branch) == 0 or len(end_branch) == 0 or len(destination) == 0:
                                if delivery_cycle:
                                    key = 'cycle_{}'.format(day_idx)
                                    data[key] = delivery_cycle[key]
                                else:
                                    key = 'cycle_{}'.format(day_idx)
                                    data[key] = {
                                        'destination': [],
                                        'start_route_branch_id': None,
                                        'end_route_branch_id': None,
                                        'route': None,
                                        'destination_order': None,
                                        'is_use_route': False
                                    }
                                # destination_per_cycle.append(data)
                            else:
                                start_branch = start_branch[0]
                                end_branch = end_branch[0]
                                try:
                                    key = 'cycle_{}'.format(day_idx)
                                    data_route = {
                                        "start_route_id": start_branch['id'],
                                        "end_route_id": end_branch['id'],
                                        "destination": destination,
                                        'is_use_route': False
                                    }
                                    r_url = 'http://{0}:{1}/controller/route/generate'.format(
                                        current_app.config['HOST_USSAGE_WSGI'], current_app.config['PORT_USSAGE_WSGI']
                                    )
                                    r = requests.post(r_url, json=data_route)
                                    response = r.json()
                                    data[key] = {
                                        'destination': destination_for_cycle,
                                        'start_route_branch_id': start_branch['id'],
                                        'end_route_branch_id': end_branch['id'],
                                        'route': response['data'][0],
                                        'destination_order': response['data'][1],
                                        'is_use_route': False
                                    }
                                except Exception as e:
                                    if delivery_cycle:
                                        key = 'cycle_{}'.format(day_idx)
                                        data[key] = delivery_cycle[key]
                                    else:
                                        key = 'cycle_{}'.format(day_idx)
                                        data[key] = {
                                            'destination': [],
                                            'start_route_branch_id': None,
                                            'end_route_branch_id': None,
                                            'route': None,
                                            'destination_order': None,
                                            'is_use_route': False
                                        }
                                # destination_per_cycle.append(data)
                        else:
                            if delivery_cycle:
                                key = 'cycle_{}'.format(day_idx)
                                data[key] = delivery_cycle[key]
                            else:
                                key = 'cycle_{}'.format(day_idx)
                                data[key] = {
                                    'destination': [],
                                    'start_route_branch_id': None,
                                    'end_route_branch_id': None,
                                    'route': None,
                                    'destination_order': None,
                                    'is_use_route': False
                                }
                            # destination_per_cycle.append(data)
                    data_per_cycle = {
                        'cycle_no': int(cno),
                        'destination_per_cycle': data
                    }
                    df_parent_user_json[idx]['cycle'].append(data_per_cycle)
        # Delete data if user id not found
        if delete_user_not_found:
            for idx in delete_user_not_found:
                del df_parent_user_json[idx]

        for key, val in df_parent_user_json.items():
            value = val
            value['user_id'] = key
            user = self.user_model.get_user_by_username(self.cursor, key)
            user = user[0]
            for cycle in value['cycle']:
                data_value = {
                    'user_id': user['id'],
                    'cycle_number': int(cycle['cycle_no']),
                    'asset_id': None,
                    'cycle_monday': json.dumps(cycle['destination_per_cycle']['cycle_monday']),
                    'cycle_tuesday': json.dumps(cycle['destination_per_cycle']['cycle_tuesday']),
                    'cycle_wednesday': json.dumps(cycle['destination_per_cycle']['cycle_wednesday']),
                    'cycle_thursday': json.dumps(cycle['destination_per_cycle']['cycle_thursday']),
                    'cycle_friday': json.dumps(cycle['destination_per_cycle']['cycle_friday']),
                    'cycle_saturday': json.dumps(cycle['destination_per_cycle']['cycle_saturday']),
                    'cycle_sunday': json.dumps(cycle['destination_per_cycle']['cycle_sunday']),
                    'is_approval': 1,
                    'approval_by': user_id,
                    'create_by': user_id,
                    'create_date': today,
                    'update_date': today,
                    'is_deleted': 0,
                    'is_delete_count': 0
                }
                batch_data.append(data_value)
            if user['customer_id'] is not None:
                user['customer_id'] = json.loads(user['customer_id'])
            else:
                user['customer_id'] = []
            old_customer = user['customer_id']
            old_customer.extend(value['customer'])
            new_customer = list(set(old_customer))
            update_data = {
                "id": user['id'],
                "customer_id": new_customer
            }
            try:
                result_update = self.user_model.update_by_id(self.cursor, update_data)
                mysql.connection.commit()
            except Exception as e:
                print("Failed update customer to user error: {}".format(e))
                pass
                # raise BadRequest(e, 200, 1)
            # print(update_data)
        # print(batch_data)

        for rec in batch_data:
            try:
                result = self.delivery_cycle_model.import_insert(
                    self.cursor, rec, 'user_id, cycle_number, is_deleted, is_delete_count'
                )
                mysql.connection.commit()
            except Exception as e:
                print("Failed Import error: {}".format(e))
                # raise BadRequest(e, 200, 1, data=[])
                pass

        return True

    def check_delivery_cycle_by_name(self, name: str, _id: int):
        """
        Check for user_id delivery cycle

        :param name: str
        :param _id: int
        :return:
            Visit Cycle Object
        """
        delivery_cycle = self.delivery_cycle_model.get_delivery_cycle_by_name(self.cursor, name, _id)

        if len(delivery_cycle) == 0:
            return False
        else:
            return True

    def check_delivery_cycle_by_user_cycle(self, user_id: int, cycle_no: int, _id: int):
        """
        Check for user_id visit cycle

        :param user_id: int
        :param cycle_no: int
        :param _id: int
        :return:
            Visit Cycle Object
        """
        delivery_cycle = self.delivery_cycle_model.get_delivery_cycle_by_user_cycle(self.cursor, user_id, cycle_no, _id)

        if len(delivery_cycle) == 0:
            return False
        else:
            return True

    def get_delivery_cycle_by_id(self, _id: int):
        """
        Get delivery cycle Information Data

        :param _id: int
        :return:
            Visit Cycle Object
        """
        delivery_cycle = self.delivery_cycle_model.get_delivery_cycle_by_id(self.cursor, _id)

        if len(delivery_cycle) == 0:
            raise BadRequest("This delivery cycle doesn't exist", 500, 1, data=[])
        else:
            delivery_cycle = delivery_cycle[0]
            if delivery_cycle['edit_data'] is not None:
                delivery_cycle['edit_data'] = json.loads(delivery_cycle['edit_data'])
            if delivery_cycle['cycle_monday'] is not None:
                delivery_cycle['cycle_monday'] = json.loads(delivery_cycle['cycle_monday'])
            if delivery_cycle['cycle_tuesday'] is not None:
                delivery_cycle['cycle_tuesday'] = json.loads(delivery_cycle['cycle_tuesday'])
            if delivery_cycle['cycle_wednesday'] is not None:
                delivery_cycle['cycle_wednesday'] = json.loads(delivery_cycle['cycle_wednesday'])
            if delivery_cycle['cycle_thursday'] is not None:
                delivery_cycle['cycle_thursday'] = json.loads(delivery_cycle['cycle_thursday'])
            if delivery_cycle['cycle_friday'] is not None:
                delivery_cycle['cycle_friday'] = json.loads(delivery_cycle['cycle_friday'])
            if delivery_cycle['cycle_saturday'] is not None:
                delivery_cycle['cycle_saturday'] = json.loads(delivery_cycle['cycle_saturday'])
            if delivery_cycle['cycle_sunday'] is not None:
                delivery_cycle['cycle_sunday'] = json.loads(delivery_cycle['cycle_sunday'])

        return delivery_cycle

    def get_all_delivery_cycle_data(
            self, page: int, limit: int, search: str, column: str, direction: str, branch_privilege: list
    ):
        """
        Get List Of delivery cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :return:
            Visit Cycle Object
        """
        cycle = {}
        data = []
        start = page * limit - limit
        where = """WHERE (dc.is_approval = 1 AND dc.is_deleted = 0) 
        AND (u.branch_id IN ({0})) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        where_original = where
        order = ''
        if column:
            if column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'username':
                order = """ORDER BY u.username {0}""".format(direction)
            elif column == 'user':
                order = """ORDER BY e.name {0}""".format(direction)
            else:
                order = """ORDER BY dc.{0} {1}""".format(column, direction)
        select = "dc.*"
        select_count = "dc.id"
        join = """as dc LEFT JOIN `users` as u ON dc.user_id = u.id 
        LEFT JOIN `branches` as b ON u.branch_id = b.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR dc.cycle_number LIKE '%{0}%' 
            OR b.name LIKE '%{0}%' OR e.name LIKE '%{0}%')""".format(search)
        delivery_cycle_data = self.delivery_cycle_model.get_all_delivery_cycle(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.delivery_cycle_model.get_count_all_delivery_cycle(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.delivery_cycle_model.get_count_all_delivery_cycle(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if delivery_cycle_data:
            for vc in delivery_cycle_data:
                list_customer = []
                if vc['edit_data'] is not None:
                    vc['edit_data'] = json.loads(vc['edit_data'])
                if vc['cycle_monday'] is not None:
                    vc['cycle_monday'] = json.loads(vc['cycle_monday'])
                    if vc['cycle_monday']['destination'] is not None:
                        for rec in vc['cycle_monday']['destination']:
                            list_customer.append(rec['customer_code'])
                if vc['cycle_tuesday'] is not None:
                    vc['cycle_tuesday'] = json.loads(vc['cycle_tuesday'])
                    if vc['cycle_tuesday']['destination'] is not None:
                        for rec in vc['cycle_tuesday']['destination']:
                            list_customer.append(rec['customer_code'])
                if vc['cycle_wednesday'] is not None:
                    vc['cycle_wednesday'] = json.loads(vc['cycle_wednesday'])
                    if vc['cycle_wednesday']['destination'] is not None:
                        for rec in vc['cycle_wednesday']['destination']:
                            list_customer.append(rec['customer_code'])
                if vc['cycle_thursday'] is not None:
                    vc['cycle_thursday'] = json.loads(vc['cycle_thursday'])
                    if vc['cycle_thursday']['destination'] is not None:
                        for rec in vc['cycle_thursday']['destination']:
                            list_customer.append(rec['customer_code'])
                if vc['cycle_friday'] is not None:
                    vc['cycle_friday'] = json.loads(vc['cycle_friday'])
                    if vc['cycle_friday']['destination'] is not None:
                        for rec in vc['cycle_friday']['destination']:
                            list_customer.append(rec['customer_code'])
                if vc['cycle_saturday'] is not None:
                    vc['cycle_saturday'] = json.loads(vc['cycle_saturday'])
                    if vc['cycle_saturday']['destination'] is not None:
                        for rec in vc['cycle_saturday']['destination']:
                            list_customer.append(rec['customer_code'])
                if vc['cycle_sunday'] is not None:
                    vc['cycle_sunday'] = json.loads(vc['cycle_sunday'])
                    if vc['cycle_sunday']['destination'] is not None:
                        for rec in vc['cycle_sunday']['destination']:
                            list_customer.append(rec['customer_code'])
                # vc['customer'] = list_customer
                vc['total_customer'] = len(set(list_customer))
                if vc['user_id'] is not None:
                    try:
                        vc['user'] = self.user_model.get_user_by_id(
                            self.cursor, vc['user_id'], select="username, employee_id, branch_id")[0]
                    except:
                        vc['user'] = {}
                    if vc['user']['employee_id'] is not None:
                        try:
                            vc['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor,
                                vc['user']['employee_id'],
                                select="""name""")[0]['name']
                        except:
                            vc['user']['name'] = None
                    if vc['user']['branch_id'] is not None:
                        try:
                            vc['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor,
                                vc['user']['branch_id'],
                                select="""name""")[0]['name']
                        except:
                            vc['user']['branch_name'] = None
                else:
                    vc['user'] = {}
                data.append(vc)
        cycle['data'] = data
        cycle['total'] = count
        cycle['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if cycle['total'] > page * limit:
            cycle['has_next'] = True
        else:
            cycle['has_next'] = False
        if limit <= page * count - count:
            cycle['has_prev'] = True
        else:
            cycle['has_prev'] = False
        return cycle

    def update_delivery_cycle(self, delivery_cycle_data: 'dict', _id: 'int'):
        """
        Update Visit cycle
        :param delivery_cycle_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.delivery_cycle_model.update_by_id(self.cursor, delivery_cycle_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_delivery_cycle_delete_count(self, user_id: 'int', cycle_no: 'int'):
        """
        Update visit cycle
        :param user_id: 'int'
        :param cycle_no: 'int'
        :return:
            Message Boolean Success or Failure
        """
        try:
            select = "is_delete_count"
            where = "WHERE `user_id` = {0} AND `cycle_number` = {1} AND `is_deleted` = 1".format(user_id, cycle_no)
            order = "ORDER BY is_delete_count DESC"
            count = self.delivery_cycle_model.get_all_delivery_cycle(
                self.cursor, select=select, where=where, order=order, start=0, limit=1000)[0]
        except Exception as e:
            count = {
                "is_delete_count": 0
            }

        return count['is_delete_count']

    def rollback_cycle_insert(self, _id: 'int'):
        """
        Rollback insert branches
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `delivery_cycle` WHERE id = {}".format(_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    # TODO: Controller for visit plan
    def generate(self, plan_data: 'dict', user_id: 'int'):
        """
        Function for create new visit cycle

        :param plan_data: dict
        :param user_id: int
        :return:
            Visit Cycle Object
        """
        result = True
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        start_date = datetime.strptime(plan_data['start_date'], "%Y-%m-%d")
        end_date = datetime.strptime(plan_data['end_date'], "%Y-%m-%d")
        general = self.general_model.get_general_by_id(self.cursor, 1)
        general = general[0]
        if general['visit_cycle_start'] is not None:
            general['visit_cycle_start'] = str(general['visit_cycle_start'])
        start_date_cycle = datetime.strptime(general['visit_cycle_start'], "%Y-%m-%d %H:%M:%S")
        try:
            total_cycle = self.delivery_cycle_model.get_all_delivery_cycle(
                self.cursor, where="""WHERE user_id = {} AND is_deleted = 0""".format(user_id), order="ORDER BY `cycle_number` DESC"
            )[0]
        except:
            raise BadRequest("User doesn't have delivery cycle", 422, 1, data=[])
        total_cycle = total_cycle['cycle_number']
        print(total_cycle)
        if total_cycle:
            for single_date in date_range(start_date, end_date):
                date_now = single_date
                cycle_number, days = get_cycle_data(start_date_cycle, date_now, total_cycle)
                cycle_data = self.delivery_cycle_model.get_delivery_cycle_by_user_cycle(self.cursor, user_id=user_id,
                                                                                  cycle_number=cycle_number)

                if cycle_data:
                    name_days = 'cycle_{}'.format(convert_date_name(days))
                    cycle_data = cycle_data[0]
                    days_data = json.loads(cycle_data[name_days])
                    # if days_data['destination'] and days_data['start_route_branch_id'] \
                    #         and days_data['end_route_branch_id'] and days_data['route']:
                    if days_data['start_route_branch_id'] and days_data['end_route_branch_id']:
                        data_route = None
                        if days_data['route'] is not None:
                            data_route = json.dumps(days_data['route'])
                        try:
                            result = self.delivery_plan_model.insert_into_db(
                                self.cursor, user_id=cycle_data['user_id'],
                                date=single_date.strftime("%Y-%m-%d %H:%M:%S"),
                                asset_id=cycle_data['asset_id'],
                                # route=json.dumps(days_data['route']),
                                route=data_route, destination=days_data['destination'],
                                destination_order=days_data['destination_order'],
                                start_route_branch_id=days_data['start_route_branch_id'],
                                end_route_branch_id=days_data['end_route_branch_id'],
                                packing_slip_id=None,
                                create_date=today, update_date=today,
                                is_approval=plan_data['is_approval'],
                                is_use_route=days_data['is_use_route'],
                                approval_by=plan_data['approval_by'],
                                create_by=user_id
                            )
                            mysql.connection.commit()
                        except Exception as e:
                            # print(e)
                            result = True
                            pass
                    else:
                        result = True
                        pass
        else:
            raise BadRequest("User doesn't have delivery cycle", 422, 1, data=[])

        return result

    def create_delivery_plan(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new delivery plan

        :param create_data: dict
        :param user_id: int
        :return:
            Visit Cycle Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        route = None
        # destination_order = None
        destination_order = create_data['destination_order']

        is_use_route = create_data['is_use_route']
        if is_use_route == 1:
            route = json.dumps(create_data['route'])
            # destination_order = create_data['destination_order']

        try:
            result = self.delivery_plan_model.insert_into_db(
                self.cursor, user_id=create_data['user_id'], asset_id=create_data['asset_id'],
                route=route, date=create_data['date'],
                destination=create_data['destination'], destination_order=destination_order,
                start_route_branch_id=create_data['start_route_branch_id'],
                end_route_branch_id=create_data['end_route_branch_id'], packing_slip_id=create_data['packing_slip_id'],
                is_use_route=create_data["is_use_route"], create_date=today, update_date=today,
                is_approval=create_data['is_approval'],approval_by=create_data['approval_by'], create_by=user_id
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id

    def get_all_delivery_plan_data(
            self, page: int, limit: int, search: str, column: str, direction: str, user_id: int,
            branch_privilege: list, data_filter: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: user_id: int
        :return:
            Visit Cycle Object
        """
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        if user_id:
            where = "WHERE (dp.is_approval = 1 AND dp.is_deleted = 0) AND dp.user_id = {0}".format(user_id)
        else:
            where = """WHERE (dp.is_approval = 1 AND dp.is_deleted = 0) 
            AND (u.branch_id IN ({0})) """.format(
                ", ".join(str(x) for x in branch_privilege)
            )
        where_original = where
        if column:
            if column == 'start_branch':
                order = """ORDER BY b1.name {0}""".format(direction)
            elif column == 'end_branch':
                order = """ORDER BY b2.name {0}""".format(direction)
            elif column == 'username':
                order = """ORDER BY u.username {0}""".format(direction)
            elif column == 'user':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY br.name {0}""".format(direction)
            else:
                order = """ORDER BY dp.{0} {1}""".format(column, direction)
        select = "dp.*"
        select_count = "dp.id"
        join = """as dp LEFT JOIN `users` as u ON dp.user_id = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id
        LEFT JOIN `branches` as br ON u.branch_id = br.id
        LEFT JOIN `branches` as b1 ON dp.start_route_branch_id = b1.id
        LEFT JOIN `branches` as b2 ON dp.end_route_branch_id = b2.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR br.name LIKE '%{0}%' OR b1.name LIKE '%{0}%' 
            OR b2.name LIKE '%{0}%' OR e.name LIKE '%{0}%')""".format(search)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                where += """AND (dp.date >= '{0} 00:00:00' AND dp.date <= '{1} 23:59:59') """.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            if data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
            if data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))

        delivery_plan_data = self.delivery_plan_model.get_all_delivery_plan(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.delivery_plan_model.get_count_all_delivery_plan(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.delivery_plan_model.get_count_all_delivery_plan(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if delivery_plan_data:
            for vp in delivery_plan_data:
                list_customer = []
                vp['start_custom_location'] = None
                vp['stop_custom_location'] = None
                if vp['edit_data'] is not None:
                    vp['edit_data'] = json.loads(vp['edit_data'])
                if vp['date'] is not None:
                    vp['date'] = str(vp['date'])
                if vp['create_date'] is not None:
                    vp['create_date'] = str(vp['create_date'])
                if vp['update_date'] is not None:
                    vp['update_date'] = str(vp['update_date'])
                # Get Activity data
                data_activity_dict = dict()
                data_activity = []
                list_nfc_code = []
                try:
                    where = """WHERE (sa.id IN (SELECT MIN(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'START' 
                                GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `logistic_activity` 
                                WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id) 
                                FROM `logistic_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, delivery_plan_id, nfc_code) 
                                OR sa.id IN (SELECT MAX(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'OUT' 
                                GROUP BY user_id, delivery_plan_id, nfc_code)) AND (delivery_plan_id = {0}) """.format(
                        vp['id'])
                    order = ""
                    select = "sa.*"
                    join = """AS sa"""
                    activity_data = self.logistic_activity_model.get_all_activity(
                        self.cursor, select=select, join=join, where=where, order=order, start=0, limit=1000
                    )
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])
                            ad['branch_name'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        ad['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ad['nfc_code'], select="""name"""
                                        )[0]['name']
                                    except:
                                        ad['branch_name'] = None
                                if ad['tap_nfc_type'] == 'START':
                                    if ad['route_breadcrumb'] is not None:
                                        vp['start_custom_location'] = json.loads(ad['route_breadcrumb'])
                                elif ad['tap_nfc_type'] == 'STOP':
                                    if ad['route_breadcrumb'] is not None:
                                        vp['stop_custom_location'] = json.loads(ad['route_breadcrumb'])
                            ad['customer_code'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}
                            if ad['nfc_code'] is not None:
                                data_activity_dict[ad['nfc_code']] = dict()
                                list_nfc_code.append(ad['nfc_code'])
                            data_activity.append(ad)
                    if data_activity:
                        for rec in data_activity:
                            if rec['tap_nfc_type'] == 'START':
                                data_activity_dict[rec['nfc_code']]['start_time'] = rec['tap_nfc_date']
                            if rec['tap_nfc_type'] == 'STOP':
                                data_activity_dict[rec['nfc_code']]['stop_time'] = rec['tap_nfc_date']
                            if rec['tap_nfc_type'] == 'IN':
                                data_activity_dict[rec['nfc_code']]['in_time'] = rec['tap_nfc_date']
                            if rec['tap_nfc_type'] == 'OUT':
                                data_activity_dict[rec['nfc_code']]['out_time'] = rec['tap_nfc_date']
                        # Calculation duration
                        unique_code = set(list_nfc_code)
                        for code in unique_code:
                            if data_activity_dict[code].get('in_time'):
                                in_time = data_activity_dict[code]['in_time']
                            else:
                                in_time = 0
                            if data_activity_dict[code].get('out_time'):
                                out_time = data_activity_dict[code]['out_time']
                            else:
                                out_time = 0
                            if in_time and out_time:
                                out_time_fmt = datetime.strptime(out_time, "%Y-%m-%d %H:%M:%S")
                                in_time_fmt = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
                                data_activity_dict[code]['duration'] = int(
                                    (out_time_fmt - in_time_fmt).seconds / 60)
                            else:
                                data_activity_dict[code]['duration'] = 0
                    print(data_activity_dict)
                    vp['data_activity'] = data_activity_dict
                except Exception as e:
                    print(e)
                    vp['data_activity'] = dict()
                if vp['destination_order'] is not None:
                    vp['destination_order'] = json.loads(vp['destination_order'])
                if vp['destination'] is not None:
                    vp['destination'] = json.loads(vp['destination'])
                    idx = 0
                    for rec in vp['destination']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination'][idx]['customer_name'] = customer['name']
                            vp['destination'][idx]['customer_email'] = customer['email']
                            vp['destination'][idx]['phone'] = customer['phone']
                            vp['destination'][idx]['address'] = customer['address']
                            vp['destination'][idx]['lng'] = customer['lng']
                            vp['destination'][idx]['lat'] = customer['lat']
                            vp['destination'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination'][idx]['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                vp['destination'][idx]['business_activity'] = None
                        except:
                            vp['destination'][idx]['customer_name'] = None
                            vp['destination'][idx]['customer_email'] = None
                            vp['destination'][idx]['phone'] = None
                            vp['destination'][idx]['address'] = None
                            vp['destination'][idx]['lng'] = None
                            vp['destination'][idx]['lat'] = None
                            vp['destination'][idx]['nfcid'] = None
                            vp['destination'][idx]['contacts'] = None
                            vp['destination'][idx]['business_activity'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1
                # vc['customer'] = list_customer
                vp['total_customer'] = len(set(list_customer))
                if vp['user_id'] is not None:
                    try:
                        vp['user'] = self.user_model.get_user_by_id(
                            self.cursor, vp['user_id'], select="username, employee_id, branch_id")[0]
                    except:
                        vp['user'] = {}
                    if vp['user']['employee_id'] is not None:
                        try:
                            vp['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor, vp['user']['employee_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['name'] = None
                    if vp['user']['branch_id'] is not None:
                        try:
                            vp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, vp['user']['branch_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['branch_name'] = None
                else:
                    vp['user'] = {}
                if vp['start_route_branch_id'] is not None:
                    try:
                        vp['start_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['start_route_branch'] = {}
                else:
                    vp['start_route_branch'] = {}
                if vp['end_route_branch_id'] is not None:
                    try:
                        vp['end_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['end_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['end_route_branch'] = {}
                else:
                    vp['end_route_branch'] = {}
                del vp['route']
                # vp['total_invoice'] = 2
                # vp['invoice_ids'] = ["SO-PSCN000005850", "SO-PSCN000005776"]
                data.append(vp)
        cycle['data'] = data
        cycle['total'] = count
        cycle['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if cycle['total_filter'] > page * limit:
            cycle['has_next'] = True
        else:
            cycle['has_next'] = False
        if limit <= page * count_filter - count_filter:
            cycle['has_prev'] = True
        else:
            cycle['has_prev'] = False
        return cycle

    def check_delivery_plan(self, user_id: int, date: str, _id: int):
        """
        Check for user_id visit plan

        :param user_id: int
        :param date: str
        :param _id: int
        :return:
            Visit plan Object
        """
        delivery_plan = self.delivery_plan_model.get_delivery_plan_by_user_date(self.cursor, user_id, date, _id)

        if len(delivery_plan) == 0:
            return False
        else:
            return True

    def get_delivery_plan_by_id(self, _id: int):
        """
        Get visit plan Information Data

        :param _id: int
        :return:
            Visit Cycle Object
        """
        delivery_plan = self.delivery_plan_model.get_delivery_plan_by_id(self.cursor, _id)

        if len(delivery_plan) == 0:
            raise BadRequest("This delivery plan doesn't exist", 500, 1, data=[])
        else:
            delivery_plan = delivery_plan[0]
            delivery_plan['start_custom_location'] = None
            delivery_plan['stop_custom_location'] = None
            list_customer = []
            if delivery_plan['edit_data'] is not None:
                delivery_plan['edit_data'] = json.loads(delivery_plan['edit_data'])
            if delivery_plan['date'] is not None:
                delivery_plan['date'] = str(delivery_plan['date'])
            if delivery_plan['create_date'] is not None:
                delivery_plan['create_date'] = str(delivery_plan['create_date'])
            if delivery_plan['update_date'] is not None:
                delivery_plan['update_date'] = str(delivery_plan['update_date'])
            # Get Activity data
            data_activity_dict = dict()
            data_activity = []
            list_nfc_code = []
            try:
                where = """WHERE (sa.id IN (SELECT MIN(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'START' 
                GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `logistic_activity` 
                WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id) 
                FROM `logistic_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, delivery_plan_id, nfc_code) 
                OR sa.id IN (SELECT MAX(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'OUT' 
                GROUP BY user_id, delivery_plan_id, nfc_code)) AND (delivery_plan_id = {0}) """.format(_id)
                order = ""
                select = "sa.*"
                join = """AS sa"""
                activity_data = self.logistic_activity_model.get_all_activity(
                    self.cursor, select=select, join=join, where=where, order=order, start=0, limit=1000
                )
                if activity_data:
                    for ad in activity_data:
                        if ad['tap_nfc_date'] is not None:
                            ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                        if ad['create_date'] is not None:
                            ad['create_date'] = str(ad['create_date'])
                        if ad['update_date'] is not None:
                            ad['update_date'] = str(ad['update_date'])
                        ad['branch_name'] = None
                        if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                            if ad['nfc_code'] is not None:
                                try:
                                    ad['branch_name'] = self.branch_model.get_branches_by_id(
                                        self.cursor, ad['nfc_code'], select="""name"""
                                    )[0]['name']
                                except:
                                    ad['branch_name'] = None
                            if ad['tap_nfc_type'] == 'START':
                                if ad['route_breadcrumb'] is not None:
                                    delivery_plan['start_custom_location'] = json.loads(ad['route_breadcrumb'])
                            elif ad['tap_nfc_type'] == 'STOP':
                                if ad['route_breadcrumb'] is not None:
                                    delivery_plan['stop_custom_location'] = json.loads(ad['route_breadcrumb'])
                        ad['customer_code'] = None
                        if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                            if ad['nfc_code'] is not None:
                                ad['customer_code'] = ad['nfc_code']
                        if ad['user_id'] is not None:
                            try:
                                ad['user'] = self.user_model.get_user_by_id(
                                    self.cursor, ad['user_id'],
                                    select="username, employee_id, branch_id, division_id"
                                )[0]
                                if ad['user']['employee_id'] is not None:
                                    try:
                                        ad['user']['name'] = self.employee_model.get_employee_by_id(
                                            self.cursor,
                                            ad['user']['employee_id'],
                                            select="""name""")[0]['name']
                                    except:
                                        ad['user']['name'] = None
                                if ad['user']['branch_id'] is not None:
                                    try:
                                        ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor,
                                            ad['user']['branch_id'],
                                            select="""name""")[0]['name']
                                    except:
                                        ad['user']['branch_name'] = None
                                if ad['user']['division_id'] is not None:
                                    try:
                                        ad['user']['division_name'] = self.division_model.get_division_by_id(
                                            self.cursor, ad['user']['division_id'], select="division_name")[0][
                                            'division_name']
                                    except:
                                        ad['user']['division_name'] = None
                            except:
                                ad['user'] = {}
                        else:
                            ad['user'] = {}
                        if ad['nfc_code'] is not None:
                            data_activity_dict[ad['nfc_code']] = dict()
                            list_nfc_code.append(ad['nfc_code'])
                        data_activity.append(ad)
                if data_activity:
                    for rec in data_activity:
                        if rec['tap_nfc_type'] == 'START':
                            data_activity_dict[rec['nfc_code']]['start_time'] = rec['tap_nfc_date']
                        if rec['tap_nfc_type'] == 'STOP':
                            data_activity_dict[rec['nfc_code']]['stop_time'] = rec['tap_nfc_date']
                        if rec['tap_nfc_type'] == 'IN':
                            data_activity_dict[rec['nfc_code']]['in_time'] = rec['tap_nfc_date']
                        if rec['tap_nfc_type'] == 'OUT':
                            data_activity_dict[rec['nfc_code']]['out_time'] = rec['tap_nfc_date']
                    # Calculation duration
                    unique_code = set(list_nfc_code)
                    for code in unique_code:
                        if data_activity_dict[code].get('in_time'):
                            in_time = data_activity_dict[code]['in_time']
                        else:
                            in_time = 0
                        if data_activity_dict[code].get('out_time'):
                            out_time = data_activity_dict[code]['out_time']
                        else:
                            out_time = 0
                        if in_time and out_time:
                            out_time_fmt = datetime.strptime(out_time, "%Y-%m-%d %H:%M:%S")
                            in_time_fmt = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
                            data_activity_dict[code]['duration'] = int(
                                (out_time_fmt - in_time_fmt).seconds / 60)
                        else:
                            data_activity_dict[code]['duration'] = 0
                # print(data_activity_dict)
                delivery_plan['data_activity'] = data_activity_dict
            except Exception as e:
                print(e)
                delivery_plan['data_activity'] = dict()
            if delivery_plan["packing_slip_id"] is not None:
                delivery_plan['packing_slip_id'] = json.loads(delivery_plan["packing_slip_id"])
                # print(delivery_plan['packing_slip_id'])
                idx = 0
                for rec in delivery_plan['packing_slip_id']:
                    try:
                        packing = self.packing_slip_model.get_packing_slip_by_id(
                            self.cursor, rec['id_packing_slip'],
                            select="code, sales_order_code, customer_code, product"
                        )[0]
                        delivery_plan['packing_slip_id'][idx]['customer_code'] = packing['customer_code']
                        delivery_plan['packing_slip_id'][idx]['sales_order_id'] = packing['sales_order_code']
                        if packing['product'] is not None:
                            delivery_plan['packing_slip_id'][idx]['product'] = json.loads(packing['product'])
                        else:
                            delivery_plan['packing_slip_id'][idx]['product'] = None
                        if packing['sales_order_code'] is not None:
                            try:
                                so_data = self.so_model.get_sales_order_by_id(
                                    self.cursor, packing['sales_order_code'],
                                    select="user_code"
                                )
                                if so_data['user_code'] is not None:
                                    try:
                                        delivery_plan['packing_slip_id'][idx]['user'] = self.user_model.get_user_by_username(
                                            self.cursor, so_data['user_code'], select="username, employee_id, branch_id")[0]
                                    except:
                                        delivery_plan['packing_slip_id'][idx]['user'] = {}
                                    if delivery_plan['packing_slip_id'][idx]['user']['employee_id'] is not None:
                                        try:
                                            delivery_plan['packing_slip_id'][idx]['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor, delivery_plan['packing_slip_id'][idx]['user']['employee_id'], select="""name""")[
                                                0]['name']
                                        except:
                                            delivery_plan['packing_slip_id'][idx]['user']['name'] = None
                                    if delivery_plan['packing_slip_id'][idx]['user']['branch_id'] is not None:
                                        try:
                                            delivery_plan['packing_slip_id'][idx]['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor, delivery_plan['packing_slip_id'][idx]['user']['branch_id'], select="""name""")[0][
                                                'name']
                                        except:
                                            delivery_plan['packing_slip_id'][idx]['user']['branch_name'] = None
                                else:
                                    delivery_plan['packing_slip_id'][idx]['user'] = {}
                            except:
                                delivery_plan['packing_slip_id'][idx]['user'] = {}
                        else:
                            delivery_plan['packing_slip_id'][idx]['user'] = {}
                    except:
                        delivery_plan['packing_slip_id'][idx]['product'] = None
                        delivery_plan['packing_slip_id'][idx]['customer_code'] = None
                        delivery_plan['packing_slip_id'][idx]['sales_order_id'] = None
                    try:
                        delivery = self.delivery_model.get_delivery_by_slip_code(
                            self.cursor, rec['id_packing_slip']
                        )
                        if delivery:
                            delivery = delivery[0]
                            if delivery['is_accepted']:
                                delivery_plan['packing_slip_id'][idx]['status'] = "Diterima"
                            elif delivery['is_rejected']:
                                delivery_plan['packing_slip_id'][idx]['status'] = "Ditolak"
                            else:
                                delivery_plan['packing_slip_id'][idx]['status'] = "Menunggu Pengiriman"
                        else:
                            delivery_plan['packing_slip_id'][idx]['status'] = "Menunggu Pengiriman"
                    except:
                        delivery_plan['packing_slip_id'][idx]['status'] = "Menunggu Pengiriman"
                    idx += 1
                delivery_plan['total_packing_slip'] = len(delivery_plan['packing_slip_id'])
            else:
                delivery_plan['packing_slip_id'] = []
                delivery_plan['total_packing_slip'] = 0
            if delivery_plan['destination_order'] is not None:
                delivery_plan['destination_order'] = json.loads(delivery_plan['destination_order'])
            if delivery_plan['destination'] is not None:
                delivery_plan['destination'] = json.loads(delivery_plan['destination'])
                idx = 0
                for rec in delivery_plan['destination']:
                    try:
                        customer = self.customer_model.get_customer_by_id(
                            self.cursor, rec['customer_code'],
                            select="name, email, phone, address, lng, lat, contacts, nfcid")[0]
                        if customer['contacts'] is not None:
                            contacts = json.loads(customer['contacts'])
                            delivery_plan['destination'][idx]['pic_name'] = contacts[0]['name']
                            delivery_plan['destination'][idx]['pic_phone'] = contacts[0]['phone']
                            delivery_plan['destination'][idx]['pic_mobile'] = contacts[0]['mobile']
                            delivery_plan['destination'][idx]['pic_job_position'] = contacts[0]['job_position']
                        else:
                            delivery_plan['destination'][idx]['pic_name'] = None
                            delivery_plan['destination'][idx]['pic_phone'] = None
                            delivery_plan['destination'][idx]['pic_mobile'] = None
                            delivery_plan['destination'][idx]['pic_job_position'] = None
                        delivery_plan['destination'][idx]['customer_name'] = customer['name']
                        delivery_plan['destination'][idx]['customer_email'] = customer['email']
                        delivery_plan['destination'][idx]['phone'] = customer['phone']
                        delivery_plan['destination'][idx]['address'] = customer['address']
                        delivery_plan['destination'][idx]['lng'] = customer['lng']
                        delivery_plan['destination'][idx]['lat'] = customer['lat']
                        delivery_plan['destination'][idx]['nfcid'] = customer['nfcid']
                        delivery_plan['destination'][idx]['total_packing_slip'] = 0
                        delivery_plan['destination'][idx]['packing_slip'] = []
                    except:
                        delivery_plan['destination'][idx]['pic_name'] = None
                        delivery_plan['destination'][idx]['pic_phone'] = None
                        delivery_plan['destination'][idx]['pic_mobile'] = None
                        delivery_plan['destination'][idx]['pic_job_position'] = None
                        delivery_plan['destination'][idx]['customer_name'] = None
                        delivery_plan['destination'][idx]['customer_email'] = None
                        delivery_plan['destination'][idx]['phone'] = None
                        delivery_plan['destination'][idx]['address'] = None
                        delivery_plan['destination'][idx]['lng'] = None
                        delivery_plan['destination'][idx]['lat'] = None
                        delivery_plan['destination'][idx]['nfcid'] = None
                        delivery_plan['destination'][idx]['total_packing_slip'] = 0
                        delivery_plan['destination'][idx]['packing_slip'] = []

                    if delivery_plan["packing_slip_id"] is not None:
                        for rec_vp in delivery_plan['packing_slip_id']:
                            if rec_vp['customer_code'] == rec['customer_code'] and rec_vp['is_confirm'] == 1:
                                delivery_plan['destination'][idx]['total_packing_slip'] += 1
                                invoice_data = {
                                    "id_packing_slip": rec_vp['id_packing_slip'],
                                    "sales_order_id": rec_vp['sales_order_id'],
                                    "product": rec_vp['product'],
                                    "customer_code": rec_vp['customer_code'],
                                    "user": rec_vp['user'],
                                    "status": rec_vp['status']
                                }
                                delivery_plan['destination'][idx]['packing_slip'].append(invoice_data)
                    list_customer.append(rec['customer_code'])
                    idx += 1
            # vc['customer'] = list_customer
            delivery_plan['total_customer'] = len(set(list_customer))
            if delivery_plan['user_id'] is not None:
                try:
                    delivery_plan['user'] = self.user_model.get_user_by_id(
                        self.cursor, delivery_plan['user_id'], select="username, employee_id, branch_id")[0]
                except:
                    delivery_plan['user'] = {}
                if delivery_plan['user']['employee_id'] is not None:
                    try:
                        delivery_plan['user']['name'] = self.employee_model.get_employee_by_id(
                            self.cursor, delivery_plan['user']['employee_id'], select="""name""")[0]['name']
                    except:
                        delivery_plan['user']['name'] = None
                if delivery_plan['user']['branch_id'] is not None:
                    try:
                        delivery_plan['user']['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, delivery_plan['user']['branch_id'], select="""name""")[0]['name']
                    except:
                        delivery_plan['user']['branch_name'] = None
            else:
                delivery_plan['user'] = {}
            if delivery_plan['start_route_branch_id'] is not None:
                try:
                    delivery_plan['start_route_branch'] = self.branch_model.get_branches_by_id(
                        self.cursor, delivery_plan['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                except:
                    delivery_plan['start_route_branch'] = {}
            else:
                delivery_plan['start_route_branch'] = {}
            if delivery_plan['end_route_branch_id'] is not None:
                try:
                    delivery_plan['end_route_branch'] = self.branch_model.get_branches_by_id(
                        self.cursor, delivery_plan['end_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                except:
                    delivery_plan['end_route_branch'] = {}
            else:
                delivery_plan['end_route_branch'] = {}

            if delivery_plan['route'] is not None:
                delivery_plan['route'] = json.loads(delivery_plan['route'])

        return delivery_plan

    def get_delivery_plan_by_user_date(self, _id: int, plan_id: int):
        """
        Get visit plan Information Data

        :param _id: int
        :param plan_id: int
        :return:
            Visit Cycle Object
        """
        # today = datetime.today()
        # today = today.strftime("%Y-%m-%d")
        # today = "2018-07-17"

        delivery_plan = self.delivery_plan_model.get_delivery_plan_by_user_date(self.cursor, _id, plan_id, None)

        if len(delivery_plan) == 0:
            raise BadRequest("This visit plan doesn't exist", 500, 1, data=[])
        else:
            delivery_plan = delivery_plan[0]
            list_customer = []
            if delivery_plan['edit_data'] is not None:
                delivery_plan['edit_data'] = json.loads(delivery_plan['edit_data'])
            if delivery_plan['date'] is not None:
                delivery_plan['date'] = str(delivery_plan['date'])
            if delivery_plan['create_date'] is not None:
                delivery_plan['create_date'] = str(delivery_plan['create_date'])
            if delivery_plan['update_date'] is not None:
                delivery_plan['update_date'] = str(delivery_plan['update_date'])
            if delivery_plan["packing_slip_id"] is not None:
                delivery_plan['packing_slip_id'] = json.loads(delivery_plan["packing_slip_id"])
                print(delivery_plan['packing_slip_id'])
                idx = 0
                for rec in delivery_plan['packing_slip_id']:
                    try:
                        packing = self.packing_slip_model.get_packing_slip_by_id(
                            self.cursor, rec['id_packing_slip'],
                            select="code, sales_order_code, customer_code, product"
                        )[0]
                        delivery_plan['packing_slip_id'][idx]['customer_code'] = packing['customer_code']
                        delivery_plan['packing_slip_id'][idx]['sales_order_id'] = packing['sales_order_code']
                        if packing['product'] is not None:
                            delivery_plan['packing_slip_id'][idx]['product'] = json.loads(packing['product'])
                        else:
                            delivery_plan['packing_slip_id'][idx]['product'] = None
                        if packing['sales_order_code'] is not None:
                            try:
                                so_data = self.so_model.get_sales_order_by_id(
                                    self.cursor, packing['sales_order_code'],
                                    select="user_code"
                                )
                                if so_data['user_code'] is not None:
                                    try:
                                        delivery_plan['packing_slip_id'][idx]['user'] = self.user_model.get_user_by_username(
                                            self.cursor, so_data['user_code'], select="username, employee_id, branch_id")[0]
                                    except:
                                        delivery_plan['packing_slip_id'][idx]['user'] = {}
                                    if delivery_plan['packing_slip_id'][idx]['user']['employee_id'] is not None:
                                        try:
                                            delivery_plan['packing_slip_id'][idx]['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor, delivery_plan['packing_slip_id'][idx]['user']['employee_id'], select="""name""")[
                                                0]['name']
                                        except:
                                            delivery_plan['packing_slip_id'][idx]['user']['name'] = None
                                    if delivery_plan['packing_slip_id'][idx]['user']['branch_id'] is not None:
                                        try:
                                            delivery_plan['packing_slip_id'][idx]['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor, delivery_plan['packing_slip_id'][idx]['user']['branch_id'], select="""name""")[0][
                                                'name']
                                        except:
                                            delivery_plan['packing_slip_id'][idx]['user']['branch_name'] = None
                                else:
                                    delivery_plan['packing_slip_id'][idx]['user'] = {}
                            except:
                                delivery_plan['packing_slip_id'][idx]['user'] = {}
                        else:
                            delivery_plan['packing_slip_id'][idx]['user'] = {}

                    except:
                        delivery_plan['packing_slip_id'][idx]['product'] = None
                        delivery_plan['packing_slip_id'][idx]['customer_code'] = None
                        delivery_plan['packing_slip_id'][idx]['sales_order_id'] = None
                        delivery_plan['packing_slip_id'][idx]['user'] = {}
                    try:
                        delivery = self.delivery_model.get_delivery_by_slip_code(
                            self.cursor, rec['id_packing_slip']
                        )
                        if delivery:
                            delivery = delivery[0]
                            if delivery['is_accepted']:
                                delivery_plan['packing_slip_id'][idx]['product'] = json.loads(delivery['product'])
                                delivery_plan['packing_slip_id'][idx]['status'] = "Diterima"
                            elif delivery['is_rejected']:
                                delivery_plan['packing_slip_id'][idx]['status'] = "Ditolak"
                            else:
                                delivery_plan['packing_slip_id'][idx]['status'] = "Menunggu Pengiriman"
                        else:
                            delivery_plan['packing_slip_id'][idx]['status'] = "Menunggu Pengiriman"
                    except:
                        delivery_plan['packing_slip_id'][idx]['status'] = "Menunggu Pengiriman"
                    idx += 1
                delivery_plan['total_packing_slip'] = len(delivery_plan['packing_slip_id'])
            else:
                delivery_plan['packing_slip_id'] = []
                delivery_plan['total_packing_slip'] = 0
            if delivery_plan['destination_order'] is not None:
                delivery_plan['destination_order'] = json.loads(delivery_plan['destination_order'])
            if delivery_plan['destination'] is not None:
                delivery_plan['destination'] = json.loads(delivery_plan['destination'])
                idx = 0
                for rec in delivery_plan['destination']:
                    try:
                        customer = self.customer_model.get_customer_by_id(
                            self.cursor, rec['customer_code'],
                            select="name, email, phone, address, lng, lat, contacts, nfcid")[0]
                        if customer['contacts'] is not None:
                            contacts = json.loads(customer['contacts'])
                            delivery_plan['destination'][idx]['pic_name'] = contacts[0]['name']
                            delivery_plan['destination'][idx]['pic_phone'] = contacts[0]['phone']
                            delivery_plan['destination'][idx]['pic_mobile'] = contacts[0]['mobile']
                            delivery_plan['destination'][idx]['pic_job_position'] = contacts[0]['job_position']
                        else:
                            delivery_plan['destination'][idx]['pic_name'] = None
                            delivery_plan['destination'][idx]['pic_phone'] = None
                            delivery_plan['destination'][idx]['pic_mobile'] = None
                            delivery_plan['destination'][idx]['pic_job_position'] = None
                        delivery_plan['destination'][idx]['customer_name'] = customer['name']
                        delivery_plan['destination'][idx]['customer_email'] = customer['email']
                        delivery_plan['destination'][idx]['phone'] = customer['phone']
                        delivery_plan['destination'][idx]['address'] = customer['address']
                        delivery_plan['destination'][idx]['lng'] = customer['lng']
                        delivery_plan['destination'][idx]['lat'] = customer['lat']
                        delivery_plan['destination'][idx]['nfcid'] = customer['nfcid']
                        delivery_plan['destination'][idx]['total_packing_slip'] = 0
                        delivery_plan['destination'][idx]['packing_slip'] = []
                    except:
                        delivery_plan['destination'][idx]['pic_name'] = None
                        delivery_plan['destination'][idx]['pic_phone'] = None
                        delivery_plan['destination'][idx]['pic_mobile'] = None
                        delivery_plan['destination'][idx]['pic_job_position'] = None
                        delivery_plan['destination'][idx]['customer_name'] = None
                        delivery_plan['destination'][idx]['customer_email'] = None
                        delivery_plan['destination'][idx]['phone'] = None
                        delivery_plan['destination'][idx]['address'] = None
                        delivery_plan['destination'][idx]['lng'] = None
                        delivery_plan['destination'][idx]['lat'] = None
                        delivery_plan['destination'][idx]['nfcid'] = None
                        delivery_plan['destination'][idx]['total_packing_slip'] = 0
                        delivery_plan['destination'][idx]['packing_slip'] = []

                    if delivery_plan["packing_slip_id"] is not None:
                        for rec_vp in delivery_plan['packing_slip_id']:
                            if rec_vp['customer_code'] == rec['customer_code'] and rec_vp['is_confirm'] == 1:
                                delivery_plan['destination'][idx]['total_packing_slip'] += 1
                                invoice_data = {
                                    "id_packing_slip": rec_vp['id_packing_slip'],
                                    "sales_order_id": rec_vp['sales_order_id'],
                                    "product": rec_vp['product'],
                                    "customer_code": rec_vp['customer_code'],
                                    "user": rec_vp['user'],
                                    "status": rec_vp['status']
                                }
                                delivery_plan['destination'][idx]['packing_slip'].append(invoice_data)

                    try:
                        select = "tap_nfc_date"
                        where = "WHERE delivery_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'IN' ".format(
                            delivery_plan['id'], rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.logistic_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            delivery_plan['destination'][idx]['arrival_time'] = str(activity['tap_nfc_date'])
                        else:
                            delivery_plan['destination'][idx]['arrival_time'] = None
                    except:
                        delivery_plan['destination'][idx]['arrival_time'] = None
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE delivery_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'OUT' ".format(
                            delivery_plan['id'], rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.logistic_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            delivery_plan['destination'][idx]['departure_time'] = str(activity['tap_nfc_date'])
                        else:
                            delivery_plan['destination'][idx]['departure_time'] = None
                    except:
                        delivery_plan['destination'][idx]['departure_time'] = None
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE nfc_code = '{0}' AND tap_nfc_type = 'OUT' ".format(
                            rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.logistic_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            delivery_plan['destination'][idx]['last_delivery_date'] = str(activity['tap_nfc_date'])
                        else:
                            delivery_plan['destination'][idx]['last_delivery_date'] = None
                    except:
                        delivery_plan['destination'][idx]['last_delivery_date'] = None
                    list_customer.append(rec['customer_code'])
                    idx += 1
            # vc['customer'] = list_customer
            delivery_plan['total_customer'] = len(set(list_customer))
            if delivery_plan['asset_id'] is not None:
                try:
                    delivery_plan['asset'] = self.asset_model.get_asset_by_id(
                        self.cursor, delivery_plan['asset_id'], select="id, code, device_code, name")[0]
                except:
                    delivery_plan['asset'] = {}
            else:
                delivery_plan['asset'] = {}
            if delivery_plan['user_id'] is not None:
                try:
                    delivery_plan['user'] = self.user_model.get_user_by_id(
                        self.cursor, delivery_plan['user_id'], select="employee_id, branch_id")[0]
                except:
                    delivery_plan['user'] = {}
                if delivery_plan['user']['employee_id'] is not None:
                    try:
                        delivery_plan['user']['name'] = self.employee_model.get_employee_by_id(
                            self.cursor, delivery_plan['user']['employee_id'], select="""name""")[0]['name']
                    except:
                        delivery_plan['user']['name'] = None
                if delivery_plan['user']['branch_id'] is not None:
                    try:
                        delivery_plan['user']['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, delivery_plan['user']['branch_id'], select="""name""")[0]['name']
                    except:
                        delivery_plan['user']['branch_name'] = None
            else:
                delivery_plan['user'] = {}
            if delivery_plan['start_route_branch_id'] is not None:
                try:
                    delivery_plan['start_route_branch'] = self.branch_model.get_branches_by_id(
                        self.cursor, delivery_plan['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                except:
                    delivery_plan['start_route_branch'] = {}
            else:
                delivery_plan['start_route_branch'] = {}
            if delivery_plan['end_route_branch_id'] is not None:
                try:
                    delivery_plan['end_route_branch'] = self.branch_model.get_branches_by_id(
                        self.cursor, delivery_plan['end_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                except:
                    delivery_plan['end_route_branch'] = {}
            else:
                delivery_plan['end_route_branch'] = {}
            if delivery_plan['route'] is not None:
                delivery_plan['route'] = json.loads(delivery_plan['route'])
            try:
                where_change_route = """WHERE `delivery_plan_id` = {0} AND `type` = 'routes' 
                AND `is_approved` = 1""".format(delivery_plan['id'])
                change_route = self.permissions_model.get_all_permission_alert(
                    self.cursor, where=where_change_route
                )
                data_change_route = []
                if change_route:
                    for rec in change_route:
                        print(rec['description'])
                        if rec['description'] is not None:
                            change_r = json.loads(rec['description'])
                            change_r['customer_code'] = rec['customer_code']
                            data_change_route.append(change_r)
                delivery_plan['change_route'] = data_change_route
            except:
                delivery_plan['change_route'] = []
        return delivery_plan

    def get_delivery_plan_list_by_user_date(self, _id: int):
        """
        Get visit plan Information Data

        :param _id: int
        :return:
            Visit Cycle Object
        """
        plan = {}
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        # today = "2018-07-17"

        result = self.delivery_plan_model.get_delivery_plan_list_by_user_date(self.cursor, _id, today, None)

        if len(result) == 0:
            raise BadRequest("This delivery plan doesn't exist", 500, 1, data=[])
        else:
            data = []
            for delivery_plan in result:
                list_customer = []
                if delivery_plan['edit_data'] is not None:
                    delivery_plan['edit_data'] = json.loads(delivery_plan['edit_data'])
                if delivery_plan['date'] is not None:
                    delivery_plan['date'] = str(delivery_plan['date'])
                if delivery_plan['create_date'] is not None:
                    delivery_plan['create_date'] = str(delivery_plan['create_date'])
                if delivery_plan['update_date'] is not None:
                    delivery_plan['update_date'] = str(delivery_plan['update_date'])
                if delivery_plan["packing_slip_id"] is not None:
                    delivery_plan['packing_slip_id'] = json.loads(delivery_plan["packing_slip_id"])
                    print(delivery_plan['packing_slip_id'])
                    idx = 0
                    for rec in delivery_plan['packing_slip_id']:
                        try:
                            packing = self.packing_slip_model.get_packing_slip_by_id(
                                self.cursor, rec['id_packing_slip'],
                                select="code, sales_order_code, customer_code, product"
                            )[0]
                            delivery_plan['packing_slip_id'][idx]['customer_code'] = packing['customer_code']
                            delivery_plan['packing_slip_id'][idx]['sales_order_id'] = packing['sales_order_code']
                            if packing['product'] is not None:
                                delivery_plan['packing_slip_id'][idx]['product'] = json.loads(packing['product'])
                            else:
                                delivery_plan['packing_slip_id'][idx]['product'] = None
                            if packing['sales_order_code'] is not None:
                                try:
                                    so_data = self.so_model.get_sales_order_by_id(
                                        self.cursor, packing['sales_order_code'],
                                        select="user_code"
                                    )
                                    if so_data['user_code'] is not None:
                                        try:
                                            delivery_plan['packing_slip_id'][idx]['user'] = self.user_model.get_user_by_username(
                                                self.cursor, so_data['user_code'], select="username, employee_id, branch_id")[0]
                                        except:
                                            delivery_plan['packing_slip_id'][idx]['user'] = {}
                                        if delivery_plan['packing_slip_id'][idx]['user']['employee_id'] is not None:
                                            try:
                                                delivery_plan['packing_slip_id'][idx]['user']['name'] = self.employee_model.get_employee_by_id(
                                                    self.cursor, delivery_plan['packing_slip_id'][idx]['user']['employee_id'], select="""name""")[
                                                    0]['name']
                                            except:
                                                delivery_plan['packing_slip_id'][idx]['user']['name'] = None
                                        if delivery_plan['packing_slip_id'][idx]['user']['branch_id'] is not None:
                                            try:
                                                delivery_plan['packing_slip_id'][idx]['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                    self.cursor, delivery_plan['packing_slip_id'][idx]['user']['branch_id'], select="""name""")[0][
                                                    'name']
                                            except:
                                                delivery_plan['packing_slip_id'][idx]['user']['branch_name'] = None
                                    else:
                                        delivery_plan['packing_slip_id'][idx]['user'] = {}
                                except:
                                    delivery_plan['packing_slip_id'][idx]['user'] = {}
                            else:
                                delivery_plan['packing_slip_id'][idx]['user'] = {}

                        except:
                            delivery_plan['packing_slip_id'][idx]['product'] = None
                            delivery_plan['packing_slip_id'][idx]['customer_code'] = None
                            delivery_plan['packing_slip_id'][idx]['sales_order_id'] = None
                            delivery_plan['packing_slip_id'][idx]['user'] = {}
                        try:
                            delivery = self.delivery_model.get_delivery_by_slip_code(
                                self.cursor, rec['id_packing_slip']
                            )
                            if delivery:
                                delivery = delivery[0]
                                if delivery['is_accepted']:
                                    delivery_plan['packing_slip_id'][idx]['product'] = json.loads(delivery['product'])
                                    delivery_plan['packing_slip_id'][idx]['status'] = "Diterima"
                                elif delivery['is_rejected']:
                                    delivery_plan['packing_slip_id'][idx]['status'] = "Ditolak"
                                else:
                                    delivery_plan['packing_slip_id'][idx]['status'] = "Menunggu Pengiriman"
                            else:
                                delivery_plan['packing_slip_id'][idx]['status'] = "Menunggu Pengiriman"
                        except:
                            delivery_plan['packing_slip_id'][idx]['status'] = "Menunggu Pengiriman"
                        idx += 1
                    delivery_plan['total_packing_slip'] = len(delivery_plan['packing_slip_id'])
                else:
                    delivery_plan['packing_slip_id'] = []
                    delivery_plan['total_packing_slip'] = 0
                if delivery_plan['destination_order'] is not None:
                    delivery_plan['destination_order'] = json.loads(delivery_plan['destination_order'])
                if delivery_plan['destination'] is not None:
                    delivery_plan['destination'] = json.loads(delivery_plan['destination'])
                    idx = 0
                    for rec in delivery_plan['destination']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, contacts, nfcid")[0]
                            if customer['contacts'] is not None:
                                contacts = json.loads(customer['contacts'])
                                delivery_plan['destination'][idx]['pic_name'] = contacts[0]['name']
                                delivery_plan['destination'][idx]['pic_phone'] = contacts[0]['phone']
                                delivery_plan['destination'][idx]['pic_mobile'] = contacts[0]['mobile']
                                delivery_plan['destination'][idx]['pic_job_position'] = contacts[0]['job_position']
                            else:
                                delivery_plan['destination'][idx]['pic_name'] = None
                                delivery_plan['destination'][idx]['pic_phone'] = None
                                delivery_plan['destination'][idx]['pic_mobile'] = None
                                delivery_plan['destination'][idx]['pic_job_position'] = None
                            delivery_plan['destination'][idx]['customer_name'] = customer['name']
                            delivery_plan['destination'][idx]['customer_email'] = customer['email']
                            delivery_plan['destination'][idx]['phone'] = customer['phone']
                            delivery_plan['destination'][idx]['address'] = customer['address']
                            delivery_plan['destination'][idx]['lng'] = customer['lng']
                            delivery_plan['destination'][idx]['lat'] = customer['lat']
                            delivery_plan['destination'][idx]['nfcid'] = customer['nfcid']
                            delivery_plan['destination'][idx]['total_packing_slip'] = 0
                            delivery_plan['destination'][idx]['packing_slip'] = []
                        except:
                            delivery_plan['destination'][idx]['pic_name'] = None
                            delivery_plan['destination'][idx]['pic_phone'] = None
                            delivery_plan['destination'][idx]['pic_mobile'] = None
                            delivery_plan['destination'][idx]['pic_job_position'] = None
                            delivery_plan['destination'][idx]['customer_name'] = None
                            delivery_plan['destination'][idx]['customer_email'] = None
                            delivery_plan['destination'][idx]['phone'] = None
                            delivery_plan['destination'][idx]['address'] = None
                            delivery_plan['destination'][idx]['lng'] = None
                            delivery_plan['destination'][idx]['lat'] = None
                            delivery_plan['destination'][idx]['nfcid'] = None
                            delivery_plan['destination'][idx]['total_packing_slip'] = 0
                            delivery_plan['destination'][idx]['packing_slip'] = []

                        if delivery_plan["packing_slip_id"] is not None:
                            for rec_vp in delivery_plan['packing_slip_id']:
                                if rec_vp['customer_code'] == rec['customer_code'] and rec_vp['is_confirm'] == 1:
                                    delivery_plan['destination'][idx]['total_packing_slip'] += 1
                                    invoice_data = {
                                        "id_packing_slip": rec_vp['id_packing_slip'],
                                        "sales_order_id": rec_vp['sales_order_id'],
                                        "product": rec_vp['product'],
                                        "customer_code": rec_vp['customer_code'],
                                        "user": rec_vp['user'],
                                        "status": rec_vp['status']
                                    }
                                    delivery_plan['destination'][idx]['packing_slip'].append(invoice_data)

                        try:
                            select = "tap_nfc_date"
                            where = "WHERE delivery_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'IN' ".format(
                                delivery_plan['id'], rec['customer_code']
                            )
                            order = "ORDER BY tap_nfc_date ASC"
                            activity = self.logistic_activity_model.get_all_activity(
                                self.cursor, select=select, where=where, order=order
                            )
                            if activity:
                                activity = activity[0]
                                delivery_plan['destination'][idx]['arrival_time'] = str(activity['tap_nfc_date'])
                            else:
                                delivery_plan['destination'][idx]['arrival_time'] = None
                        except:
                            delivery_plan['destination'][idx]['arrival_time'] = None
                        try:
                            select = "tap_nfc_date"
                            where = "WHERE delivery_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'OUT' ".format(
                                delivery_plan['id'], rec['customer_code']
                            )
                            order = "ORDER BY tap_nfc_date DESC"
                            activity = self.logistic_activity_model.get_all_activity(
                                self.cursor, select=select, where=where, order=order
                            )
                            if activity:
                                activity = activity[0]
                                delivery_plan['destination'][idx]['departure_time'] = str(activity['tap_nfc_date'])
                            else:
                                delivery_plan['destination'][idx]['departure_time'] = None
                        except:
                            delivery_plan['destination'][idx]['departure_time'] = None
                        try:
                            select = "tap_nfc_date"
                            where = "WHERE nfc_code = '{0}' AND tap_nfc_type = 'OUT' ".format(
                                rec['customer_code']
                            )
                            order = "ORDER BY tap_nfc_date DESC"
                            activity = self.logistic_activity_model.get_all_activity(
                                self.cursor, select=select, where=where, order=order
                            )
                            if activity:
                                activity = activity[0]
                                delivery_plan['destination'][idx]['last_delivery_date'] = str(activity['tap_nfc_date'])
                            else:
                                delivery_plan['destination'][idx]['last_delivery_date'] = None
                        except:
                            delivery_plan['destination'][idx]['last_delivery_date'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1
                # vc['customer'] = list_customer
                delivery_plan['total_customer'] = len(set(list_customer))
                if delivery_plan['asset_id'] is not None:
                    try:
                        delivery_plan['asset'] = self.asset_model.get_asset_by_id(
                            self.cursor, delivery_plan['asset_id'], select="id, code, device_code, name")[0]
                    except:
                        delivery_plan['asset'] = {}
                else:
                    delivery_plan['asset'] = {}
                if delivery_plan['user_id'] is not None:
                    try:
                        delivery_plan['user'] = self.user_model.get_user_by_id(
                            self.cursor, delivery_plan['user_id'], select="employee_id, branch_id")[0]
                    except:
                        delivery_plan['user'] = {}
                    if delivery_plan['user']['employee_id'] is not None:
                        try:
                            delivery_plan['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor, delivery_plan['user']['employee_id'], select="""name""")[0]['name']
                        except:
                            delivery_plan['user']['name'] = None
                    if delivery_plan['user']['branch_id'] is not None:
                        try:
                            delivery_plan['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, delivery_plan['user']['branch_id'], select="""name""")[0]['name']
                        except:
                            delivery_plan['user']['branch_name'] = None
                else:
                    delivery_plan['user'] = {}
                if delivery_plan['start_route_branch_id'] is not None:
                    try:
                        delivery_plan['start_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, delivery_plan['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        delivery_plan['start_route_branch'] = {}
                else:
                    delivery_plan['start_route_branch'] = {}
                if delivery_plan['end_route_branch_id'] is not None:
                    try:
                        delivery_plan['end_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, delivery_plan['end_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        delivery_plan['end_route_branch'] = {}
                else:
                    delivery_plan['end_route_branch'] = {}
                if delivery_plan['route'] is not None:
                    delivery_plan['route'] = json.loads(delivery_plan['route'])
                try:
                    where_change_route = """WHERE `delivery_plan_id` = {0} AND `type` = 'routes' 
                    AND `is_approved` = 1""".format(delivery_plan['id'])
                    change_route = self.permissions_model.get_all_permission_alert(
                        self.cursor, where=where_change_route
                    )
                    data_change_route = []
                    if change_route:
                        for rec in change_route:
                            print(rec['description'])
                            if rec['description'] is not None:
                                change_r = json.loads(rec['description'])
                                change_r['customer_code'] = rec['customer_code']
                                data_change_route.append(change_r)
                    delivery_plan['change_route'] = data_change_route
                except:
                    delivery_plan['change_route'] = []
                data.append(delivery_plan)

        plan['data'] = data

        return plan

    def get_delivery_plan_packingslip(self, _id: int):
        """
        Get visit plan Information Data

        :param _id: int
        :return:
            Visit Cycle Object
        """
        # today = datetime.today()
        # today = today.strftime("%Y-%m-%d")
        # today = "2018-06-08"
        response = {}
        delivery_plan = self.delivery_plan_model.get_delivery_plan_by_id(self.cursor, _id, select="packing_slip_id")

        if len(delivery_plan) == 0:
            raise BadRequest("This visit plan doesn't exist", 500, 1, data=[])
        else:
            delivery_plan = delivery_plan[0]
            data = []
            if delivery_plan["packing_slip_id"] is not None:
                delivery_plan['packing_slip_id'] = json.loads(delivery_plan["packing_slip_id"])
                print(delivery_plan['packing_slip_id'])
                for rec in delivery_plan['packing_slip_id']:
                    try:
                        packing = self.packing_slip_model.get_packing_slip_by_id(
                            self.cursor, rec['id_packing_slip'],
                            select="*"
                        )[0]
                        data.append(packing)
                    except Exception as e:
                        print(e)
                        pass
        response['data'] = data
        response['count'] = len(data)
        response['count_filter'] = len(data)
        response['has_next'] = False
        response['has_prev'] = False
        return delivery_plan

    def update_delivery_plan(self, update_data: 'dict', _id: 'int'):
        """
        Update Visit cycle
        :param update_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        
        # if update_data['is_use_route'] == 0:
        #     update_data['route'] = None
        #     update_data['destination_order'] = None

        try:
            result = self.delivery_plan_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_delivery_plan_delete_count(self, user_id: 'int', date: 'int'):
        """
        Update visit plan
        :param user_id: 'int'
        :param date: 'int'
        :return:
            Message Boolean Success or Failure
        """
        try:
            select = "is_delete_count"
            where = "WHERE `user_id` = {0} AND `date` = '{1}' AND `is_deleted` = 1".format(user_id, date)
            order = "ORDER BY is_delete_count DESC"
            count = self.delivery_plan_model.get_all_delivery_plan(
                self.cursor, select=select, where=where, order=order, start=0, limit=1000)[0]
        except Exception as e:
            count = {
                "is_delete_count": 0
            }

        return count['is_delete_count']

    def rollback_plan_insert(self, _id: 'int'):
        """
        Rollback insert branches
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `delivery_plan` WHERE id = {}".format(_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def create_summary_plan(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new visit cycle

        :param create_data: dict
        :param user_id: int
        :return:
            Visit Cycle Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.delivery_plan_summary_model.insert_into_db(
                self.cursor, plan_id=create_data["plan_id"], customer_code=create_data["customer_code"],
                notes=create_data["notes"], visit_images=create_data["visit_images"],
                have_competitor=create_data["have_competitor"], competitor_images=create_data["competitor_images"],
                create_date=today, update_date=today, create_by=user_id
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id

    def update_summary_plan(self, update_data: 'dict'):
        """
        Update Visit cycle
        :param update_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.delivery_plan_summary_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_all_delivery_plan_summary(self, plan_id: int):
        """
        Get visit plan Information Data

        :param plan_id: int
        :param customer_code: str
        :return:
            Visit Plan Summary Object
        """
        data = []
        result = {}
        summary = self.delivery_plan_summary_model.get_delivery_plan_summary_by_plan_id(
            self.cursor, plan_id
        )
        if summary:
            for rec in summary:
                if rec['visit_images'] is not None:
                    rec['visit_images'] = json.loads(rec['visit_images'])
                if rec['competitor_images'] is not None:
                    rec['competitor_images'] = json.loads(rec['competitor_images'])
                if rec['create_date'] is not None:
                    rec['create_date'] = str(rec['create_date'])
                if rec['update_date'] is not None:
                    rec['update_date'] = str(rec['update_date'])
                data.append(rec)

        result['data'] = data
        result['total'] = len(data)
        result['total_filter'] = len(data)
        result['has_next'] = False
        result['has_prev'] = False
        return result

    def get_delivery_plan_summary(self, plan_id: int, customer_code: str):
        """
        Get visit plan Information Data

        :param plan_id: int
        :param customer_code: str
        :return:
            Visit Plan Summary Object
        """
        summary = self.delivery_plan_summary_model.get_delivery_plan_summary_by_plan_id_customer_code(
            self.cursor, plan_id, customer_code
        )
        if len(summary) == 0:
            raise BadRequest("This summary doesn't exist", 500, 1, data=[])
        else:
            summary = summary[0]
            if summary['visit_images'] is not None:
                summary['visit_images'] = json.loads(summary['visit_images'])
            if summary['competitor_images'] is not None:
                summary['competitor_images'] = json.loads(summary['competitor_images'])
            if summary['create_date'] is not None:
                summary['create_date'] = str(summary['create_date'])
            if summary['update_date'] is not None:
                summary['update_date'] = str(summary['update_date'])

        return summary

    def check_delivery_plan_summary(self, plan_id: int, customer_code: str):
        """
        Get visit plan Information Data

        :param plan_id: int
        :param customer_code: str
        :return:
            Visit Plan Summary Object
        """
        summary = self.delivery_plan_summary_model.get_delivery_plan_summary_by_plan_id_customer_code(
            self.cursor, plan_id, customer_code
        )
        return summary

    # TODO: Controller for delivery
    def get_all_delivery_data(self, page: int, limit: int, search: str, column: str, direction: str, customer_code: str):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: customer_code: str
        :return:
            Visit Cycle Object
        """
        cycle = {}
        data = []
        start = page * limit - limit
        order_flag = False
        order = ''
        where = "WHERE ps.customer_code = '{}' ".format(customer_code)
        where_original = where
        if column:
            if column == 'user':
                order = """ORDER BY e.name {0}""".format(direction)
            else:
                order = """ORDER BY dd.{0} {1}""".format(column, direction)
        select = "dd.*"
        select_count = "dd.id"
        join = """as dd LEFT JOIN `users` as u ON dd.user_id = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `packing_slip` as ps ON dd.packing_slip_code = ps.code"""
        if search:
            where += """AND (dd.packing_slip_code LIKE '%{0}%' OR u.username LIKE '%{0}%' 
            OR e.name LIKE '%{0}%')""".format(search)
        delivery_data = self.delivery_model.get_all_delivery(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.delivery_model.get_count_all_delivery(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.delivery_model.get_count_all_delivery(
            self.cursor, select=select_count, join=join, where=where_original
        )

        if delivery_data:
            for dd in delivery_data:
                if dd['delivery_date'] is not None:
                    dd['delivery_date'] = str(dd['delivery_date'])
                if dd['product'] is not None:
                    dd['product'] = json.loads(dd['product'])
                if dd['user_id'] is not None:
                    try:
                        dd['user'] = self.user_model.get_user_by_id(
                            self.cursor, dd['user_id'], select="username, employee_id, branch_id"
                        )[0]
                    except:
                        dd['user'] = {}
                    if dd['user']['employee_id'] is not None:
                        try:
                            dd['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor,
                                dd['user']['employee_id'],
                                select="""name""")[0]['name']
                        except:
                            dd['user']['name'] = None
                    if dd['user']['branch_id'] is not None:
                        try:
                            dd['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor,
                                dd['user']['branch_id'],
                                select="""name""")[0]['name']
                        except:
                            dd['user']['branch_name'] = None
                else:
                    dd['user'] = {}
                data.append(dd)
        cycle['data'] = data
        cycle['total'] = count
        cycle['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if cycle['total_filter'] > page * limit:
            cycle['has_next'] = True
        else:
            cycle['has_next'] = False
        if limit <= page * count_filter - count_filter:
            cycle['has_prev'] = True
        else:
            cycle['has_prev'] = False
        return cycle

    # TODO: Controller for delivery by delivery id and customer
    def get_all_delivery_by_plan_customer_data(
            self, page: int, limit: int, search: str, column: str, direction: str, plan_id: int, customer_code: str
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: customer_code: str
        :return:
            Visit Cycle Object
        """
        cycle = {}
        data = []
        start = page * limit - limit
        order_flag = False
        order = ''
        if customer_code:
            where = "WHERE dd.customer_code = '{0}' AND dd.delivery_plan_id = {1} ".format(customer_code, plan_id)
        else:
            where = "WHERE dd.delivery_plan_id = {1} ".format(customer_code, plan_id)
        where_original = where
        if column:
            if column == 'user':
                order = """ORDER BY e.name {0}""".format(direction)
            else:
                order = """ORDER BY dd.{0} {1}""".format(column, direction)
        select = "dd.*"
        select_count = "dd.id"
        join = """as dd LEFT JOIN `users` as u ON dd.user_id = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `packing_slip` as ps ON dd.packing_slip_code = ps.code"""
        if search:
            where += """AND (dd.packing_slip_code LIKE '%{0}%' OR u.username LIKE '%{0}%' 
            OR e.name LIKE '%{0}%')""".format(search)
        delivery_data = self.delivery_model.get_all_delivery(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.delivery_model.get_count_all_delivery(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.delivery_model.get_count_all_delivery(
            self.cursor, select=select_count, join=join, where=where_original
        )

        if delivery_data:
            for dd in delivery_data:
                if dd['delivery_date'] is not None:
                    dd['delivery_date'] = str(dd['delivery_date'])
                if dd['product'] is not None:
                    dd['product'] = json.loads(dd['product'])
                if dd['user_id'] is not None:
                    try:
                        dd['user'] = self.user_model.get_user_by_id(
                            self.cursor, dd['user_id'], select="username, employee_id, branch_id"
                        )[0]
                    except:
                        dd['user'] = {}
                    if dd['user']['employee_id'] is not None:
                        try:
                            dd['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor,
                                dd['user']['employee_id'],
                                select="""name""")[0]['name']
                        except:
                            dd['user']['name'] = None
                    if dd['user']['branch_id'] is not None:
                        try:
                            dd['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor,
                                dd['user']['branch_id'],
                                select="""name""")[0]['name']
                        except:
                            dd['user']['branch_name'] = None
                else:
                    dd['user'] = {}
                data.append(dd)
        cycle['data'] = data
        cycle['total'] = count
        cycle['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if cycle['total_filter'] > page * limit:
            cycle['has_next'] = True
        else:
            cycle['has_next'] = False
        if limit <= page * count_filter - count_filter:
            cycle['has_prev'] = True
        else:
            cycle['has_prev'] = False
        return cycle

    def get_delivery_by_delivery_id(self, _id: int):
        """
        Get visit plan Information Data

        :param _id: int
        :return:
            Visit Cycle Object
        """
        delivery = self.delivery_model.get_delivery_by_id(self.cursor, _id)

        if len(delivery) == 0:
            raise BadRequest("This delivery doesn't exist", 500, 1, data=[])
        else:
            delivery = delivery[0]
            if delivery['product'] is not None:
                delivery['product'] = json.loads(delivery['product'])
            if delivery['reason_reject'] is not None:
                delivery['reason_reject'] = json.loads(delivery['reason_reject'])
            if delivery['delivery_date'] is not None:
                delivery['delivery_date'] = str(delivery['delivery_date'])
            if delivery['user_id'] is not None:
                try:
                    delivery['user'] = self.user_model.get_user_by_id(
                        self.cursor, delivery['user_id'], select="username, employee_id, branch_id"
                    )[0]
                except:
                    delivery['user'] = {}
                if delivery['user']['employee_id'] is not None:
                    try:
                        delivery['user']['name'] = self.employee_model.get_employee_by_id(
                            self.cursor,
                            delivery['user']['employee_id'],
                            select="""name""")[0]['name']
                    except:
                        delivery['user']['name'] = None
                if delivery['user']['branch_id'] is not None:
                    try:
                        delivery['user']['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor,
                            delivery['user']['branch_id'],
                            select="""name""")[0]['name']
                    except:
                        delivery['user']['branch_name'] = None
            else:
                delivery['user'] = {}
        return  delivery