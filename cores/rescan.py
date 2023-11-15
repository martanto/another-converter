import os
import numpy as np
import matplotlib.pyplot as plt
from cores.log import log
from cores.sds import SDS
from cores.save_index import SaveIndex
from config.config import Configuration
from multiprocessing import Pool
from PIL import Image

class Rescan:
    def __init__(
        self, 
        code=None, 
        converted_dir=None, 
        output_directory=None, 
        dayplot_directory=None, 
        sds_dir=None, 
        cpu_used=1, 
        replot=False, 
        overwrite_plot=True
    ):
        self.config = Configuration().get()
        self.code = self.config['code'] if code is None else code
        self.converted_dir = self.config['converted_directory'] if converted_dir is None else converted_dir
        self.output_directory = self.config['output_directory'] if output_directory is None else output_directory
        self.dayplot_directory = self.config['dayplot_directory'] if dayplot_directory is None else dayplot_directory
        self.sds_dir = os.path.join(self.converted_dir,'SDS') if sds_dir is None else sds_dir
        self.cpu_used = self.config['cpu_used'] if self.config['cpu_used']>1 else cpu_used
        self.replot = replot
        self.overwrite_plot = overwrite_plot
        
    def thumbnail(self, image, output_dir, filename):
        os.makedirs(os.path.join(output_dir,'thumbnail'), exist_ok = True)
        outfile =  os.path.join(output_dir,'thumbnail',filename+'.jpg')

        image = Image.open(image)
        
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
    
        new_image = image.resize((320, 180))        
        new_image.save(outfile)
    
    def plot(self, trace):
        
        title = trace.stats.starttime.strftime('%Y-%m-%d')+' | '+trace.id+' | '+str(trace.stats.sampling_rate)+' Hz | '+str(trace.stats.npts)+' samples'
        filename, path, full_path = SDS().get_directory(self.dayplot_directory, trace)
        outfile = '{}.png'.format(full_path)
        
        trace.plot(
            type = 'dayplot',
            interval = 60,
            one_tick_per_line = True,
            color = ['k'],
            outfile = outfile,
            number_of_ticks = 13,
            size= (1600,900),
            title = title
        )
        plt.close('all')
        
        self.thumbnail(outfile, path, filename)
        
    def rescan(self, filename, trace, overwrite=True):
        info, log_txt = SaveIndex().update(filename, trace)
        print(info)
        log(log_txt, 'rescan.csv', overwrite=overwrite)
        return filename
        
    def extract_mseed(self, mseed):
        filename, trace = SDS().extract_header(mseed)
        print('==> {}'.format(filename))
        mseed_file = self.rescan(filename, trace)
        
        if self.replot:
            print('Plotting : {}'.format(filename))
            self.plot(trace)
            
        return mseed_file
        
    def run(self):
        print('Output Directory : {}'.format(self.output_directory))
        print('SDS Directory : {}'.format(self.sds_dir))
        
        mseeds = SDS().scan(self.sds_dir)
        
        if self.cpu_used == 1:
            print('Using Single CPU')
            for mseed in mseeds:
                self.extract_mseed(mseed)

        else:
            print('Using MultiProcessing')
            with Pool(self.cpu_used) as pool:
                for result in pool.map(self.extract_mseed, mseeds):
                    print(f'Result: {result}', flush=True)
                pool.close()
                pool.join()