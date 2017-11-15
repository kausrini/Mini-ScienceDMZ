#!/usr/bin/env python3

import sys

# DO NOT PUSH TO GIT AFTER ENTERING DYNV6_API_TOKEN. IT IS THE SAME AS A PASSWORD.
DYNV6_API_TOKEN = ''
DOMAIN_NAME = ''


# Checks if valid values entered for setup settings in pi_settings.py file
def test_values():
    failure = False
    if not len(DYNV6_API_TOKEN):
        print('[ERROR] The pi_settings.py file does not have a valid DYNV6_API_TOKEN.\n'
              'Check the instructions for dynv6 api tokens in the Readme file'
              )
        failure = True

    if not len(DOMAIN_NAME):
        print('[ERROR] The pi_settings.py file does not have a valid DOMAIN_NAME.\n'
              'Check the instructions for DOMAIN_NAME in the Readme file'
              )
        failure = True

    if failure:
        sys.exit()
