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
    CisangkanCustomerModel, CisangkanDeliveryPlanModel, CisangkanUserModel, CisangkanVisitPlanSummaryModel, CisangkanPackingSlipModel, VisitPlanModel, CisangkanTotalOnlineModel, CisangkanTotalStartModel, CisangkanTotalStopModel, CisangkanTotalCheckInModel, CisangkanTotalAbsenceDailyModel
    
from rest.models.orm import VisitPlanModel as VisitPlanModelAlchemy

__author__ = 'iswan'

# dibuat sesuai keperluan
#constant
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJuYmYiOjE1NzQwNjUwODQsImV4cCI6MTU3NDY2OTg4NCwiaWRlbnRpdHkiOjEsImlhdCI6MTU3NDA2NTA4NH0.pC9h5aOYLjhq7FX_XxIV-MOfhwOG3zUfwjcln35qCdY"


class CisangkanController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.customer_model = CustomerModel()
        self.user_model = UserModel()
        self.cisangkan_customer_model = CisangkanCustomerModel()
        self.cisangkan_delivery_plan_Model = CisangkanDeliveryPlanModel()
        self.cisangkan_user_model = CisangkanUserModel()
        self.cisangkan_visit_plan_summary_model = CisangkanVisitPlanSummaryModel()
        self.cisangkan_packing_slip_model = CisangkanPackingSlipModel()
        self.cisangkan_total_online = CisangkanTotalOnlineModel()
        self.cisangkan_total_start = CisangkanTotalStartModel()
        self.cisangkan_total_stop = CisangkanTotalStopModel()
        self.cisangkan_total_check_in = CisangkanTotalCheckInModel()
        self.cisangkan_total_absence_daily = CisangkanTotalAbsenceDailyModel()
        self.visit_plan_model = VisitPlanModel()


    def valid_api_key(self, api_key):
        return API_KEY == api_key


    def request_credential(self, identity):
        b = True
        if(identity["username"] != "apps"): b = False
        if(identity["api_key"] != API_KEY): b = False
        return b


    def update_coordinate_customer(self, customer_data: 'dict', _id: 'int'):
        try:
            result = self.cisangkan_customer_model.update_coordinate_by_id(self.cursor, customer_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)
        return result


    def update_coordinate_delivery_plan(self, str_coordinate: 'string'):
        try:
            result = self.cisangkan_delivery_plan_Model.update_coordinate_delivery_plan(self.cursor, str_coordinate)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)
        return result


    def get_total_mycustomer(self, username: str):
        data = {}
        user = self.cisangkan_user_model.m_get_mycustomer_by_username(self.cursor, username)
        if (len(user) == 0) or (user == None):
            raise BadRequest("This User not exist", 200, 1)
        else:
            customers_dict = json.loads(user[0]['customer_id'])
            total = customers_dict.__len__()
            if(total != 0):
                max = 25
                cm = CustomerModel()
                customers = []
                if(total < 25):
                    max = total
                    for x in range(max-1, -1, -1):
                        customer = cm.get_customer_by_id(self.cursor, customers_dict[x])
                        customers += customer
                else:
                    if(total > 999):
                        total = 999
                        limit = 25
                    for x in range(0, 25, 1):
                        customer = cm.get_customer_by_id(self.cursor, customers_dict[x])
                        print(customers_dict[x])
                        customers += customer
                data['total'] = total
                data['mycustomer'] = customers
        return data

    
    def get_searched_mycustomer(self, username_id: str, search: str):
        data = {}
        where = """WHERE is_deleted = 0 """
        where += """AND name LIKE '%{0}%' ORDER BY create_date DESC""".format(search)
        customer_data = self.customer_model.get_all_customer(self.cursor, where=where, limit=100)                            
        data['total'] = customer_data.__len__()
        data['mycustomer'] = customer_data
        return data


    def get_searched_mycustomer_only(self, username_id: str, search: str):
        data = {}
        user = self.cisangkan_user_model.m_get_mycustomer_by_user_id(self.cursor, username_id)
        list_customer = json.loads(user[0]['customer_id'])
        where = """WHERE is_deleted = 0 """
        if list_customer:
            where += "AND `code` IN ('{0}') ".format(
                "', '".join(x for x in list_customer)
            )
        where += """AND name LIKE '%{0}%' ORDER BY create_date DESC""".format(search)
        customer_data = self.customer_model.get_all_customer(self.cursor, where=where, limit=100)                            
        data['total'] = customer_data.__len__()
        data['mycustomer'] = customer_data
        return data        


    def update_customers_sales(self, username: str, customer_id: str):
        user = self.cisangkan_user_model.m_get_mycustomer_by_username(self.cursor, username)
        updated = []
        exist = False
        if (len(user) == 0) or (user == None):
            raise BadRequest("This User not exist", 200, 1)
        else:
            customers_dict = json.loads(user[0]['customer_id'])
        if(customers_dict.__len__() > 0):
            for x in customers_dict:
                if(customer_id == x):
                    exist = True
        result = 0
        if(not exist):
            updated = [customer_id] + customers_dict
            user_data = {
                "username": username,
                "customer_id": updated
            }
            try:
                result = self.cisangkan_user_model.m_update_by_username(self.cursor, user_data)
                mysql.connection.commit()
            except Exception as e:
                raise BadRequest(e, 200, 1)
        return result

    
    def delete_customers_sales(self, username_id:str, customer_id:str):
        customer_data = {
            "code": customer_id,
            "is_deleted": 1,
            "is_delete_approval_by":username_id,
            "is_delete_count":1
        }
        try:
            result = self.cisangkan_customer_model.update_delete_customer(self.cursor, customer_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        if(result == 1):
            try:
                query = self.cisangkan_user_model.m_get_mycustomer_by_user_id(self.cursor, username_id)
                customers = json.loads(query[0]['customer_id'])
                if(customers.__len__() > 0):
                    customer = []
                    for x in customers:
                        if(x != customer_id):
                            customer.append(x)
                    user_data = {
                        "id": username_id,
                        "customer_id": customer
                    }
                    query = self.cisangkan_user_model.m_update_by_user_id(self.cursor, user_data)
                    mysql.connection.commit()
            except Exception as e:
                raise BadRequest(e, 200, 1)

        return result


    def create_mycustomer(self, customer_data: 'dict', user_id: 'int'):
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.cisangkan_customer_model.insert_into_db(self.cursor, code=customer_data['code'],
                                                        name=customer_data['name'], email=customer_data['email'],
                                                        phone=customer_data['phone'], address=customer_data['address'],
                                                        lng=customer_data['lng'], lat=customer_data['lat'],
                                                        category=customer_data['category'],
                                                        username=customer_data['username'],
                                                        password=None,
                                                        nfcid=customer_data['nfcid'],
                                                        contacts=customer_data['contacts'],
                                                        business_activity=customer_data['business_activity'],
                                                        is_branch=customer_data['is_branch'],
                                                        parent_code=(customer_data['parent_code'] if (
                                                                'parent_code' in customer_data) else ""),
                                                        create_date=today, update_date=today,
                                                        is_approval=1,
                                                        approval_by=customer_data['approval_by'], create_by=user_id)
            mysql.connection.commit()
            last_insert_id = customer_data['code']
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id


    def create_summary_plan(self, create_data: 'dict', user_id: 'int'):
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        category_visit = create_data.get("category_visit", None)
        nc = create_data.get("nc", None)
        create_data["category_visit"] = category_visit
        create_data["nc"] = nc
        try:
            result = self.cisangkan_visit_plan_summary_model.insert_into_db(
                self.cursor, 
                plan_id=create_data["plan_id"], 
                customer_code=create_data["customer_code"],
                notes=create_data["notes"], 
                visit_images=create_data["visit_images"],
                have_competitor=create_data["have_competitor"], 
                competitor_images=create_data["competitor_images"],
                create_date=today,
                update_date=today, 
                create_by=user_id, 
                category_visit=create_data["category_visit"],
                nc=nc
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id

    def create_summary_plan_collector(self, create_data: 'dict', user_id: 'int'):
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            result = self.cisangkan_visit_plan_summary_model.insert_into_db_collector(
                self.cursor, 
                plan_id=create_data["plan_id"], 
                customer_code=create_data["customer_code"],
                notes=create_data["notes"], 
                visit_images=create_data["visit_images"],
                have_competitor=create_data["have_competitor"], 
                competitor_images=create_data["competitor_images"],
                create_date=today,
                update_date=today, 
                create_by=user_id, 
                collect_method=create_data["collect_method"]
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id        


    def update_summary_plan(self, update_data: 'dict'):
        try:
            result = self.cisangkan_visit_plan_summary_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result  
        
    def genSuffixCollectMethod(self, suffix):
        if("Cheque" in suffix):
            suffix = suffix.replace("Cheque", "Cq")            
        if("Giro" in suffix):
            suffix = suffix.replace("Giro", "Go")
        if("Kontra bon" in suffix):
            suffix = suffix.replace("Kontra bon", "Kb")
        if("Transfer" in suffix):
            suffix = suffix.replace("Transfer", "Tf")
        if("Tunai" in suffix):
            suffix = suffix.replace("Tunai", "Tn")
        if("Delivery invoice" in suffix):
            suffix = suffix.replace("Delivery invoice", "Dv")
        if("Tidak tertagih" in suffix):
            suffix = suffix.replace("Tidak tertagih", "Tt")
        if("," in suffix):
            suffix = suffix.replace(", ", "_")            
        return suffix

    def saveImageToPath(self, input : 'dict'):            
        suffix = None
        if input['isLogistic']:
            ROOT_IMAGES_PATH = current_app.config["UPLOAD_FOLDER_IMAGES"] + "/delivery_plan_summary/"
        elif input['isCollector']:
            ROOT_IMAGES_PATH = current_app.config["UPLOAD_FOLDER_IMAGES"] + "/collect_plan_summary/"
            cm = input['collect_method']
            suffix = self.genSuffixCollectMethod(cm)
        else:
            ROOT_IMAGES_PATH = current_app.config["UPLOAD_FOLDER_IMAGES"] + "/visit_plan_summary/"

        sales_id = input["username"]
        sales_username = self.getUsernameById(sales_id)
        today = datetime.today()
        today = today.strftime("%Y%m%d")
        cm = CustomerModel()
        customer = cm.get_customer_by_id(self.cursor, input["customer_code"])
                
        if(customer):
            customer_name = customer[0]["name"]
        else:
            customer_name = 'undefined'

        if input["isCollector"]:            
            curr_filename = "{0}_{1}_{2}_{3}_".format(sales_username, today, input["customer_code"], suffix)            
        else:
            curr_filename = "{0}_{1}_{2}_".format(sales_username, today, customer_name)

        if (input["visit_images"] != None):
            current_path = ROOT_IMAGES_PATH + 'visit/'

            if input["isCollector"]:
                exist = self.cisangkan_visit_plan_summary_model.get_visit_plan_summary_by_plan_id_customer_code(self.cursor, input["plan_id"], input["customer_code"])
                if exist :
                    vi = json.loads(exist[0]["visit_images"])
                    for x in vi:
                        fileToRemove = x["image"]
                        if os.path.exists(fileToRemove) :
                            os.remove(fileToRemove)
                else:
                    print("no exist")
            else:
                for x in range(0, 10, 1):
                    fileToRemove = current_path + curr_filename + str(x) + ".jpg"
                    if os.path.exists(fileToRemove) :
                        os.remove(fileToRemove)

            convert_data = []
            i = 0
            for dic in input['visit_images']:
                datas = {}
                for key in dic:
                    if key == 'desc':
                        datas['desc'] = dic[key]
                    if key == 'image':
                        if not os.path.exists(current_path):
                            os.makedirs(current_path)
                        curr_image = base64.b64decode(dic[key])                            
                        pathfile = current_path + curr_filename + str(i) +".jpg"
                        with open(pathfile, 'wb') as f:
                            f.write(curr_image)
                            f.close()
                        datas["image"] = pathfile
                i += 1
                convert_data.append(datas)
            input["visit_images"] = convert_data

        if (input["competitor_images"] != None):
            current_path = ROOT_IMAGES_PATH + 'competitor/'
            for x in range(0, 10, 1):
                fileToRemove = current_path + curr_filename + str(x) + ".jpg"
                print("competitor : " + fileToRemove)
                if os.path.exists(fileToRemove) :
                    os.remove(fileToRemove)
            convert_data = []
            i = 0
            for dic in input['competitor_images']:
                datas = {}
                for key in dic:
                    if key == 'desc':
                        datas['desc'] = dic[key]
                    if key == 'image':
                        if not os.path.exists(current_path):
                            os.makedirs(current_path)
                        curr_image = base64.b64decode(dic[key])                            
                        pathfile = current_path + curr_filename + str(i) +".jpg"
                        with open(pathfile, 'wb') as f:
                            f.write(curr_image)
                            f.close()
                        datas["image"] = pathfile
                i += 1
                convert_data.append(datas)
            input["competitor_images"] = convert_data
        return input


    def loadImageFromPath(self, input : 'dict'):
        if (input["visit_images"] != None):
            revert_data = []
            i = 0
            for dic in input['visit_images']:
                datas = {}
                for key in dic:
                    if key == 'desc':
                        datas['desc'] = dic[key]
                    if key == 'image':
                        if len(dic[key]) < 255:
                            if os.path.exists(dic[key]):                            
                                f = open(dic[key], "r")
                                if f.mode == "r":
                                    with open(dic[key], 'rb') as imgFile:
                                        image = base64.b64encode(imgFile.read())
                                    datas["image"] = str(image.decode('utf-8'))
                        else:
                            datas["image"] = dic[key]
                i += 1
                revert_data.append(datas)
            input["visit_images"] = revert_data

        if (input["competitor_images"] != None):
            revert_data = []
            i = 0
            for dic in input['competitor_images']:
                datas = {}
                for key in dic:
                    if key == 'desc':
                        datas['desc'] = dic[key]
                    if key == 'image':
                        if os.path.exists(dic[key]):                            
                            f = open(dic[key], "r")
                            if f.mode == "r":
                                with open(dic[key], 'rb') as imgFile:
                                    image = base64.b64encode(imgFile.read())
                                datas["image"] = str(image.decode('utf-8'))
                i += 1
                revert_data.append(datas)
            input["competitor_images"] = revert_data
        return input


    def get_last_mycustomer_inserted_today(self, user_id : 'int'):
        try:
            result = self.cisangkan_customer_model.m_get_last_customer_inserted_today(self.cursor, user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result


    def get_visit_plan_summary_by_id(self, _id: 'int'):
        result = self.cisangkan_visit_plan_summary_model.get_visit_plan_summary_by_id(self.cursor, _id)
        return result
            

    def saveImageToPath2(self, input : 'dict'):
        ROOT_IMAGES_PATH = current_app.config["UPLOAD_FOLDER_IMAGES"] + "/visit_plan_summary/"
        sales_id = input["username"]
        today = datetime.strptime(str(input["create_date"]), '%Y-%m-%d %H:%M:%S')
        create_date = today.strftime("%Y%m%d")
        cm = CustomerModel()
        customer = cm.get_customer_by_id(self.cursor, input["customer_code"])
        if(customer):
            customer_name = customer[0]["name"]
        else:
            customer_name = 'undefined'
        curr_filename = "{0}_{1}_{2}_".format(sales_id, str(create_date), customer_name)
        if (input["visit_images"] != None):
            current_path = ROOT_IMAGES_PATH + 'visit/'
            for x in range(0, 10, 1):
                fileToRemove = current_path + curr_filename + str(x) + ".jpg"
                if os.path.exists(fileToRemove) :
                    os.remove(fileToRemove)
            convert_data = []
            i = 0
            for dic in input['visit_images']:
                datas = {}
                for key in dic:
                    if key == 'desc':
                        datas['desc'] = dic[key].replace('\n',' ')
                    if key == 'image':
                        if not os.path.exists(current_path):
                            os.makedirs(current_path)
                        curr_image = base64.b64decode(dic[key])                            
                        pathfile = current_path + curr_filename + str(i) +".jpg"
                        with open(pathfile, 'wb') as f:
                            f.write(curr_image)
                            f.close()
                        datas["image"] = pathfile
                i += 1
                convert_data.append(datas)
            input["visit_images"] = convert_data

        if (input["have_competitor"] == 1):
            current_path = ROOT_IMAGES_PATH + 'competitor/'
            for x in range(0, 10, 1):
                fileToRemove = current_path + curr_filename + str(x) + ".jpg"
                print("competitor : " + fileToRemove)
                if os.path.exists(fileToRemove) :
                    os.remove(fileToRemove)
            convert_data = []
            i = 0
            for dic in input['competitor_images']:
                datas = {}
                for key in dic:
                    if key == 'desc':
                        datas['desc'] = dic[key].replace('\n',' ')
                    if key == 'image':                        
                        if not os.path.exists(current_path):
                            os.makedirs(current_path)
                        curr_image = base64.b64decode(dic[key])                            
                        pathfile = current_path + curr_filename + str(i) +".jpg"
                        with open(pathfile, 'wb') as f:
                            f.write(curr_image)
                            f.close()
                        datas["image"] = pathfile
                i += 1
                convert_data.append(datas)
            input["competitor_images"] = convert_data
        return input


    def import_packing_slip_file_csv(self, filename: str, filename_origin: str, table: str, user_id: int):
        df = pd.read_csv(filename, sep=";", skiprows=0)
        headers = df[
            ['INVNO', 'DOCUMENTNUMBER', 'CUSTOMERKEY', 'ITEMKEY', 'ITEMDESCRIPTION', 'QTYSHIPPED', 'SHIPDATE', 'BRANCH CODE', 'DIVISION CODE']
        ]
        data_json = headers.to_json(orient='index', date_format='iso')
        data_json = json.loads(data_json)
        batch_data = []
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        
        # check if sjc has more than 1 row
        # print("json 1", data_json["1"])
        sjc_idx = []
        batch_data = []
        for i in range (0, data_json.__len__()):
            str_key = str(i)
            value = dict()
            value["code"] = data_json[str_key]["DOCUMENTNUMBER"]
            value["sales_order_code"] = data_json[str_key]["INVNO"]
            delivery_date = dateutil.parser.parse(data_json[str_key]['SHIPDATE']).strftime("%Y-%m-%d %H:%M:%S")
            value["date"] = delivery_date
            value["customer_code"] = data_json[str_key]["CUSTOMERKEY"]
            value["import_date"] = today
            value["update_date"] = today
            value["import_by"] = user_id
            if data_json[str_key]["BRANCH CODE"]:
                try:
                    branch_id = self.branch_model.get_branches_by_code(self.cursor, code=data_json[str_key]["BRANCH CODE"])[0]
                    value['branch_id'] = branch_id['id']
                except:
                    value['branch_id'] = 1
            else:
                value['branch_id'] = 1
            if data_json[str_key]["DIVISION CODE"]:
                try:
                    division_id = self.division_model.get_division_by_code(
                        self.cursor, code=data_json[str_key]["DIVISION CODE"], _id=None
                    )[0]
                    value['division_id'] = division_id['id']
                except:
                    value['division_id'] = 1
            else:
                value['division_id'] = 1
            # product
            obj = dict()
            obj["quantity"] = data_json[str_key]["QTYSHIPPED"]
            obj["product_name"] = data_json[str_key]["ITEMDESCRIPTION"]
            obj["item_number"] = data_json[str_key]["ITEMKEY"]
            obj["brand_code"] = data_json[str_key]["DOCUMENTNUMBER"]
            obj["brand_name"] = ""
            obj["division_code"] = ""
            objs = []
            objs.append(obj)
            value["product"] = objs

            idx_merge = None
            if value["code"] not in sjc_idx:
                sjc_idx.append(value["code"])
                batch_data.append(value)
            else:
                for rec in batch_data:
                    if rec["code"] == value["code"]:
                        rec["product"] += objs       

        insert_ok = 0
        insert_fail = 0
        duplicate = []
        result = {
            "success":1,
            "data": None,
            "duplicates": None
        }
        for rec in batch_data:
            exist = None
            try:
                exist = self.cisangkan_packing_slip_model.get_packing_slip_by_id(self.cursor, rec['code'])
                if(exist):
                    insert_fail += 1
                    duplicate.append(rec)
                else:
                    self.cisangkan_packing_slip_model.import_insert(self.cursor, rec, 'code')
                    mysql.connection.commit()
                    insert_ok += 1
            except Exception as e:
                pass    
        
        if(insert_ok == batch_data.__len__()):
            try:
                self.cisangkan_packing_slip_model.insert_into_tbl_file_upload(self.cursor, filename_origin, today, user_id)
                mysql.connection.commit()
            except Exception as e:
                pass
        else:
            result["success"] = None
            result["duplicates"] = insert_fail
            result["data"] = duplicate
        
        return result

    
    def update_packing_slip_batch(self, batch_data: dict):
        insert_ok = 0
        result = False

        for rec in batch_data:
            exist = None
            try:
                self.cisangkan_packing_slip_model.import_insert(self.cursor, rec, 'code')
                mysql.connection.commit()
                insert_ok += 1
            except Exception as e:
                print("exception", e)
                pass    
        
        if(insert_ok == batch_data.__len__()):
            result = True           
        
        return result


    def update_customer_batch(self, batch_data: dict):
        insert_ok = 0
        result = False

        for rec in batch_data:
            exist = None
            try:
                self.cisangkan_customer_model.insert_update_batch(self.cursor, rec, 'code')
                mysql.connection.commit()
                insert_ok += 1
            except Exception as e:
                print("exception", e)
                pass
        
        if(insert_ok == batch_data.__len__()):
            result = True           
        
        return result


    def sterilize_input(self, input:'dict'):
        if(input['username'] == 'apps'):
            input.pop('username')
        if(input['api_key']):
            input.pop('api_key')
        if(input['username_code']):
            input['username'] = input['username_code']
            input.pop('username_code')
        return input
        

    def sterilize_input_div(self, input:'dict'):   
        try:
            del input['isLogistic']
        except: pass
        try:
            del input['isCollector']
        except: pass
        return input


    def import_customer_file_csv(self, filename: str, filename_origin: str, table: str, user_id: int):
        headers = ['Customer account', 'Name', 'Telephone', 'Contact Name', 'Contact Email', 'Contact Job',
                   'Contact Phone', 'Contact Mobile', 'Contact Notes', 'Address', 'Longitude', 'Latitude',
                   'Parent Customer Account', 'Category']
        
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        # 
        df = pd.read_csv(filename, sep=";", skiprows=0)
        headers = df[
            ['Customer account', 'Name', 'Telephone', 'Contact Name', 'Contact Email', 'Contact Job',
                        'Contact Phone', 'Contact Mobile', 'Contact Notes', 'Address', 'Longitude', 'Latitude',
                        'Parent Customer Account', 'Category']
        ]
        data_json = headers.to_json(orient='index', date_format='iso')
        data_json = json.loads(data_json)

        batch_data = []
        for i in range(0, data_json.__len__(), 1):
            counter = str(i)
            obj = dict()
            obj['code'] = data_json[counter]['Customer account']
            obj['name'] = data_json[counter]['Name']
            obj['phone'] = data_json[counter]['Telephone']
            obj['address'] = data_json[counter]['Address']
            obj['lat'] = data_json[counter]['Latitude']
            obj['lng'] = data_json[counter]['Longitude']
            obj['parent_code'] = data_json[counter]['Parent Customer Account']
            obj['is_branch'] = (1 if obj['parent_code'] != None else 0)
            obj['category'] = data_json[counter]['Category']        
            
            contact = dict()
            contact['name'] = data_json[counter]['Contact Name']
            contact['email'] = data_json[counter]['Contact Email']
            contact['job'] = data_json[counter]['Contact Job']
            contact['phone'] = data_json[counter]['Contact Phone']
            contact['mobile'] = data_json[counter]['Contact Mobile']

            contact['note'] = (data_json[counter]['Contact Notes'] if data_json[counter]['Contact Notes'] is not None else "" )
            
            contacts = []
            contacts.append(contact)

            obj['contacts'] = contacts

            batch_data.append(obj)


        user_id = current_identity.id

        insert_ok = 0
        insert_fail = 0
        duplicate = []
        result = {
            "success":1,
            "data": None,
            "duplicates": None
        }

        for rec in batch_data:
            exist = None
            try:
                exist = self.customer_model.get_customer_by_code(self.cursor, rec['code'])
                if(exist):
                    insert_fail += 1
                    duplicate.append(rec)
                else:
                    self.customer_model.insert_into_db(self.cursor, code=rec['code'], name=rec['name'], 
                                                        phone=rec['phone'], address=rec['address'],
                                                        lng=rec['lng'], lat=rec['lat'],
                                                        contacts=rec['contacts'], is_branch=rec['is_branch'],
                                                        parent_code=rec['parent_code'], create_date=today, 
                                                        update_date=today, is_approval=user_id,
                                                        approval_by=user_id, create_by=user_id,
                                                        category=rec['category'],
                                                        email = None, username = None, password = None, nfcid = None, business_activity = None
                                                        )
                    mysql.connection.commit()
                    insert_ok += 1
            except Exception as e:
                print("Exception ", e)
                pass    
        
        if(insert_ok == batch_data.__len__()):
            pass
        else:
            result["success"] = None
            result["duplicates"] = insert_fail
            result["data"] = duplicate

        return result
        

    def socketCheckCollector(self, user_id: int):
        select = "u.id, u.username, e.name, e.is_collector_only"
        join = """u INNER JOIN employee e ON employee_id = e.id """
        where="WHERE u.is_deleted = 0 AND u.id = '{0}' ".format(user_id)
        result = None
        try:
            result = self.cisangkan_user_model.m_get_custom_user_properties(self.cursor, select, join, where)[0]
            mysql.connection.commit()
        except Exception as e:
            raise e
        
        return result


    # fixing bug download xls, filter user more than 1
    def getUsernameById(self, user_id: int):
        um = UserModel()
        user_data = um.get_user_by_id(self.cursor, user_id)
        return user_data[0]["username"]

    def get_visit_category_sales(self, users:list, start_date: str, end_date: str):
        select = """ vp.create_by, u.username, vp.category_visit, count(vp.category_visit) as count """
        join= """ as vp INNER JOIN users as u ON vp.create_by=u.id """
        where = """ WHERE (vp.create_date>='{0}' AND vp.create_date<='{1}') """.format(start_date, end_date)
        where += """ AND vp.create_by in ({0}) """.format(", ".join(str(x) for x in users))
        order = """ GROUP BY vp.create_by, vp.category_visit """
        order += """ ORDER BY vp.create_by ASC """
        
        print("params user_ids : ", users)

        result = self.cisangkan_visit_plan_summary_model.get_performance_visit_summary(
            self.cursor, select, join, where, order
        )

        datas = []
        if result:
            idx = []
            for i in range(0, result.__len__(), 1):
                id = result[i]['create_by']

                obj = {}
                obj_data = {}
                obj_data_category = {}

                obj_data['username'] = result[i]['username']
                catStr = str(result[i]['category_visit']).lower()
                key_category_visit = catStr.replace(' ', '_')
                obj_data_category[key_category_visit] = result[i]['count']
                obj_data['category'] = obj_data_category

                obj[id] = obj_data

                merged = False
                if id in idx:
                    merged = True

                if merged:
                    for j in range(0, datas.__len__()):
                        for key, val in datas[j].items():
                            if id == key:
                                for k, v in val.items():
                                    if k == 'category':
                                        v.update(obj_data_category)

                else:
                    idx.append(id)
                    datas.append(obj)

        return datas


    def get_collect_method_collector(self, start_date: str, end_date: str):
        result = "collect method"
        return result
    
    def get_export_total_online_user(self, page: int, limit: int, start_date:str, end_date:str):
        
        result_data = {}
        cycle = {}
        data = []
        start = page * limit - limit
   
        order = """ORDER BY usr.username"""
        where = "WHERE vp.date >= '"+start_date+"' AND vp.date <= '"+end_date+"' GROUP BY usr.username"
        
        #where = """WHERE vp.date >= 'start_date' AND vp.date <= 'end_date' GROUP BY usr.username"""
        
        select = "vp.user_id, usr.username, emp.name, COUNT(DISTINCT(vp.date)) total_on"
        select_count = ""
        join = """ as vp JOIN `users` as usr ON vp.user_id = usr.id 
        JOIN `employee` as emp ON emp.id = usr.employee_id"""
        
     
        total_online_data = self.cisangkan_total_online.get_total_user_online(
            self.cursor, select=select, join=join, where=where, order=order
        )
                
        output = BytesIO()    
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Total Online')
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
        
        data_rows = 1
        for item in total_online_data :
            worksheet.write(data_rows, 0, data_rows)
            worksheet.write(data_rows, 1, item['user_id'])
            worksheet.write(data_rows, 2, item['username'])
            worksheet.write(data_rows, 3, item['name'])
            worksheet.write(data_rows, 4, item['total_on'])           
            data_rows += 1
            
        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output
       
        return result_data
    
    def get_export_total_start_user(self, page: int, limit: int, start_date:str, end_date:str):
        result_data = {}
        cycle = {}
        data = []
        start = page * limit - limit
        
        order = """ORDER BY usr.username"""
        where = "WHERE sa.tap_nfc_date >= '"+start_date+"' AND sa.tap_nfc_date <= '"+end_date+"' AND sa.tap_nfc_type LIKE '%START' GROUP BY sa.user_id"
        #where = """WHERE sa.tap_nfc_date >= '2019-12-31' AND sa.tap_nfc_date <= '2020-11-01' AND sa.tap_nfc_type LIKE '%START' GROUP BY sa.user_id"""
        select = "sa.user_id, usr.username, emp.name, COUNT(DISTINCT(DATE(sa.tap_nfc_date))) total_start"
        join = """ as sa JOIN `users` as usr ON sa.user_id = usr.id 
        JOIN `employee` as emp ON emp.id = usr.employee_id"""
     
        total_start_data = self.cisangkan_total_start.get_total_user_start(
            self.cursor, select=select, join=join, where=where, order=order
        )
                
        output = BytesIO()    
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Total Start')
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
        worksheet.write('E1', 'Total Start', header_format)
        
        data_rows = 1
        for item in total_start_data :
            worksheet.write(data_rows, 0, data_rows)
            worksheet.write(data_rows, 1, item['user_id'])
            worksheet.write(data_rows, 2, item['username'])
            worksheet.write(data_rows, 3, item['name'])
            worksheet.write(data_rows, 4, item['total_start'])           
            data_rows += 1
            
        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output
       
        return result_data
    
    def get_export_total_stop_user(self, page: int, limit: int, start_date:str, end_date:str):
        result_data = {}
        cycle = {}
        data = []
        start = page * limit - limit
        
        order = """ORDER BY usr.username"""
        where = "WHERE sa.tap_nfc_date >= '"+start_date+"' AND sa.tap_nfc_date <= '"+end_date+"' AND sa.tap_nfc_type LIKE '%STOP' GROUP BY sa.user_id"
        select = "sa.user_id, usr.username, emp.name, COUNT(DISTINCT(DATE(sa.tap_nfc_date))) total_stop"
        join = """ as sa JOIN `users` as usr ON sa.user_id = usr.id 
        JOIN `employee` as emp ON emp.id = usr.employee_id"""
     
        total_stop_data = self.cisangkan_total_stop.get_total_user_stop(
            self.cursor, select=select, join=join, where=where, order=order
        )
                
        output = BytesIO()    
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Total Stop')
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
        worksheet.write('E1', 'Total Stop', header_format)
        
        data_rows = 1
        for item in total_stop_data :
            worksheet.write(data_rows, 0, data_rows)
            worksheet.write(data_rows, 1, item['user_id'])
            worksheet.write(data_rows, 2, item['username'])
            worksheet.write(data_rows, 3, item['name'])
            worksheet.write(data_rows, 4, item['total_stop'])           
            data_rows += 1
            
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
        #where = """WHERE sa.tap_nfc_type = 'IN' AND DATE(sa.tap_nfc_date) = '2021-02-24'"""
        select = "usr.username, emp.name, usrgrp.group_name, cs.name AS location, sa.tap_nfc_date AS check_in_date"
        join = """ as sa JOIN `users` as usr ON sa.user_id = usr.id 
        JOIN `customer` as cs ON cs.code = sa.nfc_code 
        JOIN `employee` as emp ON usr.employee_id = emp.id
        JOIN `user_groups` as usrgrp ON usr.user_group_id = usrgrp.id"""
     
        total_check_in_data = self.cisangkan_total_check_in.get_total_user_check_in(
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
     
        total_stop_data = self.cisangkan_total_stop.get_total_user_stop(
            self.cursor, select=select, join=join, where=where, order=order
        )
        # end query total stop user
        # query for total start user
        order_start = """ORDER BY usr.username"""
        where_start = "WHERE sa.tap_nfc_date >= '"+start_date+"' AND sa.tap_nfc_date <= '"+end_date+"' AND sa.tap_nfc_type LIKE '%START' GROUP BY sa.user_id"
        select_start = "sa.user_id, usr.username, emp.name, COUNT(DISTINCT(DATE(sa.tap_nfc_date))) total_start"
        join_start = """ as sa JOIN `users` as usr ON sa.user_id = usr.id 
        JOIN `employee` as emp ON emp.id = usr.employee_id"""
     
        total_start_data = self.cisangkan_total_start.get_total_user_start(
            self.cursor, select=select_start, join=join_start, where=where_start, order=order_start
        )
        # end query total start user
        #query for total online user
        order_online = """ORDER BY usr.username"""
        where_online = "WHERE vp.date >= '"+start_date+"' AND vp.date <= '"+end_date+"' GROUP BY usr.username"        
        select_online = "vp.user_id, usr.username, emp.name, COUNT(DISTINCT(vp.date)) total_on"
        join_online = """ as vp JOIN `users` as usr ON vp.user_id = usr.id 
        JOIN `employee` as emp ON emp.id = usr.employee_id"""
        total_online_data = self.cisangkan_total_online.get_total_user_online(
            self.cursor, select=select_online, join=join_online, where=where_online, order=order_online
        )
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
        
    def get_absence_daily_user(self, page: int, limit: int, search: str, column: str, direction: str, dropdown: bool, start_date:str):
        
        absence = {}
        data = []
        start = page * limit - limit
        date = datetime.now()
        date_now = date.strftime("%y/%m/%d")
        
        order = """ ORDER BY usr.username ASC """
        where = " WHERE DATE(vp.date) = '"+date_now+"' GROUP BY sa.user_id "
        
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search :
            where = " WHERE DATE(vp.date) = '"+date_now+"' AND emp.name LIKE '%{0}%' GROUP BY sa.user_id ".format(search)
        if start_date : 
            where = " WHERE DATE(vp.date) = '"+start_date+"' GROUP BY sa.user_id "
        if search and start_date :
            where = " WHERE DATE(vp.date) = '"+start_date+"' AND emp.name LIKE '%{0}%' GROUP BY sa.user_id ".format(search)   
            
        select = " sa.user_id, usr.username, emp.name, COUNT(DISTINCT(vp.date)) as total_online, b.total_start, c.total_stop "
        join = """ as sa 
        LEFT JOIN(SELECT COUNT(DISTINCT(DATE(tap_nfc_date))) total_start, user_id FROM `sales_activity` WHERE tap_nfc_type LIKE '%START' AND DATE(tap_nfc_date) = '""" +start_date+"""' GROUP BY user_id) b ON sa.user_id = b.user_id
        LEFT JOIN(SELECT COUNT(DISTINCT(DATE(tap_nfc_date))) total_stop, user_id FROM `sales_activity` WHERE tap_nfc_type LIKE '%STOP' AND DATE(tap_nfc_date) = '""" +start_date+"""' GROUP BY user_id) c ON sa.user_id = c.user_id
        JOIN `users` as usr ON sa.user_id=usr.id 
        JOIN `employee` as emp ON emp.id=usr.employee_id
        JOIN `visit_plan` as vp ON vp.user_id = usr.id
        """
        
        #get data params
        absence_user_data = self.cisangkan_total_absence_daily.get_all_absences(self.cursor, select=select, join=join, where=where, order=order, start=start,  limit=limit)
        
        #count
        #count = self.cisangkan_total_absence_daily.get_count_all_absences(self.cursor, join=join, where=where)
        count = len(absence_user_data)
        
        #count filtering
        #count_filter = self.cisangkan_total_absence_daily.get_count_all_absences(self.cursor, join=join, where=where)
        count_filter = len(absence_user_data)
        

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
        #print(absence)
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
        
        