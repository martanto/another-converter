from orator import Model
from database import database as db

Model.set_connection_resolver(db)

class SdsIndex(Model):
    __table__ = 'sds_indexes'
    __fillable__ = ['filename', 'scnl', 'date', 'sampling_rate', 'min_amplitude', 'max_amplitude', 'availability']
    __dates__ = ['date']
