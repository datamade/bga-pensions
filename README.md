# 💵 bga-pensions

_Follow the money paid to retired public-sector employees throughout Illinois._

## Requirements

- Python 3.x
- PostgreSQL 9.x +
- Node / `npm`
- `wget`

## Getting started

1. Clone this repository:

    ```bash
    git clone https://github.com/datamade/bga-pensions.git
    ```

2. Set up docker

    ```bash
	docker-compose up
    ```

## Importing data

The ETL process that supports this app encompasses two phases: formatting the
data, and importing it into the Django database.

By default, the import will run for every year of data available, as of 2019.
To run the complete import, navigate to the project directory in your shell,
activate your virtual environment, and run `make`.

```bash
docker-compose run app make
```

You can also define specific years to format and import. Simply define a custom
`DATA_YEARS` environmental variable as a string containing each of the years
you wish to import, separated by spaces.

```bash
docker-compose run -e DATA_YEARS="2018 2019" app make -e
```

If you wish to make the data without importing it, specify the `data` target.

```bash
docker-compose run app make data -e
```

## Updating Pension Fund and Annual reports

1. TK use recipe from makefile to update fixtures from production

### Infrastructure model
![Infrastructure main model](.infragenie/infrastructure_main_model.svg)
- [bga-pensions component model](.infragenie/bga-pensions_component_model.svg)

---
