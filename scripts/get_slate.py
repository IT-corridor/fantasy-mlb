import requests

from bs4 import BeautifulSoup

def get_slate(ds):
    slate = 'all'
    try:
        url = 'https://www.rotowire.com/daily/mlb/optimizer.php?site={}'.format(ds)
        r = requests.get(url).text

        soup = BeautifulSoup(r, "html.parser")
        body = soup.find('body')
        slate = body['data-slate']
        type = body['data-type']
    except:
        pass

    return slate, type
