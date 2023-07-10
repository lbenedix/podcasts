import json
import logging
import os
import pathlib

from requests.cookies import cookiejar_from_dict
from requests_html import HTMLSession

from all import get_all
from episode import get_details
from podcast import get_podcast_details

import log_util

logger = log_util.configure(logging.getLogger(__name__))

if __name__ == '__main__':
    URL = os.getenv('URL', '.')
    PATH = os.getenv('ROOT_PATH', '.')
    COOKIE = os.getenv('COOKIE', '')

    session = HTMLSession()
    session.cookies = cookiejar_from_dict({'PD-S-SESSION-ID': COOKIE})

    podcasts = get_all(
        url=URL,
        session=session
    )

    for podcast in podcasts:
        logger.info(f"{podcast['title']} - {podcast['id']}")
        podcast_details = get_podcast_details(podcast['link'], session)
        podcast_details['episodes'] = []
        if len(podcast_details.get('episode_links', [])) == 0:
            logger.info("skip podcast, no episodes")
            continue
        for episode_link in podcast_details.get('episode_links', []):
            episode = get_details(episode_link, session)
            if episode is not None:
                podcast_details['episodes'].append(episode)

        # create folder
        p = pathlib.Path(PATH)
        p = p / f'podcasts/{podcast["id"]}'
        p.mkdir(parents=True, exist_ok=True)

        # write JSON files:
        info_path = p / 'info.json'
        with info_path.open("w", encoding="UTF-8") as target:
            json.dump(podcast_details, fp=target, sort_keys=True, indent=2, ensure_ascii=False)

