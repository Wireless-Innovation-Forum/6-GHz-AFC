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
'''AFC SUT Communication Module'''

from dataclasses import dataclass
from importlib import import_module
from typing import Union
from urllib.parse import urljoin, urlparse
import requests
from requests import auth
from requests.exceptions import SSLError

from test_harness_logging import TestHarnessLogger

# Disable insecure request warning (Valid server certificate is covered via attestation)
requests.packages.urllib3.disable_warnings(requests.urllib3.exceptions.InsecureRequestWarning)

@dataclass
class ClientCertAuth:
  '''Contains information for client authentication via client-side certificates

  Attributes:
    client_cert (str): A path to the client certificate. If client_key is None,
                       this must be a combined cert/key file.
    client_key (str): A path to the private key file associated with the client_cert certificate.
                      Leave as None if client_cert is a combined cert/key file.'''
  client_cert: str
  client_key: str = None

  def get_cert_info(self):
    '''Returns the client cert and key in the format needed for the requests library "cert"
    parameter.

    If client_key is None, client_cert is returned as-is.
    Otherwise, a tuple of (client_cert, client_key) is returned.'''
    if self.client_key is None:
      return self.client_cert
    return (self.client_cert, self.client_key)

class AfcConnectionHandler(TestHarnessLogger):
  '''Handles sending requests to and receiving responses from an AFC using the supported
  authentication methods. Issues are logged using the TestHarnessLogger interface.

  Supported authentication methods include: None, Client-side HTTPS certificates, and custom
                                            methods that implement the requests library's AuthBase
                                            interface.

  At present, the default TLS settings from the requests library are used; no specific cipher
  suites or TLS version is requested by the test harness (subject to change).

  Attributes (Non-Inherited):
    base_url (str): AFC base url used for all possible AFC methods (e.g.,
                    "https://example-afc.com"). If a non-standard port is necessary, include it
                    after the hostname as usual ("https://example-afc.com:5834"). Non-HTTPS servers
                    are not allowed, per the SDI spec.
    method_url (str): The method endpoint for the desired AFC method (default:
                      "availableSpectrumInquiry"). This will be joined with the base_url to obtain
                      the full URL used for the POST request.
    auth_info (ClientCertAuth or AuthBase): Client authentication info. May be None if the AFC does
                                            not enforce client authentication, or it may be one of
                                            the supported auth types (ClientCertAuth or a object
                                            implmeneting the request library's AuthBase interface).
    timeout (float): The timeout to be used for all network operations, in seconds.'''
  base_url: str
  method_url: str = "availableSpectrumInquiry"
  auth_info: Union[ClientCertAuth, auth.AuthBase] = None
  timeout: float = 10.0
  _resp: requests.Response = None

  def __init__(self, connection, *args, auth_info: dict = None, **kwargs):
    '''Creates an instance of AfcConnectionHandler

    Parameters (Non-Inherited):
      connection (dict or str): A dictionary containing keys for base_url (required),
                                method_url (optional), and timeout (optional). If a string is
                                given, the value is used for base_url, and method_url and timeout
                                are left as their default values.
      auth_info (dict): A dictionary containing the options for client authentication.
                      These include:
                        type (str): "none", "cert" [ClientCertAuth-type], "custom" [AuthBase-type]
                        options (dict): Allowed options depend on auth_info->type.
                          Type "none": Entire dict is ignored.
                          Type "cert": Expect options matching attributes of ClientCertAuth
                          Type "custom":
                            auth_module (str): Path to python module containing desired auth class
                            auth_class (str): Name of python class implementing AuthBase
                            auth_config (dict): Any additional options required by auth_class'''
    super().__init__(*args, **kwargs)

    if isinstance(connection, dict):
      self._set_connection(**connection)
    else:
      self._set_connection(base_url=connection)
    if auth_info is not None:
      match auth_info.get('type', '').lower():
        case 'none' | '':
          self.auth_info = None
        case 'cert':
          self.auth_info = ClientCertAuth(**(auth_info['options']))
        case 'custom':
          auth_module = import_module(auth_info['options']['auth_module'])
          auth_class = getattr(auth_module, auth_info['options']['auth_class'])
          self.auth_info = auth_class(auth_info['options'].get('auth_config'))

  def _set_connection(self, base_url, method_url=None, timeout=None):
    self.base_url = base_url
    if method_url is not None:
      self.method_url = method_url
    if timeout is not None:
      self.timeout = timeout

  def _base_send_request(self, **kwargs):
    # Require HTTPS to enforce server certificate usage by AFC
    if urlparse(self.base_url).scheme != 'https':
      self._resp = None
      self._warning('Requested a non-https URL, which is disallowed.')
      raise ValueError('Non-https URLs are not permitted')

    # Add the hostname HTTP header required by the SDI spec
    # Do not perform any validation of the provided server certificate
    self._resp = requests.post(urljoin(self.base_url, self.method_url),
                               headers={'host': urlparse(self.base_url).hostname},
                               timeout=self.timeout,
                               verify=False,
                               **kwargs)

  def send_request(self, request_json: dict):
    '''Performs an HTTP Post request with the provided dictionary encoded as JSON.
    Results of any previous request are cleared, and the result of this request stored in
    the AfcConnectionHandler object for access.

    Parameters:
      request_json (dict): Request payload to be POSTed

    Returns:
      None [Result of POST can be accessed using get_last_response() and get_last_http_code()]

    Raises:
      ValueError if the configured base_url does not have an https prefix'''
    # Remove existing response
    self._resp = None

    match self.auth_info:
      case ClientCertAuth():
        try:
          self._base_send_request(cert=self.auth_info.get_cert_info(), json=request_json)
        except SSLError as ex:
          self._resp = None # Ensure response field is None to indicate missing response
          self._warning('Unable to establish secure connection with AFC; possibly a client cert '
                       f'validation error? Exception details: {ex}')

      case auth.AuthBase():
        self._base_send_request(auth=self.auth_info, json=request_json)
      case None:
        self._base_send_request(json=request_json)

  def get_last_response(self, as_json=True):
    """Gets the content received in response to the most recent request,
    if a valid response exists.

    Parameters:
      as_json (bool): If True, the response content will be JSON-decoded and returned as a dict.
                      Otherwise, the raw response content will be returned.

    Returns:
      The content of the most recent request, if any

    Raises:
      requests.exceptions.JSONDecodeError if as_json is True but the response content was not valid
        JSON."""
    if self._resp is None:
      return None
    if as_json:
      return self._resp.json()
    return self._resp.content

  def get_last_http_code(self):
    """Gets the HTTP response code received in respoonse to the most recent request, if a valid
    response exists.

    Returns:
      Ff a valid response is available: the response HTTP status code as an int
      Otherwise: None"""
    if self._resp is None:
      return None
    return self._resp.status_code

  def get_afc_url(self):
    '''Helper function for concatenating base_url and method_url.

    Returns:
      The full URL used for AFC communication'''
    return urljoin(self.base_url, self.method_url)

def main():
  """Example usage of AfcConnectionHandler.
  Loads the AFC connection configuration from a TOML file
  Sends request_sample.json
  Looks at the response code and received JSON dict"""
  with open('cfg/afc.toml', 'rb') as config_file:
    afc_config = tomli.load(config_file)
  afc_obj = AfcConnectionHandler(**afc_config)
  with open('request_sample.json', encoding='utf-8') as fin:
    req_json = json.load(fin)

  afc_obj.send_request(req_json)

  print(f'Status Code: {afc_obj.get_last_http_code()}')
  print(f'Response data: {afc_obj.get_last_response()}')

if __name__ == '__main__':
  import json
  import tomli
  main()
