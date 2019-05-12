

import re
import os
import time
import logging
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

import config_measurements

DIRECTORY_FILE = os.path.dirname(os.path.abspath(__file__))

DIRECTORY_RAW = os.path.join(DIRECTORY_FILE, '0_raw')
DIRECTORY_CONDENSED = os.path.join(DIRECTORY_FILE, '1_condensed')
DIRECTORY_RESULT = os.path.join(DIRECTORY_FILE, '2_result')

RE_CONFIG_CHANNEL = re.compile('run_config_(?P<channel>.*?).py')

class PyMeas2019:
  def __init__(self):
    for directory in (DIRECTORY_RAW, DIRECTORY_CONDENSED, DIRECTORY_RESULT):
      if not os.path.exists(directory):
        os.makedirs(directory)

class ConfigFile:
  def __init__(self, config_filename):
    self.pymeas2019 = PyMeas2019()
    self.config_filename = os.path.basename(config_filename)
    self.dict_channel = {}
    self.dict_channel.update(config_measurements.defaults)

    with open(config_filename) as f:
      dict_globals = {}
      exec(f.read(), dict_globals)
      self.dict_channel.update(dict_globals['config'])

    match = RE_CONFIG_CHANNEL.match(self.config_filename)


    assert match is not None
    channel_name = match.group('channel')
    self.dict_channel['channel_name'] = channel_name


    pass


