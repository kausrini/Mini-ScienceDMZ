#!/usr/bin/env python3
#######################################################################################################
# Author : Advait M                                                                                   #
#                                                                                                     #
# This file sends device status via email. Please import the email_config.py and secrets.py file      #
# in order to scucessfully send the device status.                                                    #
#                                                                                                     # 
# Please check the email_config.py file for more information.                                         #
#                                                                                                     #
#######################################################################################################

import difflib
import json
import os
from pathlib import Path
import smtplib
import subprocess
import sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

sys.path.insert(0, '/home/pi/minidmz/')
from guacamole_setup_files import settings


# This method reads email related configuration from the email_config.json file
def read_config(log_email_path):

    config_file = 'email_config.json'
    config_file_path = log_email_path.joinpath(config_file)
    config_errors = False
    with config_file_path.open('r') as json_data_file:
        data = json.load(json_data_file)

    credentials = data['credentials']
    mail_config = data['mail_config']

    # Removing empty strings
    mail_config['receiver_email_id'] = list(filter(None, mail_config['receiver_email_id']))

    if not credentials['username'] or not credentials['password']:
        print('[Error] The credentials are missing from the {} file'.format(config_file_path.name))
        config_errors = True

    if not mail_config['sender_email_id'] or not mail_config['receiver_email_id']:
        print('[Error] Sender email id or/and receiver email id is missing ')
        config_errors = True

    if not mail_config['smtp_server_name']:
        print('[Error] smtp server is missing')
        config_errors = True

    if config_errors:
        print('Fix {} and re-run the code.'.format(config_file_path.name))
        sys.exit()

    return credentials,mail_config


# This method generates the difference in log between original log file and log backup file.
def log_generator(generated_files_path, original_log_file, log_backup_file, diff_file_name):

    diff_file = generated_files_path.joinpath(diff_file_name)

    try:
        with original_log_file.open('r') as file_object:
            original_log_contents = file_object.readlines()
    except PermissionError:
        print("[ERROR] Code is executed as a non privileged user."
              "\n[ERROR] Please re-run the script as superuser. [ sudo ./{} ]".format(
            os.path.basename(__file__)))
        sys.exit()

    # Check if a backup file exists, if yes, take a diff between original docker guacamole file
    # the current guacamole_log_file and send that as mail attachment. Replace the backup file with new contents.
    if log_backup_file.is_file():
        with log_backup_file.open('r') as file_object:
            backup_contents = file_object.readlines()
        changed_contents = difflib.unified_diff(backup_contents, original_log_contents)
    else:
        changed_contents = original_log_contents

    with diff_file.open('w') as file_object:
        file_object.writelines(changed_contents)

    # Write the guacamole log from docker to the guacamole_log_backup file.
    with log_backup_file.open('w') as file_object:
        file_object.writelines(original_log_contents)

    if diff_file.stat().st_size is 0:
            print('There has been no changes in {} since last update'.format(diff_file_name))
            return None

    return diff_file


# This method generates the guacamole log
def guacamole_log(generated_files_path):
    print('Generating the guacamole logs required to be sent over email')

    file_location_commad = ['docker', 'inspect', "--format='{{.LogPath}}'", settings.GUACAMOLE_CONTAINER_NAME]

    # Need to obtain the path for the docker's log file for guacamole_container
    try:
        guacamole_log_file = subprocess.check_output(file_location_commad).decode("utf-8").strip().strip("'")
    except subprocess.CalledProcessError:
        print('Error occured while accessing docker log file. Please check if the container is running and '
              'has logged output.')
        sys.exit()

    # Converting to path object
    guacamole_log_file = Path(guacamole_log_file)
    guacamole_log_backup = generated_files_path.joinpath('guacamole_backup.log')
    guacamole_diff_file_name = 'guacamole_diff.log'

    return log_generator(generated_files_path, guacamole_log_file, guacamole_log_backup, guacamole_diff_file_name)


# This method generates the syslog
def generate_syslog(generated_files_path):
    print('Generating the syslog logs required to be sent over email')
    syslog_file = Path('/var/log/syslog')
    syslog_backup = generated_files_path.joinpath('syslog_backup.log')
    syslog_diff_file_name = 'syslog_diff.log'

    return log_generator(generated_files_path, syslog_file, syslog_backup, syslog_diff_file_name)


# This method generates all the attachments and returns the list of attachments
def generate_attachments(generated_files_path):
    attachment_files = [guacamole_log(generated_files_path), generate_syslog(generated_files_path)]
    return attachment_files


# This is the main method with sends the email
def send_device_status():

    directories = settings.fetch_file_directories()

    credentials, mail_config = read_config(Path(directories[settings.DIRECTORY_LOG_EMAIL]))
    username, password = credentials['username'], credentials['password']
    sender_email_id, receiver_email_id = mail_config['sender_email_id'], mail_config['receiver_email_id']
    smtp_server_name = mail_config['smtp_server_name']

    # Obtaining log files after removing None data
    log_files = list(filter(None.__ne__, generate_attachments(Path(directories[settings.DIRECTORY_GENERATED_FILES]))))

    if not log_files:
        mail_body = "Hello,\nThere has been no changes in the log files since the last mail was sent.\n " \
                    "Hence, no logs are attached to this mail."
    else:
        mail_body = "Hello,\nAny log file changes since the last email has been attached to this mail."


    # Create the email message.
    message = MIMEMultipart()
    message['Subject'] = 'Device status: ' + settings.DOMAIN_NAME
    message['From'] = sender_email_id
    message['To'] = ", ".join(receiver_email_id)
    message.preamble = 'This is the latest device log. Please inspect to check device status'
    message.attach(MIMEText(mail_body))

    for log_file in log_files:

        log_file_data = log_file.read_text()
        attachment = MIMEApplication(log_file_data, _subtype="txt")
        attachment.add_header('Content-Disposition', 'attachment', filename=log_file.name)
        message.attach(attachment)

    print("[INFO] Sending email")

    try:
        with smtplib.SMTP_SSL(smtp_server_name) as smtp:
            smtp.login(username, password)
            smtp.sendmail(sender_email_id, receiver_email_id, message.as_string())
    except smtplib.SMTPConnectError as connect_error:
        print("Error connecting to the SMTP Server. Following error was displayed.\n{}".format(
            connect_error.strerror))
    except smtplib.SMTPAuthenticationError as auth_error:
        print("[ERROR] The server didn’t accept the username/password combination.")
    except smtplib.SMTPException as base_exception:
        print("[ERROR] Something went wrong in SMTP module.")
        print(base_exception.strerror)


if __name__ == '__main__':
    send_device_status()
