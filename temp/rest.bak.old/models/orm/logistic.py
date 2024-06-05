from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON, Text

from rest.configuration import Base


class PackingSlipModel(Base):
    __tablename__ = 'packing_slip'

    code = Column(VARCHAR, primary_key=True)
    date = Column(TIMESTAMP)
    sales_order_code = Column(VARCHAR)
    product = Column(JSON)
    customer_code = Column(VARCHAR)
    notes = Column(Text)
    branch_id = Column(BigInteger)
    division_id = Column(BigInteger)
    import_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    import_by = Column(BigInteger)

    def __init__(self, logistic_model=None):
        if logistic_model is not None:
            self.code = logistic_model.code
            self.date = logistic_model.date
            self.sales_order_code = logistic_model.sales_order_code
            self.product = logistic_model.product
            self.customer_code = logistic_model.customer_code
            self.notes = logistic_model.notes
            self.branch_id = logistic_model.branch_id
            self.division_id = logistic_model.division_id
            self.import_date = logistic_model.import_date
            self.update_date = logistic_model.update_date
            self.import_by = logistic_model.import_by
