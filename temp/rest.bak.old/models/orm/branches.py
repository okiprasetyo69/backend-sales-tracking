from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, JSON, Integer, Text, Float, Time

from rest.configuration import Base


class BranchesModel(Base):
    __tablename__ = 'branches'

    id = Column(BigInteger, primary_key=True)
    name = Column(VARCHAR)
    branch_code = Column(VARCHAR)
    phone = Column(VARCHAR)
    email = Column(VARCHAR)
    address = Column(Text)
    lat = Column(Float)
    lng = Column(Float)
    working_day_start = Column(VARCHAR)
    working_day_end = Column(VARCHAR)
    working_hour_start = Column(Time)
    working_hour_end = Column(Time)
    nfcid = Column(VARCHAR)
    area_id = Column(Integer)
    division_id = Column(JSON)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    is_approval = Column(Integer)
    approval_by = Column(BigInteger)
    is_delete_approval = Column(Integer)
    is_delete_approval_by = Column(BigInteger)
    create_by = Column(BigInteger)
    edit_data = Column(JSON)
    is_deleted = Column(Integer)
    is_delete_count = Column(BigInteger)

    def __init__(self, branches_model=None):
        if branches_model is not None:
            self.id = branches_model.id
            self.name = branches_model.name
            self.branch_code = branches_model.branch_code
            self.phone = branches_model.phone
            self.email = branches_model.email
            self.address = branches_model.address
            self.lat = branches_model.lat
            self.lng = branches_model.lng
            self.working_day_start = branches_model.working_day_start
            self.working_day_end = branches_model.working_day_end
            self.working_hour_start = branches_model.working_hour_start
            self.working_hour_end = branches_model.working_hour_end
            self.nfcid = branches_model.nfcid
            self.area_id = branches_model.area_id
            self.division_id = branches_model.division_id
            self.create_date = branches_model.create_date
            self.update_date = branches_model.update_date
            self.is_approval = branches_model.is_approval
            self.is_delete_approval = branches_model.is_delete_approval
            self.is_delete_approval_by = branches_model.is_delete_approval_by
            self.create_by = branches_model.create_by
            self.edit_data = branches_model.edit_data
            self.is_deleted = branches_model.is_deleted
            self.is_delete_count = branches_model.is_delete_count
