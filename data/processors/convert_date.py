import csv
from datetime import datetime
import sys


reader = csv.DictReader(sys.stdin)
writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames)

writer.writeheader()

for row in reader:
    try:
        start_date = datetime.strptime(row['start_date'], '%m/%d/%Y')
    except ValueError:
        pass
    else:
        row['start_date'] = '{}-{}-{}'.format(start_date.year, start_date.month, start_date.day)
    finally:
        writer.writerow(row)