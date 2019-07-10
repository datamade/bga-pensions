DELETE_EXISTING=True
RAW_YEARS=2012-2017 2018 2019
INTERMEDIATE_FILES=$(patsubst %, .pensions_%.csv, $(DATA_YEARS))
INTERMEDIATE_FILES+=$(patsubst %, pensions_%.tar, $(RAW_YEARS))

.INTERMEDIATE : $(INTERMEDIATE_FILES)

.PRECIOUS : $(patsubst %, data/raw/pensions_%.csv, $(RAW_YEARS))

.PHONY :
import_% : data/finished/pensions_%.csv
	python manage.py import_data $* --delete=$(DELETE_EXISTING)

data/finished/pensions_%.csv : .pensions_%.csv
	(echo first_name,last_name,amount,years_of_service,data_year,fund,start_date,final_salary,status; \
	tail -n +2 $^ | perl -pe 's/\s{1,},/,/g') | \
	python data/processors/convert_date.py > $@

.pensions_%.csv : data/raw/pensions_%.csv
	csvcut -c FirstName,LastName,PensionAmount,YearsServed,DataYear,Agency,BenefitStart,SalaryatRetirement,Status $^ > $@

$(patsubst %, .pensions_%.csv, $(shell seq 2012 1 2017)) : data/raw/pensions_2012-2017.csv
	csvgrep -c DataYear -m $$(echo $@ | grep -oE '[0-9]+') $^ | \
	csvcut -c FirstName,LastName,PensionAmount,YearsServed,DataYear,Agency,BenefitStartDateOriginal | \
	perl -pe 's/$$/,,/' > $@

data/raw/pensions_%.csv : data/raw/pensions_%.tar
	cd $(dir $@) && tar xvfz $(notdir $<)

data/raw/pensions_%.tar :
	wget --no-use-server-timestamps \
		https://bga-pensions-database.s3.amazonaws.com/raw/$(notdir $@) -O $@
