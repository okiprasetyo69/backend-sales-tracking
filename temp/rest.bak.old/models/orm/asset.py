from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, JSON, Integer, Text

from rest.configuration import Base


class AssetModel(Base):
    __tablename__ = 'assets'

    id = Column(BigInteger, primary_key=True)
    code = Column(VARCHAR)
    device_code = Column(VARCHAR)
    name = Column(VARCHAR)
    asset_type_id = Column(Integer)
    asset_status = Column(VARCHAR)
    isUsed = Column(Integer)
    notes = Column(Text)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    is_approval = Column(Integer)
    approval_by = Column(BigInteger)
    is_delete_approval = Column(Integer)
    is_delete_approval_by = Column(BigInteger)
    create_by = Column(BigInteger)
    edit_data = Column(JSON)
    is_deleted = Column(Integer)

    def __init__(self, asset_model=None):
        if asset_model is not None:
            self.id = asset_model.id
            self.code = asset_model.code
            self.device_code = asset_model.device_code
            self.name = asset_model.name
            self.asset_type_id = asset_model.asset_type_id
            self.asset_status = asset_model.asset_status
            self.isUsed = asset_model.isUsed
            self.notes = asset_model.notes
            self.create_date = asset_model.create_date
            self.update_date = asset_model.update_date
            self.is_approval = asset_model.is_approval
            self.approval_by = asset_model.approval_by
            self.is_delete_approval = asset_model.is_delete_approval
            self.is_delete_approval_by = asset_model.is_delete_approval_by
            self.create_by = asset_model.create_by
            self.edit_data = asset_model.edit_data
            self.is_deleted = asset_model.is_deleted


class AssetTypeModel(Base):
    __tablename__ = 'asset_types'

    id = Column(BigInteger, primary_key=True)
    code = Column(VARCHAR)
    name = Column(VARCHAR)
    notes = Column(Text)
    isActive = Column(Integer)
    qty_on_hand = Column(Integer)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    tag = Column(VARCHAR)

    def __init__(self, asset_model=None):
        if asset_model is not None:
            self.id = asset_model.id
            self.code = asset_model.code
            self.name = asset_model.name
            self.notes = asset_model.notes
            self.isActive = asset_model.isActive
            self.qty_on_hand = asset_model.qty_on_hand
            self.create_date = asset_model.create_date
            self.update_date = asset_model.update_date
            self.tag = asset_model.tag
