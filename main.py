import glob
import json
import datetime
import numpy as np
import pandas as pd
import multiprocessing
import matplotlib
import os
import matplotlib.pyplot as plt
import concurrent.futures
from obspy import Stream, Trace, read, UTCDateTime
from models.SeismicData import SdsIndex
from multiprocessing import Pool

matplotlib.use('Agg')

class Configuration:
    '''
    Membaca Konfigurasi File \n
    Pastikan lokasi file config.json sudah sesuai
    '''
    def __init__(self, default=None, location='config.json'):
        self.default = default
        self.location = location

    def set_location(self, location):
        self.location = location
        return self

    def get_location(self):
        return self.location

    def check_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
        return self

    def get(self):
        with open(self.get_location()) as file_config:
            load_config = json.load(file_config)
            get_config = load_config['default']
            start_date = datetime.datetime.strptime(load_config['type'][get_config]['start_date'],'%Y-%m-%d')
            end_date = datetime.datetime.strptime(load_config['type'][get_config]['end_date'],'%Y-%m-%d')
            output_directory = load_config['output_directory']
            save_to_database = load_config['save_to_database']
            cpu_used = load_config['cpu_used']
            config = {
                'default' : get_config,
                'cpu_used': cpu_used,
                'save_to_database': save_to_database,
                'input_directory' : load_config['type'][get_config]['input_directory'],
                'start_date' : start_date,
                'end_date' : end_date,
                'output_directory' : output_directory,
                'index_directory' : os.path.join(output_directory, 'Index'),
                'converted_directory' : os.path.join(output_directory, 'Converted'),
                'dayplot_directory' : os.path.join(output_directory, 'Dayplots'),
                'spectogram_directory' : os.path.join(output_directory, 'Spectogram'),
                'channels' : load_config['type'][get_config]['channels'] if get_config == 'sac' else [],
                'type': load_config['type']
            }

            self.check_directory(config['output_directory'])
            self.check_directory(config['index_directory'])
            self.check_directory(config['converted_directory'])
            self.check_directory(config['dayplot_directory'])
            self.check_directory(config['spectogram_directory'])

            return config

class Files:
    ''' Mendapatkan semua files sesuai konfigurasi pencarian '''
    def __init__(self):
        self.config = Configuration().get()

    def search_default(self, date):
        input_directory = self.config['input_directory']
        try:
            stream = read(os.path.join(input_directory, date.strftime('%Y-%m-%d')+'*'))
            for trace in stream:
                if trace.stats.sampling_rate < 50.0:
                    stream.remove(trace)
            stream.merge(fill_value=0)
            return stream
        except Exception as e:
            print(e)

    def search_idds(self, date):
        input_directory = self.config['input_directory']
        year = date.strftime('%Y')
        julian_day = date.strftime('%j')
        try:
            stream = read(os.path.join(input_directory, year,
                          'VG', '*', '*', '*', '*'+julian_day+'*'))
            for trace in stream:
                if trace.stats.sampling_rate < 50.0:
                    stream.remove(trace)
            stream.merge(fill_value=0)
            return stream
        except Exception as e:
            print(e)

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
            for root, folders, _ in os.walk(input_directory):
                for folder in folders:
                    if filter.strftime('%Y%m%d') in folder:
                        channel_folder = os.path.join(root, folder)
                        for channel in channels:
                            channel_files = [f for f in glob.glob(os.path.join(channel_folder, channel+'*'), recursive=False)]
                            for channel_file in channel_files:
                                search_list.append(channel_file)
            stream_list.append(NewStream().get(search_list))
        return stream_list

    def search_itb(self, date):
        input_directory = os.path.join(self.config['input_directory'], date.strftime('%y%m%d'))
        new_stream = Stream()
        for root, _, files in os.walk(input_directory):
            for stream in [f for f in files if f.endswith('.mseed') or f.endswith('.sac')]:
                try:
                    read_stream = read(os.path.join(root, stream))
                    for trace in read_stream:
                        if trace.stats.sampling_rate < 50.0:
                            read_stream.remove(trace)
                    new_stream+=read_stream
                except:
                    print('Error : '+stream)
        new_stream.merge(fill_value=0)
        return new_stream

    def search_win_sinabung(self, date):
        year_month = date.strftime('%y%m')
        year_month_day = date.strftime('%y%m%d')
        input_directory = os.path.join(self.config['input_directory'], year_month, year_month_day)
        print('==== Reading ALL one minute files ====')
        streams = read(os.path.join(input_directory, '*','*'))
        stream = streams.merge(fill_value=0)
        return stream

    def search_sds(self, date):
        config = self.config['type']['sds']
        year = date.strftime('%Y')
        julian_day = date.strftime('%j')
        new_stream = Stream()
        for station in self.config['type']['sds']['stations']:
            filename = 'VG.'+station.upper()+'.00.EHZ.D.'+year+'.'+julian_day
            stream = os.path.join(self.config['input_directory'],year,'VG',station.upper(),'EHZ.D',filename)
            if os.path.exists(stream):
                stream = read(stream)
                new_stream+=stream
        return new_stream

    def get(self, date, search='default'):
        if search == 'default':
            return self.search_default(date)
        if search == 'idds':
            return self.search_idds(date)
        if search == 'sac':
            return self.search_sac(date)
        if search == 'itb':
            return self.search_itb(date)
        if search == 'win_sinabung':
            return self.search_win_sinabung(date)
        if search == 'sds':
            return self.search_sds(date)
        return "Konfigurasi pencarian tidak ditemukan"

    def save(self, trace):
        pass

class NewStream:
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

class NewTrace:
    def __init__(self, config):
        self.config = config

    def get_channel(self, trace):
        if 'Z' in trace.stats.location:
            return 'EHZ'
        if 'Z' in trace.stats.channel:
            return 'EHZ'
        if 'N' in trace.stats.channel:
            return 'EHN'
        if 'E' in trace.stats.channel:
            return 'EHE'
        if self.config['default'] == 'win_sinabung':
            stations = self.config['type']['win_sinabung']['stations']
            return stations[trace.stats.channel]['channel']

    def get_station(self, trace):
        if trace.stats.station:
            return trace.stats.station
        if self.config['default'] == 'win_sinabung':
            stations = dict(self.config['type']['win_sinabung']['stations'])
            if trace.stats.channel in stations:
                return stations[trace.stats.channel]['station']
            return trace.stats.channel

    def get(self, trace):
        trace.data = np.require(trace.data, dtype=np.int32)
        trace.stats['station'] = self.get_station(trace).upper()
        trace.stats['network'] = 'VG'
        trace.stats['channel'] = self.get_channel(trace)
        trace.stats['location'] = '00'
        return trace

class Convert:
    def __init__(self, location='config.json', save_to_database=False, save_to_csv=False, save_dayplot=False, save_spectogram=False):
        self.save_index = save_to_database
        self.save_csv = save_to_csv
        self.save_dayplot = save_dayplot
        self.save_spectogram = save_spectogram
        self.config = Configuration(location).get()
        self.search = self.config['default']
        self.cpu_used = self.config['cpu_used'] if self.config['cpu_used'] < multiprocessing.cpu_count() else int(multiprocessing.cpu_count()/2)
        self.index_directory = self.config['index_directory']
        self.output = self.config['converted_directory']
        self.dayplot_directory = self.config['dayplot_directory']
        self.spectogram_directory = self.config['spectogram_directory']

    def date_range(self):
        start_date = self.config['start_date']
        end_date = self.config['end_date']
        for n in range(int((end_date-start_date).days)+1):
            yield start_date+datetime.timedelta(n)

    def to_mseed(self):
        print('Reading configuration....')
        if self.cpu_used > 1:
            print('=== USE multiprocessing ===')

            # threads = []
            # for date in self.date_range():
            #     thread = threading.Thread(target=self._to_mseed, args=(date,))
            #     thread.start()
            #     threads.append(thread)
            # for thread in threads:
            #     thread.join()

            with concurrent.futures.ProcessPoolExecutor(max_workers=int(self.cpu_used)) as executor:
                executor.map(self._to_mseed, self.date_range())

            # with Pool(self.cpu_used) as pool:
                # [pool.apply_async(self._to_mseed, (date, )) for date in self.date_range()]
                # pool.map(self._to_mseed, self.date_range())
                # pool.close()
                # pool.join()
        else:
            print('USE single processing')
            for date in self.date_range():
                print(date)
                self._to_mseed(date)

    def _to_mseed(self, date):
        stream = Files().get(date=date, search=self.search)
        if len(stream) > 0:
            self.save(stream,date)

    def save(self,stream, date):
        for tr in stream:
            new_trace = NewTrace(self.config).get(tr)
            if new_trace.stats.sampling_rate >= 50.0:
                print(new_trace)
                path = SDS().save(self.output,new_trace)
                if self.save_index:
                    SaveIndex().save(path, new_trace, date, db=True)
                if self.save_csv==True:
                    SaveIndex().save(path, new_trace, date, csv=True, index_directory=self.index_directory)
                if self.save_dayplot==True:
                    Plot().save(trace=new_trace, save_dayplot=True, dayplot_directory=self.dayplot_directory)
                if self.save_spectogram==True:
                    Plot().save(trace=new_trace, save_spectogram=True, spectogram_directory=self.spectogram_directory)
            else:
                print('Skipped '+date.strftime('%Y-%m-%d'))
        print(':: '+date.strftime('%Y-%m-%d')+' DONE!!')

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

class SaveIndex:
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

class Plot:
    def __init__(self):
        pass

    def set_time(self, trace):
        date = trace.stats.starttime.strftime('%Y-%m-%d')
        starttime = UTCDateTime(date+'T00:00:00.000000Z')
        endtime = UTCDateTime(date+'T23:59:59.990000Z')
        return starttime, endtime

    def save(self, trace, save_dayplot=False, dayplot_directory=None, save_spectogram=False, spectogram_directory=None):
        judul = trace.stats.starttime.strftime('%Y-%m-%d')+' | '+trace.id+' | '+str(trace.stats.sampling_rate)+' Hz | '+str(trace.stats.npts)+' samples'
        if save_dayplot == True:
            _, _, full_path = SDS().get_directory(dayplot_directory, trace)
            trace.plot(
                type='dayplot',
                interval=60,
                one_tick_per_line=True,
                color=['k'],
                outfile= '{}.png'.format(full_path),
                number_of_ticks=13,
                size=(1200,900),
                title=judul
            )
            plt.close('all')

        if save_spectogram == True:
            _, _, full_path = SDS().get_directory(spectogram_directory, trace)
            trace.spectrogram(
                outfile='{}.png'.format(full_path),
                title=judul,
                show=False,
                fmt='png'
            )
            plt.close('all')

def main():
    # print("Jumlah CPU : ", config.multiprocessing.`())
    Convert(save_to_csv=True, save_dayplot=True, save_spectogram=False).to_mseed()

if __name__ == '__main__':
    main()
