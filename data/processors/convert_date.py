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
            row['start_date'] = start_date.strftime('%Y-%m-%d')
            break

    writer.writerow(row)
