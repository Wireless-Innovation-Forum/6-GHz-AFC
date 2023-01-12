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
"""AFC Common SDI Validation - SDI v1.3

Validation functions will exhaustively test all fields (i.e.,
validation does not stop on the first failure, but will report all
observed failures"""

import re
import typing
import dataclasses
from typing import List
from test_harness_logging import TestHarnessLogger

from interface_common import FrequencyRange, VendorExtension

def is_list_of_type(val, subtype):
  """Checks if value is a list containing only members of the specified type

  Parameters:
    val (list[Any]): List to be validated
    subtype (type): Expected type in list

  Returns:
    True if val is a list containing only members of the specified type
    False otherwise"""
  is_valid = isinstance(val, list) and all(isinstance(x, subtype) for x in val)
  return is_valid

def common_sdi_validator(specific_logic):
  """Decorator for handling common validation tasks for AFC SDI

  Validates:
    Object can be converted to expected type if necessary
    All type hints are satisfied
    Any additional conditions specified by the wrapped method"""

  def wrapper(*args):
    target_class = list(typing.get_type_hints(specific_logic).values())[0]
    validation_target = args[0].get_as_type(args[1], target_class)
    if validation_target is not None:
      is_valid = args[0].validate_types(validation_target)
      is_valid &= specific_logic(args[0], validation_target)
      return is_valid
    args[0]._warning('Failed to validate dataclass representation')
    return False
  return wrapper

class SDIValidatorBase(TestHarnessLogger):
  """Shared validation functionality

  Manages how violations are logged
  Validates shared SDI message types
  Provides common functionality"""

  _supported_versions = ["1.3"]

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def get_as_type(self, src_obj, target_type):
    """Attempts to convert a dictionary to a specified type

    Parameters:
      src_obj (dict or target_type): Object for conversion
      target_type (type): Intended conversion type

    Returns:
      An object of type target_type based on src_obj or
      None if conversion is not supported"""
    conv_obj = None
    if isinstance(src_obj, dict):
      try:
        conv_obj = target_type(**src_obj)
      except TypeError as err:
        self._warning(f'Exception converting from obj dict: {err}')
    elif isinstance(src_obj, target_type):
      conv_obj = src_obj
    else:
      self._warning(f'Object for validation has unsupported type: {src_obj}')
    return conv_obj

  def validate_types(self, obj):
    """Checks that all fields in a dataclass match the specified type hint

    Does not support containers other than lists--nested lists are also not supported

    Parameters:
      obj (dataclass): object for type validation

    Returns:
      True if all fields satisfy the dataclass typehints, excluding empty non-required fields
      False otherwise"""
    is_valid = dataclasses.is_dataclass(obj)
    if is_valid:
      for field_name, field_def in obj.__dataclass_fields__.items():
        field_value = field_value = getattr(obj, field_name)
        if field_def.default is not None and field_value is None:
          is_valid = False
        elif field_value is not None and field_def.type != typing.Any:
          # Handle special case for lists (No other container types are allowed in spec)
          if typing.get_origin(field_def.type) == list:
            target_subtype = typing.get_args(field_def.type)[0]
            if not is_list_of_type(field_value, target_subtype):
              is_valid = False
              self._warning(f'{type(obj).__name__}.{field_name} has non '
                            f'list[{target_subtype.__name__}] value: {field_value}')
          # Handle non-list cases
          elif not isinstance(field_value, field_def.type):
            is_valid = False
            self._warning(f'{type(obj).__name__}.{field_name} has non '
                          f'{field_def.type.__name__} value: {getattr(obj, field_name)}')
    return is_valid

  @common_sdi_validator
  def validate_frequency_range(self, freq_range: FrequencyRange):
    """Validates a FrequencyRange object

    Checks:
      low_frequency must be strictly less than high_frequency

    Parameters:
      freq_range (FrequencyRange): range to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    is_valid = True
    # Require frequency order to be correct
    try:
      if freq_range.highFrequency <= freq_range.lowFrequency:
        is_valid = False
        self._warning(f'highFrequency ({freq_range.highFrequency}) should '
                      f'be greater than lowFrequency ({freq_range.lowFrequency})')
    except TypeError as ex:
      is_valid = False
      self._warning(f'Could not ensure correct ordering in frequency '
                    f'range (low: {freq_range.lowFrequency} high: {freq_range.highFrequency}: {ex}')
    return is_valid

  @common_sdi_validator
  def validate_vendor_extension(self, ext: VendorExtension):
    """Validates that a VendorExtension object satisfies the SDI spec

    Checks:
      No additional checks beyond the common type checks

    Parameters:
      ext (VendorExtension): VendorExtension to be validated

    Returns:
      True always"""
    return True

  def validate_version(self, version: str):
    """Validates a version string

    Checks:
      version must be of format n.m where n and m are non-negative integers

    Parameters:
      version (string): version string to be validated

    Returns:
      True if version string is valid
      False otherwise"""
    is_valid = True
    try:
      if re.match("\\A[0-9]+\\.[0-9]+\\Z", version) is None:
        is_valid = False
        self._warning(f'Invalid version string format: {version}')
    except TypeError:
      is_valid = False
      self._warning(f'Could not parse version string: {version}')

    if is_valid and version not in self._supported_versions:
      self._warning(f'Message version ({version}) is not in list of supported versions '
                    f'({self._supported_versions}). Errors in validation and comparison may '
                     'result.')
    return is_valid

  def validate_vendor_extension_list(self, exts: List[VendorExtension]):
    """Dispatches list of extensions to validate_vendor_extension

    Checks:
      All contained vendor extensions are valid

    Parameters:
      exts (List[VendorExtension]): list of VendorExtensions to be validated

    Returns:
      True if all are valid
      False otherwise"""
    is_valid = True
    if exts is not None:
      try:
        is_valid &= all([self.validate_vendor_extension(x) for x in exts])
      except TypeError as ex:
        self._warning(f'Exception caught validating vendor extensions: {ex}')
        is_valid = False
    return is_valid
