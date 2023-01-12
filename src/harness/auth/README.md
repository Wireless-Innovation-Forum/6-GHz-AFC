This directory contains implementation files for client authentication used by the test harness. It is recommended that any additional files needed for authentication (client certificates, bearer token files, etc.) are also stored here.

Information about the authentication methods available to the test harness are described in the default AFC configuration file in `../cfg/afc.toml`.

An example implementation using the "custom" authentication method is provided in `./custom_auth.py`.