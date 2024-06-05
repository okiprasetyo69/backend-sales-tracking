import json

from rest.helpers import mysql
from .model import Model


__author__ = 'iswan'

# dibuat sesuai keperluan

class CisangkanCustomerModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'customer'

    def update_coordinate_by_id(self, cursor, customer_data):
        try:
            return self.update_key(cursor, customer_data, 'code', 'is_deleted', 0)
        except Exception as e:
            raise e

    def update_delete_customer(self, cursor, customer_data):
        try:
            return self.update(cursor, customer_data, 'code')
        except Exception as e:
            raise e 

    def insert_into_db(self, cursor, code, name, email, phone, address, lng, lat, category, username, password, nfcid, contacts,
                       business_activity, is_branch, parent_code, create_date, update_date, is_approval, approval_by,
                       create_by):
        try:
            value = {
                "code": code, "name": name, "email": email, "phone": phone, "address": address, "lng": lng, "lat": lat, "category": category,
                "username": username, "password": password, "nfcid": nfcid, "contacts": contacts,
                "business_activity": business_activity, "is_branch": is_branch, "parent_code": parent_code,
                "create_date": create_date,
                "update_date": update_date, "is_approval": is_approval,
                "approval_by": approval_by, "create_by": create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e    


    def insert_update_batch(self, cursor, data, key):
        try:
            return self.insert_update(cursor, data, key)
        except Exception as e:
            raise e      


    def m_get_last_customer_inserted_today(self, cursor, user_id):
        # mysql syntax
        # select count(code) from cisangkan.customer where create_by = 115 and DATE(create_date) = CURDATE();
        select = "COUNT(code) as last"
        where = "WHERE create_by = {} AND DATE(create_date) = CURDATE()".format(user_id)
        try:
            return self.get(cursor, fields=select, where=where)
        except Exception as e:
            raise e
    
class CisangkanUserModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'users'

    def m_get_mycustomer_by_username(self, cursor, username, select='customer_id'):
        try:
            return self.get(cursor, fields=select, where="WHERE username = '{}' AND is_deleted = 0".format(username))
        except Exception as e:
            raise e

    def m_get_mycustomer_by_user_id(self, cursor, id, select='customer_id'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = '{}'".format(id))
        except Exception as e:
            raise e

    def m_update_by_username(self, cursor, user_data):
        try:
            return self.update(cursor, user_data, 'username')
        except Exception as e:
            raise e

    def m_update_by_user_id(self, cursor, user_data):
        try:
            return self.update(cursor, user_data, 'id')
        except Exception as e:
            raise e   

    # custom join
    def m_get_custom_user_properties(self, cursor, select, join, where):
        try:
            return self.get(cursor, fields=select, join=join, where=where)
            # return self.get(cursor, fields=select, join=join, where="WHERE is_deleted = 0 AND id = '{0}'".format(user_id))
        except Exception as e:
            raise e

class CisangkanDeliveryPlanModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'delivery_plan'

    def update_coordinate_delivery_plan(self, cursor, data):
        try:
            str_coordinate = ''
            updated_rows = (
                session.query(self)
                .filter(delivery_plan.id == id)
                .update({delivery_plan.destination_order: func.replace(delivery_plan.destination_order, '"lat": 0, "lng": 0,', str_coordinate)},
                        synchronize_session=False)
                )

            return ("Updated {} rows".format(updated_rows))

        except Exception as e:
            raise e

class CisangkanVisitPlanSummaryModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'visit_plan_summary'

    def get_visit_plan_summary_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = '{}'".format(_id))
        except Exception as e:
            raise e

    def get_visit_plan_summary_by_plan_id_customer_code(self, cursor, plan_id, customer_code, _id=''):
        try:
            where = "WHERE `plan_id` = '{0}' AND `customer_code` = '{1}' ".format(plan_id, customer_code)
            if _id:
                where = "WHERE `plan_id` = '{0}' AND `customer_code` = '{1}' AND `id` != {1} ".format(plan_id, customer_code, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def insert_into_db(
            self, cursor, plan_id, customer_code, notes, visit_images, have_competitor, competitor_images,
            create_date, update_date, create_by, category_visit, nc
    ):
        try:
            value = {
                "plan_id": plan_id, "customer_code": customer_code, "notes": notes, "visit_images": visit_images,
                "have_competitor": have_competitor, "competitor_images": competitor_images,
                "create_date": create_date, "update_date": update_date, "create_by": create_by, "category_visit":category_visit, "nc":nc
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e


    def insert_into_db_collector(
            self, cursor, plan_id, customer_code, notes, visit_images, have_competitor, competitor_images,
            create_date, update_date, create_by, collect_method
    ):
        try:
            value = {
                "plan_id": plan_id, "customer_code": customer_code, "notes": notes, "visit_images": visit_images,
                "have_competitor": have_competitor, "competitor_images": competitor_images,
                "create_date": create_date, "update_date": update_date, "create_by": create_by, "collect_method": collect_method
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, update_data):
        try:
            return self.update(cursor, update_data, 'id')
        except Exception as e:
            raise e

    def get_statistic_summary_visit(self, cursor, select, where):
        try:
            return self.get(cursor, fields=select, where=where)
        except Exception as e:
            raise e

    def get_performance_visit_summary(self, cursor, fields, join, where, order):
        try:
            return self.get(cursor, fields=fields, join=join, where=where, order=order)
        except Exception as e:
            raise e

class CisangkanPackingSlipModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'packing_slip'
        self.table_import = 'file_upload'

    def get_packing_slip_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE code = '{}'".format(_id))
        except Exception as e:
            raise e

    def import_insert(self, cursor, data, key):
        try:
            return self.insert_update(cursor, data, key)
        except Exception as e:
            raise e        

    def import_insert_file_csv(self, cursor, file_name, file_name_origin, table, create_date, update_date, create_by):
        try:
            value = {"file_name": file_name, "file_name_origin": file_name_origin, "table_name": "packing_slip",
                     "create_date": create_date, "update_date": update_date, "create_by": create_by}
            
            self.change_charset_to_utf8mb4(cursor)
            try:
                sql = self.qb.insert(value, self.table_import, True)
                # print("import csv file " ,sql)
                return cursor.execute(sql)
            except Exception:
                raise
        except Exception as e:
            raise e

    def insert_into_tbl_file_upload(
        self, cursor, file_path, file_name_origin, status, create_date, create_by
    ):
        value = {
            "table_name": self.table, "file_name": file_path, "file_name_origin": file_name_origin, "status": status,
            "create_date": create_date, "create_by": create_by}
            
        # self.change_charset_to_utf8mb4(cursor)
        try:
            sql = self.qb.insert(value, self.table_import, False)
            # print("import csv file " ,sql)
            return cursor.execute(sql)
        except Exception:
            raise

class CisangkanStatisticModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table_users = 'users'
        self.table_divisions = 'divisions'
        
class CisangkanTotalOnlineModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'visit_plan'
    
    def get_total_user_online(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e
        
class CisangkanTotalStartModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'sales_activity'
        
    def get_total_user_start(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

class CisangkanTotalStopModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'sales_activity'
        
    def get_total_user_stop(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e
        
class CisangkanTotalCheckInModel(Model) :
    def __init__(self) :
        Model.__init__(self)
        self.table = 'sales_activity'
    
    def get_total_user_check_in(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e
        
class CisangkanTotalAbsenceDailyModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'sales_activity'
    
    def get_all_absences(self, cursor, start=0, limit=200, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order, limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e 
        
    def get_count_all_absences(self, cursor, select='vp.date', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e
    
    def get_total_absence_user(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e
    
  
        
  