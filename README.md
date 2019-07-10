# 💵 bga-pensions

_Follow the money paid to retired public-sector employees throughout Illinois._

## Requirements

- Python 3.x
- PostgreSQL 9.x +
- Node / `npm`

## Getting started

1. Clone this repository:

    ```bash
    git clone https://github.com/datamade/bga-pensions.git
    cd bga-pensions
    ```

2. Create a virtual environment and install the Python requirements. We
like `virtualenvwrapper` for managing Python environments, but you can use
whatever package you like.

    ```bash
    mkvirtualenv bga-pensions
    pip install -r requirements.txt
    ```

3. Make sure you have `npm` installed. (See https://www.npmjs.com/get-npm.) Then,
install the Node requirements.

    ```bash
    npm install
    ```

4. Copy the example configuration to a live file.

    ```bash
    cp bga_database/local_settings.py.example bga_database/local_settings.py
    ```

5. Create your database and add a superuser.


    ```bash
    createdb bga_pensions && python manage.py migrate
    python manage.py createsuperuser
    ```

6. Run the application.

    ```bash
    python manage.py runserver
    ```

## Importing data

The ETL process that supports this app encompasses two phases: formatting the
data, and importing it into the Django database. The import includes recipes to
retrieve and inflate compressed raw data from a public S3 bucket.

By default, the import will run for every year of data available, as of 2019.
To run the complete import, navigate to the project directory in your shell,
activate your virtual environment, and run `make`.

```bash
cd /path/to/bga-pensions
workon bga-pensions
make
```

You can also define specific years to format and import. Simply define a custom
`DATA_YEARS` environmental variable as a string containing each of the years
you wish to import, separated by spaces.

```bash
export DATA_YEARS="2018 2019"
make -e
```

If you wish to make the data without importing it, specify the `data` target.

```bash
make data -e
```
