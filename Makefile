DATA_YEARS=2012 2013 2014 2015 2016 2017 2018 2019
PENSION_DATA=$(patsubst %, data/finished/pensions_%.csv, $(DATA_YEARS))
IMPORT_DATA=$(patsubst %, import_%, $(DATA_YEARS))

all : import

data : $(PENSION_DATA)

import : $(IMPORT_DATA)

clean :
	rm data/finished/*

include data/individuals.mk
