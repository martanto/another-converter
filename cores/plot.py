import matplotlib.pyplot as plt
import os
from obspy import UTCDateTime
from cores.sds import SDS
from PIL import Image

class Plot:
    def __init__(self, overwrite=False):
        self.overwrite = overwrite

    def set_time(self, trace):
        date = trace.stats.starttime.strftime('%Y-%m-%d')
        starttime = UTCDateTime(date+'T00:00:00.000000Z')
        endtime = UTCDateTime(date+'T23:59:59.990000Z')
        return starttime, endtime
    
    def thumbnail(self, image, output_dir, filename):
        os.makedirs(os.path.join(output_dir,'thumbnail'), exist_ok = True)
        outfile =  os.path.join(output_dir,'thumbnail',filename+'.jpg')

        image = Image.open(image)
        
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
    
        new_image = image.resize((320, 180))        
        new_image.save(outfile)

    def save(self, trace, save_dayplot=False, dayplot_directory=None, save_spectogram=False, spectogram_directory=None):
        judul = trace.stats.starttime.strftime('%Y-%m-%d')+' | '+trace.id+' | '+str(trace.stats.sampling_rate)+' Hz | '+str(trace.stats.npts)+' samples'
        if save_dayplot == True:
            filename, path, full_path = SDS().get_directory(dayplot_directory, trace)
            
            outfile = '{}.png'.format(full_path)
            
            trace.plot(
                type='dayplot',
                # interval=30,
                one_tick_per_line=True,
                color=['k'],
                outfile= outfile,
                number_of_ticks=13,
                size=(1600,900),
                title=judul
            )
            plt.close('all')
            
            self.thumbnail(outfile, path, filename)

        if save_spectogram == True:
            _, _, full_path = SDS().get_directory(spectogram_directory, trace)
            trace.spectrogram(
                outfile='{}.png'.format(full_path),
                title=judul,
                show=False,
                fmt='png'
            )
            plt.close('all')