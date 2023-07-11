import json
import os
from pathlib import Path
import logging

from mutagen.mp3 import MP3, HeaderNotFoundError

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
    chapter_js_template = Template(Path('templates/chapters.js.jinja2').read_text(encoding="UTF-8"))
    chapter_txt_template = Template(Path('templates/chapters.txt.jinja2').read_text(encoding="UTF-8"))
    episode_js_template = Template(Path('templates/episode.js.jinja2').read_text(encoding="UTF-8"))

    podcasts = []
    for p in path.rglob("*"):
        if p.name == 'info.json':
            podcast_id = f'{p.parent}'.split('/')[-1]
            podcast = json.loads(p.read_text(encoding="UTF-8"))
            podcasts.append(podcast)

            podcast['episodes'] = sorted(podcast['episodes'], key=lambda x: x['short_title'], reverse=True)

            logger.info(f'{podcast["title"]} - {podcast["id"]}')

            for episode in podcast['episodes']:
                episode_mp3_path = Path(p.parent / f"{episode['id']}.mp3")
                try:
                    audio = MP3(episode_mp3_path)
                    episode['bytes'] = os.stat(episode_mp3_path).st_size
                    hours, remainder = divmod(audio.info.length, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    episode['length'] = f'{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}:000'
                except HeaderNotFoundError:
                    logger.warning(f"can't get size of {episode_mp3_path}")
                    pass

                e = episode_template.render(podcast=podcast,
                                            episode=episode,
                                            base_url=BASE_URL)
                episode_path = Path(p.parent / f"{episode['id']}.html")
                episode_path.open("w").write(e)

                #  write chapter mark files
                if episode.get('chapters') is not None:
                    # txt
                    chapter_txt_path = Path(p.parent / f"{episode['id']}_chapters.txt")
                    chapter_txt_path.open("w").write(
                        chapter_txt_template.render(episode=episode)
                    )
                    # js
                    chapter_js_path = Path(p.parent / f"{episode['id']}_chapters.js")
                    chapter_js_path.open("w").write(
                        chapter_js_template.render(episode=episode)
                    )

                # write podlove player config
                episode_js_path = Path(p.parent / f"{episode['id']}.js")
                episode_js_path.open("w").write(
                    episode_js_template.render(podcast=podcast,
                                               episode=episode,
                                               base_url=BASE_URL)
                )

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
