#!/usr/bin/python
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

import logging
import time
import socket
import config
import json
import urllib
# TODO: urllib2 does not exist in python 3.5+
import urllib2
if not config.API_ENABLED:
	import cymysql

class DbTransfer(object):

    instance = None

    def __init__(self):
        self.last_get_transfer = {}

    @staticmethod
    def get_instance():
        if DbTransfer.instance is None:
            DbTransfer.instance = DbTransfer()
        return DbTransfer.instance

    @staticmethod
    def send_command(cmd):
        data = ''
        try:
            cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            cli.settimeout(2)
            cli.sendto(cmd, ('%s' % config.MANAGE_BIND_IP, config.MANAGE_PORT))
            data, addr = cli.recvfrom(1500)
            cli.close()
            # TODO: bad way solve timed out
            time.sleep(0.05)
        except Exception as e:
            if config.SS_VERBOSE:
                import traceback
                traceback.print_exc()
            logging.warn('Exception thrown when sending command: %s' % e)
        return data

    @staticmethod
    def get_servers_transfer():
        dt_transfer = {}
        cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cli.settimeout(2)
        cli.sendto('transfer: {}', (config.MANAGE_BIND_IP, config.MANAGE_PORT))
        while True:
            data, addr = cli.recvfrom(1500)
            if data == 'e':
                break
            data = json.loads(data)
            # print data
            dt_transfer.update(data)
        cli.close()
        return dt_transfer

    def push_db_all_user(self):
        dt_transfer = self.get_servers_transfer()

        if config.API_ENABLED:
            i = 0
            if config.SS_VERBOSE:
                logging.info('api upload: pushing transfer statistics')
            users = DbTransfer.pull_api_user()
            for port in dt_transfer.keys():
                user = None
                for result in users:
                    if str(result[0]) == port:
                        user = result[9]
                        break
                if not user:
                    logging.warn('U[%s] User Not Found', port)
                    server = json.loads(DbTransfer.get_instance().send_command(
                        'stat: {"server_port":%s}' % port))
                    if server['stat'] != 'ko':
                        logging.info(
                            'U[%s] Server has been stopped: user is removed' % port)
                        DbTransfer.send_command(
                            'remove: {"server_port":%s}' % port)
                    continue
                if config.SS_VERBOSE:
                    logging.info('U[%s] User ID Obtained:%s' % (port, user))
                tran = str(dt_transfer[port])
                data = {'d': tran, 'node_id': config.NODE_ID, 'u': '0'}
                url = config.API_URL + '/users/' + \
                    str(user) + '/traffic?key=' + config.API_PASS
                data = urllib.urlencode(data)
                req = urllib2.Request(url, data)
                response = urllib2.urlopen(req)
                the_page = response.read()
                if config.SS_VERBOSE:
                    logging.info('%s - %s - %s' % (url, data, the_page))
                i += 1

            # online user count
            if config.SS_VERBOSE:
                logging.info('api upload: pushing online user count')
            data = {'count': i}
            url = config.API_URL + '/nodes/' + config.NODE_ID + \
                '/online_count?key=' + config.API_PASS
            data = urllib.urlencode(data)
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req)
            the_page = response.read()
            if config.SS_VERBOSE:
                logging.info('%s - %s - %s' % (url, data, the_page))

            # load info
            if config.SS_VERBOSE:
                logging.info('api upload: pushing node status')
            url = config.API_URL + '/nodes/' + config.NODE_ID + '/info?key=' + config.API_PASS
            f = open("/proc/loadavg")
            load = f.read().split()
            f.close()
            loadavg = load[0] + ' ' + load[1] + ' ' + \
                load[2] + ' ' + load[3] + ' ' + load[4]
            f = open("/proc/uptime")
            uptime = f.read().split()
            uptime = uptime[0]
            f.close()
            data = {'load': loadavg, 'uptime': uptime}
            data = urllib.urlencode(data)
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req)
            the_page = response.read()
            if config.SS_VERBOSE:
                logging.info('%s - %s - %s' % (url, data, the_page))
                logging.info('api uploaded')
        else:
            query_head = 'UPDATE `user`'
            query_sub_when = ''
            query_sub_when2 = ''
            query_sub_in = None
            last_time = time.time()
            for port in dt_transfer.keys():
                query_sub_when += ' WHEN %s THEN `u`+%s' % (port, 0)  # all in d
                query_sub_when2 += ' WHEN %s THEN `d`+%s' % (
                    port, dt_transfer[port])
                if query_sub_in is not None:
                    query_sub_in += ',%s' % port
                else:
                    query_sub_in = '%s' % port
            if query_sub_when == '':
                return
            query_sql = query_head + ' SET u = CASE port' + query_sub_when + \
                ' END, d = CASE port' + query_sub_when2 + \
                ' END, t = ' + str(int(last_time)) + \
                ' WHERE port IN (%s)' % query_sub_in
            # print query_sql
            conn = cymysql.connect(host=config.MYSQL_HOST, port=config.MYSQL_PORT, user=config.MYSQL_USER,
                                   passwd=config.MYSQL_PASS, db=config.MYSQL_DB, charset='utf8')
            cur = conn.cursor()
            cur.execute(query_sql)
            cur.close()
            conn.commit()
            conn.close()
            if config.SS_VERBOSE:
                logging.info('db uploaded')

    @staticmethod
    def del_server_out_of_bound_safe(rows):
        for row in rows:
            server = json.loads(DbTransfer.get_instance().send_command(
                'stat: {"server_port":%s}' % row[0]))
            if server['stat'] != 'ko':
                if row[5] == 0 or row[6] == 0:
                    # stop disabled or switched-off user
                    logging.info(
                        'U[%d] Server has been stopped: user is disabled' % row[0])
                    DbTransfer.send_command(
                        'remove: {"server_port":%d}' % row[0])
                elif row[1] + row[2] >= row[3]:
                    # stop user that exceeds bandwidth limit
                    logging.info(
                        'U[%d] Server has been stopped: bandwith exceeded' % row[0])
                    DbTransfer.send_command(
                        'remove: {"server_port":%d}' % row[0])
                elif server['password'] != row[4]:
                    # password changed
                    logging.info(
                        'U[%d] Server is restarting: password is changed' % row[0])
                    DbTransfer.send_command(
                        'remove: {"server_port":%d}' % row[0])
                else:
                    if not config.CUSTOM_METHOD:
                        row[7] = config.SS_METHOD
                    if server['method'] != row[7]:
                        # encryption method changed
                        logging.info(
                            'U[%d] Server is restarting: encryption method is changed' % row[0])
                        DbTransfer.send_command(
                            'remove: {"server_port":%d}' % row[0])
            else:
                if (row[5] == 1 or row[5] == "1") and row[6] == 1 and row[1] + row[2] < row[3]:
                    if not config.CUSTOM_METHOD:
                        row[7] = config.SS_METHOD
                    DbTransfer.send_command(
                        'add: {"server_port": %d, "password":"%s", "method":"%s", "email":"%s"}' % (row[0], row[4], row[7], row[8]))
                    if config.MANAGE_BIND_IP != '127.0.0.1':
                        logging.info(
                            'U[%s] Server Started with password [%s] and method [%s]' % (row[0], row[4], row[7]))

    @staticmethod
    def thread_db():
        socket.setdefaulttimeout(config.MYSQL_TIMEOUT)
        while True:
            try:
                rows = DbTransfer.pull_db_all_user()
                DbTransfer.del_server_out_of_bound_safe(rows)
            except Exception as e:
                if config.SS_VERBOSE:
                    import traceback
                    traceback.print_exc()
                logging.error('Except thrown while pulling user data:%s' % e)
            finally:
                time.sleep(config.CHECKTIME)

    @staticmethod
    def thread_push():
        socket.setdefaulttimeout(config.MYSQL_TIMEOUT)
        while True:
            try:
                DbTransfer.get_instance().push_db_all_user()
            except Exception as e:
                import traceback
                if config.SS_VERBOSE:
                    traceback.print_exc()
                logging.error('Except thrown while pushing user data:%s' % e)
            finally:
                time.sleep(config.SYNCTIME)

    @staticmethod
    def pull_db_all_user():
        if config.API_ENABLED:
            rows = DbTransfer.pull_api_user()
            if config.SS_VERBOSE:
                logging.info('api downloaded')
            return rows
        else:
            string = ''
            for index in range(len(config.SS_SKIP_PORTS)):
                port = config.SS_SKIP_PORTS[index]
                if config.SS_VERBOSE:
                    logging.info('db skipped port %d' % port)
                if index == 0:
                    string = ' WHERE `port`<>%d' % port
                else:
                    string = '%s AND `port`<>%d' % (string, port)
            conn = cymysql.connect(host=config.MYSQL_HOST, port=config.MYSQL_PORT, user=config.MYSQL_USER,
                                   passwd=config.MYSQL_PASS, db=config.MYSQL_DB, charset='utf8')
            cur = conn.cursor()
            cur.execute('SELECT port, u, d, transfer_enable, passwd, switch, enable, method, email FROM %s%s ORDER BY `port` ASC'
                        % (config.MYSQL_USER_TABLE, string))
            rows = []
            for r in cur.fetchall():
                rows.append(list(r))
            # Release resources
            cur.close()
            conn.close()
            if config.SS_VERBOSE:
                logging.info('db downloaded')
            return rows

    @staticmethod
    def pull_api_user():
        # Node parameter is not included for the ORIGINAL version of SS-Panel V3
        url = config.API_URL + '/users?key=' + config.API_PASS + '&node=' + config.NODE_ID
        f = urllib.urlopen(url)
        data = json.load(f)
        f.close()
        rows = []
        for user in data['data']:
            if user['port'] in config.SS_SKIP_PORTS:
                if config.SS_VERBOSE:
                    logging.info('api skipped port %d' % user['port'])
            else:
                rows.append([
                    user['port'],
                    user['u'],
                    user['d'],
                    user['transfer_enable'],
                    user['passwd'],
                    user['switch'],
                    user['enable'],
                    user['method'],
                    user['email'],
                    user['id']
                ])
        return rows
