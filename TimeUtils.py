import datetime
from datetime import datetime
from datetime import date
from datetime import timedelta

start_date = datetime(2021, 1, 1)
end_date   = datetime(2021, 8, 15)
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
'October', 'November', 'December']


class BullTimer(object):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 
    'August', 'September', 'October', 'November', 'December']
    today = date.today()

    def __init__(self):
        day = date.today().day
        month = ((date.today().month - timeframe) % 12)
        year  = date.today().year - 5 
        if (timeframe >= month):
            year -= 1
        date_string = f'%d %s %d' % (day, months[month-1], year)
        self.start = datetime.strptime(date_string, '%d %B %Y')


