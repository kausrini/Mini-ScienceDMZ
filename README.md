# Mini-ScienceDMZ
The project designs, develops, and tests the deployment of a small device (Raspberry Pi) that functions as a firewall, large file transfer facility, and network performance monitor

1. Follow the instructions on the official raspberry pi page to install Raspbian on a SD card. 
   https://www.raspberrypi.org/documentation/installation/installing-images/

2. Create an account in https://dynv6.com/ and register a DOMAIN_NAME.

3. Download the files from https://github.com/kausrini/Mini-ScienceDMZ/tree/master/pi_setup_files

4. Place the above files in the boot directory of the SD card.

5. Go to https://dynv6.com/docs/apis and obtain 'Your API token'. 

6. Edit the dynv6_token.txt to replace 'TOKEN_WILL_REPLACE_THIS' with 'Your API token'. 

7. Edit the pi_settings.py and store the DOMAIN_NAME you registered in step 2 in the variable DOMAIN_NAME.

8. Insert the sd card in the pi and connect power cable, HDMI, Keyboard to it.

9. Connect the pi to the RDP enabled equipment using a lan cable.

10. Log into the raspberry pi with default credentials. (Username : pi, Password : raspberry)

11. Enter the following commands

12. sudo chmod 700 /boot/*.py

13. sudo /boot/pi_initial_setup.py -s 'YOUR_WIFI_SSID' 
   
   Replace YOUR_WIFI_SSID with your wifi ssid. (Quotes is required only if the ssid has any whitespace characters)
   Answer the prompt if the wifi network is WPA-Enterprise.
   If answered with yes, you will be prompted for username. Provide the username.
   Enter the wifi password when you are prompted for it.
   Change the default raspberry pi password to a NEW_PASSWORD when prompted for it.
   The pi will reboot after configuration.

14. Log into the raspberry pi with the username pi and the NEW_PASSWORD.

15. sudo /boot/pi_final_setup.py -t -e YOUR_EMAIL_ADDRESS
    
	-t obtains invalid HTTPS certificate for testing purposes.
    The pi will reboot after configuring the raspberry pi.

16. Login to pi with username pi and the password set by you.

17. Edit the file /home/pi/minidmz/guacamole_setup_files/settings.py and change DOMAIN_NAME to the registered DOMAIN_NAME

18. /home/pi/minidmz/guacamole_setup_files/setup.py -u CAS_USERNAME
    
    Replace the CAS_USERNAME with the username used to authenticate with CAS server. This username (user) will be the administrator for the application.
    This administrator would also be able to add other users to the application granting them access to the scientific device.

19. The Guacamole page can be visited at https://DOMAIN_NAME/guacamole/

Note:

An WPA-Enterprise wifi network requires an username and password for connection. Examples are corporate networks or university networks.
A WPA-Personal wifi network requires only password for connection. Examples are home wifi network.

The script tries to configure Wireless connection using standard configurations. If the wireless is not configured, manual configuration may be 
required. Check wpa_supplicant.conf, interfaces for modifications.

For production purposes do not use the option -t or --testing with pi_final_setup.py. It obtains an invalid certificate for testing purposes. For futher
details check https://letsencrypt.org/docs/staging-environment/

Email address is required by pi_final_setup.py to setup TLS on the raspberrypi. The certificate is obtained from letsencrypt and they require email address
for notifying in case of certificate expiring and for revoking certificates.




