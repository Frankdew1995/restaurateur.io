
from app.models import User, Visit, Order, Food
from app import app, db

from app.utilities import receipt_templating


details = {
    "Coffee": 12,
    "Noodle": 23,
    "Soup": 123
}

import time
from pathlib import Path
start = time.time()

temp_file = str(Path(app.root_path) / 'static' / 'docx' / 'receipt_temp_inhouse.docx')

temp_file1 = str(Path(app.root_path) / 'static' / 'docx' / 'receipt_temp_out.docx')


receipt_templating(
                context={"details": details,
                         "company_name": "Xstar",
                         "address": "Maxmann Strasse",
                         "now": "2018 12 33 12:00:00",
                         "tax_id": "121731723",
                         "table_name": "34",
                         "wait_number": 23,
                         "total": 455,
                         "pay_via": "KARTE",
                         "VAT": round((455 / 1.07)*0.07, 2)
                         },
                temp_file=temp_file1)

end = time.time()

print("Took", end - start)