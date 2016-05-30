#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 mengskysama
# Copyright 2016 Howard Liu
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import os
import logging
import thread
import config
import time
import subprocess

if config.LOG_ENABLE:
    logging.basicConfig(format=config.LOG_FORMAT,
                        datefmt=config.LOG_DATE_FORMAT, filename=config.LOG_FILE, level=config.LOG_LEVEL)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
import manager
from dbtransfer import DbTransfer


def handler_SIGQUIT():
    return


def main():
    configer = {
        'server': config.SS_BIND_IP,
        'local_port': 1081,
        'port_password': {},
        'method': config.SS_METHOD,
        'manager_address': '%s:%s' % (config.MANAGE_BIND_IP, config.MANAGE_PORT),
        'timeout': config.SS_TIMEOUT,
        'fast_open': config.SS_FASTOPEN,
        'verbose': config.SS_VERBOSE,
        'one_time_auth': config.SS_OTA,
        'forbidden_ip': config.SS_FORBIDDEN_IP,
        'banned_ports': config.SS_BAN_PORTS
    }
    logging.info('\nMulti-User Shadowsocks Server Starting...')
    logging.info('Current Server Version: %s' % subprocess.check_output(["git", "describe"]))
    thread.start_new_thread(manager.run, (configer,))
    time.sleep(1)
    thread.start_new_thread(DbTransfer.thread_db, ())
    time.sleep(1)
    thread.start_new_thread(DbTransfer.thread_push, ())
    
    while True:
        time.sleep(100)



if __name__ == '__main__':
    main()
