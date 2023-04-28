import datetime
import multiprocessing
import concurrent.futures
from cores.files import Files, NewTrace
from cores.sds import SDS
from cores.plot import Plot
from cores.save_index import SaveIndex
from config.config import Configuration
from multiprocessing import Pool

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
                print('==================================')
                print('Converting date: {}'.format(date))
                print('==================================')
                self._to_mseed(date)

    def _to_mseed(self, date):
        stream = Files().get(date=date, search=self.search)
        if len(stream) > 0:
            self.save(stream,date)
        else:
            print('File(s) not found!')

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