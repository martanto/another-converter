import os

log_dir = os.path.abspath(os.path.join(os.getcwd(), 'log'))
os.makedirs(log_dir, exist_ok = True)

def log(content, filename = 'log.txt', mode = 'a', overwrite=False):
    log_file = os.path.join(log_dir, filename)
    
    if overwrite:
        log_files = open(log_file, 'w')
        log_files.write('')
        log_files.close()
    
    log_files = open(log_file, mode)
    log_files.write(content+'\n')
    log_files.close()
    