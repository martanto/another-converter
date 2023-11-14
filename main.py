import datetime
from cores.convert import Convert

def main():
    start_time = datetime.datetime.now()
    
    Convert(
        save_to_database=True,
        save_to_csv=True,
        save_dayplot=True,
    ).to_mseed()
    
    end_time = datetime.datetime.now()

    print('Duration: {}'.format(end_time - start_time))
    
if __name__ == '__main__':
    main()