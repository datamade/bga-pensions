import csv
from datetime import datetime
import sys


reader = csv.DictReader(sys.stdin)
writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames)

writer.writeheader()

DATE_FORMATS = ('%m/%d/%Y', '%m/%d/%y')

for row in reader:
    for fmt in DATE_FORMATS:
        try:
            start_date = datetime.strptime(row['start_date'], fmt)
        except ValueError:
            pass
        else:
            row['start_date'] = '{}-{}-{}'.format(start_date.year, start_date.month, start_date.day)

    writer.writerow(row)
