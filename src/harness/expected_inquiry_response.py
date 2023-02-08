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
"""Expected Available Spectrum Inquiry Response Definitions"""

from dataclasses import dataclass
from contextlib import suppress
from operator import attrgetter
from typing import Union

from interface_common import FrequencyRange, init_from_dicts
import available_spectrum_inquiry_response as afc_resp

@dataclass
class ExpectedPowerRange:
  """Expected Power Range for Response Validation

  Describes the bounds on the expected power permitted in a frequency range or channel

  Attributes:
    upperBound: Maximum acceptable value (inclusive) [required]
    nominalValue: The anchor point of the expected value [Default: None]
    lowerBound: Minimum acceptable value (inclusive) [Default: -inf]
  """
  upperBound: Union[float, int]
  nominalValue: Union[float, int] = None
  lowerBound: Union[float, int] = None

  def __post_init__(self):
    if self.lowerBound is None:
      self.lowerBound = float('-inf')

  # Use @classmethod to make new constructors for other types of bounds,
  #   if desired (fixed +/- range, std, etc.)
  # Example:
  # @classmethod
  # def from_equal_bounds(cls, nominalValue, bound):
  #   return cls(nominalValue=nominalValue, upperBound=(nominalValue + bound),
  #              lowerBound=(nominalValue - bound)

  def in_range(self, val: Union[float, int]):
    """Determines if a value satisfies the ExpectedPowerRange

    Parameters:
      val (numeric): value to check

    Returns:
      True if val is in range (inclusive)
      False otherwise
    """
    return self.lowerBound <= val <= self.upperBound

  def __str__(self):
    if self.lowerBound == float('-inf'):
      return f'x <= {self.upperBound}'
    return (f'{self.lowerBound} <= '
            f'{self.nominalValue if self.nominalValue is not None else "x"} <= '
            f'{self.upperBound}')

@dataclass
class ExpectedAvailableFrequencyInfo:
  """Expected Available Frequency Information

  Reports the expected range in maximum allowed power for a given frequency range

  Attributes:
    frequencyRange: The frequency range restricted by maxPsd
      If initialized with a dict, dict will be converted to a FrequencyRange type
    maxPsd: Maximum permissible EIRP in any one MHz bin, expressed a a power
      spectral density with units of dBm/MHz. Stored as an expected range object to accommodate
      variance in AFC system calculation
  """
  frequencyRange: afc_resp.FrequencyRange
  maxPsd: ExpectedPowerRange

  def __post_init__(self):
    if isinstance(self.frequencyRange, dict):
      with suppress(TypeError):
        self.frequencyRange = FrequencyRange(**self.frequencyRange)

    if isinstance(self.maxPsd, dict):
      with suppress(TypeError):
        self.maxPsd = ExpectedPowerRange(**self.maxPsd)

@dataclass
class ExpectedAvailableChannelInfo:
  """Expected Available Channel Information

  Reports the expected range in maximum allowed power for given channels

  Attributes:
    globalOperatingClass: Used to define the channel center frequency indices
      and operating bandwidth
    channelCfi: List of channel center frequency indices that are available
    maxEirp: Maximum permissible EIRP for each channel in channelCfi, expressed in dBm. Stored as
      an expected range object to accommodate variance in AFC system calculation
  """
  globalOperatingClass: Union[float, int]
  channelCfi: list[Union[float, int]]
  maxEirp: list[ExpectedPowerRange]

  def __post_init__(self):
    with suppress(TypeError):
      self.maxEirp = init_from_dicts(self.maxEirp, ExpectedPowerRange)

@dataclass
class ExpectedSpectrumInquiryResponse:
  """Expected Spectrum Inquiry Response

  Contains the expected spectrum availability info for comparison to a received response

  Attributes:
    requestId: Unique ID provided in the spectrum request
    rulesetId: The regulatory rules used by the AFC System to determine availability
    expectedResponseCodes: List of allowable response codes that could be returned
                           (Vendor codes permitted by default, but warn)
    expectedFrequencyInfo: Expected spectrum availability expressed in terms of frequency ranges
    expectedChannelInfo: Expected spectrum availability expressed in terms of channels
    vendorExtensions: Optional vendor extensions
  """
  requestId: str
  rulesetId: str
  expectedResponseCodes: list[afc_resp.ResponseCode]
  expectedFrequencyInfo: list[ExpectedAvailableFrequencyInfo] = None
  expectedChannelInfo: list[ExpectedAvailableChannelInfo] = None
  vendorExtensions: list[afc_resp.VendorExtension] = None

  def __post_init__(self):
    with suppress(TypeError):
      for idx, code in enumerate(self.expectedResponseCodes):
        if not isinstance(code, afc_resp.ResponseCode):
          with suppress(ValueError):
            self.expectedResponseCodes[idx] = afc_resp.ResponseCode(code)
      self.disallowedResponseCodes = [code for code in afc_resp.ResponseCode
                                      if code not in self.expectedResponseCodes]
    if self.expectedFrequencyInfo is not None:
      with suppress(TypeError):
        self.expectedFrequencyInfo = init_from_dicts(self.expectedFrequencyInfo,
                                                      ExpectedAvailableFrequencyInfo)
        self.expectedFrequencyInfo.sort(key=attrgetter('frequencyRange.lowFrequency'))
    if self.expectedChannelInfo is not None:
      with suppress(TypeError):
        self.expectedChannelInfo = init_from_dicts(self.expectedChannelInfo,
                                                   ExpectedAvailableChannelInfo)
        self.expectedChannelInfo.sort(key=attrgetter('channelCfi'))

@dataclass
class ExpectedSpectrumInquiryResponseMessage:
  """Top-level Expected Spectrum Inquiry Response Message

  Contains expected responses to one or more spectrum inquiries

  Attributes:
    version: version number of the inquiry request
    expectedSpectrumInquiryResponses: list of expected responses to inquiry requests
    vendorExtensions: Optional vendor extensions
  """
  version: str
  expectedSpectrumInquiryResponses: list[ExpectedSpectrumInquiryResponse]
  vendorExtensions: list[afc_resp.VendorExtension] = None

  def __post_init__(self):
    with suppress(TypeError):
      self.expectedSpectrumInquiryResponses = init_from_dicts(
                                               self.expectedSpectrumInquiryResponses,
                                               ExpectedSpectrumInquiryResponse)
    if self.vendorExtensions is not None:
      with suppress(TypeError):
        self.vendorExtensions = init_from_dicts(self.vendorExtensions, afc_resp.VendorExtension)
