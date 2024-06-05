from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON, Text, Float

from rest.configuration import Base


class CompanyModel(Base):
    __tablename__ = 'company'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(VARCHAR)
    branch_code = Column(VARCHAR)
    phone = Column(VARCHAR)
    email = Column(VARCHAR)
    address = Column(Text)
    lng = Column(Float)
    lat = Column(Float)
    working_day_start = Column(VARCHAR)
    working_day_end = Column(VARCHAR)
    working_hour_start = Column(TIMESTAMP)
    working_hour_end = Column(TIMESTAMP)
    nfcid = Column(VARCHAR)
    area_id = Column(BigInteger)
    division_id = Column(JSON)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    is_approval = Column(Integer)
    approval_by = Column(BigInteger)
    create_by = Column(BigInteger)
    edit_data = Column(JSON)
    is_deleted = Column(Integer)

    def __init__(self, company_model=None):
        if company_model is not None:
            self.id = company_model.id
            self.name = company_model.name
            self.branch_code = company_model.branch_code
            self.phone = company_model.phone
            self.email = company_model.email
            self.address = company_model.address
            self.lng = company_model.lng
            self.lat = company_model.lat
            self.working_day_start = company_model.working_day_start
            self.working_day_end = company_model.working_day_end
            self.working_hour_start = company_model.working_hour_start
            self.working_hour_end = company_model.working_hour_end
            self.nfcid = company_model.nfcid
            self.area_id = company_model.area_id
            self.division_id = company_model.division_id
            self.create_date = company_model.create_date
            self.update_date = company_model.update_date
            self.is_approval = company_model.is_approval
            self.approval_by = company_model.approval_by
            self.create_by = company_model.create_by
            self.edit_data = company_model.edit_data
            self.is_deleted = company_model.is_deleted


class GeneralModel(Base):
    __tablename__ = 'setting_general'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    is_using_nfc = Column(Integer)
    alert_wrong_route = Column(Integer)
    alert_break_time = Column(Integer)
    max_length_visit_time = Column(Integer)
    max_length_unloading = Column(Integer)
    max_idle_time = Column(Integer)
    max_geofence_area = Column(Integer)
    activate_permission = Column(Integer)
    max_breaktime_time = Column(Integer)
    max_order_sales_to_sales_order_time_reguler = Column(Integer)
    max_sales_order_to_packing_slip_time_reguler = Column(Integer)
    max_order_sales_to_sales_order_time_special = Column(Integer)
    max_sales_order_to_packing_slip_time_special = Column(Integer)
    invoicing_time = Column(Integer)
    visit_cycle_start = Column(TIMESTAMP)
    logo_image = Column(Text)
    blacklist_apps = Column(Text)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    def __init__(self, general_model=None):
        if general_model is not None:
            self.id = general_model.id
            self.is_using_nfc = general_model.is_using_nfc
            self.alert_wrong_route = general_model.alert_wrong_route
            self.alert_break_time = general_model.alert_break_time
            self.max_length_visit_time = general_model.max_length_visit_time
            self.max_length_unloading = general_model.max_length_unloading
            self.max_idle_time = general_model.max_idle_time
            self.max_geofence_area = general_model.max_geofence_area
            self.activate_permission = general_model.activate_permission
            self.max_breaktime_time = general_model.max_breaktime_time
            self.max_order_sales_to_sales_order_time_reguler = general_model.max_order_sales_to_sales_order_time_reguler
            self.max_sales_order_to_packing_slip_time_reguler = general_model.max_sales_order_to_packing_slip_time_reguler
            self.max_order_sales_to_sales_order_time_special = general_model.max_order_sales_to_sales_order_time_special
            self.max_sales_order_to_packing_slip_time_special = general_model.max_sales_order_to_packing_slip_time_special
            self.invoicing_time = general_model.invoicing_time
            self.visit_cycle_start = general_model.visit_cycle_start
            self.logo_image = general_model.logo_image
            self.blacklist_apps = general_model.blacklist_apps
            self.create_date = general_model.create_date
            self.update_date = general_model.update_date


class NotifModel(Base):
    __tablename__ = 'setting_notifications'

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    activity_name = Column(VARCHAR)
    activity_slug = Column(VARCHAR)
    category = Column(VARCHAR)
    receive_email_notification = Column(Integer)
    receive_app_notification = Column(Integer)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    is_approval = Column(Integer)
    approval_by = Column(BigInteger)
    create_by = Column(BigInteger)
    edit_data = Column(JSON)
    is_deleted = Column(Integer)

    def __init__(self, notif_model=None):
        if notif_model is not None:
            self.id = notif_model.id
            self.activity_name = notif_model.activity_name
            self.activity_slug = notif_model.activity_slug
            self.category = notif_model.category
            self.receive_email = notif_model.receive_email
            self.receive_app_notification = notif_model.receive_app_notification
            self.create_date = notif_model.create_date
            self.update_date = notif_model.update_date
            self.is_approval = notif_model.is_approval
            self.approval_by = notif_model.approval_by
            self.create_by = notif_model.create_by
            self.edit_data = notif_model.edit_data
            self.is_deleted = notif_model.is_deleted
