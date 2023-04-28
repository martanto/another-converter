from masoniteorm.models import Model

class SeismicData(Model):
    
    __primary_key__ = "id"
    
    __fillable__ = [
        'filename',
        'scnl',
        'date',
        'sampling_rate',
        'max_amplitude',
        'availability',
        'filesize'
    ]
    
#     __dates__ = [
#         'date'
#     ]
    
#     def set_date_attribute(self, date):
#         return date.strftime("%Y-%m-%d")