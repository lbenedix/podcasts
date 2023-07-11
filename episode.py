import json
import logging
import os
import re

from datetime import datetime
from email import utils
from typing import cast

from bs4 import BeautifulSoup
from furl import furl
from requests.cookies import cookiejar_from_dict
from requests_html import HTMLResponse, HTMLSession

import log_util

logger = log_util.configure(logging.getLogger(__name__))


def get_details(url, session):
    result = {}

    r = cast(HTMLResponse, session.get(url))
    logger.info(f"{r.url} - {r.status_code}")

    if 'not yet have a published version available' in r.text or 'Diese Seite hat noch keine veröffentlichte Version' in r.text:
        logger.info('episode not available')
        return None

    f = furl(r.html.base_url)
    base_url = f.origin

    result['title'] = r.html.find('h1', first=True).text
    result['source_link'] = url
    result['source_cover'] = base_url + r.html.find("img.podcast-cover", first=True).attrs.get("src")
    result['source_audio'] = base_url + r.html.find("audio > source", first=True).attrs.get("src")
    result['id'] = r.html.find('small', first=True).text.split(':')[-1].strip()

    try:
        shownotes = r.html.find('div#shownotes', first=True)
        if len(shownotes.text.strip()) > 0:
            result['shownotes'] = shownotes.html
            logger.info('shownotes!')
    except AttributeError:
        pass

    try:
        regex = re.search(r'^(\D*)(\d+)(.*)$', result['title'])
        short = regex.groups()[0].strip()
        number = int(regex.groups()[1])

        result['short_title'] = short + f'{number:03d}'
        result['short_title'] = result['short_title'].replace(':', '')
        # print(f"\r{episode['short_title']};{episode['title']}", end="\n\r")
    except AttributeError as result:
        print('💥', result['link'])
        result['short_title'] = result['title']

    # parse right pane of page
    episode_details = r.html.find('div.channel-inner', first=True)
    soup = BeautifulSoup(episode_details.html, 'html.parser')
    for tag in soup.find_all():
        if len(list(tag.parents)) == 2:
            tag.extract()
    content = soup.text.strip().split('\n')
    result['summary'] = content[0]
    result['participants'] = content[-1].strip().split('; ')
    result['subtitle'] = episode_details.find('p', first=True).text

    # parse metadata pane (left)
    soup = BeautifulSoup(r.text, 'html.parser')
    result['author'] = soup.find("i", {'class': 'fa-v5-user'}).parent.text.strip()
    result['date'] = soup.find("i", {'class': 'fa-v5-calendar'}).parent.text.strip()
    result['pub_date'] = utils.format_datetime(datetime.strptime(result['date'], "%d.%m.%Y"))
    result['tags'] = [x.strip() for x in soup.find("i", {'class': 'fa-v5-folder'}).parent.text.strip().split(',')]

    # chapters
    chapter_table = r.html.find('.media-chapters-table', first=True)
    if chapter_table is not None:
        logger.info('chapter marks!')
        result['chapters'] = []
        for chapter in chapter_table.find('.chapter-row'):
            start = float(chapter.attrs.get('start-time'))
            hours, remainder = divmod(start, 3600)
            minutes, seconds = divmod(remainder, 60)
            result['chapters'].append({
                "start": f'{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}.000',
                "title": chapter.find('.chapter-title', first=True).text,
            })

    # lower your expectations
    if "Deutsch.png" in r.text:
        result['lang'] = 'de-de'
    elif "English.png" in r.text:
        result['lang'] = 'en-us'

    return result


if __name__ == '__main__':
    URL = os.getenv('URL', '.')
    PATH = os.getenv('ROOT_PATH', '.')
    COOKIE = os.getenv('COOKIE', '')

    session = HTMLSession()
    session.cookies = cookiejar_from_dict({'PD-S-SESSION-ID': COOKIE})

    episode = get_details(
        url=URL,
        session=session)

    print(json.dumps(episode, indent=2, sort_keys=True))
