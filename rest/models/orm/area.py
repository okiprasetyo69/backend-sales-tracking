from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, JSON, Integer, Text

from rest.configuration import Base


class AreaModel(Base):
    __tablename__ = 'area'

    id = Column(BigInteger, primary_key=True)
    name = Column(VARCHAR)
    marker_type = Column(VARCHAR)
    marker_color = Column(VARCHAR)
    markers = Column(JSON)
    description = Column(Text)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    is_approval = Column(Integer)
    approval_by = Column(BigInteger)
    is_delete_approval = Column(Integer)
    is_delete_approval_by = Column(BigInteger)
    create_by = Column(BigInteger)
    edit_data = Column(JSON)
    is_deleted = Column(Integer)

    def __init__(self, area_model=None):
        if area_model is not None:
            self.id = area_model.id
            self.name = area_model.name
            self.marker_type = area_model.marker_type
            self.marker_color = area_model.marker_color
            self.markers = area_model.markers
            self.description = area_model.description
            self.create_date = area_model.create_date
            self.update_date = area_model.update_date
            self.is_approval = area_model.is_approval
            self.approval_by = area_model.approval_by
            self.is_delete_approval = area_model.is_delete_approval
            self.is_delete_approval_by = area_model.is_delete_approval_by
            self.create_by = area_model.create_by
            self.edit_data = area_model.edit_data
            self.is_deleted = area_model.is_deleted
