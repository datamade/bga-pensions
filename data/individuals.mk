DELETE_EXISTING=True
INTERMEDIATE_FILES=$(patsubst %, pensions_%.csv, $(DATA_YEARS))

.INTERMEDIATE : $(INTERMEDIATE_FILES)

.PHONY :
import_% : data/finished/pensions_%.csv
	python manage.py import_data $* --delete=$(DELETE_EXISTING)

data/finished/pensions_%.csv : pensions_%.csv
	(echo first_name,last_name,amount,years_of_service,data_year,fund,final_salary,start_date,status; \
	tail -n +2 $^ | perl -pe 's/\s{1,},/,/g') | \
	python data/processors/convert_date.py > $@

pensions_%.csv : data/raw/pensions_%.csv
	csvcut -c FirstName,LastName,PensionAmount,YearsServed,DataYear,Agency,SalaryatRetirement,BenefitStart,Status $^ > $@

pensions_2012.csv : data/raw/pensions_2012-2017.csv
pensions_2013.csv : data/raw/pensions_2012-2017.csv
pensions_2014.csv : data/raw/pensions_2012-2017.csv
pensions_2015.csv : data/raw/pensions_2012-2017.csv
pensions_2016.csv : data/raw/pensions_2012-2017.csv
pensions_2017.csv : data/raw/pensions_2012-2017.csv
pensions_%.csv :
	csvgrep -c DataYear -m $* $^ | \
	csvcut -c FirstName,LastName,PensionAmount,YearsServed,DataYear,Agency,FinalAverageSalary,BenefitStartDateOriginal | \
	perl -pe 's/$$/,/' > $@
