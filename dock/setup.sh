#!/bin/bash

#This method is used to start the required services
start_services()
{
	/etc/init.d/guacd start
	/opt/tomcat/bin/catalina.sh start
	/bin/bash

}

####################################
# Main Body of script
####################################

start_services

