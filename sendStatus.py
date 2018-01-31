#######################################################################################################
# Author : Advait M                                                                                   #
#                                                                                                     #
# This file sends device status via email. Please import the email_config.py and secrets.py file      #
# in order to scucessfully send the device status.                                                    #
#                                                                                                     # 
# Please check the email_config.py file for more information.                                         #
#                                                                                                     #
#######################################################################################################


# Import smtplib for the actual sending function
from smtplib import SMTP_SSL as SMTP
import sys
import difflib
import shutil
import os
from email_config import sender,receiver,smtp_server,path_for_logs,path_for_backup,path_for_diff

# Uncomment this and enter the path for secrets.py file which we will pull the username and password from.
from secrets import username,password

# Python email packages used.
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:   
    # Function takes 4 arguments. Sender's email id, receiver's email id, the smtp server that you'll be using and the path to the log file. These parameters should be defined in the email_config file. Customize these to meet your needs.
    
    def sendDeviceStatus(sender_email_id,receiver_email_id,smtp_server_name,log_path):
        # Create the email message.
        msg = MIMEMultipart()
        msg['Subject'] = 'Device status'
        msg['From'] = sender_email_id
        msg['To'] = receiver_email_id
        msg.preamble = 'This is the latest device log. Please inspect to check device status'
        fp = open(log_path, 'rb')
        log_file = MIMEText(fp.read())
        fp.close()
        msg.attach(log_file)
        conn = SMTP(smtp_server_name)
        conn.login(username,password)
        conn.sendmail(sender,receiver,msg.as_string())
        conn.quit()


    # Check if backup log file exists. THis branch will only be executed once.
    if not os.path.isfile(path_for_backup):
        # Create a copy of the log file to calculate difference later if the file does not exist
        backup_log_file = file("log_copy","wb")
        shutil.copyfile(path_for_logs,path_for_backup)
        backup_log_file.close()

        # Send email with the device logs.
        sendDeviceStatus(sender,receiver,smtp_server,path_for_logs)

    else:
        # Clear the old diff file.
        if os.path.isfile(path_for_diff):
            os.remove(path_for_diff)

        # Create a new file with latest diff.
        changes = open(path_for_diff,"wb")
        changed_contents = difflib.unified_diff(open(path_for_backup).readlines(),open(path_for_logs).readlines(),n=0)
        changes.writelines(changed_contents)
        changes.close()

        # Send status email only if there are changes in the logs. 
        if os.stat(path_for_diff).st_size != 0:
            sendDeviceStatus(sender,receiver,smtp_server,path_for_diff)    # Logs have changed, send update!

            # Remove the old backup file and update it with latest logs"
            os.remove(path_for_backup)
            backup_log_file = file("log_copy","wb")
            shutil.copyfile(path_for_logs,path_for_backup)
            backup_log_file.close()
            print "email sent!"
        else:
            print "No change since last status"

except:
    print " Oops! Something went wrong! Make sure your email_config.py and secrets.py files are correct!"
