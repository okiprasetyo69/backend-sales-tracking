from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON, Text, Float, Date

from rest.configuration import Base


class RequestOrderModel(Base):
    __tablename__ = 'request_orders'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(VARCHAR)
    date = Column(TIMESTAMP)
    user_id = Column(BigInteger)
    customer_code = Column(VARCHAR)
    is_special_order = Column(Integer)
    contacts = Column(VARCHAR)
    delivery_address = Column(Text)
    lng = Column(Float)
    lat = Column(Float)
    notes = Column(Text)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    def __init__(self, request_order_model=None):
        if request_order_model is not None:
            self.id = request_order_model.id
            self.code = request_order_model.code
            self.date = request_order_model.date
            self.user_id = request_order_model.user_id
            self.customer_code = request_order_model.customer_code
            self.is_special_order = request_order_model.is_special_order
            self.contacts = request_order_model.contacts
            self.delivery_address = request_order_model.delivery_address
            self.lng = request_order_model.lng
            self.lat = request_order_model.lat
            self.notes = request_order_model.notes
            self.create_date = request_order_model.create_date
            self.update_date = request_order_model.update_date


class RequestOrderProductModel(Base):
    __tablename__ = 'request_orders_product'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_orders_id = Column(BigInteger)
    item_code = Column(VARCHAR)
    item_name = Column(VARCHAR)
    qty = Column(Integer)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    def __init__(self, request_order_product_model=None):
        if request_order_product_model is not None:
            self.id = request_order_product_model.id
            self.request_orders_id = request_order_product_model.request_orders_id
            self.item_code = request_order_product_model.item_code
            self.item_name = request_order_product_model.item_name
            self.qty = request_order_product_model.qty
            self.create_date = request_order_product_model.create_date
            self.update_date = request_order_product_model.update_date


class RequestOrderImageModel(Base):
    __tablename__ = 'request_orders_image'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_order_id = Column(BigInteger)
    filename = Column(VARCHAR)
    file = Column(Text)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    def __init__(self, request_order_image_model=None):
        if request_order_image_model is not None:
            self.id = request_order_image_model.id
            self.request_orders_id = request_order_image_model.request_orders_id
            self.filename = request_order_image_model.filename
            self.file = request_order_image_model.file
            self.create_date = request_order_image_model.create_date


class SalesOrderModel(Base):
    __tablename__ = 'sales_orders'

    code = Column(VARCHAR)
    create_date = Column(TIMESTAMP)
    customer_code = Column(VARCHAR)
    customer_branch_code = Column(VARCHAR)
    status = Column(VARCHAR)
    notes = Column(Text)
    packing_slip_code = Column(VARCHAR)
    packing_slip_date = Column(Date)
    invoice_code = Column(VARCHAR)
    invoice_date = Column(Date)
    product = Column(JSON)
    branch_id = Column(BigInteger)
    division_id = Column(BigInteger)
    division_code = Column(VARCHAR)
    user_code = Column(VARCHAR)
    cycle_number = Column(VARCHAR)
    sales_group = Column(VARCHAR)
    import_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    import_by = Column(BigInteger)

    def __init__(self, sales_order_model=None):
        if sales_order_model is not None:
            self.code = sales_order_model.code
            self.create_date = sales_order_model.create_date
            self.customer_code = sales_order_model.customer_code
            self.customer_branch_code = sales_order_model.customer_branch_code
            self.status = sales_order_model.status
            self.notes = sales_order_model.notes
            self.packing_slip_code = sales_order_model.packing_slip_code
            self.packing_slip_date = sales_order_model.packing_slip_date
            self.invoice_code = sales_order_model.invoice_code
            self.invoice_date = sales_order_model.invoice_date
            self.product = sales_order_model.product
            self.branch_id = sales_order_model.branch_id
            self.division_id = sales_order_model.division_id
            self.division_code = sales_order_model.division_code
            self.user_code = sales_order_model.user_code
            self.cycle_number = sales_order_model.cycle_number
            self.sales_group = sales_order_model.sales_group
            self.import_date = sales_order_model.import_date
            self.update_date = sales_order_model.update_date
            self.import_by = sales_order_model.import_by


class SalesPaymentModel(Base):
    __tablename__ = 'sales_payment'

    code = Column(VARCHAR, primary_key=True)
    invoice_date = Column(TIMESTAMP)
    invoice_due_date = Column(TIMESTAMP)
    invoice_code = Column(VARCHAR)
    status = Column(VARCHAR)
    notes = Column(Text)
    packing_slip_code = Column(VARCHAR)
    packing_slip_date = Column(Date)
    sales_order_code = Column(VARCHAR)
    sales_order_date = Column(TIMESTAMP)
    payment_date = Column(TIMESTAMP)
    payment_due_date = Column(TIMESTAMP)
    invoice_amount = Column(BigInteger)
    payment_amount = Column(BigInteger)
    product = Column(JSON)
    branch_id = Column(BigInteger)
    division_id = Column(BigInteger)
    import_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    import_by = Column(BigInteger)

    def __init__(self, sales_payment_model=None):
        if sales_payment_model is not None:
            self.code = sales_payment_model.code
            self.invoice_date = sales_payment_model.invoice_date
            self.invoice_due_date = sales_payment_model.invoice_due_date
            self.invoice_code = sales_payment_model.invoice_code
            self.status = sales_payment_model.status
            self.notes = sales_payment_model.notes
            self.packing_slip_code = sales_payment_model.packing_slip_code
            self.packing_slip_date = sales_payment_model.packing_slip_date
            self.packing_slip_code = sales_payment_model.packing_slip_code
            self.packing_slip_date = sales_payment_model.packing_slip_date
            self.payment_date = sales_payment_model.payment_date
            self.payment_due_date = sales_payment_model.payment_due_date
            self.invoice_amount = sales_payment_model.invoice_amount
            self.payment_amount = sales_payment_model.payment_amount
            self.product = sales_payment_model.product
            self.branch_id = sales_payment_model.branch_id
            self.import_date = sales_payment_model.import_date
            self.update_date = sales_payment_model.update_date
            self.import_by = sales_payment_model.import_by


class SalesPaymentMobileModel(Base):
    __tablename__ = 'sales_payment_mobile'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(VARCHAR)
    visit_plan_id = Column(BigInteger)
    customer_code = Column(VARCHAR)
    invoice = Column(JSON)
    invoice_amount = Column(BigInteger)
    payment_amount = Column(Integer)
    payment_date = Column(TIMESTAMP)
    receipt_code = Column(VARCHAR)
    receipt_printed = Column(Integer)
    receipt_reprint = Column(Integer)
    payment_method = Column(VARCHAR)
    payment_info = Column(JSON)
    is_confirm = Column(Integer)
    is_confirm_cancel = Column(Integer)
    is_canceled = Column(Integer)
    create_by = Column(BigInteger)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    def __init__(self, sales_payment_model=None):
        if sales_payment_model is not None:
            self.id = sales_payment_model.id
            self.code = sales_payment_model.code
            self.visit_plan_id = sales_payment_model.visit_plan_id
            self.customer_code = sales_payment_model.customer_code
            self.invoice = sales_payment_model.invoice
            self.invoice_amount = sales_payment_model.invoice_amount
            self.payment_amount = sales_payment_model.payment_amount
            self.payment_date = sales_payment_model.payment_date
            self.receipt_code = sales_payment_model.receipt_code
            self.receipt_printed = sales_payment_model.receipt_printed
            self.receipt_reprint = sales_payment_model.receipt_reprint
            self.payment_method = sales_payment_model.payment_method
            self.payment_info = sales_payment_model.payment_info
            self.is_confirm = sales_payment_model.is_confirm
            self.is_confirm_cancel = sales_payment_model.is_confirm_cancel
            self.is_canceled = sales_payment_model.is_canceled
            self.create_by = sales_payment_model.create_by
            self.create_date = sales_payment_model.create_date
            self.update_date = sales_payment_model.update_date
