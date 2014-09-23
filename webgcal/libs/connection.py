# -*- coding: utf-8 -*-
from django.db import connection
from swampdragon_auth.socketconnection import HttpDataConnection
from tornado import ioloop

class MysqlHeartbeatConnection(HttpDataConnection):
    def _close_db_connection(self):
        connection.close()

    def on_open(self, request):
        super(MysqlHeartbeatConnection, self).on_open(request)
        # Change the callback time to be closer to DB timeout
        iol = ioloop.IOLoop.current()
        self.db_heartbeat = ioloop.PeriodicCallback(self._close_db_connection, callback_time=300, io_loop=iol)
        self.db_heartbeat.start()

    def on_close(self):
        super(MysqlHeartbeatConnection, self).on_close()
        self._close_db_connection()
        self.db_heartbeat.stop()

    def on_message(self, data):
        self.db_heartbeat.stop()
        self.db_heartbeat.start()
        super(MysqlHeartbeatConnection, self).on_message(data)
