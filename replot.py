from obspy import read
from models.SeismicData import SeismicData
from config.config import Configuration
import os
from cores.rescan import Rescan
from multiprocessing import Pool

config = Configuration().get()
converted_directory = config['converted_directory']
dayplot_directory = config['dayplot_directory']
cpu_used = 8

def run(seismic):
    try:
        trace = read(os.path.join(converted_directory, seismic.filename))[0]
        Rescan().plot(trace)
        return '==> Replotted {}'.format(seismic.filename)
    except:
        seismic.delete()
        return 'Tidak ditemukan: {}'.format(seismic.filename)

def main():    
    print('Load database....')
    seismics = SeismicData.order_by('date').get()
    
    print('Data count : {}'.format(seismics.count()))
        
    if cpu_used == 1:
        print('Using Single CPU')
        for seismic in seismics:
            # print('{}_{}'.format(trace.id, trace.stats.starttime.strftime('%Y-%m-%d')))
            print(run(seismic))

    else:
        print('Using MultiProcessing : {} CPU used'.format(cpu_used))
        with Pool(cpu_used) as pool:
            for result in pool.map(run, seismics):
                print(f'Result: {result}', flush=True)
            pool.close()
            pool.join()

if __name__ == '__main__':
    main()