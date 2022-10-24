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
"""AFC System to AFC Device Interface Common Classes - SDI v1.3"""

from dataclasses import dataclass
from typing import Any

@dataclass
class FrequencyRange:
  """Frequency Range specification for spectrum availabilty requests and responses

  Attributes:
    lowFrequency: lowest frequency in the range, expressed in MHz
    highFrequency: highest frequency in the range, expressed in MHz"""
  lowFrequency: int
  highFrequency: int

  def __str__(self):
    return f"lowFrequency: {self.lowFrequency}\nhighFrequency: {self.highFrequency}"

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
    dicts (list[dict]): list of dictionarys for instantiation as objects
    cls (class type): target class for dictionary conversion

  Returns:
    dicts with all dictionaries converted to objects of type cls"""
  return [cls(**x) if isinstance(x, dict) else x for x in dicts]
