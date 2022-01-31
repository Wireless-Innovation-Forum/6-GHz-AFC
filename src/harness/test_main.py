#    Copyright 2022 6 GHz AFC Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
"""Top main script of the test harness.

If writing your own top level script to run the test harness,
look here how the setup is performed.
"""

import argparse
import logging
import sys

#----------------------------------------
# Setup the command line arguments
parser = argparse.ArgumentParser(description='Test Main')
# - Generic config.
parser.add_argument('--log_level', type=str, default='info',
                    help='Logging level: debug, info, warning or error')

# Setup the logger
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter(
        '[%(levelname)s] %(asctime)s %(filename)s:%(lineno)d %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

_LOGGER_MAP = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR
}

