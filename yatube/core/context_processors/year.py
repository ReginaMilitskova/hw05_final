import datetime as dt


def year(request):
    time_now = dt.datetime.today().year
    return {
        'year': time_now,
    }
