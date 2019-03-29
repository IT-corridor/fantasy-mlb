import random
import datetime
import requests

import os
from os import sys, path
import django

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_mlb.settings")
django.setup()

from general.models import *
from general import html2text

def _deviation_projection(val, salary, ds):
    TC = {
        'DraftKings': (9000, 3900),
        'FanDuel': (9600, 4000),
        'Yahoo': (38, 0)
    }

    tc = TC[ds]
    if salary >= tc[0]:
        factor = (25, 50)
    elif salary >= tc[1]:
        factor = (5, 25)
    else:
        factor = (2, 10)

    return float(val) + random.randrange(factor[0], factor[1]) / 10.0

def get_players(data_source):
    try:
        slate = 'all' if data_source == 'Yahoo' else 'Opening Day'
        slate = 'all'
        slate = 'Main' if data_source == 'FanDuel' else 'all'

        url = 'https://www.rotowire.com/daily/tables/optimizer-mlb.php?sport=MLB&' + \
              'site={}&projections=&type=main&slate={}'.format(data_source, slate)

        players = requests.get(url).json()

        fields = ['money_line', 'position', 'proj_ceiling', 'opponent', 'actual_position', 
                  'salary', 'team', 'opp_pitcher_id']

        print data_source, len(players)
        if len(players) > 20:
            Player.objects.filter(data_source=data_source).update(play_today=False)

            for ii in players:
                defaults = { key: str(ii[key]).replace(',', '') for key in fields }
                defaults['play_today'] = True
                defaults['injury'] = html2text.html2text(ii['injury']).strip()

                player = Player.objects.filter(uid=ii['id'], data_source=data_source).first()
                if not player:
                    defaults['uid'] = ii['id']
                    defaults['data_source'] = data_source
                    defaults['proj_points'] = _deviation_projection(ii['proj_points'], ii['salary'], data_source)
                    defaults['first_name'] = ii['first_name'].replace('.', '')
                    defaults['last_name'] = ii['last_name'].replace('.', '')
        
                    Player.objects.create(**defaults)
                else:
                    if player.lock_update:
                        player.play_today = True
                    else:
                        criteria = datetime.datetime.combine(datetime.date.today(), datetime.time(22, 30, 0)) # utc time - 5:30 pm EST
                        if player.updated_at.replace(tzinfo=None) < criteria:
                            defaults['proj_points'] = _deviation_projection(ii['proj_points'], ii['salary'], data_source)

                        for attr, value in defaults.items():
                            setattr(player, attr, value)
                    player.save()
    except:
        print("*** some thing is wrong ***")

if __name__ == "__main__":
    for ds in ['DraftKings', 'Yahoo', 'FanDuel']:
        get_players(ds)
