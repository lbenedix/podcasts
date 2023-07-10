import json
import os
from pathlib import Path
import logging

import log_util
from jinja2 import Template

logger = log_util.configure(logging.getLogger(__name__))

if __name__ == '__main__':
    PATH = os.getenv('ROOT_PATH', '.')
    BASE_URL = os.getenv('BASE_URL', '')

    path = Path(PATH)
    path = path / "podcasts"

    feed_template = Template(Path('templates/feed.xml.jinja2').read_text(encoding="UTF-8"))
    index_template = Template(Path('templates/index.html.jinja2').read_text(encoding="UTF-8"))
    podcast_template = Template(Path('templates/podcast.html.jinja2').read_text(encoding="UTF-8"))
    episode_template = Template(Path('templates/episode.html.jinja2').read_text(encoding="UTF-8"))

    podcasts = []
    for p in path.rglob("*"):
        if p.name == 'info.json':
            podcast_id = f'{p.parent}'.split('/')[-1]
            podcast = json.loads(p.read_text(encoding="UTF-8"))
            podcasts.append(podcast)

            podcast['episodes'] = sorted(podcast['episodes'], key=lambda x: x['short_title'], reverse=True)

            logger.info(f'{podcast["title"]} - {podcast["id"]}')

            for episode in podcast['episodes']:
                e = episode_template.render(podcast=podcast,
                                            episode=episode,
                                            base_url=BASE_URL)
                episode_path = Path(p.parent / f"{episode['id']}.html")
                episode_path.open("w").write(e)

            feed = feed_template.render(podcast=podcast, base_url=BASE_URL)
            feed_path = p.parent / "feed.xml"
            logger.info(f"writing feed to {feed_path}")
            Path(feed_path).open("w").write(feed)

            index = podcast_template.render(podcast=podcast, base_url=BASE_URL)
            podcast_path = Path(p.parent / "index.html")
            podcast_path.open("w").write(index)

    podcasts = sorted(podcasts, key=lambda x: x['title'])
    index = index_template.render(podcasts=podcasts)
    index_path = path / "index.html"
    logger.info(f"writing index to {index_path}")
    index_path.open("w").write(index)
