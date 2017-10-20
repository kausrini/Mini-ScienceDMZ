# First argument is the mysql user password
# Second argument is the ip address of equipment

mysql -u guacamole_user -p$1 guacamole_db -Bse "UPDATE guacamole_connection_parameter SET parameter_value='$2' WHERE parameter_name='hostname';"