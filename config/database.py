from masoniteorm.connections import ConnectionResolver

DATABASES = {
  "default": "mysql",
  "mysql": {
    "host": "127.0.0.1",
    "driver": "mysql",
    "database": "seismic",
    "user": "homestead",
    "password": "secret",
    "port": 33060,
    "log_queries": False,
  }
}

DB = ConnectionResolver().set_connection_details(DATABASES)