from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON

from rest.configuration import Base


class EmployeeModel(Base):
    __tablename__ = 'employee'

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    name = Column(VARCHAR)
    nip = Column(VARCHAR)
    email = Column(VARCHAR)
    phone = Column(VARCHAR)
    job_function = Column(VARCHAR)
    is_supervisor_sales = Column(Integer)
    is_supervisor_logistic = Column(Integer)
    is_collector_only = Column(Integer)
    is_can_collect = Column(Integer)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    is_approval = Column(Integer)
    approval_by = Column(BigInteger)
    is_delete_approval = Column(Integer)
    is_delete_approval_by = Column(Integer)
    create_by = Column(BigInteger)
    edit_data = Column(JSON)
    is_deleted = Column(Integer)
    is_delete_count = Column(BigInteger)

    def __init__(self, employee_model=None):
        if employee_model is not None:
            self.id = employee_model.id
            self.name = employee_model.name
            self.nip = employee_model.nip
            self.email = employee_model.email
            self.phone = employee_model.phone
            self.job_function = employee_model.job_function
            self.is_supervisor_sales = employee_model.is_supervisor_sales
            self.is_supervisor_logistic = employee_model.is_supervisor_logistic
            self.is_collector_only = employee_model.is_collector_only
            self.is_can_collect = employee_model.is_can_collect
            self.create_date = employee_model.create_date
            self.update_date = employee_model.update_date
            self.is_approval = employee_model.is_approval
            self.approval_by = employee_model.approval_by
            self.is_delete_approval = employee_model.is_delete_approval
            self.is_delete_approval_by = employee_model.is_delete_approval_by
            self.create_by = employee_model.create_by
            self.edit_data = employee_model.edit_data
            self.is_deleted = employee_model.is_deleted
            self.is_delete_count = employee_model.is_delete_count
