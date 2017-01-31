FROM python:2.7-alpine
MAINTAINER coderfox<coderfox.fu@gmail.com>
COPY . /shadowsocks
WORKDIR /shadowsocks/shadowsocks
RUN pip install cymysql
CMD python servers.py
