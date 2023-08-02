import matplotlib.pyplot as plt
from obspy import UTCDateTime
from cores.sds import SDS

class Plot:
    def __init__(self, overwrite=False):
        self.overwrite = overwrite

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