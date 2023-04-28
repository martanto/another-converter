from config.config import Configuration
from obspy import read, Stream
import os

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
    
    def search_ijen(self, date):
        input_directory = self.config['input_directory']
        year = date.strftime('%Y')
        directory = date.strftime('%Y%m%d')
        year_month_date = date.strftime('%Y-%m-%d')

        if os.path.exists(os.path.join(input_directory, year, directory)):
            try:
                stream = read(os.path.join(input_directory, year, directory, '*','{}*'.format(year_month_date)))
                
                try:
                    stream_last = read(os.path.join(input_directory, year, directory, '*','*-2350-*'))
                    stream+=stream_last
                except:
                    pass
                    
                stream.merge(fill_value=0)
                return stream
            except Exception as e:
                print(e)
        
        return Stream()


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
        if search == 'ijen':
            return self.search_ijen(date)
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
        # trace.data = np.require(trace.data, dtype=np.int32)
        trace.stats['station'] = self.get_station(trace).upper()
        trace.stats['network'] = 'VG'
        trace.stats['channel'] = self.get_channel(trace)
        trace.stats['location'] = '00'
        return trace