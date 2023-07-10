import json
import logging
import os
from typing import cast

from furl import furl
from requests.cookies import cookiejar_from_dict
from requests_html import HTMLSession, HTMLResponse

import log_util

logger = log_util.configure(logging.getLogger(__name__))


def get_all(url, session):
    result = []

    r = cast(HTMLResponse, session.get(url))
    logger.info(f"{r.url} - {r.status_code}")

    f = furl(r.html.base_url)
    base_url = f.origin

    for podcast_page in r.html.find('div.podcast-thumbnail'):
        link = podcast_page.absolute_links.pop()
        result.append({
            'title': podcast_page.find('h2', first=True).text,
            'link': link,
            'subtitle': podcast_page.find('p')[-1].text,
            'cover_img': base_url + podcast_page.find("img.podcast-cover", first=True).attrs.get("src"),
            'id': furl(link).args['pageId'],
        })

    return result


if __name__ == '__main__':
    URL = os.getenv('URL', '.')

    cookie = ""
    session = HTMLSession()
    session.cookies = cookiejar_from_dict({'PD-S-SESSION-ID': cookie})

    all = get_all(
        url=URL,
        session=session)

    print(json.dumps(all, indent=2, sort_keys=True, ensure_ascii=False))
