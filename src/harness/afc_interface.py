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
"""AFC interfaces for testing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc
import six

class AfcInterface(six.with_metaclass(abc.ABCMeta, object)):
  """WinnForum standardized interfaces.

  Includes AFC-SPD interface

  """

  @abc.abstractmethod
  def SpectrumInquiry(self, request, ssl_cert=None, ssl_key=None):
    """AFC-SPD SpectrumInquiry interface.

    Performs spectrum inquiry for SPDs.

    Request and response are both lists of dictionaries. Each dictionary
    contains all fields of a single request/response.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "spectrumInquiryRequest" and the value is a list of individual SPD
        spectrum inquiry requests (each of which is itself a dictionary).
      ssl_cert: Path to SSL cert file, if None, will use default cert file.
      ssl_key: Path to SSL key file, if None, will use default key file.
    Returns:
      A dictionary with a single key-value pair where the key is
      "spectrumInquiryResponse" and the value is a list of individual SPD
      spectrum inquiry responses (each of which is itself a dictionary).
    """
    pass


class AfcAdminInterface(six.with_metaclass(abc.ABCMeta, object)):
  """Minimal test control interface for the AFC under test."""


  @abc.abstractmethod
  def Reset(self):
    """AFC admin interface to reset the AFC between test cases."""
    pass


  @abc.abstractmethod
  def InjectFs(self, request):
    """AFC admin interface to inject FS information into AFC under test.

    Args:
      request: a fixed service receiver object.
    """
    pass
