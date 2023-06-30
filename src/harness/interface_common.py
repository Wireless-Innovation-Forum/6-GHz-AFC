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
"""AFC System to AFC Device Interface Common Classes - SDI Protocol v1.4"""

import dataclasses
from dataclasses import dataclass
from itertools import repeat
import json
from typing import Any
import enum

@dataclass
class FrequencyRange:
  """Frequency Range specification for spectrum availability requests and responses

  Ranges run from lowFrequency (inclusive) up to but not including highFrequency,
  that is: the range [lowFrequency, highFrequency). Current SDI spec (as of protocol document v1.5)
  does not specify this interpretation, but it is implied by the spec's sample_response (contiguous
  frequency ranges sharing a high/low freq value)

  Attributes:
    lowFrequency: lowest frequency in the range, expressed in MHz
    highFrequency: highest frequency in the range, expressed in MHz
  """
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
      False otherwise
    """
    return self.lowFrequency < other.highFrequency and other.lowFrequency < self.highFrequency

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

  def __str__(self):
    return self.name

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
    dicts with all dictionaries converted to objects of type cls
  """
  return [cls(**x) if isinstance(x, dict) else x for x in dicts]

class JSONEncoderSDI(json.JSONEncoder):
  """Modified version of JSONEncoder that serializes dataclasses and SDI-specific behavior."""
  def default(self, o):
    # Handle dataclasses by converting to dict and passing through clean_nones
    if dataclasses.is_dataclass(o):
      return self.clean_nones(dataclasses.asdict(o))
    # Handle ResponseCodes by using the raw numeric value
    elif isinstance(o, ResponseCode):
      return ResponseCode.get_raw_value(o)
    return super().default(o)

  @classmethod
  def clean_nones(cls, value):
    """Recursively remove all None values from dictionaries and lists, and returns
    the result as a new dictionary or list.
    Also removes -Infinity to handle ExpectedPowerRange lowerBound.
    Empty lists are left unmodified.

    Parameters:
      value: variable to be filtered

    Returns:
      Filtered variable with Nones and -infs removed
    """
    if isinstance(value, list):
      return [cls.clean_nones(x) for x in value if x is not None]
    elif isinstance(value, dict):
      try:
        return {
          key: cls.clean_nones(val)
          for key, val in value.items()
          if val is not None and val != float('-inf')
        }
      except:
        return {
          key: cls.clean_nones(val)
          for key, val in value.items()
          if val is not None and val != float('-inf')
        }
    else:
      return value

def pformat_sdi(o, indent=4) -> str:
  """Pretty-formats a string representation of a value, intended for use with
  SDI dataclass types.

  For non-dataclass objects, the formatted string is equivalent to str(o)
  
  Parameters:
    o (Any): Value to be formatted
    indent: Amount of spaces to indent each nested layer by (default: 4)
    
  Returns:
    The pretty-formatted string representation of an object
  """
  if dataclasses.is_dataclass(o):
    string_rep = ""
    for field in dataclasses.fields(o):
      value = getattr(o, field.name)
      if value is not None:
        if hasattr(value, "__len__") and any(dataclasses.is_dataclass(x) for x in value):
          # Non-scalar dataclass field
          for (idx, item) in enumerate(value):
            string_rep += f'{field.name}[{idx}]:' \
                        + (' '*indent).join(('\n'+pformat_sdi(item).lstrip()).splitlines(True)) \
                        + '\n'
          string_rep = string_rep.rstrip()
        elif hasattr(value, "__len__") and not isinstance(value, str):
          # Other non-scalar non-string fields
          string_rep += f'{field.name}: ' \
                      + str(value)[0] \
                      + ", ".join(map(pformat_sdi, value, repeat(indent))) \
                      + str(value)[-1]
        elif dataclasses.is_dataclass(value) and type(value).__str__ is object.__str__:
          # Scalar dataclass field with default __str__
          string_rep += f'{field.name}:' \
                      + (' '*indent).join(('\n'+pformat_sdi(value).lstrip()).splitlines(True))
        else:
          # Other fields
          string_rep += f'{field.name}: {value}'
        string_rep += '\n'
    return string_rep.rstrip()

  # For collections, ensure str() is used instead of repr()
  if hasattr(o, "__len__") and not isinstance(o, str):
    return f'{str(o)[0]}{", ".join(map(pformat_sdi, o, repeat(indent)))}{str(o)[-1]}'

  # Return normal string for scalar non-dataclasses
  return str(o)
