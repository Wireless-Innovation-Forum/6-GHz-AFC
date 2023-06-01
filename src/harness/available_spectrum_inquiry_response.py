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
"""Available Spectrum Inquiry Response Definitions - SDI Protocol v1.4"""

from dataclasses import dataclass
from typing import Union
from contextlib import suppress

from interface_common import FrequencyRange, ResponseCode, VendorExtension, init_from_dicts

@dataclass
class SupplementalInfo:
  """Supplemental Info for Specific Response Codes

  Only one field should be populated to provide explanation for a specific
  response code value

  Attributes:
    missingParams: a list of names of missing parameters (ResponseCode.MISSING_PARAM)
    invalidParams: a list of names of parameters with invalid values
      (ResponseCode.INVALID_VALUE)
    unexpectedParams: a list of names of unexpected parameters (ResponseCode.UNEXPECTED_PARAM)
  """
  missingParams: list[str] = None
  invalidParams: list[str] = None
  unexpectedParams: list[str] = None

  def __str__(self):
    string_rep = ""
    if self.missingParams is not None:
      string_rep += f"\nmissingParams: {self.missingParams}"
    if self.invalidParams is not None:
      string_rep += f"\ninvalidParams: {self.invalidParams}"
    if self.unexpectedParams is not None:
      string_rep += f"\nunexpectedParams: {self.unexpectedParams}"
    return string_rep.strip()

@dataclass
class Response:
  """Response field for a inquiry response

  Attributes:
    responseCode: Numeric response code reporting success or failure
    shortDescription: Short description of the response indicated by responseCode
      May be human readable
    supplementalInfo: Contains supplemental info that can help resolve errors
      If initialized with a dict, dict will be converted to SupplementalInfo type
  """
  responseCode: Union[ResponseCode, int]
  shortDescription: str = None
  supplementalInfo: SupplementalInfo = None

  def __post_init__(self):
    if not isinstance(self.responseCode, ResponseCode):
      with suppress(ValueError):
        self.responseCode = ResponseCode(self.responseCode)

    if isinstance(self.supplementalInfo, dict):
      with suppress(TypeError):
        self.supplementalInfo = SupplementalInfo(**self.supplementalInfo)

  def __str__(self):
    string_rep = f"responseCode: {str(self.responseCode)}"
    if self.shortDescription is not None:
      string_rep += f"\nshortDescription: {self.shortDescription}"
    if self.supplementalInfo is not None:
      string_rep += f"\nsupplementalInfo: {str(self.supplementalInfo)}"
    return string_rep

@dataclass
class AvailableFrequencyInfo:
  """Available Frequency Information

  Reports the maximum power available in a given frequency range

  Attributes:
    frequencyRange: The frequency range restricted by maxPsd
      If initialized with a dict, dict will be converted to a FrequencyRange type
    maxPsd: Maximum permissible EIRP in any one MHz bin, expressed a a power
      spectral density with units of dBm/MHz
  """
  frequencyRange: FrequencyRange
  maxPsd: Union[float, int]

  def __post_init__(self):
    if isinstance(self.frequencyRange, dict):
      with suppress(TypeError):
        self.frequencyRange = FrequencyRange(**self.frequencyRange)

  def __str__(self):
    return ("frequencyRange:" +
      '\t'.join(('\n'+str(self.frequencyRange).lstrip()).splitlines(True)) +
      f"\nmaxPsd: {self.maxPsd}")

@dataclass
class AvailableChannelInfo:
  """Available Channel Information

  Reports the maximum power available in a given channel

  Attributes:
    globalOperatingClass: Used to define the channel center frequency indices
      and operating bandwidth
    channelCfi: List of channel center frequency indices that are available
    maxEirp: Maximum permissible EIRP for each channel in channelCfi, expressed in dBm
  """
  globalOperatingClass: Union[float, int]
  channelCfi: list[Union[float, int]]
  maxEirp: list[Union[float, int]]

  def __str__(self):
    return (f"globalOperatingClass: {self.globalOperatingClass}" +
        f"\nchannelCfi: {self.channelCfi}" +
        f"\nmaxEirp: {self.maxEirp}")

@dataclass
class AvailableSpectrumInquiryResponse:
  """Available Spectrum Inquiry Response

  Contains spectrum availability info in response to a received request

  Attributes:
    requestId: Unique ID provided in the spectrum request
    rulesetId: The regulatory rules used by the AFC System to determine availability
    response: Information about the outcome of the spectrum inquiry
    availableFrequencyInfo: Spectrum availability expressed in terms of frequency ranges
    availableChannelInfo: Spectrum availability expressed in terms of channels
    availabilityExpireTime: The time when the specified spectrum availability expires
    vendorExtensions: Optional vendor extensions
  """
  requestId: str
  rulesetId: str
  response: Response
  availableFrequencyInfo: list[AvailableFrequencyInfo] = None
  availableChannelInfo: list[AvailableChannelInfo] = None
  availabilityExpireTime: str = None
  vendorExtensions: list[VendorExtension] = None

  def __post_init__(self):
    if self.availableFrequencyInfo is not None:
      with suppress(TypeError):
        self.availableFrequencyInfo = init_from_dicts(self.availableFrequencyInfo,
                                                      AvailableFrequencyInfo)
    if self.availableChannelInfo is not None:
      with suppress(TypeError):
        self.availableChannelInfo = init_from_dicts(self.availableChannelInfo, AvailableChannelInfo)
    if isinstance(self.response, dict):
      with suppress(TypeError):
        self.response = Response(**self.response)
    if self.vendorExtensions is not None:
      with suppress(TypeError):
        self.vendorExtensions = init_from_dicts(self.vendorExtensions, VendorExtension)

  def __str__(self):
    string_rep = f"requestId: {self.requestId}\nrulesetId: {self.rulesetId}"
    if self.availableFrequencyInfo is not None:
      string_rep += "\navailableFrequencyInfo:"
      for freq_info in self.availableFrequencyInfo:
        string_rep += '\t'.join(('\n'+str(freq_info).lstrip()).splitlines(True))
    if self.availableChannelInfo is not None:
      string_rep += "\navailableChannelInfo:"
      for chan_info in self.availableChannelInfo:
        string_rep += '\t'.join(('\n'+str(chan_info).lstrip()).splitlines(True))
    if self.availabilityExpireTime is not None:
      string_rep += (f"\navailabilityExpireTime: {self.availabilityExpireTime}")
    string_rep += "\nresponse:" + '\t'.join(('\n'+str(self.response).lstrip()).splitlines(True))
    return string_rep

@dataclass
class AvailableSpectrumInquiryResponseMessage:
  """Top-level Spectrum Inquiry Response Message

  Contains responses to one or more spectrum inquiries

  Attributes:
    version: version number of the inquiry response
    availableSpectrumInquiryResponses: list of responses to inquiry requests
    vendorExtensions: Optional vendor extensions
  """
  version: str
  availableSpectrumInquiryResponses: list[AvailableSpectrumInquiryResponse]
  vendorExtensions: list[VendorExtension] = None

  def __post_init__(self):
    with suppress(TypeError):
      self.availableSpectrumInquiryResponses = init_from_dicts(
                                               self.availableSpectrumInquiryResponses,
                                               AvailableSpectrumInquiryResponse)
    if self.vendorExtensions is not None:
      with suppress(TypeError):
        self.vendorExtensions = init_from_dicts(self.vendorExtensions, VendorExtension)

  def __str__(self):
    string_rep = f"version: {self.version}\navailableSpectrumInquiryResponses:"
    for resp in self.availableSpectrumInquiryResponses:
      string_rep += '\t'.join(('\n'+str(resp).lstrip()).splitlines(True))
    return string_rep

def main():
  """Demonstrates loading and printing inquiry responses"""

  raw_obj = json.loads('{"version": "5",'
    '"availableSpectrumInquiryResponses": '
      '[{"requestId": "1", "response": {"responseCode": -1}, "rulesetId": "2"}, '
      '{"requestId": "2", "rulesetId": "4", "response": {"responseCode": 0}}]}')

  conv_obj = AvailableSpectrumInquiryResponseMessage(**raw_obj)
  print(conv_obj)
  with open('src/harness/response_sample.json', encoding="UTF-8") as sample_file:
    sample_json = json.load(sample_file)
    sample_conv = AvailableSpectrumInquiryResponseMessage(**sample_json)
    sample_conv2 = AvailableSpectrumInquiryResponseMessage(**sample_json)

    print(f"Repr for ResponseCode: {repr(ResponseCode.INVALID_VALUE)}")
    print(f"Messages from same source report equal: {sample_conv == sample_conv2}")
    print(f"Can recreate object from repr: {eval(repr(sample_conv)) == sample_conv}")
    print(sample_conv)

if __name__ == '__main__':
  import json
  main()
