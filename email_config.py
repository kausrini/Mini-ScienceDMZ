import os


current_dir = os.getcwd()

sender = 'minidmz@iu.edu'     					# Sender's email address

receiver = ''						# Receiver's email address

smtp_server = 'mail-relay.iu.edu'			# Email relay to be used

path_for_logs = '/var/log/syslog'					# Location for the logs to be sent e.g. /var/log/syslog



# Only change the following if you want the backup logs to be stored somewhere else.

path_for_backup = current_dir+"/log_copy"		# Location where these logs will be backed up just to compute the diff. Prepend user's 

path_for_diff = current_dir+'/diff'			# Location where the log diff will be stored.

