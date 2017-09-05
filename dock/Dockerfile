############################################################
# Dockerfile to build Guacd container images
# Based on Raspbian:jessie
# on Raspberry Pi
############################################################

# Set the base image to Ubuntu
FROM resin/rpi-raspbian:jessie-20170111


# File Author / Maintainer
MAINTAINER Kaushik Srinivasan <kausrini@iu.edu>

# Setting Environment variables
ENV GUACAMOLE_HOME /etc/guacamole

# Arguments passed during build time
ARG TOMCAT_VERSION
ARG GUACAMOLE_VERSION
ARG MYSQL_CONNECTOR_VERSION


# Java Development Kit dependency installed
RUN apt-get update && apt-get install -y \
	curl \
	default-jdk && \
	rm -rf /var/lib/apt/lists/*

	
# Create new group and user to run tomcat
RUN groupadd tomcat \
	&&  useradd -s /bin/false -g tomcat -d /opt/tomcat tomcat

	
# Downloading Apache Tomcat 8 from official site
RUN cd /tmp && \
	curl -O https://www-us.apache.org/dist/tomcat/tomcat-8/v$TOMCAT_VERSION/bin/apache-tomcat-$TOMCAT_VERSION.tar.gz && \
	mkdir /opt/tomcat && \
	tar xzf apache-tomcat-*tar.gz -C /opt/tomcat --strip-components=1 && \
	rm apache-tomcat-*tar.gz

	
# Giving the tomcat group ownership over the entire installation directory
# Giving the tomcat group read access to the conf directory
# Giving execute access to the conf directory itself
# Making the tomcat user the owner of the following directories
RUN cd /opt/tomcat && \
	chgrp -R tomcat /opt/tomcat && \
	chmod -R g+r conf && \
	chmod g+x conf && \
	chown -R tomcat webapps/ work/ temp/ logs/


#Installing Guacamole Prerequisites
RUN apt-get update && apt-get install -y \
	gcc \
	libcairo2-dev \
	libjpeg62-turbo-dev \
	libpng12-dev \
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
RUN curl -O http://apache.mirrors.tds.net/incubator/guacamole/$GUACAMOLE_VERSION-incubating/source/guacamole-server-$GUACAMOLE_VERSION-incubating.tar.gz && \	
    tar -xzf guacamole-server-$GUACAMOLE_VERSION-incubating.tar.gz -C /home && \
    rm guacamole-server-$GUACAMOLE_VERSION-incubating.tar.gz && \
    cd /home/guacamole-server-$GUACAMOLE_VERSION-incubating/ && \
    ./configure --with-init-dir=/etc/init.d && \
    make && \
    make install && \
    ldconfig

	
# Downloading Guacamole-Client war file  and moving to tomcat webapp folder
RUN curl -O http://apache.mirrors.tds.net/incubator/guacamole/$GUACAMOLE_VERSION-incubating/binary/guacamole-$GUACAMOLE_VERSION-incubating.war && \
	mv guacamole-$GUACAMOLE_VERSION-incubating.war /opt/tomcat/webapps/guacamole.war

	
# Setting up the required folders for guacamole
RUN mkdir /etc/guacamole && \
	mkdir /etc/guacamole/extensions && \
	mkdir /etc/guacamole/lib 

	
#Copying config files to docker container	
COPY guacamole.properties /etc/guacamole/

	
# Guacamole configurations for ARM architecture
RUN mkdir /usr/lib/arm-linux-gnueabihf/freerdp/ && \
    ln -s /home/guacamole-server-$GUACAMOLE_VERSION-incubating/src/protocols/rdp/.libs/guacsnd-client.so  /usr/lib/arm-linux-gnueabihf/freerdp/guacsnd-client.so && \
    ln -s /home/guacamole-server-$GUACAMOLE_VERSION-incubating/src/protocols/rdp/.libs/guacdr-client.so /usr/lib/arm-linux-gnueabihf/freerdp/guacdr-client.so    && \
    chown tomcat:tomcat /etc/guacamole/guacamole.properties


# Downloading the CAS authentication module
RUN curl -O http://apache.mirrors.tds.net/incubator/guacamole/$GUACAMOLE_VERSION-incubating/binary/guacamole-auth-cas-$GUACAMOLE_VERSION-incubating.tar.gz && \
	tar -xzf guacamole-auth-cas-$GUACAMOLE_VERSION-incubating.tar.gz && \
	mv ./guacamole-auth-cas-$GUACAMOLE_VERSION-incubating/guacamole-auth-cas-$GUACAMOLE_VERSION-incubating.jar /etc/guacamole/extensions && \
    rm guacamole-auth-cas-$GUACAMOLE_VERSION-incubating.tar.gz && \
	rm -rf guacamole-auth-cas-$GUACAMOLE_VERSION-incubating


# Downloading the guacamole-auth-jdbc module for database authentication
RUN curl -O http://apache.mirrors.lucidnetworks.net/incubator/guacamole/$GUACAMOLE_VERSION-incubating/binary/guacamole-auth-jdbc-$GUACAMOLE_VERSION-incubating.tar.gz && \
	tar -xzf guacamole-auth-jdbc-$GUACAMOLE_VERSION-incubating.tar.gz && \
	mv ./guacamole-auth-jdbc-$GUACAMOLE_VERSION-incubating/mysql/guacamole-auth-jdbc-mysql-$GUACAMOLE_VERSION-incubating.jar /etc/guacamole/extensions && \
    rm guacamole-auth-jdbc-$GUACAMOLE_VERSION-incubating.tar.gz && \
	rm -rf guacamole-auth-jdbc-$GUACAMOLE_VERSION-incubating 


# Downloading the MySQL jdbc connector for database authentication	
RUN curl -O https://cdn.mysql.com//Downloads/Connector-J/mysql-connector-java-$MYSQL_CONNECTOR_VERSION.tar.gz && \
	tar -xzf mysql-connector-java-$MYSQL_CONNECTOR_VERSION.tar.gz && \
	mv ./mysql-connector-java-$MYSQL_CONNECTOR_VERSION/mysql-connector-java-$MYSQL_CONNECTOR_VERSION-bin.jar /etc/guacamole/lib && \
	rm mysql-connector-java-$MYSQL_CONNECTOR_VERSION.tar.gz && \
	rm -rf mysql-connector-java-$MYSQL_CONNECTOR_VERSION

	
# Creating a script file to start required services
RUN echo "/etc/init.d/guacd start" > /home/setup.sh && \
	echo "/opt/tomcat/bin/catalina.sh run" >> /home/setup.sh
RUN chmod 700 /home/setup.sh


#Remove this finally. Docker containers dont need unnecessary stuff
RUN apt-get update && apt-get install -y nano 


#Setting to execute the shell script when the container is launched
CMD ["/home/setup.sh"]


