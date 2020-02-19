import glob
import json
import datetime
import os
from obspy import Stream, Trace, read
import numpy as np
import pandas as pd
import orator
from models.sds_index import SdsIndex
import multiprocessing
from multiprocessing import Pool

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

    def get(self):
        with open(self.get_location()) as file_config:
            load_config = json.load(file_config)
            get_config = load_config['default']
            start_date = datetime.datetime.strptime(load_config['start_date'],'%Y-%m-%d')
            end_date = datetime.datetime.strptime(load_config['end_date'],'%Y-%m-%d')
            config = {
                'input_directory' : load_config['input_directory'],
                'start_date' : start_date,
                'end_date' : end_date,
                'output_directory' : load_config['output_directory'],
                'index_directory' : os.path.join(load_config['output_directory'], 'Index'),
                'converted_directory' : os.path.join(load_config['output_directory'], 'Converted'),
                'dayplot_directory' : os.path.join(load_config['output_directory'], 'Dayplots'),
                'channels' : load_config['type'][get_config]['channels'] if get_config == 'sac' else []
            }
            return config

class Files():
    ''' Mendapatkan semua files sesuai konfigurasi pencarian '''
    def __init__(self):
        self.config = Configuration().get()

    def search_default(self, date):
        input_directory = self.config['input_directory']
        stream_files = glob.glob(input_directory+'\\'+date.strftime('%Y-%m-%d')+'*')
        if len(stream_files) > 0:
            new_stream = Stream()
            for stream in stream_files:
                try:
                    read_stream = read(stream)
                    for trace in read_stream:
                        if trace.stats.sampling_rate < 50.0:
                            read_stream.remove(trace)
                    new_stream+=read_stream
                except:
                    print('Error : '+stream)
            new_stream.merge(fill_value=0)
            return new_stream

    def search_sac(self, date):
        search_list = []
        stream_list = []
        input_directory = self.config['input_directory']
        start_date = self.config['start_date']
        end_date = self.config['end_date']
        channels = self.config['channels']
        print('Searching files....')
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
            stream_list.append(NewStream().get(search_list))
        return stream_list

    def get(self, date, search='default'):
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
                list_traces.append(trace)

        return Stream(list_traces)

class NewTrace():
    def __init__(self):
        pass

    def get_channel(self, trace):
        if 'Z' in trace.stats.location:
            return 'EHZ'
        if 'Z' in trace.stats.channel:
            return 'EHZ'
        if 'N' in trace.stats.channel:
            return 'EHN'
        if 'E' in trace.stats.channel:
            return 'EHE'

    def get(self, trace):
        trace.data = np.require(trace.data, dtype=np.int32)
        trace.stats['network'] = 'VG'
        trace.stats['channel'] = self.get_channel(trace)
        trace.stats['location'] = '00'
        return trace

class Convert():
    def __init__(self, location='config.json', save_to_database=False, save_to_csv=False):
        self.files = Files()
        self.sds = SDS()
        self.save_index = save_to_database
        self.save_csv = save_to_csv
        self.index = SaveIndex()
        self.config = Configuration(location).get()
        self.index_directory = self.config['index_directory']
        self.output = self.config['converted_directory']

    def date_range(self):
        start_date = self.config['start_date']
        end_date = self.config['end_date']
        for n in range(int((end_date-start_date).days)+1):
            yield start_date+datetime.timedelta(n)

    def to_mseed(self, use_cpu=2):
        print('Reading configuration....')
        with Pool(use_cpu) as pool:
            pool.map(self._to_mseed, self.date_range())
        return self 

    def _to_mseed(self, date):
        stream = Files().get(date)
        self.save(stream,date)

    def save(self,stream, date):
        for tr in stream:
            new_trace = NewTrace().get(tr)
            if new_trace.stats.sampling_rate >= 50.0:
                print(new_trace)
                path = self.sds.save(self.output,new_trace)
                if self.save_index:
                    self.index.save(path, new_trace, date, db=True)
                if self.save_csv==True:
                    self.index.save(path, new_trace, date, csv=True, index_directory=self.index_directory)
            else:
                print('Skipped '+date.strftime('%Y-%m-%d'))
        print(':: '+date.strftime('%Y-%m-%d')+' DONE!!')

class SDS():
    def __init__(self):
        pass

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
        availability = float(round(trace.stats.npts/(trace.stats.sampling_rate*3600*24)*100,2))
        return availability

    def get_filesize(self,filename):
        file_mseed = os.path.join(Configuration().get()['converted_directory'], filename)
        trace = read(file_mseed)[0]
        return trace.stats.mseed.filesize

    def save(self, filename, trace, date, db=False, csv=False, index_directory=None):
        attributes = {
            'scnl':self.get_scnl(trace),
            'date':date,
        }

        values = {
            'filename':filename,
            'sampling_rate':self.get_sampling_rate(trace),
            'max_amplitude':float(abs(trace.max())),
            'availability':self.get_availability(trace),
            'filesize':self.get_filesize(filename)
        }

        if db:
            SdsIndex.update_or_create(attributes=attributes, values=values)

        if csv:
            if not os.path.exists(index_directory):
                os.makedirs(index_directory)

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
                df.to_csv(file_csv, header=['scnl','date','sampling_rate','max_amplitude','availability','filesize'], index=False, date_format='%Y-%m-%d')
            else:
                df.to_csv(file_csv, mode='a', header=False, index=False, date_format='%Y-%m-%d')
            
def main():
    print("Jumlah CPU : ", multiprocessing.cpu_count())
    cpu = int(multiprocessing.cpu_count()/2)
    print('CPU yang digunakan: '+str(cpu))
    Convert(save_to_csv=True).to_mseed(cpu)

if __name__ == '__main__':
    main()