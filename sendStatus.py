# Import smtplib for the actual sending function
from smtplib import SMTP_SSL as SMTP
import sys
# Uncomment this and enter the path for secrets.py file which we will pull the username and password from.
# sys.path.append('')
from secrets import username,password

# Python email packages used.
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#Sender's email address.
frm = 'xyz@iu.edu'

#Reveiver's email address.
to = 'abc@iu.edu'

# Use your own email relay here and store the corresponding authentication credentials in secrets.py file.
smtp_server = 'mail-relay.iu.edu'

# Path for log file to be mailed.
# path_for_logs = '/var/log/syslog'

# Create the email message.
msg = MIMEMultipart()

msg['Subject'] = 'Device status'


msg['From'] = frm
msg['To'] = to
msg.preamble = 'This is the latest device log. Please inspect to check device status'

fp = open(path_for_logs, 'rb')
log_file = MIMEText(fp.read())
fp.close()
msg.attach(log_file)


conn = SMTP(smtp_server)
conn.login(username,password)

conn.sendmail(frm,to,msg.as_string())

conn.quit()
