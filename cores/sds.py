import os
from obspy import Trace
from obspy.clients.filesystem.sds import Client
import numpy as np
import pandas as pd

class SDS:
    def __init__(self, root_dir = None, overwrite=False):
        self.root_dir = root_dir
        self.overwrite = overwrite
        
    def check_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
        return self

    def file_not_exists(self, file):
        return not os.path.exists(file)

    def get_directory(self, output, trace):
        structure = {
            'year' : trace.stats.starttime.strftime('%Y'),
            'julian_day' : trace.stats.starttime.strftime('%j'),
            'station' : trace.stats.station,
            'channel' : trace.stats.channel,
            'type' : 'D',
            'network': trace.stats.network,
            'location': trace.stats.location
        }

        filename = '.'.join([
            structure['network'],
            structure['station'],
            structure['location'],
            structure['channel'],
            structure['type'],
            structure['year'],
            structure['julian_day']
        ])

        path = os.path.join(
            'SDS',
            structure['year'],
            structure['network'],
            structure['station'],
            structure['channel']+'.'+structure['type']
        )

        self.check_directory(os.path.join(output,path))
        full_path = os.path.join(output,path,filename)
        path = os.path.join(output,path)
        
        return filename, path, full_path

    def _converting_masked_array_to_pandas_then_to_numpy_array(self, trace_masked_array_data):
        return pd.DataFrame(trace_masked_array_data)[0].to_numpy(dtype=np.int32)

    def save(self, output, trace=Trace, encoding='STEIM2'):
        filename, path, full_path = self.get_directory(output, trace)
        
        if self.file_not_exists(full_path) or self.overwrite:
            trace.data = np.where(trace.data == -2 ** 31, 0, trace.data)
            trace.data = trace.data.astype(np.int32)

            if isinstance(trace.data, np.ma.masked_array):
                trace.data = self._converting_masked_array_to_pandas_then_to_numpy_array(trace.data)
            try:
                trace.write(full_path, format='MSEED', encoding=encoding)
            except:
                trace.data = trace.data.clip(-2e30, 2e30)
                trace.write(full_path, format='MSEED', encoding=encoding)

        is_overwrite = '(overwrite)' if self.overwrite else ''

        print('>> Output {}: {}'.format(is_overwrite, full_path))
        
        return os.path.join(path,filename)
