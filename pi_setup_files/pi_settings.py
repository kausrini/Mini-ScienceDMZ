#!/usr/bin/env python3

import sys

# Store your registered Domain name here.
DOMAIN_NAME = ''


# Checks if valid values entered for setup settings in pi_settings.py file
def test_values():

    if not len(DOMAIN_NAME):
        print('[ERROR] The pi_settings.py file does not have a valid DOMAIN_NAME.\n'
              'Check the instructions for DOMAIN_NAME in the Readme file'
              )
        sys.exit()


