import glob
import json
import datetime
import os
from fnmatch import fnmatch
from obspy import Stream, Trace, read
import numpy as np

class Configuration():
    '''
    Membaca Konfigurasi File \n
    Pastikan lokasi file config.json sudah sesuai 
    '''
    def __init__(self, location='config.json'):
        self.location = location
        pass

    def set_location(self, location):
        self.location = location
        return self

    def get_location(self):
        return self.location

    def get(self, type='default'):
        print('Reading configuration....')
        with open(self.get_location()) as file_config:
            config = json.load(file_config)
            config['type'][type]['start_date'] = datetime.datetime.strptime(config['type'][type]['start_date'],'%Y-%m-%d')
            config['type'][type]['end_date'] = datetime.datetime.strptime(config['type'][type]['end_date'],'%Y-%m-%d')
            return config['type'][type]

class Files():
    ''' Mendapatkan semua files sesuai konfigurasi pencarian '''
    def __init__(self):
        self.config = Configuration()

    def search_default(self):
        pass

    def search_sac(self):
        search_list = []
        stream_list = []
        self.config = self.config.get('sac')
        input_directory = self.config['input_directory']
        start_date = self.config['start_date']
        end_date = self.config['end_date']
        channels = self.config['channels']
        for n in range(int((end_date-start_date).days)+1):
            filter = start_date+datetime.timedelta(n)
            for root, folders, files in os.walk(input_directory):
                for folder in folders:
                    if filter.strftime('%Y%m%d') in folder:
                        channel_folder = os.path.join(root, folder)
                        for channel in channels:
                            channel_files = [f for f in glob.glob(channel_folder + "\\"+channel+'*', recursive=False)]
                            for channel_file in channel_files:
                                search_list.append(channel_file)
            stream_list.append(NewStream(search_list).get())
        return stream_list

    def get(self, search):
        print('Reading files....')
        searches = {
            'default': self.search_default(),
            'sac': self.search_sac(),
        }
        return searches.get(search, "Konfigurasi pencarian tidak ditemukan")

class NewStream():
    def __init__(self, files):
        self.files = files

    def get(self):
        list_traces = []
        for file in self.files:
            try:
                stream = read(file)
                # print(stream[0].stats)
            except:
                pass
            else:
                list_traces.append(stream[0])

        return Stream(list_traces)

class NewTrace():
    def __init__(self):
        pass

    def get_channel(self, channel):
        if 'Z' in channel:
            return 'EHZ'
        if 'N' in channel:
            return 'EHN'
        if 'E' in channel:
            return 'EHE'

    def get(self, stream_list):
        for stream in stream_list:
            for tr in stream:
                tr.data = np.require(tr.data, dtype=np.int32)
                tr.stats['network'] = 'VG'
                tr.stats['channel'] = self.get_channel(tr.stats.channel)
                tr.stats['location'] = '00'
        return stream_list

class Convert():
    def __init__(self):
        self.files = Files()
        self.sds = SDS()
        self.stream_list = []
        self.search = 'default'

    def to_mseed(self, search):
        new_stream_list = []
        stream_list = self.files.get(search)
        for stream in stream_list:
            new_stream = stream.merge(fill_value=0)
            new_stream_list.append(new_stream)
        self.stream_list = NewTrace().get(new_stream_list)
        self.search = search
        return self

    def get(self):
        return self.stream_list

    def save(self):
        print('Saving....')
        for stream in self.stream_list:
            for tr in stream:
                sds = self.sds.save(tr,self.search)
                print(sds)

class SDS():
    def __init__(self):
        self.config = Configuration()

    def check_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
        return self

    def file_not_exists(self, file):
        return not os.path.exists(file)

    def save(self, trace=Trace, search='default'):
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
            self.config.get(search)['output_directory'],
            'SDS',
            structure['year'],
            structure['network'],
            structure['station'],
            structure['channel']+'.'+structure['type']
        )

        self.check_directory(path)
        full_path = os.path.join(path,filename)
        if self.file_not_exists(full_path):
            try:
                trace.write(full_path, format='MSEED', encoding=11)
            except:
                trace.data = trace.data.clip(-2e30, 2e30)
                trace.write(full_path, format='MSEED')
        return True

convert = Convert()
streams = convert.to_mseed('sac').save()