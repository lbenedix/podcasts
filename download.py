import json
import logging
import os
from pathlib import Path

from requests.cookies import cookiejar_from_dict
from requests_html import HTMLSession

import log_util

logger = log_util.configure(logging.getLogger(__name__))


def download_file(url, path, session):
    if path.exists():
        logger.info(f"skip: {url}")
        return

    logger.info(f'downloading: {url}')
    r = session.get(url, allow_redirects=True)
    path.open("wb").write(r.content)


if __name__ == '__main__':
    PATH = os.getenv('ROOT_PATH', '.')
    COOKIE = os.getenv('COOKIE', '')

    path = Path(PATH)
    path = path / "podcasts"

    session = HTMLSession()
    session.cookies = cookiejar_from_dict({'PD-S-SESSION-ID': COOKIE})

    for p in path.rglob("*"):
        if p.name == 'info.json':
            podcast_id = f'{p.parent}'.split('/')[-1]
            podcast = json.loads(p.read_text(encoding="UTF-8"))
            logger.info(f'{podcast["title"]} - {podcast["id"]}')

            # download cover
            cover_path = p.parent / "cover.jpg"
            download_file(podcast['source_cover'], cover_path, session)

            for episode in podcast["episodes"]:
                # download episode
                episode_path = p.parent / f'{episode["id"]}.mp3'
                download_file(episode['source_audio'], episode_path, session)
                episode['bytes'] = os.stat(episode_path).st_size

                # download episode cover
                episode_cover_path = p.parent / f'{episode["id"]}.jpeg'
                download_file(episode['source_cover'], episode_cover_path, session)

            # write JSON files:
            with p.open("w", encoding="UTF-8") as target:
                json.dump(podcast, fp=target, sort_keys=True, indent=2, ensure_ascii=False)
