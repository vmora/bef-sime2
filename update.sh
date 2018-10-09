#!/bin/bash
echo $PWD
docker cp trytond.conf tryton:/etc/
docker cp trytond_log.conf tryton:/etc/
docker cp uwsgi.conf tryton:/etc/
docker cp trytond/trytond tryton:/usr/local/lib/python3.5/dist-packages/
docker cp modules/wfs tryton:/usr/local/lib/python3.5/dist-packages/trytond/modules/
docker cp modules/fr_commune tryton:/usr/local/lib/python3.5/dist-packages/trytond/modules/
docker cp modules/geotools tryton:/usr/local/lib/python3.5/dist-packages/trytond/modules/
docker cp modules/qgis tryton:/usr/local/lib/python3.5/dist-packages/trytond/modules/
