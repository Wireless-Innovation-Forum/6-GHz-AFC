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

'''tests_to_run.py establishes which tests to run.

For each test <test> in the list tests_to_run, the corresponding spectrum
inquiry file <test>.json must exist in the /inquiries directory. The
inquiry file is read by the test code, submitted to the SUT, and the
response from the SUT is compared to the allowed mask for that test.

If the first element of the list is 'all', all test files (*.json) that
are in the /inquiries directory are run. The contents of the list after
the first element ('all') are ignored.
'''

def tests_to_run():
  '''Returns the list of tests to be run'''
  return ['all',
          'AFCS.FSP.1',
          'AFCS.FSP.2',
          'AFCS.SIP.5',
          'AFCS.URS.4']
