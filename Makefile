DATA_YEARS=2012 2013 2014 2015 2016 2017 2018 2019
RAW_YEARS=2012-2017 2018 2019

DELETE_EXISTING=True

INTERMEDIATE_FILES=$(patsubst %, pensions_%.reordered.csv, $(DATA_YEARS))
INTERMEDIATE_FILES+=$(patsubst %, pensions_%.tar, $(RAW_YEARS))

.INTERMEDIATE : $(INTERMEDIATE_FILES)
.PRECIOUS : $(patsubst %, data/raw/pensions_%.csv, $(RAW_YEARS))
.PHONY : all data import clean

all : import

data : $(patsubst %, data/finished/pensions_%.csv, $(DATA_YEARS))

import : $(patsubst %, import_%, $(DATA_YEARS))

clean :
	rm data/finished/*

import_% : data/finished/pensions_%.csv
	python manage.py import_data $(realpath $<) $* --delete=$(DELETE_EXISTING)

data/finished/pensions_%.csv : pensions_%.renamed.csv
	# 1. Omit rows without an amount.
	# 2. Remove trailing whitespace from column values.
	# 3. Convert MM/DD/YYYY dates to YYYY-MM-DD dates.
	csvgrep -c amount -r '^$$' -i $< | \
	perl -pe 's/\s{1,},/,/g' | \
	python data/processors/convert_date.py > $@

pensions_%.renamed.csv : pensions_%.reordered.csv
	# Rename the header row to correspond to model attributes.
	(echo first_name,last_name,amount,years_of_service,data_year,fund,start_date,final_salary,status; tail -n +2 $^ ) > $@

pensions_%.reordered.csv : data/raw/pensions_%.csv
	# Reorder the rows to conform with the expected format.
	csvcut -c FirstName,LastName,PensionAmount,YearsServed,DataYear,Agency,BenefitStart,SalaryatRetirement,Status $^ > $@

$(patsubst %, pensions_%.reordered.csv, $(shell seq 2012 1 2017)) : data/raw/pensions_2012-2017.csv
	# 1. Grab the rows relating to the given data year, which is parsed from the target filename.
	# 2. Reorder the rows to conform with the expected format.
	# 3. Add two extra empty columns for fields not requested prior to 2018.
	csvgrep -c DataYear -m $$(echo $@ | grep -oE '[0-9]+') $^ | \
	csvcut -c FirstName,LastName,PensionAmount,YearsServed,DataYear,Agency,BenefitStartDateOriginal | \
	perl -pe 's/$$/,,/' > $@

data/raw/pensions_%.csv : data/raw/pensions_%.tar
	cd $(dir $@) && tar xvfz $(notdir $<)

data/raw/pensions_%.tar :
	wget --no-use-server-timestamps \
		https://bga-pensions-database.s3.amazonaws.com/raw/$(notdir $@) -O $@
