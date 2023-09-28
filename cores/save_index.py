import os
import pandas as pd
import numpy as np
from config.config import Configuration
from obspy import read
from models.SeismicData import SeismicData

class SaveIndex:
    def __init__(self, overwrite=False):
        self.overwrite = overwrite

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
        availability = float(
            round((trace.stats.npts - count_zero_or_nan_value)/(trace.stats.sampling_rate*3600*24)*100,2)
		)
        return availability

    def get_filesize(self,filename):
        file_mseed = os.path.join(Configuration().get()['converted_directory'], filename)
        trace = read(file_mseed)[0]
        return trace.stats.mseed.filesize
    
    def update_or_create(self, attributes, values):
        exists = SeismicData.where('scnl', attributes['scnl']).where('date', attributes['date']).first()
        if not exists:
            merged_attributes_values = {**attributes, **values}
            print("==> Database CREATED")
            return SeismicData.create(merged_attributes_values)
        print("==> Database UPDATED")
        return exists.update(values)

    def save(self, filename, trace, date, db=False, csv=False, index_directory=None):
        attributes = {
            'scnl':self.get_scnl(trace),
            'date':date.strftime('%Y-%m-%d'),
        }

        values = {
            'filename':filename,
            'sampling_rate':self.get_sampling_rate(trace),
            'max_amplitude':float(abs(trace.max())),
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