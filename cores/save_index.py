import os
import pandas as pd
import numpy as np
import math
from config.config import Configuration
from cores.sds import SDS
from obspy import read
from models.SeismicData import SeismicData
from models.SeismicChannel import SeismicChannel

class SaveIndex:
    def __init__(self, overwrite=False, maximum = 0, rescan=False):
        self.overwrite = overwrite
        self.maximum = maximum
        self.config = Configuration().get()
        self.code = None if rescan else self.config['code']

    def _count_zero_or_nan_value(self, trace):
        count_nan = np.count_nonzero(np.isnan(trace.data))
        count_zero = np.count_nonzero(trace.data==0)
        return count_nan+count_zero
    
    def get_scnl(self,trace):
        scnl = trace.stats.station+'_'+trace.stats.channel+'_'+trace.stats.network+'_'+trace.stats.location
        return scnl

    def get_sampling_rate(self,trace):
        return float(round(trace.stats.sampling_rate, 2))

    def get_availability(self,trace):
        count_zero_or_nan_value = self._count_zero_or_nan_value(trace)
        availability = float(round((trace.stats.npts - count_zero_or_nan_value)/(trace.stats.sampling_rate*3600*24)*100,2))

        return availability

    def get_filesize(self,filename):
        file_mseed = os.path.join(self.config['converted_directory'], filename)
        trace = read(file_mseed)[0]
        return trace.stats.mseed.filesize
    
    def update_or_create(self, attributes, values):
        channel_exists = SeismicChannel.where('scnl', attributes['scnl']).first()
        if not channel_exists:
            SeismicChannel.create({
                'code' : self.code,
                'scnl' : attributes['scnl'],
                'is_active' : 1
            })
            
        exists = SeismicData.where('scnl', attributes['scnl']).where('date', attributes['date']).first()
        if not exists:
            merged_attributes_values = {**attributes, **values}
            SeismicData.create(merged_attributes_values)
            return print("==> Database CREATED")
        print("==> Database UPDATED")
        return exists.update(values)

    def update(self, filename, trace):
        scnl = self.get_scnl(trace)
        date = trace.stats.starttime.strftime('%Y-%m-%d')
        maximum = np.nanmax(trace.data)

        channels = {
            'scnl' : scnl,
            'is_active' : 1
        }
        
        attributes = {
            'scnl' : scnl,
            'date' : date,
        }
        
        values = {
            'filename' : filename,
            'sampling_rate' : self.get_sampling_rate(trace),
            'max_amplitude' : maximum,
            'availability' : self.get_availability(trace),
            'filesize' : trace.stats.mseed.filesize
        }
        
        seismic_data = SeismicData.where('scnl', scnl).where('date', date).first()
        status = 'new' if not seismic_data else 'old'
        
        SeismicChannel.update_or_create({'scnl' : scnl}, {'code' : self.code, 'is_active' : 1})
        
        while True:
            try:
                SeismicData.update_or_create(attributes, values)
            except:
                seismic_data = SeismicData.where('scnl', scnl).where('date', date).first()
                seismic_data.update(values)
            else:
                break

        info_txt = '{} {} {}'.format(date, scnl, status)
        log_txt = '{},{},{}'.format(date, scnl, status)
        
        return info_txt, log_txt

    def save(self, filename, trace, date, db=False, code=None, csv=False, index_directory=None):
        attributes = {
            'scnl':self.get_scnl(trace),
            'date':date.strftime('%Y-%m-%d'),
        }

        values = {
            'filename':filename,
            'sampling_rate':self.get_sampling_rate(trace),
            'max_amplitude':self.maximum,
            'availability':self.get_availability(trace),
            'filesize':self.get_filesize(filename)
        }
        

        if db:
            self.update_or_create(attributes, values)

        if csv:
            df = {
                'scnl' : [attributes['scnl']],
                'date' : [attributes['date']],
                'sampling_rate' : [values['sampling_rate']],
                'max_amplitude' : [values['max_amplitude']],
                'availability' : [values['availability']],
                'filesize' : [values['filesize']],
            }

            df = pd.DataFrame(df)

            file_csv = os.path.join(index_directory,attributes['scnl']+'.csv')

            if not os.path.isfile(file_csv):
                df.to_csv(file_csv, header=['scnl','date','sampling_rate','max_amplitude','availability','filesize'], index=False)
            elif self.overwrite:
                df.to_csv(file_csv, header=['scnl','date','sampling_rate','max_amplitude','availability','filesize'], index=False, mode='w+')
            else:
                df.to_csv(file_csv, mode='a', header=False, index=False)