# Tryton stack
#
# This image includes the following tools
# - SIME BEF
# - QGIS 3.2
# - R 3.5
#
# Version 1.0

FROM node as builder-node
ENV SERIES 4.8
RUN npm install -g bower
RUN curl https://downloads.tryton.org/${SERIES}/tryton-sao-last.tgz | tar zxf - -C /
RUN cd /package && bower install --allow-root

FROM debian:stretch-slim
MAINTAINER Pascal Obstetar <pascal.obstetar@bioecoforests.com>

# ---------- DEBUT --------------

# On évite les messages debconf
ENV DEBIAN_FRONTEND noninteractive

# Ajoute gosub pour faciliter les actions en root
ENV GOSU_VERSION 1.10
RUN set -x \
	&& apt-get update && apt-get install -y --no-install-recommends ca-certificates wget && rm -rf /var/lib/apt/lists/* \
	&& wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$(dpkg --print-architecture)" \
	&& wget -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$(dpkg --print-architecture).asc" \
	&& export GNUPGHOME="$(mktemp -d)" \
	&& gpg --keyserver ha.pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
	&& gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu \
	&& rm -r "$GNUPGHOME" /usr/local/bin/gosu.asc \
	&& chmod +x /usr/local/bin/gosu \
	&& gosu nobody true \
	&& apt-get purge -y --auto-remove ca-certificates

# version de tryton
ENV SERIES 4.8
ENV LANG C.UTF-8
	
RUN groupadd -r trytond \
    && useradd --no-log-init -r -d /var/lib/trytond -m -g trytond trytond \
    && mkdir /var/lib/trytond/db && chown trytond:trytond /var/lib/trytond/db \
    && mkdir /var/lib/trytond/www

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        software-properties-common \        
        python3 \
        python3-pip \
        python3-setuptools \
        uwsgi \
        uwsgi-plugin-python3 \
        # trytond
        python3-lxml \
        python3-genshi \
        python3-polib \
        python3-werkzeug \
        python3-wrapt \
        python3-psycopg2 \
        python3-bcrypt \
        # modules
        python3-dateutil \
        python3-html2text \
        #python3-ldap3 \ requires >= 2.0.7
        python3-magic \
        python3-ofxparse \
        python3-pypdf2 \
        python3-requests \
        python3-simpleeval \
        python3-stdnum \
        python3-tz \
        python3-zeep \
    && rm -rf /var/lib/apt/lists/*
    
# On ajoute le dépôt QGIS et R    
RUN add-apt-repository ppa:ubuntugis/ubuntugis-unstable
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 314DF160
    
# On ajoute le dépôt QGIS
#RUN echo "deb http://qgis.org/debian stretch main" > /etc/apt/sources.list.d/qgis.list
#RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-key CAEB3DC3BDF7FB45

# On ajoute le dépôt R
#RUN echo "deb http://cran.irsn.fr/bin/linux/ubuntu bionic-cran35/" > /etc/apt/sources.list.d/rcran.list
#RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9

# On met à jour
RUN apt-get -y update    
    
RUN pip3 install --no-cache-dir trytond-gis  

RUN pip3 install --no-cache-dir \
    "trytond == ${SERIES}.*" \
    && for module in `curl https://downloads.tryton.org/${SERIES}/modules.txt`; do \
        pip3 install --no-cache-dir "trytond_${module} == ${SERIES}.*"; \
        done \
    && pip3 install --no-cache-dir phonenumbers   

# On installe les dépendances de PostgreSQL, R et QGIS
# Pour QGIS, R, Tryton
RUN apt-get update && apt-get install --yes --force-yes git python3-gdal python3-rpy2 libgeos-dev apache2 qgis qgis-server libapache2-mod-fcgid && rm -rf /var/lib/apt/lists/*

# On ajoute le groupe www-data à root pour QGIS-server
RUN addgroup www-data root

# Ajoute les fichiers de conf d'apache
ADD apache.conf /etc/apache2/sites-enabled/000-default.conf
ADD fcgid.conf /etc/apache2/mods-available/fcgid.conf
ADD fqdn.conf /etc/apache2/conf-available/fqdn.conf

# Active fqdn.conf pour éviter le message d'erreur au lancement du serveur apache en localhost
RUN a2enconf fqdn

# On ajoute les librairies "sp" et "rgeos" nécessaire à QGIS, R et Tryton
RUN echo 'install.packages(c("sp", "rgeos"), repos="http://cran.us.r-project.org", dependencies=TRUE)' > /tmp/packages.R \
    && Rscript /tmp/packages.R

# === On ajoute les modules SIME de Bio Eco Forests ===

#ADD ./tryton.tar.gz /opt/

COPY --from=builder-node /package /var/lib/trytond/www
COPY entrypoint.sh /
COPY trytond.conf /etc/trytond.conf
COPY qgis_server.conf /etc/qgis_server.conf
COPY uwsgi.conf /etc/uwsgi.conf

# Variables d'environnement apache
ENV APACHE_RUN_USER    www-data
ENV APACHE_RUN_GROUP   www-data
ENV APACHE_PID_FILE    /var/run/apache2.pid
ENV APACHE_RUN_DIR     /var/run/apache2
ENV APACHE_LOCK_DIR    /var/lock/apache2
ENV APACHE_LOG_DIR     /var/log/apache2
ENV LANG               C

# Expose le port 80 pour Apache
EXPOSE 80

# on expose 8000 pour tryton et sao
EXPOSE 8000

# Expose le port 8001 pour QGIS server et http
EXPOSE 8001

VOLUME ["/var/lib/trytond/db"]
ENV TRYTOND_CONFIG=/etc/trytond.conf
USER trytond
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uwsgi", "--ini", "/etc/uwsgi.conf"]

# ---------- FIN --------------

