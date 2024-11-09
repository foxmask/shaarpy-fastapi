# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""
from datetime import datetime, timezone
import html
import re
from typing import NoReturn

from sqlmodel import Session, create_engine, select

from config import settings
from core.articles import get_article
from core.hashed_urls import small_hash

from models import Links


engine = create_engine(settings.DATABASE_URL)


async def import_shaarli(the_file: str, reload_article_from_url: str) -> NoReturn:  # noqa: C901
    """
    the_file: name of the file to import
    reload_article_from_url: article url
    """
    private = 0
    with open(the_file, 'r', encoding="utf-8") as f:
        data = f.read()

    if data.startswith('<!DOCTYPE NETSCAPE-Bookmark-file-1>'):
        i = 0

        for html_article in data.split('<DT>'):
            i += 1
            link = {'url': '',
                    'title': '',
                    'text': '',
                    'tags': '',
                    'image': None,
                    'video': None,
                    'date_created': '',
                    'private': False}
            if i == 1:
                continue

            if len(html_article.split('<DD>')) == 2:
                line, text = html_article.split('<DD>')
                link['text'] = html.unescape(text)

            for line in html_article.split('<DD>'):
                if line.startswith('<A '):
                    matches = re.match(r"<A (.*?)>(.*?)</A>", line)

                    attrs = matches[1]

                    link['title'] = matches[2] if matches[2] else ''
                    link['title'] = html.unescape(link['title'])

                    for attr in attrs.split(" "):
                        matches = re.match(r'([A-Z_]+)="(.+)"', attr)
                        attr_found = matches[1]
                        value_found = matches[2]
                        if attr_found == 'HREF':
                            link['url'] = html.unescape(value_found)
                        elif attr_found == 'ADD_DATE':
                            raw_add_date = int(value_found)
                            if raw_add_date > 30000000000:
                                raw_add_date /= 1000
                            link['date_created'] = datetime.fromtimestamp(raw_add_date).replace(tzinfo=timezone.utc)
                        elif attr == 'PRIVATE':
                            link['private'] = 0 if value_found == '0' else 1
                        elif attr == 'TAGS':
                            link['tags'] = value_found

                    if link['url'] != '' and link['url']:

                        if reload_article_from_url:
                            if link['url'].startswith('?'):
                                continue
                            link['title'], link['text'], link['image'], link['video'] = await get_article(link['url'])

                        if private:
                            link['private'] = 1

                        with Session(engine) as session:
                            # check if the URL already exists
                            statement = select(Links).where(Links.url == link['url'])
                            link = session.exec(statement).first()
                            url_hashed = await small_hash(link['date_created'].strftime("%Y%m%d_%H%M%S"))
                            # if the url does not already exist add it
                            if not link:
                                link_to_add = Links(url=link['url'],
                                                    title=link['title'],
                                                    text=link['text'],
                                                    tags=link['tags'],
                                                    private=private,
                                                    sticky=False,
                                                    date_created=link['date_created'],
                                                    image=link['image'],
                                                    video=link['video'],
                                                    url_hashed=url_hashed)
                                session.add(link_to_add)
                                session.commit()
