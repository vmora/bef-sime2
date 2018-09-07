# What is Tryton?
Tryton Is a three-tier high-level general purpose
application platform under the license GPL-3 written in Python and using
PostgreSQL as database engine.

It is the core base of a complete business solution providing modularity,
scalability and security.

## How to use this image

### Start a PostgreSQL/Postgis instance
$ docker run --name tryton-postgres -e POSTGRES_PASSWORD=tryton -e POSTGRES_DB=tryton -d kartoza/postgis:9.6-2.4

### Setup the database
$ docker run --link tryton-postgres:postgres -it pobsteta/bef-sime2 trytond-admin -d tryton --all

### Start a Tryton instance
$ docker run --name tryton -p 8000:8000 --link tryton-postgres:postgres -d pobsteta/bef-sime2

You can connect to Tryton using http://localhost:8000/

