# Mini-ScienceDMZ
The project designs, develops, and tests the deployment of a small device (Raspberry Pi) that functions as a firewall, large file transfer facility, and network performance monitor

1. Follow the instructions on the official raspberry pi page to install Raspbian on the raspberry pi sd card. 
   https://www.raspberrypi.org/documentation/installation/installing-images/

2. Download the files from https://github.com/kausrini/Mini-ScienceDMZ/tree/master/pi_setup_files 

3. Place the above files in the boot directory of the above SD card.

4. Edit the dynv6_token.txt to replace 'TOKEN_WILL_REPLACE_THIS' with the actual token for dynamic dns. 
   
   For more information login to https://dynv6.com/docs/apis and obtain the token.

4. Insert the sd card in the pi and connect power cable, HDMI, Keyboard to it.

5. Log into the raspberry pi with default credentials. (Username : pi, Password : raspberry)

6. Enter the following commands

7. sudo chmod 770 /boot/*.py

8. sudo /boot/pi_initial_setup.py -u IU_USERNAME
   
   Replace IU_USERNAME with your IU username.
   Enter your IU password when you are prompted for it.
   Change the password (new password) for the raspberry pi when prompted for it.
   The pi will reboot after configuration.

9. Log into the raspberry pi with the username pi and the new password.

10. sudo /boot/pi_final_setup.py
    
    The pi will reboot after configuring the raspberry pi.

11. Login to pi with username pi and the password set by you.

12. /home/pi/minidmz/guacamole_setup_files/setup.py -u IU_USERNAME
    
    Replace the IU_USERNAME with the IU username who will be the administrator for the application.
    This administrator would also be able to add other users to the application granting them access to the scientific device.

