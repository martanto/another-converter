from masoniteorm.models import Model

class SeismicChannel(Model):
    
    __primary_key__ = "id"
    
    __fillable__ = [
        'code',
        'slug_peralatan',
        'scnl',
        'is_active'
    ]