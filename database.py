from orator import DatabaseManager
import json

with open('database.json') as db_config:
    DATABASES = json.load(db_config)
    print(type(DATABASES))

    database = DatabaseManager(DATABASES)