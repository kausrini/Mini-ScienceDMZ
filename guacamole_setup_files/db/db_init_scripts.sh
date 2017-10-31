# First argument is the mysql database root password
# Second argument is the mysql user password
# Third argument is the guacamole administrator Indiana University Username
# Fourth argument is the ip address of equipment

# Creates a MySQL user account to access the guacamole_db database
mysql -u root -p$1 -Bse "CREATE DATABASE guacamole_db;"
mysql -u root -p$1 -Bse "CREATE USER 'guacamole_user'@'%' IDENTIFIED BY '$2';"
mysql -u root -p$1 -Bse "GRANT SELECT,INSERT,UPDATE,DELETE ON guacamole_db.* TO 'guacamole_user'@'%';"
mysql -u root -p$1 -Bse "CREATE USER 'guacamole_user'@'localhost' IDENTIFIED BY '$2';"
mysql -u root -p$1 -Bse "GRANT SELECT,INSERT,UPDATE,DELETE ON guacamole_db.* TO 'guacamole_user'@'localhost';"
mysql -u root -p$1 -Bse "FLUSH PRIVILEGES;"

# Executes the guacamole scripts for initializing the database 
cat /docker-entrypoint-initdb.d/*.sql | mysql -u root -p$1 guacamole_db

# Stores our RDP connection data and enables file transfer 
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_connection (connection_name, protocol, max_connections_per_user) VALUES ('RDP_Connection', 'rdp', '0');"
# This sql statement SELECT connection_id FROM guacamole_connection WHERE connection_name = 'RDP_Connection' AND parent_id IS NULL;
# provides the connection id needed for inserting values in the guacamole_connection_parameter table
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_connection_parameter VALUES ((SELECT connection_id FROM guacamole_connection WHERE connection_name = 'RDP_Connection' AND parent_id IS NULL), 'hostname', '$4');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_connection_parameter VALUES ((SELECT connection_id FROM guacamole_connection WHERE connection_name = 'RDP_Connection' AND parent_id IS NULL), 'port', '3389');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_connection_parameter VALUES ((SELECT connection_id FROM guacamole_connection WHERE connection_name = 'RDP_Connection' AND parent_id IS NULL), 'enable-drive', 'true');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_connection_parameter VALUES ((SELECT connection_id FROM guacamole_connection WHERE connection_name = 'RDP_Connection' AND parent_id IS NULL), 'drive-path', '/home/virtual_drive/');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_connection_parameter VALUES ((SELECT connection_id FROM guacamole_connection WHERE connection_name = 'RDP_Connection' AND parent_id IS NULL), 'create-drive-path', 'true');"

# Create a administrator for the guacamole application
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_user(username,password_date) VALUES ('$3',NOW());"

# Providing the administrator all System permissions
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_system_permission(user_id,permission) VALUES ((SELECT user_id FROM guacamole_user WHERE username='$3'),'ADMINISTER');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_system_permission(user_id,permission) VALUES ((SELECT user_id FROM guacamole_user WHERE username='$3'),'CREATE_USER');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_system_permission(user_id,permission) VALUES ((SELECT user_id FROM guacamole_user WHERE username='$3'),'CREATE_SHARING_PROFILE');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_system_permission(user_id,permission) VALUES ((SELECT user_id FROM guacamole_user WHERE username='$3'),'CREATE_CONNECTION_GROUP');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_system_permission(user_id,permission) VALUES ((SELECT user_id FROM guacamole_user WHERE username='$3'),'CREATE_CONNECTION');"

# Providing the administrator all user permissions over the administrator itself
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_user_permission (user_id,affected_user_id,permission) VALUES ((SELECT user_id FROM guacamole_user WHERE username='$3'),(SELECT user_id FROM guacamole_user WHERE username='$3'),'ADMINISTER');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_user_permission (user_id,affected_user_id,permission) VALUES ((SELECT user_id FROM guacamole_user WHERE username='$3'),(SELECT user_id FROM guacamole_user WHERE username='$3'),'UPDATE');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "INSERT INTO guacamole_user_permission (user_id,affected_user_id,permission) VALUES ((SELECT user_id FROM guacamole_user WHERE username='$3'),(SELECT user_id FROM guacamole_user WHERE username='$3'),'READ');"

# Removing the default MySQL Administrator guacadmin and removing all permissions granted
mysql -u guacamole_user -p$2 guacamole_db -Bse "DELETE FROM guacamole_system_permission WHERE user_id=(SELECT user_id from guacamole_user WHERE username='guacadmin');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "DELETE FROM guacamole_user_permission WHERE user_id=(SELECT user_id from guacamole_user WHERE username='guacadmin');"
mysql -u guacamole_user -p$2 guacamole_db -Bse "DELETE FROM guacamole_user WHERE username='guacadmin';"

