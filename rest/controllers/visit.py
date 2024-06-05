import re
import json
import pandas as pd
import requests

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql, get_cycle_data, date_range, convert_date_name
from rest.models import VisitCycleModel, VisitPlanModel, VisitPlanSummaryModel, GeneralModel, UserModel, BranchesModel, EmployeeModel, \
    CustomerModel, SalesOrderModel, SalesPaymentModel, PermissionsModel, DivisionModel, SalesActivityModel, \
    RequestOrderModel, SalesPaymentMobileModel

__author__ = 'Junior'


class VisitController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.visit_cycle_model = VisitCycleModel()
        self.visit_plan_model = VisitPlanModel()
        self.visit_plan_summary_model = VisitPlanSummaryModel()
        self.general_model = GeneralModel()
        self.user_model = UserModel()
        self.branch_model = BranchesModel()
        self.division_model = DivisionModel()
        self.employee_model = EmployeeModel()
        self.customer_model = CustomerModel()
        self.so_model = SalesOrderModel()
        self.sp_model = SalesPaymentModel()
        self.spm_model = SalesPaymentMobileModel()
        self.ro_model = RequestOrderModel()
        self.permissions_model = PermissionsModel()
        self.sales_activity_model = SalesActivityModel()

    # TODO: Controller for visit cycle
    def create(self, visit_cycle_data: 'dict', user_id: 'int'):
        """
        Function for create new visit cycle

        :param visit_cycle_data: dict
        :param user_id: int
        :return:
            Visit Cycle Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.visit_cycle_model.insert_into_db(self.cursor, user_id=visit_cycle_data['user_id'],
                                                           asset_id=visit_cycle_data['asset_id'],
                                                           cycle_number=visit_cycle_data['cycle_number'],
                                                           cycle_monday=json.dumps(visit_cycle_data['cycle_monday']),
                                                           cycle_tuesday=json.dumps(visit_cycle_data['cycle_tuesday']),
                                                           cycle_wednesday=json.dumps(visit_cycle_data['cycle_wednesday']),
                                                           cycle_thursday=json.dumps(visit_cycle_data['cycle_thursday']),
                                                           cycle_friday=json.dumps(visit_cycle_data['cycle_friday']),
                                                           cycle_saturday=json.dumps(visit_cycle_data['cycle_saturday']),
                                                           cycle_sunday=json.dumps(visit_cycle_data['cycle_sunday']),
                                                           create_date=today, update_date=today,
                                                           is_approval=visit_cycle_data['is_approval'],
                                                           approval_by=visit_cycle_data['approval_by'],
                                                           create_by=user_id)
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id

    def import_visit_cycle(self, file, user_id: 'int'):
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
                    if len(customer) != 0:
                        df_parent_user_json[idx]['customer'].append(cus)
                df_parent_user_json[idx]['cycle'] = []
                for cno in df_cycle:
                    visit_cycle = self.visit_cycle_model.get_visit_cycle_by_user_cycle(
                        self.cursor, user['id'], cno, None
                    )
                    if len(visit_cycle) == 0:
                        visit_cycle = False
                    else:
                        visit_cycle = visit_cycle[0]
                        if visit_cycle['cycle_monday'] is not None:
                            visit_cycle['cycle_monday'] = json.loads(visit_cycle['cycle_monday'])
                        if visit_cycle['cycle_tuesday'] is not None:
                            visit_cycle['cycle_tuesday'] = json.loads(visit_cycle['cycle_tuesday'])
                        if visit_cycle['cycle_wednesday'] is not None:
                            visit_cycle['cycle_wednesday'] = json.loads(visit_cycle['cycle_wednesday'])
                        if visit_cycle['cycle_thursday'] is not None:
                            visit_cycle['cycle_thursday'] = json.loads(visit_cycle['cycle_thursday'])
                        if visit_cycle['cycle_friday'] is not None:
                            visit_cycle['cycle_friday'] = json.loads(visit_cycle['cycle_friday'])
                        if visit_cycle['cycle_saturday'] is not None:
                            visit_cycle['cycle_saturday'] = json.loads(visit_cycle['cycle_saturday'])
                        if visit_cycle['cycle_sunday'] is not None:
                            visit_cycle['cycle_sunday'] = json.loads(visit_cycle['cycle_sunday'])
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
                                if visit_cycle:
                                    key = 'cycle_{}'.format(day_idx)
                                    data[key] = visit_cycle[key]
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
                                        "is_use_route": False
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
                                    if visit_cycle:
                                        key = 'cycle_{}'.format(day_idx)
                                        data[key] = visit_cycle[key]
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
                            if visit_cycle:
                                key = 'cycle_{}'.format(day_idx)
                                data[key] = visit_cycle[key]
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
        for rec in batch_data:
            try:
                result = self.visit_cycle_model.import_insert(
                    self.cursor, rec, 'user_id, cycle_number, is_deleted, is_delete_count'
                )
                mysql.connection.commit()
            except Exception as e:
                print("Failed Import error: {}".format(e))
                # raise BadRequest(e, 200, 1, data=[])
                pass

        return True

    def check_visit_cycle_by_name(self, name: str, _id: int):
        """
        Check for user_id visit cycle

        :param name: str
        :param _id: int
        :return:
            Visit Cycle Object
        """
        visit_cycle = self.visit_cycle_model.get_visit_cycle_by_name(self.cursor, name, _id)

        if len(visit_cycle) == 0:
            return False
        else:
            return True

    def check_visit_cycle_by_user_cycle(self, user_id: int, cycle_no: int, _id: int):
        """
        Check for user_id visit cycle

        :param user_id: int
        :param cycle_no: int
        :param _id: int
        :return:
            Visit Cycle Object
        """
        visit_cycle = self.visit_cycle_model.get_visit_cycle_by_user_cycle(self.cursor, user_id, cycle_no, _id)

        if len(visit_cycle) == 0:
            return False
        else:
            return True

    def get_visit_cycle_by_id(self, _id: int):
        """
        Get visit cycle Information Data

        :param _id: int
        :return:
            Visit Cycle Object
        """
        visit_cycle = self.visit_cycle_model.get_visit_cycle_by_id(self.cursor, _id)

        if len(visit_cycle) == 0:
            raise BadRequest("This visit cycle doesn't exist", 500, 1, data=[])
        else:
            visit_cycle = visit_cycle[0]
            if visit_cycle['edit_data'] is not None:
                visit_cycle['edit_data'] = json.loads(visit_cycle['edit_data'])
            if visit_cycle['cycle_monday'] is not None:
                visit_cycle['cycle_monday'] = json.loads(visit_cycle['cycle_monday'])
            if visit_cycle['cycle_tuesday'] is not None:
                visit_cycle['cycle_tuesday'] = json.loads(visit_cycle['cycle_tuesday'])
            if visit_cycle['cycle_wednesday'] is not None:
                visit_cycle['cycle_wednesday'] = json.loads(visit_cycle['cycle_wednesday'])
            if visit_cycle['cycle_thursday'] is not None:
                visit_cycle['cycle_thursday'] = json.loads(visit_cycle['cycle_thursday'])
            if visit_cycle['cycle_friday'] is not None:
                visit_cycle['cycle_friday'] = json.loads(visit_cycle['cycle_friday'])
            if visit_cycle['cycle_saturday'] is not None:
                visit_cycle['cycle_saturday'] = json.loads(visit_cycle['cycle_saturday'])
            if visit_cycle['cycle_sunday'] is not None:
                visit_cycle['cycle_sunday'] = json.loads(visit_cycle['cycle_sunday'])

        return visit_cycle

    def get_all_visit_cycle_data(
            self, page: int, limit: int, search: str, column: str, direction: str,
            branch_privilege: list, division_privilege: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilige: list
        :param: division_privilige: list
        :return:
            Visit Cycle Object
        """
        cycle = {}
        data = []
        start = page * limit - limit
        where = """WHERE (vc.is_approval = 1 AND vc.is_deleted = 0) 
        AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
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
                order = """ORDER BY vc.{0} {1}""".format(column, direction)
        select = "vc.*"
        select_count = "vc.id"
        join = """as vc LEFT JOIN `users` as u ON vc.user_id = u.id 
        LEFT JOIN `branches` as b ON u.branch_id = b.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR vc.cycle_number LIKE '%{0}%' 
            OR b.name LIKE '%{0}%' OR e.name LIKE '%{0}%')""".format(search)
        visit_cycle_data = self.visit_cycle_model.get_all_visit_cycle(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.visit_cycle_model.get_count_all_visit_cycle(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.visit_cycle_model.get_count_all_visit_cycle(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if visit_cycle_data:
            for vc in visit_cycle_data:
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
                            self.cursor, vc['user_id'], select="username, employee_id, branch_id, division_id"
                        )[0]
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
                    if vc['user']['division_id'] is not None:
                        try:
                            vc['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, vc['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            vc['user']['division_name'] = None
                    else:
                        vc['user']['division_name'] = None
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

    def update_visit_cycle(self, visit_cycle_data: 'dict', _id: 'int'):
        """
        Update Visit cycle
        :param visit_cycle_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.visit_cycle_model.update_by_id(self.cursor, visit_cycle_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_visit_cycle_delete_count(self, user_id: 'int', cycle_no: 'int'):
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
            count = self.visit_cycle_model.get_all_visit_cycle(
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
            query = "DELETE from `visit_cycle` WHERE id = {}".format(_id)
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
            total_cycle = self.visit_cycle_model.get_all_visit_cycle(
                self.cursor, where="""WHERE user_id = {} AND is_deleted = 0""".format(user_id), order="ORDER BY `cycle_number` DESC"
            )[0]
        except:
            raise BadRequest("User doesn't have visit cycle", 422, 1, data=[])
        total_cycle = total_cycle['cycle_number']
        print(total_cycle)
        if total_cycle:
            for single_date in date_range(start_date, end_date):
                date_now = single_date
                cycle_number, days = get_cycle_data(start_date_cycle, date_now, total_cycle)
                cycle_data = self.visit_cycle_model.get_visit_cycle_by_user_cycle(self.cursor, user_id=user_id,
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
                            result = self.visit_plan_model.insert_into_db(
                                self.cursor, user_id=cycle_data['user_id'],
                                date=single_date.strftime("%Y-%m-%d %H:%M:%S"),
                                asset_id=cycle_data['asset_id'],
                                # route=json.dumps(days_data['route']),
                                route=data_route,
                                destination=days_data['destination'],
                                destination_order=days_data['destination_order'],
                                start_route_branch_id=days_data['start_route_branch_id'],
                                end_route_branch_id=days_data['end_route_branch_id'],
                                invoice_id=None,
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
            raise BadRequest("User doesn't have visit cycle", 422, 1, data=[])

        return result

    def create_visit_plan(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new visit cycle

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
            result = self.visit_plan_model.insert_into_db(
                self.cursor, user_id=create_data['user_id'], asset_id=create_data['asset_id'],
                route=route, date=create_data['date'],
                destination=create_data['destination'], destination_order=destination_order,
                start_route_branch_id=create_data['start_route_branch_id'],
                end_route_branch_id=create_data['end_route_branch_id'], invoice_id=create_data['invoice_id'],
                is_use_route=create_data['is_use_route'], create_date=today, update_date=today,
                is_approval=create_data['is_approval'], approval_by=create_data['approval_by'], create_by=user_id
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id

    def get_all_visit_plan_data(
            self, page: int, limit: int, search: str, column: str, direction: str, user_id: int,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: user_id: int
        :param: branch_privilege: list
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            Visit Cycle Object
        """
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        if user_id:
            where = "WHERE (vp.is_approval = 1 AND vp.is_deleted = 0) AND vp.user_id = {0}".format(user_id)
        else:
            # where = """WHERE (vp.is_approval = 1 AND vp.is_deleted = 0) 
            # AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            #     ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            # )
            where = """WHERE (vp.is_approval = 1 AND vp.is_deleted = 0) 
            AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
                ", ".join(str(x) for x in branch_privilege), 2
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
            elif column == 'division':
                order = """ORDER BY dv.division_name {0}""".format(direction)
            elif column == 'date':
                order = """ORDER BY vp.{0} {1}, vp.create_date {1}""".format(column, direction)
            else:
                order = """ORDER BY vp.{0} {1}""".format(column, direction)
        select = "vp.*"
        select_count = "vp.id"
        join = """as vp LEFT JOIN `users` as u ON vp.user_id = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id
        LEFT JOIN `branches` as br ON u.branch_id = br.id
        LEFT JOIN `divisions` as dv ON u.division_id = dv.id
        LEFT JOIN `branches` as b1 ON vp.start_route_branch_id = b1.id
        LEFT JOIN `branches` as b2 ON vp.end_route_branch_id = b2.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR br.name LIKE '%{0}%' OR dv.division_name LIKE '%{0}%' 
            OR b1.name LIKE '%{0}%' OR b2.name LIKE '%{0}%' OR e.name LIKE '%{0}%')""".format(search)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                where += """AND (vp.date >= '{0} 00:00:00' AND vp.date <= '{1} 23:59:59') """.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            if data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
            if data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
            if data_filter['division_id']:
                where += """AND u.division_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['division_id']))
        visit_plan_data = self.visit_plan_model.get_all_visit_plan(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.visit_plan_model.get_count_all_visit_plan(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.visit_plan_model.get_count_all_visit_plan(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if visit_plan_data:
            for vp in visit_plan_data:
                list_customer = []
                vp['start_custom_location'] = None
                vp['stop_custom_location'] = None
                if vp['edit_data'] is not None:
                    vp['edit_data'] = json.loads(vp['edit_data'])
                if vp['date'] is not None:
                    my_date = datetime.strftime(vp['date'], "%Y-%m-%d")
                    vp['date'] = str(my_date)
                if vp['create_date'] is not None:
                    vp['create_date'] = str(vp['create_date'])
                if vp['update_date'] is not None:
                    vp['update_date'] = str(vp['update_date'])
                # Get Activity data
                data_activity_dict = dict()
                data_activity = []
                list_nfc_code = []
                try:
                    where = """WHERE (sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START' 
                                GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `sales_activity` 
                                WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id) 
                                FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, visit_plan_id, nfc_code) 
                                OR sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT' 
                                GROUP BY user_id, visit_plan_id, nfc_code)) AND (visit_plan_id = {0}) """.format(
                        vp['id'])
                    order = ""
                    select = "sa.*"
                    join = """AS sa"""
                    activity_data = self.sales_activity_model.get_all_activity(
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
                if vp['destination_new'] is not None:
                    vp['destination_new'] = json.loads(vp['destination_new'])
                    idx = 0
                    for rec in vp['destination_new']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination_new'][idx]['customer_name'] = customer['name']
                            vp['destination_new'][idx]['customer_email'] = customer['email']
                            vp['destination_new'][idx]['phone'] = customer['phone']
                            vp['destination_new'][idx]['address'] = customer['address']
                            vp['destination_new'][idx]['lng'] = customer['lng']
                            vp['destination_new'][idx]['lat'] = customer['lat']
                            vp['destination_new'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination_new'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination_new'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination_new'][idx]['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                vp['destination_new'][idx]['business_activity'] = None
                        except:
                            vp['destination_new'][idx]['customer_name'] = None
                            vp['destination_new'][idx]['customer_email'] = None
                            vp['destination_new'][idx]['phone'] = None
                            vp['destination_new'][idx]['address'] = None
                            vp['destination_new'][idx]['lng'] = None
                            vp['destination_new'][idx]['lat'] = None
                            vp['destination_new'][idx]['nfcid'] = None
                            vp['destination_new'][idx]['contacts'] = None
                            vp['destination_new'][idx]['business_activity'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1
                # vc['customer'] = list_customer
                vp['total_customer'] = len(set(list_customer))
                if vp['user_id'] is not None:
                    try:
                        vp['user'] = self.user_model.get_user_by_id(
                            self.cursor, vp['user_id'], select="username, employee_id, branch_id, division_id")[0]
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
                    if vp['user']['division_id'] is not None:
                        try:
                            vp['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, vp['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            vp['user']['division_name'] = None
                    else:
                        vp['user']['division_name'] = None
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


    def get_all_visit_plan_data_sales(
        self, page: int, limit: int, search: str, column: str, direction: str, user_id: int,
        branch_privilege: list, division_privilege: list, data_filter: list
    ):
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        if user_id:
            where = "WHERE (vp.is_approval = 1 AND vp.is_deleted = 0) AND vp.user_id = {0}".format(user_id)
        else:
            where = """WHERE (vp.is_approval = 1 AND vp.is_deleted = 0) 
            AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
                ", ".join(str(x) for x in branch_privilege), 2
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
            elif column == 'division':
                order = """ORDER BY dv.division_name {0}""".format(direction)
            elif column == 'date':
                order = """ORDER BY vp.{0} {1}, vp.create_date {1}""".format(column, direction)
            else:
                order = """ORDER BY vp.{0} {1}""".format(column, direction)
        select = "vp.*"
        select_count = "vp.id"
        join = """as vp LEFT JOIN `users` as u ON vp.user_id = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id
        LEFT JOIN `branches` as br ON u.branch_id = br.id
        LEFT JOIN `divisions` as dv ON u.division_id = dv.id
        LEFT JOIN `branches` as b1 ON vp.start_route_branch_id = b1.id
        LEFT JOIN `branches` as b2 ON vp.end_route_branch_id = b2.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR br.name LIKE '%{0}%' OR dv.division_name LIKE '%{0}%' 
            OR b1.name LIKE '%{0}%' OR b2.name LIKE '%{0}%' OR e.name LIKE '%{0}%')""".format(search)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                where += """AND (vp.date >= '{0} 00:00:00' AND vp.date <= '{1} 23:59:59') """.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            if data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
            if data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
            if data_filter['division_id']:
                where += """AND u.division_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['division_id']))
        visit_plan_data = self.visit_plan_model.get_all_visit_plan(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.visit_plan_model.get_count_all_visit_plan(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.visit_plan_model.get_count_all_visit_plan(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if visit_plan_data:
            for vp in visit_plan_data:
                list_customer = []
                vp['start_custom_location'] = None
                vp['stop_custom_location'] = None
                if vp['edit_data'] is not None:
                    vp['edit_data'] = json.loads(vp['edit_data'])
                if vp['date'] is not None:
                    my_date = datetime.strftime(vp['date'], "%Y-%m-%d")
                    vp['date'] = str(my_date)
                if vp['create_date'] is not None:
                    vp['create_date'] = str(vp['create_date'])
                if vp['update_date'] is not None:
                    vp['update_date'] = str(vp['update_date'])
                # Get Activity data
                data_activity_dict = dict()
                data_activity = []
                list_nfc_code = []
                try:
                    where = """WHERE (sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START' 
                                GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `sales_activity` 
                                WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id) 
                                FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, visit_plan_id, nfc_code) 
                                OR sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT' 
                                GROUP BY user_id, visit_plan_id, nfc_code)) AND (visit_plan_id = {0}) """.format(
                        vp['id'])
                    order = ""
                    select = "sa.*"
                    join = """AS sa"""
                    activity_data = self.sales_activity_model.get_all_activity(
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
                if vp['destination_new'] is not None:
                    vp['destination_new'] = json.loads(vp['destination_new'])
                    idx = 0
                    for rec in vp['destination_new']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination_new'][idx]['customer_name'] = customer['name']
                            vp['destination_new'][idx]['customer_email'] = customer['email']
                            vp['destination_new'][idx]['phone'] = customer['phone']
                            vp['destination_new'][idx]['address'] = customer['address']
                            vp['destination_new'][idx]['lng'] = customer['lng']
                            vp['destination_new'][idx]['lat'] = customer['lat']
                            vp['destination_new'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination_new'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination_new'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination_new'][idx]['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                vp['destination_new'][idx]['business_activity'] = None
                        except:
                            vp['destination_new'][idx]['customer_name'] = None
                            vp['destination_new'][idx]['customer_email'] = None
                            vp['destination_new'][idx]['phone'] = None
                            vp['destination_new'][idx]['address'] = None
                            vp['destination_new'][idx]['lng'] = None
                            vp['destination_new'][idx]['lat'] = None
                            vp['destination_new'][idx]['nfcid'] = None
                            vp['destination_new'][idx]['contacts'] = None
                            vp['destination_new'][idx]['business_activity'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1
                # vc['customer'] = list_customer
                vp['total_customer'] = len(set(list_customer))
                if vp['user_id'] is not None:
                    try:
                        vp['user'] = self.user_model.get_user_by_id(
                            self.cursor, vp['user_id'], select="username, employee_id, branch_id, division_id")[0]
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
                    if vp['user']['division_id'] is not None:
                        try:
                            vp['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, vp['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            vp['user']['division_name'] = None
                    else:
                        vp['user']['division_name'] = None
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


    def get_all_visit_plan_data_collector(
        self, page: int, limit: int, search: str, column: str, direction: str, user_id: int,
        branch_privilege: list, division_privilege: list, data_filter: list
    ):
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        if user_id:
            where = "WHERE (vp.is_approval = 1 AND vp.is_deleted = 0) AND vp.user_id = {0}".format(user_id)
        else:
            where = """WHERE (vp.is_approval = 1 AND vp.is_deleted = 0) 
            AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
                ", ".join(str(x) for x in branch_privilege), 4
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
            elif column == 'division':
                order = """ORDER BY dv.division_name {0}""".format(direction)
            elif column == 'date':
                order = """ORDER BY vp.{0} {1}, vp.create_date {1}""".format(column, direction)
            else:
                order = """ORDER BY vp.{0} {1}""".format(column, direction)
        select = "vp.*"
        select_count = "vp.id"
        join = """as vp LEFT JOIN `users` as u ON vp.user_id = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id
        LEFT JOIN `branches` as br ON u.branch_id = br.id
        LEFT JOIN `divisions` as dv ON u.division_id = dv.id
        LEFT JOIN `branches` as b1 ON vp.start_route_branch_id = b1.id
        LEFT JOIN `branches` as b2 ON vp.end_route_branch_id = b2.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR br.name LIKE '%{0}%' OR dv.division_name LIKE '%{0}%' 
            OR b1.name LIKE '%{0}%' OR b2.name LIKE '%{0}%' OR e.name LIKE '%{0}%')""".format(search)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                where += """AND (vp.date >= '{0} 00:00:00' AND vp.date <= '{1} 23:59:59') """.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            if data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
            if data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
            if data_filter['division_id']:
                where += """AND u.division_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['division_id']))
        visit_plan_data = self.visit_plan_model.get_all_visit_plan(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.visit_plan_model.get_count_all_visit_plan(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.visit_plan_model.get_count_all_visit_plan(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if visit_plan_data:
            for vp in visit_plan_data:
                list_customer = []
                vp['start_custom_location'] = None
                vp['stop_custom_location'] = None
                if vp['edit_data'] is not None:
                    vp['edit_data'] = json.loads(vp['edit_data'])
                if vp['date'] is not None:
                    my_date = datetime.strftime(vp['date'], "%Y-%m-%d")
                    vp['date'] = str(my_date)
                if vp['create_date'] is not None:
                    vp['create_date'] = str(vp['create_date'])
                if vp['update_date'] is not None:
                    vp['update_date'] = str(vp['update_date'])
                # Get Activity data
                data_activity_dict = dict()
                data_activity = []
                list_nfc_code = []
                try:
                    where = """WHERE (sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START' 
                                GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `sales_activity` 
                                WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id) 
                                FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, visit_plan_id, nfc_code) 
                                OR sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT' 
                                GROUP BY user_id, visit_plan_id, nfc_code)) AND (visit_plan_id = {0}) """.format(
                        vp['id'])
                    order = ""
                    select = "sa.*"
                    join = """AS sa"""
                    activity_data = self.sales_activity_model.get_all_activity(
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
                if vp['destination_new'] is not None:
                    vp['destination_new'] = json.loads(vp['destination_new'])
                    idx = 0
                    for rec in vp['destination_new']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination_new'][idx]['customer_name'] = customer['name']
                            vp['destination_new'][idx]['customer_email'] = customer['email']
                            vp['destination_new'][idx]['phone'] = customer['phone']
                            vp['destination_new'][idx]['address'] = customer['address']
                            vp['destination_new'][idx]['lng'] = customer['lng']
                            vp['destination_new'][idx]['lat'] = customer['lat']
                            vp['destination_new'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination_new'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination_new'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination_new'][idx]['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                vp['destination_new'][idx]['business_activity'] = None
                        except:
                            vp['destination_new'][idx]['customer_name'] = None
                            vp['destination_new'][idx]['customer_email'] = None
                            vp['destination_new'][idx]['phone'] = None
                            vp['destination_new'][idx]['address'] = None
                            vp['destination_new'][idx]['lng'] = None
                            vp['destination_new'][idx]['lat'] = None
                            vp['destination_new'][idx]['nfcid'] = None
                            vp['destination_new'][idx]['contacts'] = None
                            vp['destination_new'][idx]['business_activity'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1
                # vc['customer'] = list_customer
                vp['total_customer'] = len(set(list_customer))
                if vp['user_id'] is not None:
                    try:
                        vp['user'] = self.user_model.get_user_by_id(
                            self.cursor, vp['user_id'], select="username, employee_id, branch_id, division_id")[0]
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
                    if vp['user']['division_id'] is not None:
                        try:
                            vp['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, vp['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            vp['user']['division_name'] = None
                    else:
                        vp['user']['division_name'] = None
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


    def check_visit_plan(self, user_id: int, date: str, _id: int):
        """
        Check for user_id visit plan

        :param user_id: int
        :param date: str
        :param _id: int
        :return:
            Visit plan Object
        """
        visit_plan = self.visit_plan_model.get_visit_plan_by_user_date(self.cursor, user_id, date, _id)

        if len(visit_plan) == 0:
            return False
        else:
            return True

    def get_visit_plan_by_id(self, _id: int):
        """
        Get visit plan Information Data

        :param _id: int
        :return:
            Visit Cycle Object
        """
        visit_plan = self.visit_plan_model.get_visit_plan_by_id(self.cursor, _id)

        if len(visit_plan) == 0:
            raise BadRequest("This visit cycle doesn't exist", 500, 1, data=[])
        else:
            visit_plan = visit_plan[0]
            visit_plan['start_custom_location'] = None
            visit_plan['stop_custom_location'] = None
            list_customer = []
            if visit_plan['edit_data'] is not None:
                visit_plan['edit_data'] = json.loads(visit_plan['edit_data'])
            if visit_plan['date'] is not None:
                visit_plan['date'] = str(visit_plan['date'])
            if visit_plan['create_date'] is not None:
                visit_plan['create_date'] = str(visit_plan['create_date'])
            if visit_plan['update_date'] is not None:
                visit_plan['update_date'] = str(visit_plan['update_date'])
            # Get Activity data
            data_activity_dict = dict()
            data_activity = []
            list_nfc_code = []
            try:
                where = """WHERE (sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START' 
                GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `sales_activity` 
                WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id) 
                FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, visit_plan_id, nfc_code) 
                OR sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT' 
                GROUP BY user_id, visit_plan_id, nfc_code)) AND (visit_plan_id = {0}) """.format(_id)
                order = ""
                select = "sa.*"
                join = """AS sa"""
                activity_data = self.sales_activity_model.get_all_activity(
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
                                    visit_plan['start_custom_location'] = json.loads(ad['route_breadcrumb'])
                            elif ad['tap_nfc_type'] == 'STOP':
                                if ad['route_breadcrumb'] is not None:
                                    visit_plan['stop_custom_location'] = json.loads(ad['route_breadcrumb'])
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
                visit_plan['data_activity'] = data_activity_dict
            except Exception as e:
                print(e)
                visit_plan['data_activity'] = dict()
            if visit_plan["invoice_id"] is not None:
                visit_plan['invoice_id'] = json.loads(visit_plan["invoice_id"])
                # print(visit_plan['invoice_id'])
                idx = 0
                for rec in visit_plan['invoice_id']:
                    try:
                        invoice = self.sp_model.get_sales_payment_by_id(
                            self.cursor, rec['id_invoice'],
                            select="code, customer_code, sales_order_code, invoice_amount, product, "
                                   "packing_slip_code, packing_slip_date, payment_due_date"
                        )[0]
                        if invoice['product'] is not None:
                            visit_plan['invoice_id'][idx]['product'] = json.loads(invoice['product'])
                        else:
                            visit_plan['invoice_id'][idx]['product'] = None
                        visit_plan['invoice_id'][idx]['customer_code'] = invoice['customer_code']
                        try:
                            customer_data = self.customer_model.get_customer_by_id(
                                self.cursor, invoice['customer_code'],
                                select="name, address")[0]
                            visit_plan['invoice_id'][idx]['customer_name'] = customer_data['name']
                            visit_plan['invoice_id'][idx]['address'] = customer_data['address']
                        except:
                            visit_plan['invoice_id'][idx]['customer_name'] = None
                            visit_plan['invoice_id'][idx]['address'] = None
                        visit_plan['invoice_id'][idx]['code'] = invoice['code']
                        visit_plan['invoice_id'][idx]['sales_order_id'] = invoice['sales_order_code']
                        visit_plan['invoice_id'][idx]['invoice_amount'] = invoice['invoice_amount']
                        visit_plan['invoice_id'][idx]['packing_slip_code'] = invoice['packing_slip_code']
                        visit_plan['invoice_id'][idx]['packing_slip_date'] = str(invoice['packing_slip_date'])
                        visit_plan['invoice_id'][idx]['invoice_due_date'] = str(invoice['payment_due_date'])
                    except:
                        visit_plan['invoice_id'][idx]['product'] = None
                        visit_plan['invoice_id'][idx]['customer_code'] = None
                        visit_plan['invoice_id'][idx]['code'] = rec['id_invoice']
                        visit_plan['invoice_id'][idx]['sales_order_id'] = None
                        visit_plan['invoice_id'][idx]['invoice_amount'] = None
                        visit_plan['invoice_id'][idx]['packing_slip_code'] = None
                        visit_plan['invoice_id'][idx]['packing_slip_date'] = None
                        visit_plan['invoice_id'][idx]['invoice_due_date'] = None
                    idx += 1
                visit_plan['total_invoice'] = len(visit_plan['invoice_id'])
            else:
                visit_plan['invoice_id'] = []
                visit_plan['total_invoice'] = 0
            if visit_plan['destination'] is not None:
                visit_plan['destination'] = json.loads(visit_plan['destination'])
                idx = 0
                for rec in visit_plan['destination']:
                    try:
                        customer = self.customer_model.get_customer_by_id(
                            self.cursor, rec['customer_code'],
                            select="name, email, phone, address, lng, lat, contacts, nfcid")[0]
                        if customer['contacts'] is not None:
                            contacts = json.loads(customer['contacts'])
                            visit_plan['destination'][idx]['pic_name'] = contacts[0]['name']
                            visit_plan['destination'][idx]['pic_phone'] = contacts[0]['phone']
                            visit_plan['destination'][idx]['pic_mobile'] = contacts[0]['mobile']
                            visit_plan['destination'][idx]['pic_job_position'] = contacts[0]['job_position']
                        else:
                            visit_plan['destination'][idx]['pic_name'] = None
                            visit_plan['destination'][idx]['pic_phone'] = None
                            visit_plan['destination'][idx]['pic_mobile'] = None
                            visit_plan['destination'][idx]['pic_job_position'] = None
                        visit_plan['destination'][idx]['customer_name'] = customer['name']
                        visit_plan['destination'][idx]['customer_email'] = customer['email']
                        visit_plan['destination'][idx]['phone'] = customer['phone']
                        visit_plan['destination'][idx]['address'] = customer['address']
                        visit_plan['destination'][idx]['lng'] = customer['lng']
                        visit_plan['destination'][idx]['lat'] = customer['lat']
                        visit_plan['destination'][idx]['nfcid'] = customer['nfcid']
                        visit_plan['destination'][idx]['total_invoice'] = 0
                        visit_plan['destination'][idx]['invoice'] = []
                    except:
                        visit_plan['destination'][idx]['pic_name'] = None
                        visit_plan['destination'][idx]['pic_phone'] = None
                        visit_plan['destination'][idx]['pic_mobile'] = None
                        visit_plan['destination'][idx]['pic_job_position'] = None
                        visit_plan['destination'][idx]['customer_name'] = None
                        visit_plan['destination'][idx]['customer_email'] = None
                        visit_plan['destination'][idx]['phone'] = None
                        visit_plan['destination'][idx]['address'] = None
                        visit_plan['destination'][idx]['lng'] = None
                        visit_plan['destination'][idx]['lat'] = None
                        visit_plan['destination'][idx]['nfcid'] = None
                        visit_plan['destination'][idx]['total_invoice'] = 0
                        visit_plan['destination'][idx]['invoice'] = []
                    if visit_plan["invoice_id"] is not None:
                        for rec_vp in visit_plan['invoice_id']:
                            if rec_vp['customer_code'] == rec['customer_code'] and rec_vp['is_confirm'] == 1:
                                visit_plan['destination'][idx]['total_invoice'] += 1
                                invoice_data = {
                                    "id_invoice": rec_vp['id_invoice'],
                                    "sales_order_id": rec_vp['sales_order_id'],
                                    "packing_slip_code": rec_vp['packing_slip_code'],
                                    "packing_slip_date": str(rec_vp['packing_slip_date']),
                                    "invoice_due_date": str(rec_vp['invoice_due_date']),
                                    "invoice_amount": rec_vp['invoice_amount']
                                }
                                visit_plan['destination'][idx]['invoice'].append(invoice_data)
                    list_customer.append(rec['customer_code'])
                    idx += 1
            if visit_plan['destination_new'] is not None:
                visit_plan['destination_new'] = json.loads(visit_plan['destination_new'])
                idx = 0
                for rec in visit_plan['destination_new']:
                    try:
                        customer = self.customer_model.get_customer_by_id(
                            self.cursor, rec['customer_code'],
                            select="name, email, phone, address, lng, lat, contacts, nfcid")[0]
                        if customer['contacts'] is not None:
                            contacts = json.loads(customer['contacts'])
                            visit_plan['destination_new'][idx]['pic_name'] = contacts[0]['name']
                            visit_plan['destination_new'][idx]['pic_phone'] = contacts[0]['phone']
                            visit_plan['destination_new'][idx]['pic_mobile'] = contacts[0]['mobile']
                            visit_plan['destination_new'][idx]['pic_job_position'] = contacts[0]['job_position']
                        else:
                            visit_plan['destination_new'][idx]['pic_name'] = None
                            visit_plan['destination_new'][idx]['pic_phone'] = None
                            visit_plan['destination_new'][idx]['pic_mobile'] = None
                            visit_plan['destination_new'][idx]['pic_job_position'] = None
                        visit_plan['destination_new'][idx]['customer_name'] = customer['name']
                        visit_plan['destination_new'][idx]['customer_email'] = customer['email']
                        visit_plan['destination_new'][idx]['phone'] = customer['phone']
                        visit_plan['destination_new'][idx]['address'] = customer['address']
                        visit_plan['destination_new'][idx]['lng'] = customer['lng']
                        visit_plan['destination_new'][idx]['lat'] = customer['lat']
                        visit_plan['destination_new'][idx]['nfcid'] = customer['nfcid']
                        visit_plan['destination_new'][idx]['total_invoice'] = 0
                        visit_plan['destination_new'][idx]['invoice'] = []
                    except:
                        visit_plan['destination_new'][idx]['pic_name'] = None
                        visit_plan['destination_new'][idx]['pic_phone'] = None
                        visit_plan['destination_new'][idx]['pic_mobile'] = None
                        visit_plan['destination_new'][idx]['pic_job_position'] = None
                        visit_plan['destination_new'][idx]['customer_name'] = None
                        visit_plan['destination_new'][idx]['customer_email'] = None
                        visit_plan['destination_new'][idx]['phone'] = None
                        visit_plan['destination_new'][idx]['address'] = None
                        visit_plan['destination_new'][idx]['lng'] = None
                        visit_plan['destination_new'][idx]['lat'] = None
                        visit_plan['destination_new'][idx]['nfcid'] = None
                        visit_plan['destination_new'][idx]['total_invoice'] = 0
                        visit_plan['destination_new'][idx]['invoice'] = []
                    if visit_plan["invoice_id"] is not None:
                        for rec_vp in visit_plan['invoice_id']:
                            if rec_vp['customer_code'] == rec['customer_code'] and rec_vp['is_confirm'] == 1:
                                visit_plan['destination_new'][idx]['total_invoice'] += 1
                                invoice_data = {
                                    "id_invoice": rec_vp['id_invoice'],
                                    "sales_order_id": rec_vp['sales_order_id'],
                                    "packing_slip_code": rec_vp['packing_slip_code'],
                                    "packing_slip_date": str(rec_vp['packing_slip_date']),
                                    "invoice_due_date": str(rec_vp['invoice_due_date']),
                                    "invoice_amount": rec_vp['invoice_amount']
                                }
                                visit_plan['destination_new'][idx]['invoice'].append(invoice_data)
                    list_customer.append(rec['customer_code'])
                    idx += 1

            # vc['customer'] = list_customer
            visit_plan['total_customer'] = len(set(list_customer))
            if visit_plan['user_id'] is not None:
                try:
                    visit_plan['user'] = self.user_model.get_user_by_id(
                        self.cursor, visit_plan['user_id'], select="username, employee_id, branch_id, division_id")[0]
                except:
                    visit_plan['user'] = {}
                if visit_plan['user']['employee_id'] is not None:
                    try:
                        visit_plan['user']['name'] = self.employee_model.get_employee_by_id(
                            self.cursor, visit_plan['user']['employee_id'], select="""name""")[0]['name']
                    except:
                        visit_plan['user']['name'] = None
                if visit_plan['user']['branch_id'] is not None:
                    try:
                        visit_plan['user']['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, visit_plan['user']['branch_id'], select="""name""")[0]['name']
                    except:
                        visit_plan['user']['branch_name'] = None
                if visit_plan['user']['division_id'] is not None:
                    try:
                        visit_plan['user']['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, visit_plan['user']['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        visit_plan['user']['division_name'] = None
                else:
                    visit_plan['user']['division_name'] = None
            else:
                visit_plan['user'] = {}
            if visit_plan['start_route_branch_id'] is not None:
                try:
                    visit_plan['start_route_branch'] = self.branch_model.get_branches_by_id(
                        self.cursor, visit_plan['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                except:
                    visit_plan['start_route_branch'] = {}
            else:
                visit_plan['start_route_branch'] = {}
            if visit_plan['end_route_branch_id'] is not None:
                try:
                    visit_plan['end_route_branch'] = self.branch_model.get_branches_by_id(
                        self.cursor, visit_plan['end_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                except:
                    visit_plan['end_route_branch'] = {}
            else:
                visit_plan['end_route_branch'] = {}

            if visit_plan['route'] is not None:
                visit_plan['route'] = json.loads(visit_plan['route'])

            try:
                where_change_route = "WHERE `visit_plan_id` = {0} AND `type` = 'routes' AND `is_approved` = 1".format(visit_plan['id'])
                change_route = self.permissions_model.get_all_permission_alert(
                    self.cursor, where=where_change_route
                )
                data_change_route = []
                if change_route:
                    for rec in change_route:
                        print(rec['description'])
                        if rec['description'] is not None:
                            data_change_route.append(json.loads(rec['description']))
                visit_plan['change_route'] = data_change_route
            except:
                visit_plan['change_route'] = []
            if visit_plan['destination_order'] is not None:
                visit_plan['destination_order'] = json.loads(visit_plan['destination_order'])
        return visit_plan

    def get_visit_plan_by_user_date(self, _id: int):
        """
        Get visit plan Information Data

        :param _id: int
        :return:
            Visit Cycle Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        # today = "2018-08-10"

        visit_plan = self.visit_plan_model.get_visit_plan_by_user_date(self.cursor, _id, today, None)

        if len(visit_plan) == 0:
            raise BadRequest("This visit plan doesn't exist", 500, 1, data=[])
        else:
            visit_plan = visit_plan[0]
            list_customer = []
            if visit_plan['edit_data'] is not None:
                visit_plan['edit_data'] = json.loads(visit_plan['edit_data'])
            if visit_plan['date'] is not None:
                visit_plan['date'] = str(visit_plan['date'])
            if visit_plan['create_date'] is not None:
                visit_plan['create_date'] = str(visit_plan['create_date'])
            if visit_plan['update_date'] is not None:
                visit_plan['update_date'] = str(visit_plan['update_date'])
            if visit_plan["invoice_id"] is not None:
                visit_plan['invoice_id'] = json.loads(visit_plan["invoice_id"])
                print(visit_plan['invoice_id'])
                idx = 0
                for rec in visit_plan['invoice_id']:
                    try:
                        # invoice = self.so_model.get_sales_order_by_invoice_id(
                        #     self.cursor, rec['id_invoice'],
                        #     select="code, customer_code, invoice_amount, product, packing_slip_code, packing_slip_date"
                        # )[0]
                        invoice = self.sp_model.get_sales_payment_by_id(
                            self.cursor, rec['id_invoice'],
                            select="code, customer_code, sales_order_code, invoice_amount, payment_amount, product, "
                                   "packing_slip_code, packing_slip_date, payment_due_date"
                        )[0]
                        if invoice['product'] is not None:
                            visit_plan['invoice_id'][idx]['product'] = json.loads(invoice['product'])
                        else:
                            visit_plan['invoice_id'][idx]['product'] = None
                        visit_plan['invoice_id'][idx]['customer_code'] = invoice['customer_code']
                        try:
                            customer_data = self.customer_model.get_customer_by_id(
                                self.cursor, invoice['customer_code'],
                                select="name, address")[0]
                            visit_plan['invoice_id'][idx]['customer_name'] = customer_data['name']
                            visit_plan['invoice_id'][idx]['address'] = customer_data['address']
                        except:
                            visit_plan['invoice_id'][idx]['customer_name'] = None
                            visit_plan['invoice_id'][idx]['address'] = None
                        visit_plan['invoice_id'][idx]['code'] = invoice['code']
                        visit_plan['invoice_id'][idx]['sales_order_id'] = invoice['sales_order_code']
                        visit_plan['invoice_id'][idx]['packing_slip_code'] = invoice['packing_slip_code']
                        visit_plan['invoice_id'][idx]['packing_slip_date'] = str(invoice['packing_slip_date'])
                        visit_plan['invoice_id'][idx]['invoice_due_date'] = str(invoice['payment_due_date'])
                        try:
                            payment_mobile = self.spm_model.get_all_sales_payment(
                                self.cursor, select="invoice", order="ORDER BY payment_date DESC",
                                where="""WHERE JSON_CONTAINS(`invoice`, '{{\"invoice_id\": \"{0}\"}}') 
                                AND is_confirm = 1""".format(
                                    invoice['code']
                                )
                            )
                            if payment_mobile:
                                for pay in payment_mobile:
                                    amount_payment = json.loads(pay['invoice'])
                                    if amount_payment:
                                        for rec_pay in amount_payment:
                                            if rec_pay['invoice_id'] == invoice['code']:
                                                invoice['payment_amount'] += rec_pay['payment_amount']
                        except Exception as e:
                            pass
                            print("tidak ada payment")
                        visit_plan['invoice_id'][idx]['invoice_amount'] = invoice['invoice_amount'] - invoice['payment_amount']
                    except:
                        visit_plan['invoice_id'][idx]['product'] = None
                        visit_plan['invoice_id'][idx]['customer_code'] = None
                        visit_plan['invoice_id'][idx]['code'] = rec['id_invoice']
                        visit_plan['invoice_id'][idx]['sales_order_id'] = None
                        visit_plan['invoice_id'][idx]['invoice_amount'] = None
                        visit_plan['invoice_id'][idx]['packing_slip_code'] = None
                        visit_plan['invoice_id'][idx]['packing_slip_date'] = None
                        visit_plan['invoice_id'][idx]['invoice_due_date'] = None
                    idx += 1
                visit_plan['total_invoice'] = len(visit_plan['invoice_id'])
            else:
                visit_plan['invoice_id'] = []
                visit_plan['total_invoice'] = 0
            if visit_plan['destination_order'] is not None:
                visit_plan['destination_order'] = json.loads(visit_plan['destination_order'])
            if visit_plan['destination'] is not None:
                visit_plan['destination'] = json.loads(visit_plan['destination'])
                idx = 0
                for rec in visit_plan['destination']:
                    try:
                        customer = self.customer_model.get_customer_by_id(
                            self.cursor, rec['customer_code'],
                            select="name, email, phone, address, lng, lat, contacts, nfcid")[0]
                        if customer['contacts'] is not None:
                            contacts = json.loads(customer['contacts'])
                            visit_plan['destination'][idx]['pic_name'] = contacts[0]['name']
                            visit_plan['destination'][idx]['pic_phone'] = contacts[0]['phone']
                            visit_plan['destination'][idx]['pic_mobile'] = contacts[0]['mobile']
                            visit_plan['destination'][idx]['pic_job_position'] = contacts[0]['job_position']
                        else:
                            visit_plan['destination'][idx]['pic_name'] = None
                            visit_plan['destination'][idx]['pic_phone'] = None
                            visit_plan['destination'][idx]['pic_mobile'] = None
                            visit_plan['destination'][idx]['pic_job_position'] = None
                        visit_plan['destination'][idx]['customer_name'] = customer['name']
                        visit_plan['destination'][idx]['customer_email'] = customer['email']
                        visit_plan['destination'][idx]['phone'] = customer['phone']
                        visit_plan['destination'][idx]['address'] = customer['address']
                        visit_plan['destination'][idx]['lng'] = customer['lng']
                        visit_plan['destination'][idx]['lat'] = customer['lat']
                        visit_plan['destination'][idx]['nfcid'] = customer['nfcid']
                        visit_plan['destination'][idx]['total_invoice'] = 0
                        visit_plan['destination'][idx]['invoice'] = []

                    except:
                        visit_plan['destination'][idx]['pic_name'] = None
                        visit_plan['destination'][idx]['pic_phone'] = None
                        visit_plan['destination'][idx]['pic_mobile'] = None
                        visit_plan['destination'][idx]['pic_job_position'] = None
                        visit_plan['destination'][idx]['customer_name'] = None
                        visit_plan['destination'][idx]['customer_email'] = None
                        visit_plan['destination'][idx]['phone'] = None
                        visit_plan['destination'][idx]['address'] = None
                        visit_plan['destination'][idx]['lng'] = None
                        visit_plan['destination'][idx]['lat'] = None
                        visit_plan['destination'][idx]['nfcid'] = None
                        visit_plan['destination'][idx]['total_invoice'] = 0
                        visit_plan['destination'][idx]['invoice'] = []
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE visit_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'IN' ".format(
                            visit_plan['id'], rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination'][idx]['arrival_time'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination'][idx]['arrival_time'] = None
                    except:
                        visit_plan['destination'][idx]['arrival_time'] = None
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE visit_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'OUT' ".format(
                            visit_plan['id'], rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination'][idx]['departure_time'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination'][idx]['departure_time'] = None
                    except:
                        visit_plan['destination'][idx]['departure_time'] = None
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE nfc_code = '{0}' AND tap_nfc_type = 'OUT' ".format(
                            rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination'][idx]['last_visited_date'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination'][idx]['last_visited_date'] = None
                    except:
                        visit_plan['destination'][idx]['last_visited_date'] = None
                    try:
                        select = "date"
                        where = "WHERE customer_code = '{0}'".format(
                            rec['customer_code']
                        )
                        order = "ORDER BY date DESC"
                        request = self.ro_model.get_all_request_order(
                            self.cursor, select=select, where=where, order=order
                        )
                        if request:
                            request = request[0]
                            visit_plan['destination'][idx]['last_request_order'] = str(request['date'])
                        else:
                            visit_plan['destination'][idx]['last_request_order'] = None
                    except:
                        visit_plan['destination'][idx]['last_request_order'] = None
                    if visit_plan["invoice_id"] is not None:
                        for rec_vp in visit_plan['invoice_id']:
                            if rec_vp['customer_code'] == rec['customer_code'] and rec_vp['is_confirm'] == 1:
                                visit_plan['destination'][idx]['total_invoice'] += 1
                                invoice_data = {
                                    "id_invoice": rec_vp['id_invoice'],
                                    "sales_order_id": rec_vp['sales_order_id'],
                                    "packing_slip_code": rec_vp['packing_slip_code'],
                                    "packing_slip_date": str(rec_vp['packing_slip_date']),
                                    "invoice_due_date": str(rec_vp['invoice_due_date']),
                                    "invoice_amount": rec_vp['invoice_amount']
                                }
                                visit_plan['destination'][idx]['invoice'].append(invoice_data)
                    list_customer.append(rec['customer_code'])
                    idx += 1
            if visit_plan['destination_new'] is not None:
                visit_plan['destination_new'] = json.loads(visit_plan['destination_new'])
                idx = 0
                for rec in visit_plan['destination_new']:
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE visit_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'IN' ".format(
                            visit_plan['id'], rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date ASC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination_new'][idx]['arrival_time'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination_new'][idx]['arrival_time'] = None
                    except:
                        visit_plan['destination_new'][idx]['arrival_time'] = None
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE visit_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'OUT' ".format(
                            visit_plan['id'], rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination_new'][idx]['departure_time'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination_new'][idx]['departure_time'] = None
                    except:
                        visit_plan['destination_new'][idx]['departure_time'] = None
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE nfc_code = '{0}' AND tap_nfc_type = 'OUT' ".format(
                            rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination_new'][idx]['last_visited_date'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination_new'][idx]['last_visited_date'] = None
                    except:
                        visit_plan['destination_new'][idx]['last_visited_date'] = None
                    try:
                        select = "date"
                        where = "WHERE customer_code = '{0}'".format(
                            rec['customer_code']
                        )
                        order = "ORDER BY date DESC"
                        request = self.ro_model.get_all_request_order(
                            self.cursor, select=select, where=where, order=order
                        )
                        if request:
                            request = request[0]
                            visit_plan['destination_new'][idx]['last_request_order'] = str(request['date'])
                        else:
                            visit_plan['destination_new'][idx]['last_request_order'] = None
                    except:
                        visit_plan['destination_new'][idx]['last_request_order'] = None
                    if visit_plan["invoice_id"] is not None:
                        for rec_vp in visit_plan['invoice_id']:
                            if rec_vp['customer_code'] == rec['customer_code'] and rec_vp['is_confirm'] == 1:
                                visit_plan['destination_new'][idx]['total_invoice'] += 1
                                invoice_data = {
                                    "id_invoice": rec_vp['id_invoice'],
                                    "sales_order_id": rec_vp['sales_order_id'],
                                    "packing_slip_code": rec_vp['packing_slip_code'],
                                    "packing_slip_date": str(rec_vp['packing_slip_date']),
                                    "invoice_due_date": str(rec_vp['invoice_due_date']),
                                    "invoice_amount": rec_vp['invoice_amount']
                                }
                                visit_plan['destination_new'][idx]['invoice'].append(invoice_data)
                    list_customer.append(rec['customer_code'])
                    idx += 1
            # vc['customer'] = list_customer
            visit_plan['total_customer'] = len(set(list_customer))
            if visit_plan['user_id'] is not None:
                try:
                    visit_plan['user'] = self.user_model.get_user_by_id(
                        self.cursor, visit_plan['user_id'], select="username, employee_id, branch_id, division_id")[0]
                except:
                    visit_plan['user'] = {}
                if visit_plan['user']['employee_id'] is not None:
                    try:
                        visit_plan['user']['name'] = self.employee_model.get_employee_by_id(
                            self.cursor, visit_plan['user']['employee_id'], select="""name""")[0]['name']
                    except:
                        visit_plan['user']['name'] = None
                if visit_plan['user']['branch_id'] is not None:
                    try:
                        visit_plan['user']['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, visit_plan['user']['branch_id'], select="""name""")[0]['name']
                    except:
                        visit_plan['user']['branch_name'] = None
                if visit_plan['user']['division_id'] is not None:
                    try:
                        visit_plan['user']['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, visit_plan['user']['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        visit_plan['user']['division_name'] = None
                else:
                    visit_plan['user']['division_name'] = None
            else:
                visit_plan['user'] = {}
            if visit_plan['start_route_branch_id'] is not None:
                try:
                    visit_plan['start_route_branch'] = self.branch_model.get_branches_by_id(
                        self.cursor, visit_plan['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                except:
                    visit_plan['start_route_branch'] = {}
            else:
                visit_plan['start_route_branch'] = {}
            if visit_plan['end_route_branch_id'] is not None:
                try:
                    visit_plan['end_route_branch'] = self.branch_model.get_branches_by_id(
                        self.cursor, visit_plan['end_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                except:
                    visit_plan['end_route_branch'] = {}
            else:
                visit_plan['end_route_branch'] = {}
            if visit_plan['route'] is not None:
                visit_plan['route'] = json.loads(visit_plan['route'])
            else:
                visit_plan['route'] = {}
            try:
                where_change_route = "WHERE `visit_plan_id` = {0} AND `type` = 'routes' AND `is_approved` = 1".format(visit_plan['id'])
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
                visit_plan['change_route'] = data_change_route
            except:
                visit_plan['change_route'] = []
        return visit_plan

    
    def get_visit_plan_by_user_date_collector(self, _id: int):
        
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        # today = "2018-08-10"

        visit_plan = self.visit_plan_model.get_visit_plan_by_user_date(self.cursor, _id, today, None)

        if len(visit_plan) == 0:
            raise BadRequest("This visit plan doesn't exist", 500, 1, data=[])
        else:
            visit_plan = visit_plan[0]
            list_customer = []
            if visit_plan['edit_data'] is not None:
                visit_plan['edit_data'] = json.loads(visit_plan['edit_data'])
            if visit_plan['date'] is not None:
                visit_plan['date'] = str(visit_plan['date'])
            if visit_plan['create_date'] is not None:
                visit_plan['create_date'] = str(visit_plan['create_date'])
            if visit_plan['update_date'] is not None:
                visit_plan['update_date'] = str(visit_plan['update_date'])
            if visit_plan["invoice_id"] is not None:
                visit_plan['invoice_id'] = json.loads(visit_plan["invoice_id"])
                print(visit_plan['invoice_id'])
                idx = 0
                for rec in visit_plan['invoice_id']:
                    try:
                        # invoice = self.so_model.get_sales_order_by_invoice_id(
                        #     self.cursor, rec['id_invoice'],
                        #     select="code, customer_code, invoice_amount, product, packing_slip_code, packing_slip_date"
                        # )[0]
                        invoice = self.sp_model.get_sales_payment_by_id(
                            self.cursor, rec['id_invoice'],
                            select="code, customer_code, sales_order_code, invoice_amount, payment_amount, product, "
                                   "packing_slip_code, packing_slip_date, payment_due_date"
                        )[0]
                        if invoice['product'] is not None:
                            visit_plan['invoice_id'][idx]['product'] = json.loads(invoice['product'])
                        else:
                            visit_plan['invoice_id'][idx]['product'] = None
                        visit_plan['invoice_id'][idx]['customer_code'] = invoice['customer_code']
                        try:
                            customer_data = self.customer_model.get_customer_by_id(
                                self.cursor, invoice['customer_code'],
                                select="name, address")[0]
                            visit_plan['invoice_id'][idx]['customer_name'] = customer_data['name']
                            visit_plan['invoice_id'][idx]['address'] = customer_data['address']
                        except:
                            visit_plan['invoice_id'][idx]['customer_name'] = None
                            visit_plan['invoice_id'][idx]['address'] = None
                        visit_plan['invoice_id'][idx]['code'] = invoice['code']
                        visit_plan['invoice_id'][idx]['sales_order_id'] = invoice['sales_order_code']
                        visit_plan['invoice_id'][idx]['packing_slip_code'] = invoice['packing_slip_code']
                        visit_plan['invoice_id'][idx]['packing_slip_date'] = str(invoice['packing_slip_date'])
                        visit_plan['invoice_id'][idx]['invoice_due_date'] = str(invoice['payment_due_date'])
                        try:
                            payment_mobile = self.spm_model.get_all_sales_payment(
                                self.cursor, select="invoice", order="ORDER BY payment_date DESC",
                                where="""WHERE JSON_CONTAINS(`invoice`, '{{\"invoice_id\": \"{0}\"}}') 
                                AND is_confirm = 1""".format(
                                    invoice['code']
                                )
                            )
                            if payment_mobile:
                                for pay in payment_mobile:
                                    amount_payment = json.loads(pay['invoice'])
                                    if amount_payment:
                                        for rec_pay in amount_payment:
                                            if rec_pay['invoice_id'] == invoice['code']:
                                                invoice['payment_amount'] += rec_pay['payment_amount']
                        except Exception as e:
                            pass
                            print("tidak ada payment")
                        visit_plan['invoice_id'][idx]['invoice_amount'] = invoice['invoice_amount'] - invoice['payment_amount']
                    except:
                        visit_plan['invoice_id'][idx]['product'] = None
                        visit_plan['invoice_id'][idx]['customer_code'] = None
                        visit_plan['invoice_id'][idx]['code'] = rec['id_invoice']
                        visit_plan['invoice_id'][idx]['sales_order_id'] = None
                        visit_plan['invoice_id'][idx]['invoice_amount'] = None
                        visit_plan['invoice_id'][idx]['packing_slip_code'] = None
                        visit_plan['invoice_id'][idx]['packing_slip_date'] = None
                        visit_plan['invoice_id'][idx]['invoice_due_date'] = None
                    idx += 1
                visit_plan['total_invoice'] = len(visit_plan['invoice_id'])
            else:
                visit_plan['invoice_id'] = []
                visit_plan['total_invoice'] = 0
            if visit_plan['destination_order'] is not None:
                visit_plan['destination_order'] = json.loads(visit_plan['destination_order'])
            if visit_plan['destination'] is not None:
                visit_plan['destination'] = json.loads(visit_plan['destination'])
                idx = 0
                for rec in visit_plan['destination']:
                    try:
                        customer = self.customer_model.get_customer_by_id(
                            self.cursor, rec['customer_code'],
                            select="name, email, phone, address, lng, lat, contacts, nfcid")[0]
                        if customer['contacts'] is not None:
                            contacts = json.loads(customer['contacts'])
                            visit_plan['destination'][idx]['pic_name'] = contacts[0]['name']
                            visit_plan['destination'][idx]['pic_phone'] = contacts[0]['phone']
                            visit_plan['destination'][idx]['pic_mobile'] = contacts[0]['mobile']
                            visit_plan['destination'][idx]['pic_job_position'] = contacts[0]['job_position']
                        else:
                            visit_plan['destination'][idx]['pic_name'] = None
                            visit_plan['destination'][idx]['pic_phone'] = None
                            visit_plan['destination'][idx]['pic_mobile'] = None
                            visit_plan['destination'][idx]['pic_job_position'] = None
                        visit_plan['destination'][idx]['customer_name'] = customer['name']
                        visit_plan['destination'][idx]['customer_email'] = customer['email']
                        visit_plan['destination'][idx]['phone'] = customer['phone']
                        visit_plan['destination'][idx]['address'] = customer['address']
                        visit_plan['destination'][idx]['lng'] = customer['lng']
                        visit_plan['destination'][idx]['lat'] = customer['lat']
                        visit_plan['destination'][idx]['nfcid'] = customer['nfcid']
                        visit_plan['destination'][idx]['total_invoice'] = 0
                        visit_plan['destination'][idx]['invoice'] = []

                    except:
                        visit_plan['destination'][idx]['pic_name'] = None
                        visit_plan['destination'][idx]['pic_phone'] = None
                        visit_plan['destination'][idx]['pic_mobile'] = None
                        visit_plan['destination'][idx]['pic_job_position'] = None
                        visit_plan['destination'][idx]['customer_name'] = None
                        visit_plan['destination'][idx]['customer_email'] = None
                        visit_plan['destination'][idx]['phone'] = None
                        visit_plan['destination'][idx]['address'] = None
                        visit_plan['destination'][idx]['lng'] = None
                        visit_plan['destination'][idx]['lat'] = None
                        visit_plan['destination'][idx]['nfcid'] = None
                        visit_plan['destination'][idx]['total_invoice'] = 0
                        visit_plan['destination'][idx]['invoice'] = []
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE visit_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'IN' ".format(
                            visit_plan['id'], rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination'][idx]['arrival_time'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination'][idx]['arrival_time'] = None
                    except:
                        visit_plan['destination'][idx]['arrival_time'] = None
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE visit_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'OUT' ".format(
                            visit_plan['id'], rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination'][idx]['departure_time'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination'][idx]['departure_time'] = None
                    except:
                        visit_plan['destination'][idx]['departure_time'] = None
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE nfc_code = '{0}' AND tap_nfc_type = 'OUT' ".format(
                            rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination'][idx]['last_visited_date'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination'][idx]['last_visited_date'] = None
                    except:
                        visit_plan['destination'][idx]['last_visited_date'] = None
                    try:
                        select = "date"
                        where = "WHERE customer_code = '{0}'".format(
                            rec['customer_code']
                        )
                        order = "ORDER BY date DESC"
                        request = self.ro_model.get_all_request_order(
                            self.cursor, select=select, where=where, order=order
                        )
                        if request:
                            request = request[0]
                            visit_plan['destination'][idx]['last_request_order'] = str(request['date'])
                        else:
                            visit_plan['destination'][idx]['last_request_order'] = None
                    except:
                        visit_plan['destination'][idx]['last_request_order'] = None
                    if visit_plan["invoice_id"] is not None:
                        for rec_vp in visit_plan['invoice_id']:
                            if rec_vp['customer_code'] == rec['customer_code'] and rec_vp['is_confirm'] == 1:
                                visit_plan['destination'][idx]['total_invoice'] += 1
                                invoice_data = {
                                    "id_invoice": rec_vp['id_invoice'],
                                    "sales_order_id": rec_vp['sales_order_id'],
                                    "packing_slip_code": rec_vp['packing_slip_code'],
                                    "packing_slip_date": str(rec_vp['packing_slip_date']),
                                    "invoice_due_date": str(rec_vp['invoice_due_date']),
                                    "invoice_amount": rec_vp['invoice_amount']
                                }
                                visit_plan['destination'][idx]['invoice'].append(invoice_data)
                    list_customer.append(rec['customer_code'])
                    idx += 1
            if visit_plan['destination_new'] is not None:
                visit_plan['destination_new'] = json.loads(visit_plan['destination_new'])
                idx = 0
                for rec in visit_plan['destination_new']:
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE visit_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'IN' ".format(
                            visit_plan['id'], rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date ASC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination_new'][idx]['arrival_time'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination_new'][idx]['arrival_time'] = None
                    except:
                        visit_plan['destination_new'][idx]['arrival_time'] = None
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE visit_plan_id = {0} AND nfc_code = '{1}' AND tap_nfc_type = 'OUT' ".format(
                            visit_plan['id'], rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination_new'][idx]['departure_time'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination_new'][idx]['departure_time'] = None
                    except:
                        visit_plan['destination_new'][idx]['departure_time'] = None
                    try:
                        select = "tap_nfc_date"
                        where = "WHERE nfc_code = '{0}' AND tap_nfc_type = 'OUT' ".format(
                            rec['customer_code']
                        )
                        order = "ORDER BY tap_nfc_date DESC"
                        activity = self.sales_activity_model.get_all_activity(
                            self.cursor, select=select, where=where, order=order
                        )
                        if activity:
                            activity = activity[0]
                            visit_plan['destination_new'][idx]['last_visited_date'] = str(activity['tap_nfc_date'])
                        else:
                            visit_plan['destination_new'][idx]['last_visited_date'] = None
                    except:
                        visit_plan['destination_new'][idx]['last_visited_date'] = None
                    try:
                        select = "date"
                        where = "WHERE customer_code = '{0}'".format(
                            rec['customer_code']
                        )
                        order = "ORDER BY date DESC"
                        request = self.ro_model.get_all_request_order(
                            self.cursor, select=select, where=where, order=order
                        )
                        if request:
                            request = request[0]
                            visit_plan['destination_new'][idx]['last_request_order'] = str(request['date'])
                        else:
                            visit_plan['destination_new'][idx]['last_request_order'] = None
                    except:
                        visit_plan['destination_new'][idx]['last_request_order'] = None
                    if visit_plan["invoice_id"] is not None:
                        for rec_vp in visit_plan['invoice_id']:
                            if rec_vp['customer_code'] == rec['customer_code'] and rec_vp['is_confirm'] == 1:
                                visit_plan['destination_new'][idx]['total_invoice'] += 1
                                invoice_data = {
                                    "id_invoice": rec_vp['id_invoice'],
                                    "sales_order_id": rec_vp['sales_order_id'],
                                    "packing_slip_code": rec_vp['packing_slip_code'],
                                    "packing_slip_date": str(rec_vp['packing_slip_date']),
                                    "invoice_due_date": str(rec_vp['invoice_due_date']),
                                    "invoice_amount": rec_vp['invoice_amount']
                                }
                                visit_plan['destination_new'][idx]['invoice'].append(invoice_data)
                    list_customer.append(rec['customer_code'])
                    idx += 1
            # vc['customer'] = list_customer
            visit_plan['total_customer'] = len(set(list_customer))
            if visit_plan['user_id'] is not None:
                try:
                    visit_plan['user'] = self.user_model.get_user_by_id(
                        self.cursor, visit_plan['user_id'], select="username, employee_id, branch_id, division_id")[0]
                except:
                    visit_plan['user'] = {}
                if visit_plan['user']['employee_id'] is not None:
                    try:
                        visit_plan['user']['name'] = self.employee_model.get_employee_by_id(
                            self.cursor, visit_plan['user']['employee_id'], select="""name""")[0]['name']
                    except:
                        visit_plan['user']['name'] = None
                if visit_plan['user']['branch_id'] is not None:
                    try:
                        visit_plan['user']['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor, visit_plan['user']['branch_id'], select="""name""")[0]['name']
                    except:
                        visit_plan['user']['branch_name'] = None
                if visit_plan['user']['division_id'] is not None:
                    try:
                        visit_plan['user']['division_name'] = self.division_model.get_division_by_id(
                            self.cursor, visit_plan['user']['division_id'], select="division_name")[0][
                            'division_name']
                    except:
                        visit_plan['user']['division_name'] = None
                else:
                    visit_plan['user']['division_name'] = None
            else:
                visit_plan['user'] = {}
            if visit_plan['start_route_branch_id'] is not None:
                try:
                    visit_plan['start_route_branch'] = self.branch_model.get_branches_by_id(
                        self.cursor, visit_plan['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                except:
                    visit_plan['start_route_branch'] = {}
            else:
                visit_plan['start_route_branch'] = {}
            if visit_plan['end_route_branch_id'] is not None:
                try:
                    visit_plan['end_route_branch'] = self.branch_model.get_branches_by_id(
                        self.cursor, visit_plan['end_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                except:
                    visit_plan['end_route_branch'] = {}
            else:
                visit_plan['end_route_branch'] = {}
            if visit_plan['route'] is not None:
                visit_plan['route'] = json.loads(visit_plan['route'])
            else:
                visit_plan['route'] = {}
            try:
                where_change_route = "WHERE `visit_plan_id` = {0} AND `type` = 'routes' AND `is_approved` = 1".format(visit_plan['id'])
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
                visit_plan['change_route'] = data_change_route
            except:
                visit_plan['change_route'] = []
        return visit_plan

    def get_visit_plan_invoice(self, _id: int):
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
        visit_plan = self.visit_plan_model.get_visit_plan_by_id(self.cursor, _id, select="invoice_id")

        if len(visit_plan) == 0:
            raise BadRequest("This visit plan doesn't exist", 500, 1, data=[])
        else:
            visit_plan = visit_plan[0]
            data = []
            if visit_plan["invoice_id"] is not None:
                visit_plan['invoice_id'] = json.loads(visit_plan["invoice_id"])
                print(visit_plan['invoice_id'])
                for rec in visit_plan['invoice_id']:
                    try:
                        # invoice = self.so_model.get_sales_order_by_invoice_id(
                        #     self.cursor, rec['id_invoice'],
                        #     select="*"
                        # )[0]
                        invoice = self.sp_model.get_sales_payment_by_id(
                            self.cursor, rec['id_invoice'],
                            select="*"
                        )[0]
                        data.append(invoice)
                    except Exception as e:
                        print(e)
                        pass
        response['data'] = data
        response['count'] = len(data)
        response['count_filter'] = len(data)
        response['has_next'] = False
        response['has_prev'] = False
        return visit_plan

    def update_visit_plan(self, update_data: 'dict', _id: 'int'):
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
            result = self.visit_plan_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_visit_plan_delete_count(self, user_id: 'int', date: 'int'):
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
            count = self.visit_plan_model.get_all_visit_plan(
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
            query = "DELETE from `visit_plan` WHERE id = {}".format(_id)
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
            result = self.visit_plan_summary_model.insert_into_db(
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
            result = self.visit_plan_summary_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_all_visit_plan_summary(self, plan_id: int):
        """
        Get visit plan Information Data

        :param plan_id: int
        :param customer_code: str
        :return:
            Visit Plan Summary Object
        """
        data = []
        result = {}
        summary = self.visit_plan_summary_model.get_visit_plan_summary_by_plan_id(
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

    def get_visit_plan_summary(self, plan_id: int, customer_code: str):
        """
        Get visit plan Information Data

        :param plan_id: int
        :param customer_code: str
        :return:
            Visit Plan Summary Object
        """
        summary = self.visit_plan_summary_model.get_visit_plan_summary_by_plan_id_customer_code(
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

    def check_visit_plan_summary(self, plan_id: int, customer_code: str):
        """
        Get visit plan Information Data

        :param plan_id: int
        :param customer_code: str
        :return:
            Visit Plan Summary Object
        """
        summary = self.visit_plan_summary_model.get_visit_plan_summary_by_plan_id_customer_code(
            self.cursor, plan_id, customer_code
        )
        return summary
