############################################################
# Dockerfile to build Guacamole container image
# Based on tomcat image for Raspberry Pi
############################################################

# Set the base image to tomcat image
FROM arm32v7/tomcat

# File Author / Maintainer
MAINTAINER Kaushik Srinivasan <kausrini@iu.edu>

# Setting Environment variable
ENV GUACAMOLE_HOME /etc/guacamole

# Arguments passed during build time
ARG GUACAMOLE_VERSION
ARG MYSQL_CONNECTOR_VERSION


# Java Development Kit dependency installed
RUN apt-get update && apt-get install -y \
	curl && \
	rm -rf /var/lib/apt/lists/*
	

#Installing Guacamole Prerequisites
RUN apt-get update && apt-get install -y \
	gcc \
	libcairo2-dev \
	libjpeg62-turbo-dev \
	libpng-dev \
	libossp-uuid-dev \
	libavcodec-dev  libavutil-dev  libswscale-dev \
	libfreerdp-dev \
	libpango1.0-dev  libssh2-1-dev \ 
	libvncserver-dev \
	libssl-dev \
	make \
	perl && \
	rm -rf /var/lib/apt/lists/*
	

# Downloading and Installing Guacamole Server
RUN curl -O http://apache.mirrors.tds.net/guacamole/$GUACAMOLE_VERSION/source/guacamole-server-$GUACAMOLE_VERSION.tar.gz && \	
    tar -xzf guacamole-server-$GUACAMOLE_VERSION.tar.gz -C /home && \
    rm guacamole-server-$GUACAMOLE_VERSION.tar.gz && \
    cd /home/guacamole-server-$GUACAMOLE_VERSION/ && \
    ./configure --with-init-dir=/etc/init.d && \
    make && \
    make install && \
    ldconfig

	
# Downloading Guacamole-Client war file  and moving to tomcat webapp folder
RUN curl -O http://apache.mirrors.tds.net/guacamole/$GUACAMOLE_VERSION/binary/guacamole-$GUACAMOLE_VERSION.war && \
	mv guacamole-$GUACAMOLE_VERSION.war /usr/local/tomcat/webapps/guacamole.war

	
# Setting up the required folders for guacamole
RUN mkdir /etc/guacamole && \
	mkdir /etc/guacamole/extensions && \
	mkdir /etc/guacamole/lib 

	
#Copying guacamole config file to docker container	
COPY guacamole.properties /etc/guacamole/

	
# Guacamole configurations for ARM architecture
RUN mkdir /usr/lib/arm-linux-gnueabihf/freerdp/ && \
    ln -s /home/guacamole-server-$GUACAMOLE_VERSION/src/protocols/rdp/.libs/guacsnd-client.so  /usr/lib/arm-linux-gnueabihf/freerdp/guacsnd-client.so && \
    ln -s /home/guacamole-server-$GUACAMOLE_VERSION/src/protocols/rdp/.libs/guacdr-client.so /usr/lib/arm-linux-gnueabihf/freerdp/guacdr-client.so    


# Downloading the CAS authentication module
RUN curl -O http://apache.mirrors.tds.net/guacamole/$GUACAMOLE_VERSION/binary/guacamole-auth-cas-$GUACAMOLE_VERSION.tar.gz && \
	tar -xzf guacamole-auth-cas-$GUACAMOLE_VERSION.tar.gz && \
	mv ./guacamole-auth-cas-$GUACAMOLE_VERSION/guacamole-auth-cas-$GUACAMOLE_VERSION.jar /etc/guacamole/extensions && \
    rm guacamole-auth-cas-$GUACAMOLE_VERSION.tar.gz && \
	rm -rf guacamole-auth-cas-$GUACAMOLE_VERSION


# Downloading the guacamole-auth-jdbc module for database authentication
RUN curl -O http://apache.mirrors.lucidnetworks.net/guacamole/$GUACAMOLE_VERSION/binary/guacamole-auth-jdbc-$GUACAMOLE_VERSION.tar.gz && \
	tar -xzf guacamole-auth-jdbc-$GUACAMOLE_VERSION.tar.gz && \
	mv ./guacamole-auth-jdbc-$GUACAMOLE_VERSION/mysql/guacamole-auth-jdbc-mysql-$GUACAMOLE_VERSION.jar /etc/guacamole/extensions && \
    rm guacamole-auth-jdbc-$GUACAMOLE_VERSION.tar.gz && \
	rm -rf guacamole-auth-jdbc-$GUACAMOLE_VERSION 


# Downloading the MySQL jdbc connector for database authentication	
RUN curl -O https://cdn.mysql.com//Downloads/Connector-J/mysql-connector-java-$MYSQL_CONNECTOR_VERSION.tar.gz && \
	tar -xzf mysql-connector-java-$MYSQL_CONNECTOR_VERSION.tar.gz && \
	mv ./mysql-connector-java-$MYSQL_CONNECTOR_VERSION/mysql-connector-java-$MYSQL_CONNECTOR_VERSION-bin.jar /etc/guacamole/lib && \
	rm mysql-connector-java-$MYSQL_CONNECTOR_VERSION.tar.gz && \
	rm -rf mysql-connector-java-$MYSQL_CONNECTOR_VERSION

	
# Starting the guacd process with tomcat
RUN sed -i -- 's|#!/usr/bin/env bash|#!/usr/bin/env bash\n\n/etc/init.d/guacd start\n|' /usr/local/tomcat/bin/catalina.sh
