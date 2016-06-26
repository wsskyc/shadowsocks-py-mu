About shadowsocks-python manyuser
=================================
This is a multi-user version of shadowsocks-python. Requires a mysql database or a panel which supports SS MU API.

Install instruction for database user
-------------------------------------
1. install MySQL Server 5.x.x
2. install cymysql library by `pip install cymysql`
3. create a database named `shadowsocks`
4. import `shadowsocks.sql` into `shadowsocks`
5. copy `config_example.py` to `config.py` and edit it following the notes inside (but DO NOT delete the example file). You do not need to edit the API section.
6. TestRun `cd shadowsocks && python servers.py` (not server.py)

Install instruction for MU API user
-----------------------------------
1. install a panel which supports MU API (the known one is [SS-Panel V3](https://github.com/orvice/ss-panel))
2. copy `config_example.py` to `config.py` and edit it following the notes inside (but DO NOT delete the example file). You do not need to edit the MySQL Database section.
3. TestRun `cd shadowsocks && python servers.py` (not server.py)

Reminders for Windows User
--------------------------
1. install pyuv by `pip install pyuv`
2. if git is not configured in your `%PATH%` environmental variable, you can create a file named `.nogit` to avoid using `git describe`

if no exception thown the server will startup. By default logging is enabled.
You should be able to see this kind of thing in `shadowsocks.log`(default log file name)
```
Jun 24 01:06:08 INFO -----------------------------------------
Jun 24 01:06:08 INFO Multi-User Shadowsocks Server Starting...
Jun 24 01:06:08 INFO Current Server Version: 3.1.0-1-gc2ac618

Jun 24 01:10:11 INFO api downloaded
Jun 24 01:10:13 INFO api skipped port 443
Jun 24 01:10:13 INFO Server Added:   P[XXXXX], M[rc4-md5], E[XXXXX@gmail.com]
Jun 24 01:10:13 INFO Server Added:   P[XXXXX], M[rc4-md5], E[XXXXX@gmail.com]
```

Explanation of the log output
-----------------------------
When adding server:

`P[XXX]` client port (assigned by database)

`M[XXX]` client encryption method

`E[XXX]` client email address

When data connection being established/blocked

`U[XXX]` client port (assigned by database)

`RP[XXX]` remote port (the port the client wants to connect)

`A[XXX-->XXX]` from the client address to the remote address

Database user table column
--------------------------
`passwd` server pass

`port` server port

`t` last connecting time

`u` upload transfer

`d` download transfer

`method` encryption method

`transfer_enable` if u + d > transfer_enable this server will be stop (method del_server_out_of_bound_safe in dbtransfer.py)

Compatibility with other frontend UIs
-------------------------------------
It is fully compatible (SS MU API) with [ss-panel V3](https://github.com/orvice/ss-panel).

Open source license
-------------------
This program is licensed under [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0)