import os
from obspy import Trace

class SDS:
    def __init__(self):
        pass

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
        return filename, path, full_path

    def save(self, output, trace=Trace):
        filename, path, full_path = self.get_directory(output, trace)
        print('>> Output : '+full_path)
        if self.file_not_exists(full_path):
            try:
                trace.write(full_path, format='MSEED', encoding='STEIM2')
            except:
                trace.data = trace.data.clip(-2e30, 2e30)
                trace.write(full_path, format='MSEED', encoding='STEIM2')
        return os.path.join(path,filename)
