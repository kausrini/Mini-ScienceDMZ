#First argument is the MYSQL_ROOT_PASSWORD
#Second argument is MYSQL_USER_PASSWORD

mysql -u root -p$1 -Bse "CREATE DATABASE guacamole_db;"
mysql -u root -p$1 -Bse "CREATE USER 'guacamole_user'@'%' IDENTIFIED BY '$2';"
mysql -u root -p$1 -Bse "GRANT SELECT,INSERT,UPDATE,DELETE ON guacamole_db.* TO 'guacamole_user'@'%';"
mysql -u root -p$1 -Bse "CREATE USER 'guacamole_user'@'localhost' IDENTIFIED BY '$2';"
mysql -u root -p$1 -Bse "GRANT SELECT,INSERT,UPDATE,DELETE ON guacamole_db.* TO 'guacamole_user'@'localhost';"
mysql -u root -p$1 -Bse "FLUSH PRIVILEGES;"


cat /docker-entrypoint-initdb.d/*.sql | mysql -u root -p$1 guacamole_db

mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_connection (connection_name, protocol) VALUES ('RDP_Connection', 'rdp');"

# This sql statement SELECT connection_id FROM guacamole_connection WHERE connection_name = 'RDP_Connection' AND parent_id IS NULL;
# provides the connection id needed for inserting values in the guacamole_connection_parameter table
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_connection_parameter VALUES ((SELECT connection_id FROM guacamole_connection WHERE connection_name = 'RDP_Connection' AND parent_id IS NULL), 'hostname', '192.168.0.7');"

mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_connection_parameter VALUES ((SELECT connection_id FROM guacamole_connection WHERE connection_name = 'RDP_Connection' AND parent_id IS NULL), 'port', '3389');"
