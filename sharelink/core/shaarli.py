# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""

import html
import re
from datetime import datetime, timezone

from sqlmodel import Session, create_engine, select

from sharelink.config import settings
from sharelink.core.hashed_urls import small_hash
from sharelink.models import Links

engine = create_engine(settings.DATABASE_URL)


async def import_shaarli(the_file: str) -> None:
    """
    the_file: name of the file to import
    """
    private = 0
    date_created: datetime
    with open(the_file, "r", encoding="utf-8") as f:
        data = f.read()

    if data.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>"):
        i = 0

        for html_article in data.split("<DT>"):
            i += 1
            link = {
                "url": "",
                "title": "",
                "text": "",
                "tags": "",
                "image": None,
                "video": None,
                "private": False,
            }
            if i == 1:
                continue

            if len(html_article.split("<DD>")) == 2:
                line, text = html_article.split("<DD>")
                link["text"] = html.unescape(text)

            for line in html_article.split("<DD>"):
                if line.startswith("<A "):
                    matches = re.match(r"<A (.*?)>(.*?)</A>", line)
                    if matches:
                        attrs = matches.group(1)

                        link["title"] = matches.group(2) if matches.group(2) else ""
                        link["title"] = html.unescape(str(link["title"]))

                    for attr in attrs.split(" "):
                        matches = re.match(r'([A-Z_]+)="(.+)"', attr)
                        attr_found = matches.group(1) if matches else ""
                        value_found = matches.group(2) if matches else ""
                        if attr_found == "HREF":
                            link["url"] = html.unescape(value_found)
                        elif attr_found == "ADD_DATE":
                            raw_add_date = float(value_found)
                            if raw_add_date > 30000000000:
                                raw_add_date /= 1000
                            date_created = datetime.fromtimestamp(raw_add_date).replace(
                                tzinfo=timezone.utc
                            )
                        elif attr == "PRIVATE":
                            link["private"] = False if value_found == "0" else True
                        elif attr == "TAGS":
                            link["tags"] = value_found

                    if link["url"] != "" and link["url"]:
                        if private:
                            link["private"] = True

                        with Session(engine) as session:
                            # check if the URL already exists
                            statement = select(Links).where(Links.url == link["url"])
                            my_link = session.exec(statement).first()
                            to_hash = date_created.strftime("%Y%m%d_%H%M%S")
                            url_hashed = await small_hash(to_hash)
                            # if the url does not already exist add it
                            if not my_link:
                                link_to_add = Links(
                                    url=link["url"],
                                    title=str(link["title"]),
                                    text=str(link["text"]),
                                    tags=str(link["tags"]),
                                    private=bool(private),
                                    date_created=date_created,
                                    image=str(link["image"]),
                                    video=str(link["video"]),
                                    url_hashed=url_hashed,
                                )
                                session.add(link_to_add)
                                session.commit()
