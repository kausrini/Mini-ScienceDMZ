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
import ntpath
import subprocess
from email_config import sender,receiver,smtp_server,path_for_logs,path_for_backup,path_for_diff

# Uncomment this and enter the path for secrets.py file which we will pull the username and password from.
from secrets import username,password

# Python email packages used.
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import Encoders
from email.mime.application import MIMEApplication

try:   
    # Function takes 4 arguments. Sender's email id, receiver's email id, the smtp server that you'll be using and the path to the log file. These parameters should be defined in the email_config file. Customize these to meet your needs.
    def generate_docker_logs():
        file_ = file("docker_log","wb")
        d = subprocess.Popen(["docker","logs","guacamole_container"], stdout=subprocess.PIPE)
        file_.write(d.stdout.read())
        file_.close()
        current_dir = os.getcwd()
        path_for_logs.append(current_dir+"/docker_log")
        path_for_backup.append(current_dir+"/docker_log_backup")
        path_for_diff.append(current_dir+"/docker_log_diff")
        
    def sendDeviceStatus(sender_email_id,receiver_email_id,smtp_server_name,log_path):
        print "sending email"
        # Create the email message.
        msg = MIMEMultipart()
        msg['Subject'] = 'Device status'
        msg['From'] = sender_email_id
        msg['To'] = ", ".join(receiver_email_id)
        msg.preamble = 'This is the latest device log. Please inspect to check device status'
        msg.attach(MIMEText("Syslog and Docker container logs are attached with this email"))
        try:
            for p in log_path:
                attachment = MIMEApplication(open(p, "r").read(), _subtype="txt")
                attachment.add_header('Content-Disposition', 'attachment' ,filename=ntpath.basename(p))
                msg.attach(attachment)
        except:
            print "Failed to attach files"

        try:    
            conn = SMTP(smtp_server_name)
        except:
            print "Check your email relay"
            
        try:
            conn.login(username,password)
        except:
            print "Auhtentication problem. Please check your credentials in the secrets.py file"
            
        conn.sendmail(sender,receiver,msg.as_string())
        conn.quit()

        
    def prepare_logs(log_path_list,backup_file_path_list,diff_file_path_list):
        final_paths = []
        for i in range(0,len(log_path_list)):
            # Check if backup log file exists. This branch will only be executed once.
            if not os.path.isfile(backup_file_path_list[i]):
                # Create a copy of the log file to calculate difference later if the file does not exist
                backup_log_file = file(ntpath.basename(backup_file_path_list[i]),"wb")
                shutil.copyfile(log_path_list[i],backup_file_path_list[i])
                backup_log_file.close()

                # Send email with the device logs.
                #sendDeviceStatus(sender,receiver,smtp_server,path_for_logs)
                final_paths.append(log_path_list[i])
            else:
                # Clear the old diff file.
                if os.path.isfile(diff_file_path_list[i]):
                    os.remove(diff_file_path_list[i])

                # Create a new file with latest diff.
                changes = file(ntpath.basename(diff_file_path_list[i]),"wb")
                changed_contents = difflib.unified_diff(open(backup_file_path_list[i]).readlines(),open(log_path_list[i]).readlines(),n=0)
                changes.writelines(changed_contents)
                changes.close()

                # Send status email only if there are changes in the logs. 
                if os.stat(diff_file_path_list[i]).st_size != 0:
                    #sendDeviceStatus(sender,receiver,smtp_server,path_for_diff)    # Logs have changed, send update!
                    final_paths.append(diff_file_path_list[i])

                    # Remove the old backup file and update it with latest logs"
                    os.remove(backup_file_path_list[i])
                    backup_log_file = file(ntpath.basename(backup_file_path_list[i]),"wb")
                    shutil.copyfile(log_path_list[i],backup_file_path_list[i])
                    backup_log_file.close()
            
        return final_paths

    try:
        generate_docker_logs()
    except:
        print "Error generating docker logs. Check if Docker is configured."
        
    rslt = prepare_logs(path_for_logs,path_for_backup,path_for_diff)
    if rslt:
        sendDeviceStatus(sender,receiver,smtp_server,rslt)
    else:
        print "No change since last status, email not sent!"
except:
    
    print " Oops! Something went wrong! Make sure your email_config.py and secrets.py files are correct!"

