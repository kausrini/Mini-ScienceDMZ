############################################################
# Dockerfile to build Mysql image for Guacamole application
# Based on 
# on Raspberry Pi
############################################################

#Base image is hypriot mysql version 5.5
From hypriot/rpi-mysql:5.5

# File Author / Maintainer
MAINTAINER Kaushik Srinivasan <kausrini@iu.edu>

# Arguments passed during the build time
ARG GUACAMOLE_VERSION

RUN apt-get update && apt-get install -y \
	curl 
	
COPY db_init_scripts.sh /docker-entrypoint-initdb.d/

RUN curl -O http://apache.mirrors.lucidnetworks.net/incubator/guacamole/$GUACAMOLE_VERSION-incubating/binary/guacamole-auth-jdbc-$GUACAMOLE_VERSION-incubating.tar.gz \
	&& tar -xzf guacamole-auth-jdbc-$GUACAMOLE_VERSION-incubating.tar.gz \
	&& mv ./guacamole-auth-jdbc-$GUACAMOLE_VERSION-incubating/mysql/schema/*.sql /docker-entrypoint-initdb.d/ \
	&& rm guacamole-auth-jdbc-$GUACAMOLE_VERSION-incubating.tar.gz \
	&& rm -rf guacamole-auth-jdbc-$GUACAMOLE_VERSION-incubating

RUN chmod 700 /docker-entrypoint-initdb.d/db_init_scripts.sh

