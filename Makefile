DATA_YEARS=2012 2013 2014 2015 2016 2017 2018 2019

all : import

data : $(patsubst %, data/finished/pensions_%.csv, $(DATA_YEARS))

import : $(patsubst %, import_%, $(DATA_YEARS))

clean :
	rm data/finished/*

include data/individuals.mk
