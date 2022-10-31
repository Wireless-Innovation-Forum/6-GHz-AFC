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
"""AFC SUT Test Harness Logging

Implements logging options for:
  Python logging framework
  Log files
  Console logging"""

import logging

def auto_run_non_python_logging(logging_func):
  """Decorator for calling non-python logging implementation on all logging levels"""

  def wrapper(*args):
    if args[0]._logger is not None:
      logging_func(args[0], args[1])
    if args[0].append_msg_level:
      final_msg = f'({logging_func.__name__[1:].upper()}) {args[1]}'
    else:
      final_msg = args[1]
    args[0]._file_log(final_msg)
    args[0]._console_log(final_msg)
  return wrapper

class ConsoleInfoModuleFilter(logging.Filter):
  """Logging filter that only permits level INFO if the message is from the main function"""
  def filter(self, record: logging.LogRecord):
    if record.levelno != logging.INFO or record.funcName == 'main':
      return True
    else:
      return False

class TestHarnessLogger:
  """Base class for handling various logging implementations

  Can use python logging framework (recommended), a log file, or echo to the console.
  Introduced originally before rest of harness code used the logging framework.
  May be revised/removed in future releases, depending on how the logging structure evolves.

  Properties:
    echo_log (bool): Enable echoing long messages to the console
    append_msg_level (bool): Includes the message level in console and log file output
                             Has no effect on logging framework output"""
  echo_log: bool
  append_msg_level: bool
  _logger: logging.Logger = None
  _log_file: str = None

  def __init__(self, logger=None, echo_log=False, append_level=True):
    if isinstance(logger, str):
      self._log_file = logger
    elif isinstance(logger, logging.Logger):
      self._logger = logger
    self.echo_log = echo_log
    self.append_msg_level = append_level

  @auto_run_non_python_logging
  def _fatal(self, msg):
    if self._logger is not None:
      self._logger.fatal(msg)

  @auto_run_non_python_logging
  def _error(self, msg):
    if self._logger is not None:
      self._logger.error(msg)

  @auto_run_non_python_logging
  def _warning(self, msg):
    if self._logger is not None:
      self._logger.warning(msg)

  @auto_run_non_python_logging
  def _info(self, msg):
    if self._logger is not None:
      self._logger.info(msg)

  def _file_log(self, msg):
    if self._log_file is not None:
      with open(self._log_file, 'a', encoding='utf-8') as flog:
        flog.write(msg +'\n')

  def _console_log(self, msg):
    if self.echo_log:
      print(msg)
