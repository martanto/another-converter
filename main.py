import glob
import json
import datetime
import os
from orator import Model, DatabaseManager
from fnmatch import fnmatch
from obspy import Stream, Trace, read
import numpy as np
import orator
from models.sds_index import SdsIndex

class Configuration():
    '''
    Membaca Konfigurasi File \n
    Pastikan lokasi file config.json sudah sesuai 
    '''
    def __init__(self, location='config.json'):
        self.location = location

    def set_location(self, location):
        self.location = location
        return self

    def get_location(self):
        return self.location

    def get(self, type='default'):
        with open(self.get_location()) as file_config:
            load_config = json.load(file_config)
            start_date = datetime.datetime.strptime(load_config['start_date'],'%Y-%m-%d')
            end_date = datetime.datetime.strptime(load_config['end_date'],'%Y-%m-%d')
            config = {
                'input_directory' : load_config['input_directory'],
                'start_date' : start_date,
                'end_date' : end_date,
                'output_directory' : load_config['output_directory'],
                'dayplot_directory' : load_config['dayplot_directory'],
                'channels' : load_config['type'][type]['channels'] if type == 'sac' else []
            }
            return config

class Files():
    ''' Mendapatkan semua files sesuai konfigurasi pencarian '''
    def __init__(self, config=Configuration()):
        self.config = config

    def search_default(self, date):
        input_directory = self.config['input_directory']
        stream_files = glob.glob(input_directory+'\\'+date.strftime('%Y-%m-%d')+'*')
        if len(stream_files) > 0:
            new_stream = Stream()
            for stream in stream_files:
                new_stream+=read(stream)
            new_stream.merge(fill_value=0)
            return new_stream
        pass

    def search_sac(self, date):
        pass
        # search_list = []
        # stream_list = []
        # input_directory = self.config['input_directory']
        # start_date = self.config['start_date']
        # end_date = self.config['end_date']
        # channels = self.config['channels']
        # print('Searching files....')
        # for n in range(int((end_date-start_date).days)+1):
        #     filter = start_date+datetime.timedelta(n)
        #     for root, folders, files in os.walk(input_directory):
        #         for folder in folders:
        #             if filter.strftime('%Y%m%d') in folder:
        #                 channel_folder = os.path.join(root, folder)
        #                 for channel in channels:
        #                     channel_files = [f for f in glob.glob(channel_folder + "\\"+channel+'*', recursive=False)]
        #                     for channel_file in channel_files:
        #                         search_list.append(channel_file)
        #     stream_list.append(NewStream(search_list).get())
        # return stream_list

    def get(self, search, date):
        if search == 'default':
            return self.search_default(date)
        if search == 'sac':
            return self.search_sac(date)
        return "Konfigurasi pencarian tidak ditemukan"

    def save(self, trace):
        pass

class NewStream():
    def __init__(self):
        pass

    def get(self, stream):
        list_traces = []
        for trace in stream:
            try:
                stream = read(stream)
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

    def get(self, trace):
        trace.data = np.require(trace.data, dtype=np.int32)
        trace.stats['network'] = 'VG'
        trace.stats['channel'] = self.get_channel(trace.stats.channel)
        trace.stats['location'] = '00'
        return trace

class Convert():
    def __init__(self, location='config.json'):
        self.files = Files()
        self.sds = SDS()
        self.index = SaveIndex()
        self.config = Configuration(location)

    def date_range(self, start_date, end_date):
        for n in range(int((end_date-start_date).days)+1):
            yield start_date+datetime.timedelta(n)

    def to_mseed(self, search='default'):
        print('Reading configuration....')
        config = self.config.get(search)
        start_date = config['start_date']
        end_date = config['end_date']
        for date in self.date_range(start_date, end_date):
            stream = Files(config).get(search,date)
            self.save(stream,config['output_directory'],date)
        return self

    def save(self,stream, output, date):
        for tr in stream:
            new_trace = NewTrace().get(tr)
            if new_trace.stats.sampling_rate >= 50.0:
                print(new_trace)
                path = self.sds.save(output,new_trace)
                self.index.save(path, new_trace, date)
            else:
                print('Skipped : %s' %new_trace)
        print('DONE!!')

class SDS():
    def __init__(self, config=Configuration()):
        self.config = config

    def check_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
        return self

    def file_not_exists(self, file):
        return not os.path.exists(file)

    def save(self, output, trace=Trace):
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
        if self.file_not_exists(full_path):
            try:
                trace.write(full_path, format='MSEED', encoding=11)
            except:
                trace.data = trace.data.clip(-2e30, 2e30)
                trace.write(full_path, format='MSEED')
        return os.path.join(path,filename)

class SaveIndex():
    def __init__(self):
        pass

    def get_scnl(self,trace):
        scnl = trace.stats.station+'_'+trace.stats.channel+'_'+trace.stats.network+'_'+trace.stats.location
        return scnl

    def get_sampling_rate(self,trace):
        return float(round(trace.stats.sampling_rate, 2))

    def get_availability(self,trace):
        availability = float(round(trace.stats.npts/8640000*100,2))
        return availability

    def save(self, filename, trace, date):
        attributes = {
            'scnl':self.get_scnl(trace),
            'date':date,
        }

        values = {
            'filename':filename,
            'sampling_rate':self.get_sampling_rate(trace),
            'max_amplitude':float(abs(trace.max())),
            'availability':self.get_availability(trace)
        }
        
        SdsIndex.update_or_create(attributes=attributes, values=values)

convert = Convert()
streams = convert.to_mseed()