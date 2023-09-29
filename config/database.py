from masoniteorm.connections import ConnectionResolver

DATABASES = {
  "default": "mysql",
  "mysql": {
    "host": "localhost",
    "driver": "mysql",
    "database": "seismic",
    "user": "root",
    "password": "",
    "port": 3306,
    "log_queries": False,
  }
}

DB = ConnectionResolver().set_connection_details(DATABASES)