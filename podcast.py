import os
import json
import logging
from datetime import datetime
from email import utils
from typing import cast

from bs4 import BeautifulSoup
from furl import furl
from requests.cookies import cookiejar_from_dict
from requests_html import HTMLSession, HTMLResponse

import log_util

logger = log_util.configure(logging.getLogger(__name__))


def get_podcast_details(url, session):
    result = {}

    r = cast(HTMLResponse, session.get(url))
    logger.info(f"{r.url} - {r.status_code}")

    f = furl(r.html.base_url)
    base_url = f.origin

    if 'Für den Inhalt des verlinkten Podcasts ist der Anbieter verantwortlich' in r.text:
        logger.info('skip, public podcast')
        return {}

    result['title'] = r.html.find('h1', first=True).text
    result['source_link'] = url
    result['source_cover'] = f'{base_url}{r.html.find("img.podcast-cover", first=True).attrs.get("src")}'
    result['id'] = r.html.find('small', first=True).text.split(':')[-1].strip()

    # parse right pane of page
    details = r.html.find('div.channel-inner', first=True)
    result['summary'] = details.find('p', first=True).text

    result['episode_links'] = [x for x in details.absolute_links]

    # parse metadata pane (left)
    soup = BeautifulSoup(r.text, 'html.parser')
    result['author'] = soup.find("i", {'class': 'fa-v5-user'}).parent.text.strip()
    result['date'] = soup.find("i", {'class': 'fa-v5-calendar'}).parent.text.strip()
    result['pub_date'] = utils.format_datetime(datetime.strptime(result['date'], "%d.%m.%Y"))
    result['tags'] = [x.strip() for x in soup.find("i", {'class': 'fa-v5-folder'}).parent.text.strip().split(',')]

    # lower your expectations
    if "Deutsch.png" in r.text:
        result['lang'] = 'de-de'
    elif "English.png" in r.text:
        result['lang'] = 'en-us'

    return result


if __name__ == '__main__':
    URL = os.getenv('URL', '.')
    COOKIE = os.getenv('COOKIE', '')

    session = HTMLSession()
    session.cookies = cookiejar_from_dict({'PD-S-SESSION-ID': COOKIE})

    podcast = get_podcast_details(
        url=URL,
        session=session)

    print(json.dumps(podcast, indent=2, sort_keys=True, ensure_ascii=False))
