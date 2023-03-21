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
"""AFC System to AFC Device Interface Common Classes - SDI Protocol v1.3"""

from dataclasses import dataclass
from typing import Any
import enum

@dataclass
class FrequencyRange:
  """Frequency Range specification for spectrum availability requests and responses

  Ranges run from lowFrequency (inclusive) up to but not including highFrequency,
  that is: the range [lowFrequency, highFrequency). Current SDI spec (as of protocol document v1.4)
  does not specify this interpretation, but it is implied by the spec's sample_response (contiguous
  frequency ranges sharing a high/low freq value)

  Attributes:
    lowFrequency: lowest frequency in the range, expressed in MHz
    highFrequency: highest frequency in the range, expressed in MHz"""
  lowFrequency: int
  highFrequency: int

  def overlaps(self, other: 'FrequencyRange'):
    """Determines if two FrequencyRange objects define overlapping ranges

    Per current interpretation of SDI spec, a range with a high frequency of X does not overlap a
    range with low frequency of X

    Parameters:
      other (FrequencyRange): Other range to check for overlap

    Returns:
      True if ranges overlap (At least one range endpoint is contained within the other range
      False otherwise"""
    return self.lowFrequency < other.highFrequency and other.lowFrequency < self.highFrequency

  def __str__(self):
    return f"lowFrequency: {self.lowFrequency}\nhighFrequency: {self.highFrequency}"

@enum.unique
class ResponseCode(enum.Enum):
  """Available Spectrum Inquiry Response Code Definition

  Reports success or failure of an available spectrum inquiry

  Code -1 represents a general failure
  Code  0 represents success
  Codes 100-199 represent errors related to the protocol
  Codes 300-399 represent errors specific to message exchanges
    for the inquiry
  """

  GENERAL_FAILURE = -1
  SUCCESS = 0
  VERSION_NOT_SUPPORTED = 100
  DEVICE_DISALLOWED = 101
  MISSING_PARAM = 102
  INVALID_VALUE = 103
  UNEXPECTED_PARAM = 106
  UNSUPPORTED_SPECTRUM = 300
  UNSUPPORTED_BASIS = 301
  # Other vendor specific codes are allowed by specification
  # Adding new enum values at runtime not supported by stdlib enum
  # Could add vendor codes to list or use 3rd party aenum class to add
  #   unexpected codes at runtime
  # Currently, Response object creation will try to reference ResponseCode
  #   enum--if it fails, it falls back to a plain int. All validation checks
  #   are performed against the enum's value using get_raw_value
  #VENDOR_SPECIFIC = "VENDOR_SPECIFIC"

  @classmethod
  def get_raw_value(cls, code):
    """Returns the raw value of an unknown-typed ResponseCode

    Parameters:
      code (ResponseCode or int): response code to convert to raw value

    Returns:
      raw response code values as an int
    """
    if isinstance(code, int):
      return code
    elif isinstance(code, ResponseCode):
      return code.value
    else:
      return None

  def __repr__(self):
    return f"ResponseCode({self.value})"

@dataclass
class VendorExtension:
  """Standard Vendor Extension Interface

  Attributes:
    extensionId: Identifies the vendor and field type of an extension
    parameters: The payload as specified by the extension corresponding
      to extensionId
  """
  extensionId: str
  parameters: Any

def init_from_dicts(dicts: list[dict], cls):
  """Converts all dicts in a list to the specified type

  Any non-dict objects in the list are unmodified

  Parameters:
    dicts (list[dict]): list of dictionaries for instantiation as objects
    cls (class type): target class for dictionary conversion

  Returns:
    dicts with all dictionaries converted to objects of type cls"""
  return [cls(**x) if isinstance(x, dict) else x for x in dicts]
