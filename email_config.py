import os
import ntpath

current_dir = os.getcwd()

sender = 'minidmz@iu.edu'     					# Sender's email address

receiver = []						# Receiver's email address
smtp_server = 'mail-relay.iu.edu'			# Email relay to be used
path_for_logs = []	                                # Location for the logs to be sent e.g. /var/log/syslog

path_for_backup = []
path_for_diff = []

# Only change the following if you want the backup logs to be stored somewhere else.


for path in path_for_logs:
    filenm = ntpath.basename(path)
    path_for_backup.append(current_dir+"/"+filenm+"_backup")
    path_for_diff.append(current_dir+"/"+filenm+"_diff")



