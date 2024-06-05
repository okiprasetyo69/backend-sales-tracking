from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, JSON, Integer, Text, Float, Time

from rest.configuration import Base


class CustomerModel(Base):
    __tablename__ = 'customer'

    code = Column(VARCHAR, primary_key=True)
    email = Column(VARCHAR)
    phone = Column(VARCHAR)
    address = Column(Text)
    lat = Column(Float)
    lng = Column(Float)
    username = Column(VARCHAR)
    password = Column(VARCHAR)
    nfcid = Column(VARCHAR)
    contacts = Column(JSON)
    business_activity = Column(JSON)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    is_branch = Column(Integer)
    parent_code = Column(VARCHAR)
    import_date = Column(TIMESTAMP)
    import_by = Column(BigInteger)
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
            self.code = branches_model.code
            self.name = branches_model.name
            self.email = branches_model.email
            self.phone = branches_model.phone
            self.address = branches_model.address
            self.lng = branches_model.lng
            self.lat = branches_model.lat
            self.username = branches_model.username
            self.password = branches_model.password
            self.nfcid = branches_model.nfcid
            self.contacts = branches_model.contacts
            self.business_activity = branches_model.business_activity
            self.create_date = branches_model.create_date
            self.update_date = branches_model.update_date
            self.is_branch = branches_model.is_branch
            self.parent_code = branches_model.parent_code
            self.import_date = branches_model.import_date
            self.import_by = branches_model.import_by
            self.is_approval = branches_model.is_approval
            self.approval_by = branches_model.approval_by
            self.is_delete_approval = branches_model.is_delete_approval
            self.is_delete_approval_by = branches_model.is_delete_approval_by
            self.create_by = branches_model.create_by
            self.edit_data = branches_model.edit_data
            self.is_deleted = branches_model.is_deleted
            self.is_delete_count = branches_model.is_delete_count
