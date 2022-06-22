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
"""Implementation of AfcInterface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

#from six.moves import configparser
import configparser

from request_handler import TlsConfig, RequestPost, RequestGet
import afc_interface

def GetTestingAfc():
  config_parser = configparser.RawConfigParser()
  config_parser.read(['afc.cfg'])
  admin_api_base_url = config_parser.get('AfcConfig', 'AdminApiBaseUrl')
  spd_afc_base_url = config_parser.get('AfcConfig', 'SpdAfcBaseUrl')
  return AfcImpl(spd_afc_base_url), AfcAdminImpl(admin_api_base_url)


def GetDefaultDomainProxySSLCertPath():
  return os.path.join('certs', 'domain_proxy.cert')


def GetDefaultDomainProxySSLKeyPath():
  return os.path.join('certs', 'domain_proxy.key')


class AfcImpl(afc_interface.AfcInterface):
  """Implementation of AfcInterface for AFC certification testing."""

  def __init__(self, spd_afc_base_url):
    self.spd_afc_base_url = spd_afc_base_url
    self._tls_config = TlsConfig()

  def SpectrumInquiry(self, request, ssl_cert=None, ssl_key=None):
    return self._SpdRequest('availablespectruminquiryrequest', request, ssl_cert, ssl_key)

 
  def _SpdRequest(self, method_name, request, ssl_cert=None, ssl_key=None):
    return RequestPost('http://%s/%s' % (self.spd_afc_base_url,
                                             method_name), request,
                       self._tls_config.WithClientCertificate(
                           ssl_cert or GetDefaultDomainProxySSLCertPath(),
                           ssl_key or GetDefaultDomainProxySSLKeyPath()))


class AfcAdminImpl(afc_interface.AfcAdminInterface):
  """Implementation of AfcAdminInterface for AFC certification testing."""

  def __init__(self, base_url):
    self._base_url = base_url
    self._tls_config = TlsConfig().WithClientCertificate(
        self._GetDefaultAdminSSLCertPath(), self._GetDefaultAdminSSLKeyPath())


  def Reset(self):
    RequestPost('https://%s/admin/reset' % self._base_url, None,
                self._tls_config)

 
  def InjectFs(self, request):
    RequestPost('https://%s/admin/injectdata/fs' % self._base_url, request,
                self._tls_config)

  
  def _GetDefaultAdminSSLCertPath(self):
    return os.path.join('certs', 'admin.cert')

  def _GetDefaultAdminSSLKeyPath(self):
    return os.path.join('certs', 'admin.key')

 
