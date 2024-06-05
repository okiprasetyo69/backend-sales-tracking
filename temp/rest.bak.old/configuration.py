import os

from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# get absolute path static directory in root project
upload_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads'))

# TODO: Logging formatter based on
# https://docs.python.org/3.5/howto/logging-cookbook.html#an-example-dictionary-based-configuration
log_configuration = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        }
    },
    'handlers': {
        'console': {
            'class': "logging.StreamHandler",
            'level': "DEBUG",
            'formatter': "verbose",
            'stream': "ext://sys.stdout"
        }
    },
    'loggers': {
        '*': {
            'propagate': False,
            'handlers': ['console']
        }
    },
    'root': {
        'level': "DEBUG",
        'handlers': [
            "console"
        ]
    }
}

menu_configuration = {
    "menu": [
        {
            "title": "Dashboard",
            "code": "dashboard",
            "icon": "nb-home",
            "link": "/pages/dashboard",
            "home": True
        },
        {
            "title": "Module",
            "code": "module",
            "group": True
        },
        {
            "title": "Live Map",
            "code": "livemap",
            "icon": "nb-location",
            "link": "/pages/livemap/map/index"
        },
        {
            "title": "Sales",
            "code": "sales",
            "icon": "ion-ios-briefcase-outline",
            "link": "/pages/sales",
            "children": [
                {
                    "title": "Dashboard",
                    "code": "sales-dashboard",
                    "link": "/pages/sales/dashboard/index"
                },
                {
                    "title": "Data",
                    "code": "sales-data",
                    "children": [
                        {
                            "title": "Sales Rep",
                            "code": "sales-data-representative",
                            "link": "/pages/employee/sales/index"
                        },
                        {
                            "title": "Visit Cycle",
                            "code": "sales-data-visit-cycle",
                            "link": "/pages/sales/visit_cycle/index"
                        }
                    ]
                },
                {
                    "title": "ACTIVITIES",
                    "code": "sales-activities",
                    "children": [
                        {
                            "title": "Request Order",
                            "code": "sales-activities-request-order",
                            "link": "/pages/sales/activities/request_order/index"
                        },
                        # {
                        #     "title": "Sales Order",
                        #     "code": "sales-activities-sales-order",
                        #     "link": "/pages/sales/activities/sales_order/index"
                        # },
                        {
                            "title": "Invoice",
                            "code": "sales-activities-invoice",
                            "link": "/pages/sales/activities/invoice/index"
                        },
                        {
                            "title": "Payment",
                            "code": "sales-activities-payment",
                            "link": "/pages/sales/activities/payment/index"
                        },
                        {
                            "title": "Visit Plan",
                            "code": "sales-activities-visit-plan",
                            "link": "/pages/sales/activities/visit_plan/index"
                        },
                        {
                            "title": "Permission",
                            "code": "sales-activities-permission",
                            "link": "/pages/permission/sales/index"
                        },
                        {
                            "title": "Alert",
                            "code": "sales-activities-alert",
                            "link": "/pages/alert/sales/index"
                        }
                    ]
                },
                {
                    "title": "REPORT",
                    "code": "sales-report",
                    "children": [
                        {
                            "title": "Performance",
                            "code": "sales-report-performance",
                            "link": "/pages/sales/report_performance/index"
                        },
                        {
                            "title": "Request Order",
                            "code": "sales-report-order-sales",
                            "link": "/pages/sales/report_order_sales/index"
                        },
                        # {
                        #     "title": "Sales Order",
                        #     "code": "sales-report-sales-order",
                        #     "link": "/pages/sales/report_sales_order/index"
                        # },
                        {
                            "title": "Invoice",
                            "code": "sales-report-invoice",
                            "link": "/pages/sales/report_invoice/index"
                        },
                        {
                            "title": "Payment",
                            "code": "sales-report-payment",
                            "link": "/pages/sales/report_payment/index"
                        },
                        {
                            "title": "Visit Plan",
                            "code": "sales-report-visit-plan",
                            "link": "/pages/sales/report_visit_plan/index"
                        },
                        {
                            "title": "Customer Visit",
                            "code": "sales-report-customer-visit",
                            "link": "/pages/sales/report_customer_visit/index"
                        },
                        {
                            "title": "Visit Eye History",
                            "code": "sales-report-visit-eye-history",
                            "link": "/pages/sales/report_visit_eye_history/index"
                        },
                        {
                            "title": "Permission",
                            "code": "sales-report-permission",
                            "link": "/pages/sales/report_permission/index"
                        },
                        {
                            "title": "Alert",
                            "code": "sales-report-alert",
                            "link": "/pages/sales/report_alert/index"
                        }
                    ]
                }
                # {
                #     "title": "CONFIGURATION",
                #     "code": "sales-config",
                #     "children": [
                #         {
                #             "title": "Group Visit Plan",
                #             "code": "sales-config-group-visit-plan",
                #             "link": "/pages/sales/configurations_visit_plan/index"
                #         }
                #     ]
                # }
            ]
        },
        {
            "title": "Logistic",
            "code": "logistic",
            "icon": "ion-ios-box-outline",
            "link": "/pages/logistic",
            "children": [
                {
                    "title": "DASHBOARD",
                    "code": "logistic-dashboard",
                    "link": "/pages/logistic/dashboard/index"
                },
                {
                    "title": "DATA",
                    "code": "logistic-data",
                    "children": [
                        # {
                        #     "title": "Customers",
                        #     "code": "logistic-data-customers",
                        #     "link": "/pages/customers/logistic/index"
                        # },
                        {
                            "title": "Crew",
                            "code": "logistic-data-crew",
                            "link": "/pages/employee/logistic/index"
                        },
                        {
                            "title": "Delivery Cycle",
                            "code": "logistic-data-delivery-cycle",
                            "link": "/pages/logistic/delivery_cycle/index"
                        }
                    ]
                },
                {
                    "title": "ACTIVITIES",
                    "code": "logistic-activities",
                    "children": [
                        {
                            "title": "Packing Slip",
                            "code": "logistic-activities-packing-slip",
                            "link": "/pages/logistic/activities/packing_slip/index"
                        },
                        {
                            "title": "Delivery Route",
                            "code": "logistic-activities-delivery-route",
                            "link": "/pages/logistic/activities/delivery_route/index"
                        },
                        {
                            "title": "Permission",
                            "code": "logistic-activities-permission",
                            "link": "/pages/permission/logistic/index"
                        },
                        {
                            "title": "Alert",
                            "code": "logistic-activities-alert",
                            "link": "/pages/alert/logistic/index"
                        }
                    ]
                },
                {
                    "title": "REPORT",
                    "code": "logistic-report",
                    "children": [
                        {
                            "title": "Performance",
                            "code": "logistic-report-performance",
                            "link": "/pages/logistic/report_performance/index"
                        },
                        {
                            "title": "Packing Slip",
                            "code": "logistic-report-packing-slip",
                            "link": "/pages/logistic/report_packing_slip/index"
                        },
                        {
                            "title": "Delivery Plan",
                            "code": "logistic-report-delivery-plan",
                            "link": "/pages/logistic/report_delivery_plan/index"
                        },
                        {
                            "title": "Customer Delivery",
                            "code": "logistic-report-customer-delivery",
                            "link": "/pages/logistic/report_customer_delivery/index"
                        },
                        {
                            "title": "Permission",
                            "code": "logistic-report-permission",
                            "link": "/pages/logistic/report_permission/index"
                        },
                        {
                            "title": "Alert",
                            "code": "logistic-report-alert",
                            "link": "/pages/logistic/report_alert/index"
                        }
                    ]
                },
            ]
        },
        {
            "title": "Assets",
            "code": "assets",
            "icon": "ion-android-phone-portrait",
            "link": "/pages/assets",
            "children": [
                {
                    "title": "DATA",
                    "code": "assets-data",
                    "children": [
                        {
                            "title": "Assets",
                            "code": "assets-data-assets",
                            "link": "/pages/assets/assets/index"
                        },
                        {
                            "title": "Assets Type",
                            "code": "assets-data-assets-type",
                            "link": "/pages/assets/assets_type/index"
                        }
                    ]
                }
            ]
        },
        {
            "title": "Setting",
            "code": "setting",
            "icon": "nb-gear",
            "link": "/pages/setting",
            "children": [
                {
                    "title": "DATA",
                    "code": "setting-data",
                    "children": [
                        {
                            "title": "Company Information",
                            "code": "setting-data-company-info",
                            "link": "/pages/settings/company/show"
                        },
                        {
                            "title": "Divisions",
                            "code": "setting-data-division",
                            "link": "/pages/settings/divisions/index"
                        },
                        {
                            "title": "Branches",
                            "code": "setting-data-branches",
                            "link": "/pages/settings/branch/index"
                        },
                        {
                            "title": "Customers",
                            "code": "setting-data-customers",
                            "link": "/pages/settings/customers/index"
                        }
                    ]
                },
                {
                    "title": "USER",
                    "code": "setting-user",
                    "children": [
                        {
                            "title": "Supervisor",
                            "code": "setting-user-admin",
                            "link": "/pages/employee/supervisor/index"
                        },
                        {
                            "title": "User Group",
                            "code": "setting-user-group",
                            "link": "/pages/settings/user_groups/index"
                        },
                        {
                            "title": "User",
                            "code": "setting-user-user",
                            "link": "/pages/settings/user/index"
                        }
                    ]
                },
                # {
                #     "title": "NOTIFICATION",
                #     "code": "setting-notif",
                #     "children": [
                #         {
                #             "title": "Sales",
                #             "code": "setting-notif-sales",
                #             "link": "/pages/settings/notifications/sales"
                #         },
                #         {
                #             "title": "Logistic",
                #             "code": "setting-notif-logistic",
                #             "link": "/pages/settings/notifications/logistic"
                #         },
                #         {
                #             "title": "Routing",
                #             "code": "setting-notif-routing",
                #             "link": "/pages/settings/notifications/routing"
                #         },
                #         {
                #             "title": "Asset",
                #             "code": "setting-notif-asset",
                #             "link": "/pages/settings/notifications/asset"
                #         }
                #     ]
                # },
                {
                    "title": "CONFIGURATIONS",
                    "code": "setting-config",
                    "children": [
                        {
                            "title": "General",
                            "code": "setting-config-general",
                            "link": "/pages/settings/configurations_general/view"
                        },
                        {
                            "title": "Area",
                            "code": "setting-config-area",
                            "link": "/pages/settings/area/index"
                        }
                    ]
                }
            ]
        },
    ]
}

permission_config = {
    "dashboard": {
        "name": "Dashboard",
        "rule-view": 10
    },
    "livemap": {
        "name": "Live Map",
        "rule-view": 10
    },
    "sales": {
        "name": "Sales",
        "rule-view": 10,
        "data": {
            "sales-dashboard": {
                "name": "Dashboard",
                "rule-view": 10
            },
            "sales-data": {
                "name": "Data",
                "rule-view": 10,
                "data": {
                    "sales-data-representative": {
                        "name": "Sales Rep.",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-data-visit-cycle": {
                        "name": "Visit Cycle",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            },
            "sales-activities": {
                "name": "Activities",
                "rule-view": 10,
                "data": {
                    "sales-activities-request-order": {
                        "name": "Request Order",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-activities-sales-order": {
                        "name": "Sales Order",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-activities-invoice": {
                        "name": "Invoice",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-activities-payment": {
                        "name": "Payment",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-activities-visit-plan": {
                        "name": "Visit Plan",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-activities-permission": {
                        "name": "Permission",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-activities-alert": {
                        "name": "Alert",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            },
            "sales-report": {
                "name": "Report",
                "rule-view": 10,
                "data": {
                    "sales-report-performance": {
                        "name": "Performance",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-report-order-sales": {
                        "name": "Request Order",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-report-sales-order": {
                        "name": "Sales Order",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-report-invoice": {
                        "name": "Invoice",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-report-payment": {
                        "name": "Payment",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-report-visit-plan": {
                        "name": "Visit Plan",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-report-customer-visit": {
                        "name": "Customer Visit",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-report-visit-eye-history": {
                        "name": "Visit Eye History",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-report-permission": {
                        "name": "Permission",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "sales-report-alert": {
                        "name": "Alert",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            }
        }
    },
    "logistic": {
        "name": "Logistic",
        "rule-view": 10,
        "data": {
            "logistic-dashboard": {
                "name": "Dashboard",
                "rule-view": 10
            },
            "logistic-data": {
                "name": "Data",
                "rule-view": 10,
                "data": {
                    "logistic-data-crew": {
                        "name": "Crew",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "logistic-data-delivery-cycle": {
                        "name": "Delivery Cycle",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            },
            "logistic-activities": {
                "name": "Activities",
                "rule-view": 10,
                "data": {
                    "logistic-activities-packing-slip": {
                        "name": "Packing Slip",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "logistic-activities-delivery-route": {
                        "name": "Delivery Route",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "logistic-activities-permission": {
                        "name": "Permission",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "logistic-activities-alert": {
                        "name": "Alert",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            },
            "logistic-report": {
                "name": "Report",
                "rule-view": 10,
                "data": {
                    "logistic-report-performance": {
                        "name": "Performance",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "logistic-report-packing-slip": {
                        "name": "Packing Slip",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "logistic-report-delivery-plan": {
                        "name": "Delivery Plan",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "logistic-report-customer-delivery": {
                        "name": "Customer Delivery",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "logistic-report-permission": {
                        "name": "Permission",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "logistic-report-alert": {
                        "name": "Alert",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            }
        }
    },
    "assets": {
        "name": "Assets",
        "rule-view": 10,
        "data": {
            "assets-data": {
                "name": "Data",
                "rule-view": 10,
                "data": {
                    "assets-data-assets": {
                        "name": "Assets",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "assets-data-assets-type": {
                        "name": "Assets Type",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            }
        }
    },
    "setting": {
        "name": "Setting",
        "rule-view": 10,
        "data": {
            "setting-data": {
                "name": "Data",
                "rule-view": 10,
                "data": {
                    "setting-data-company-info": {
                        "name": "Company Information",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "setting-data-branches": {
                        "name": "Branches",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "setting-data-division": {
                        "name": "Divisions",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "setting-data-customers": {
                        "name": "Customers",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            },
            "setting-user": {
                "name": "User",
                "rule-view": 10,
                "data": {
                    "setting-user-admin": {
                        "name": "Administrators Profile",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "setting-user-group": {
                        "name": "User Groups",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "setting-user-user": {
                        "name": "User",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            },
            "setting-notif": {
                "name": "Notification",
                "rule-view": 10,
                "data": {
                    "setting-notif-sales": {
                        "name": "Sales",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "setting-notif-logistic": {
                        "name": "Logistic",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "setting-notif-routing": {
                        "name": "Routing",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "setting-notif-asset": {
                        "name": "Asset",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            },
            "setting-config": {
                "name": "Configurations",
                "rule-view": 10,
                "data": {
                    "setting-config-general": {
                        "name": "General",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    },
                    "setting-config-area": {
                        "name": "Area",
                        "rule-view": 10,
                        "rule": [10, 10, 10, 10, 10, 10]
                    }
                }
            }
        }
    }
}

permission_group_config = {
    "dashboard": {
        "name": "Dashboard",
        "rule-view": 0
    },
    "livemap": {
        "name": "Live Map",
        "rule-view": 0
    },
    "sales": {
        "name": "Sales",
        "rule-view": 0,
        "data": {
            "sales-dashboard": {
                "name": "Dashboard",
                "rule-view": 0
            },
            "sales-data": {
                "name": "Data",
                "rule-view": 0,
                "data": {
                    "sales-data-representative": {
                        "name": "Sales Rep.",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-data-visit-cycle": {
                        "name": "Visit Cycle",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            },
            "sales-activities": {
                "name": "Activities",
                "rule-view": 0,
                "data": {
                    "sales-activities-request-order": {
                        "name": "Request Order",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-activities-sales-order": {
                        "name": "Sales Order",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-activities-invoice": {
                        "name": "Invoice",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-activities-payment": {
                        "name": "Payment",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-activities-visit-plan": {
                        "name": "Visit Plan",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-activities-permission": {
                        "name": "Permission",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-activities-alert": {
                        "name": "Alert",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            },
            "sales-report": {
                "name": "Report",
                "rule-view": 0,
                "data": {
                    "sales-report-performance": {
                        "name": "Performance",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-report-order-sales": {
                        "name": "Request Order",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-report-sales-order": {
                        "name": "Sales Order",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-report-invoice": {
                        "name": "Invoice",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-report-payment": {
                        "name": "Payment",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-report-visit-plan": {
                        "name": "Visit Plan",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-report-customer-visit": {
                        "name": "Customer Visit",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-report-visit-eye-history": {
                        "name": "Visit Eye History",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-report-permission": {
                        "name": "Alert",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "sales-report-alert": {
                        "name": "Alert",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            }
        }
    },
    "logistic": {
        "name": "Logistic",
        "rule-view": 0,
        "data": {
            "logistic-dashboard": {
                "name": "Dashboard",
                "rule-view": 0
            },
            "logistic-data": {
                "name": "Data",
                "rule-view": 0,
                "data": {
                    "logistic-data-crew": {
                        "name": "Crew",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "logistic-data-delivery-cycle": {
                        "name": "Delivery Cycle",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            },
            "logistic-activities": {
                "name": "Activities",
                "rule-view": 0,
                "data": {
                    "logistic-activities-packing-slip": {
                        "name": "Packing Slip",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "logistic-activities-delivery-route": {
                        "name": "Delivery Route",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "logistic-activities-permission": {
                        "name": "Permission",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "logistic-activities-alert": {
                        "name": "Alert",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            },
            "logistic-report": {
                "name": "Report",
                "rule-view": 0,
                "data": {
                    "logistic-report-performance": {
                        "name": "Performance",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "logistic-report-packing-slip": {
                        "name": "Packing Slip",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "logistic-report-delivery-plan": {
                        "name": "Delivery Plan",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "logistic-report-customer-delivery": {
                        "name": "Customer Delivery",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "logistic-report-permission": {
                        "name": "Permission",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "logistic-report-alert": {
                        "name": "Alert",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            }
        }
    },
    "assets": {
        "name": "Assets",
        "rule-view": 0,
        "data": {
            "assets-data": {
                "name": "Data",
                "rule-view": 0,
                "data": {
                    "assets-data-assets": {
                        "name": "Assets",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "assets-data-assets-type": {
                        "name": "Assets Type",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            }
        }
    },
    "setting": {
        "name": "Setting",
        "rule-view": 0,
        "data": {
            "setting-data": {
                "name": "Data",
                "rule-view": 0,
                "data": {
                    "setting-data-company-info": {
                        "name": "Company Information",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "setting-data-branches": {
                        "name": "Branches",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "setting-data-division": {
                        "name": "Divisions",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "setting-data-customers": {
                        "name": "Customers",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            },
            "setting-user": {
                "name": "User",
                "rule-view": 0,
                "data": {
                    "setting-user-admin": {
                        "name": "Administrators Profile",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "setting-user-group": {
                        "name": "User Groups",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "setting-user-user": {
                        "name": "User",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            },
            "setting-notif": {
                "name": "Notification",
                "rule-view": 0,
                "data": {
                    "setting-notif-sales": {
                        "name": "Sales",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "setting-notif-logistic": {
                        "name": "Logistic",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "setting-notif-routing": {
                        "name": "Routing",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "setting-notif-asset": {
                        "name": "Asset",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            },
            "setting-config": {
                "name": "Configurations",
                "rule-view": 0,
                "data": {
                    "setting-config-general": {
                        "name": "General",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    },
                    "setting-config-area": {
                        "name": "Area",
                        "rule-view": 0,
                        "rule": [0, 0, 0, 0, 0, 0]
                    }
                }
            }
        }
    }
}


class Configuration(object):
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'admin'
    MYSQL_PASSWORD = 'Beb@s123'
    MYSQL_DB = 'trackgo_cisangkan'
    MYSQL_CURSORCLASS = 'DictCursor'
    MYSQL_CONNECT_TIMEOUT = 30

    # TODO: Log Configuration
    LOG_CONFIGURATION = log_configuration
    LOG_FILE = '/var/log/trackgo/trackgo.log'
    LOG_MAX_BYTES = 100000000
    LOG_ROTATE_COUNT = 5
    MENU_CONFIGURATION = menu_configuration
    PERMISSION_CONFIGURATION = permission_config
    PERMISSION_GROUP_CONFIGURATION = permission_group_config

    # TODO: FCM Configuration
    FCM_API_KEY = 'AAAAHMtABDw:APA91bGOGjbQYy4EQAaiUf1ej-YrWsKBA46V1Yhzl1bO67L6v016PWb2ZkHyzlu9G1C-vlQsT2FhOFFYia7gz27PC6cn4hATiuMv2wZoBbhWA_NoDWZy1dFhIALU-LHP4Z25YTylhgrH'

    # TODO: JWT Configuration
    JWT_ALGORITHM = "HS256"
    JWT_SECRET_KEY = "secret123 me"
    JWT_AUTH_URL_RULE = None
    JWT_EXPIRATION_DELTA = timedelta(days=7)

    # TODO: Session Configuration
    SECRET_KEY = 'top-secret!'
    SESSION_TYPE = 'filesystem'
    HOST_USSAGE_WSGI = 'localhost'
    PORT_USSAGE_WSGI = '7091'

    # TODO: Email Configuration
    MAIL_DEFAULT_SENDER = "mis@cisangkan.com"
    MAIL_FINANCE_RECIPIENTS = "mis@cisangkan.com"

    # TODO: Maps Api Key Configuration
    MAPS_KEY = "AIzaSyBFGgSfBdkoCCnbbpgD3EupW9meQXxkDk8"
    MAPS_ROUTES_URL = "https://maps.googleapis.com/maps/api/directions/json"

    # TODO: path to the upload directory Configuration
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", upload_folder)
    UPLOAD_FOLDER_IMAGES = os.path.join(UPLOAD_FOLDER, 'images')
    UPLOAD_FOLDER_VIDEOS = os.path.join(UPLOAD_FOLDER, 'videos')
    PROJECT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    SQLALCHEMY_POOL_RECYCLE = 3600


# Create engine for SQLAlchemy
engine = create_engine(
    'mysql://{0}:{1}@{2}/{3}'.format(
        Configuration.MYSQL_USER,
        Configuration.MYSQL_PASSWORD,
        Configuration.MYSQL_HOST,
        Configuration.MYSQL_DB
    ),
)

Base = declarative_base()

Session = sessionmaker(autocommit=True)
Session.configure(bind=engine)
session = Session()
