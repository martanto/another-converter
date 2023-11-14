#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
from obspy import read
from glob import glob
from cores.sds import SDS
from cores.plot import Plot
from cores.save_index import SaveIndex
from cores.log import log
from config.config import Configuration


# In[ ]:


config = Configuration(location='config.json', create_directory=False).get()


# In[ ]:


converted_dir = config['converted_directory']
sds_dir =  os.path.join(converted_dir,'SDS')

print('SDS Directory : {}'. format(sds_dir))


# In[ ]:


mseeds = SDS().scan(sds_dir)


# In[ ]:


filename_and_traces = [SDS().extract_header(mseed) for mseed in mseeds]


# In[ ]:


for filename, trace in filename_and_traces:
    info, log_txt = SaveIndex().update(filename, trace)
    print(info)
    log(log_txt, 'rescan.csv', overwrite=True)

