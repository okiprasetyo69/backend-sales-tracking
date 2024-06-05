from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

from rest.configuration import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(VARCHAR)
    password = Column(VARCHAR)
    email = Column(VARCHAR)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    permissions = Column(JSON)
    branch_privilege_id = Column(JSON)
    division_privilege_id = Column(JSON)
    customer_id = Column(JSON)
    employee_id = Column(BigInteger, ForeignKey("employee.id"))
    mobile_device_id = Column(BigInteger)
    mobile_no_id = Column(BigInteger)
    printer_device_id = Column(BigInteger)
    area_id = Column(BigInteger)
    branch_id = Column(BigInteger, ForeignKey("branches.id"))
    user_group_id = Column(BigInteger)
    division_id = Column(BigInteger, ForeignKey("divisions.id"))
    handle_division_id = Column(JSON)
    max_account_usages = Column(Integer)
    is_super_admin = Column(Integer)
    is_approval = Column(Integer)
    approval_by = Column(BigInteger)
    is_delete_approval = Column(Integer)
    is_delete_approval_by = Column(BigInteger)
    create_by = Column(BigInteger)
    edit_data = Column(JSON)
    is_deleted = Column(Integer)
    is_delete_count = Column(BigInteger)

    employee = relationship("EmployeeModel", foreign_keys=[employee_id])
    division = relationship("DivisionModel", foreign_keys=[division_id])
    branch = relationship("BranchesModel", foreign_keys=[branch_id])

    def __init__(self, user_model=None):
        if user_model is not None:
            self.id = user_model.id
            self.username = user_model.username
            self.password = user_model.password
            self.email = user_model.email
            self.create_date = user_model.create_date
            self.update_date = user_model.update_date
            self.permissions = user_model.permissions
            self.branch_privilege_id = user_model.branch_privilege_id
            self.division_privilege_id = user_model.division_privilege_id
            self.customer_id = user_model.customer_id
            self.employee_id = user_model.employee_id
            self.mobile_device_id = user_model.mobile_device_id
            self.mobile_no_id = user_model.mobile_no_id
            self.printer_device_id = user_model.printer_device_id
            self.area_id = user_model.area_id
            self.branch_id = user_model.branch_id
            self.user_group_id = user_model.user_group_id
            self.division_id = user_model.division_id
            self.handle_division_id = user_model.handle_division_id
            self.max_account_usages = user_model.max_account_usages
            self.is_super_admin = user_model.is_super_admin
            self.is_approval = user_model.is_approval
            self.approval_by = user_model.approval_by
            self.is_delete_approval = user_model.is_delete_approval
            self.is_delete_approval_by = user_model.is_delete_approval_by
            self.create_by = user_model.create_by
            self.edit_data = user_model.edit_data
            self.is_deleted = user_model.is_deleted
            self.is_delete_count = user_model.is_delete_count
            self.employee = user_model.employee


class DeviceTokenModel(Base):
    __tablename__ = "device_token"

    user_id = Column(BigInteger, primary_key=True)
    update_date = Column(TIMESTAMP)
    token = Column(Text)

    def __init__(self, device_token_model=None):
        if device_token_model is not None:
            self.user_id = device_token_model.user_id
            self.update_date = device_token_model.update_date
            self.token = device_token_model.token


class UserLoginStatusModel(Base):
    __tablename__ = "user_login"

    username = Column(VARCHAR, primary_key=True)
    type = Column(VARCHAR)
    login_date = Column(TIMESTAMP)

    def __init__(self, user_login_status_model=None):
        if user_login_status_model is not None:
            self.id = user_login_status_model.id
            self.type = user_login_status_model.type
            self.login_date = user_login_status_model.login_date
