# What is Tryton?
Tryton Is a three-tier high-level general purpose
application platform under the license GPL-3 written in Python and using
PostgreSQL as database engine.

It is the core base of a complete business solution providing modularity,
scalability and security.

## How to use this image

### Start a PostgreSQL/Postgis instance
$ docker run --name tryton-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=tryton -e POSTGRES_DB=tryton -d kartoza/postgis:9.6-2.4

### Setup the database
$ docker run --link tryton-postgres:postgres -it pobsteta/bef-sime2 trytond-admin -d tryton --all

### Start a Tryton instance
$ docker run --name tryton -p 8000:8000 --link tryton-postgres:postgres -d pobsteta/bef-sime2

You can connect to Tryton using http://localhost:8000/

curl  -d '{"user":"admin", "application":"wfs"}' -H "Content-Type: application/json" -X POST  http://localhost:8000/tryton/user/application/

curl -H 'Authorization: Bearer 6153defdd49e4fa0a880113b17d95863d36060633d4c483a9e8552b4f04d966474d1b1225c224757aacc37c8b3f4b3c4e927b4aa423249638ccd5339765566c1'  GET http://localhost:8000/tryton/wfs

