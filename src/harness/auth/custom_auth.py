#    Copyright 2022 AFC Project Authors. All Rights Reserved.
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
'''Example implementation of a custom AFC authentication method

Custom authentication implementations should inherit from requests.auth.AuthBase and modify the
request object as necessary within the __call__ method.

The __init__ method should also take a single argument for configuration purposes, even if no extra
info is required by this implementation. The AfcConnectionHandler class will instantiate this auth
method by passing the content of auth_info.options.auth_config from the AFC config file. If no
extra info is required, this field should be set to some empty value ({}, "", etc.) in the config
file. Multiple configuration values can be provided by passing a table/dict for
auth_info.options.auth_config, as is done in this example.'''

from requests.auth import AuthBase

class TokenFileAuth(AuthBase):
  '''Implements bearer token authentication using the full contents of a file as the token.
  The path to the token file is provided in the config dict under "token_file"'''
  def __init__(self, config):
    token_file = config['token_file']
    with open(token_file, encoding='utf-8') as token_file:
      self.token = token_file.read()

  def __call__(self, r):
    '''This is where any authentication-related changes to the request message should be made. This
    method will be called by the test harness just before sending each request to the AFC.

    For bearer token solutions, this involves adding the Bearer token string as the Authorization
    HTTP header. More complex implementations that have time-varying tokens should take any actions
    needed to get a current token, and then modify the header accordingly.'''
    r.headers["Authorization"] = "Bearer " + self.token
    return r
