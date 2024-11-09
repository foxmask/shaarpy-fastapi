# coding: utf-8

import copy
from urllib.parse import urlparse

from bs4 import BeautifulSoup

import newspaper
import pypandoc


async def url_cleaning(url: str) -> str:
    """
    drop unexpected content of the URL from the bookmarklet

    param url: url of the website
    :return string url
    """

    if url:
        for pattern in ('&utm_source=', '?utm_source=', '&utm_medium=', '#xtor=RSS-'):
            pos = url.find(pattern)
            if pos > 0:
                url = url[0:pos]
    return url


# ARTICLES MANAGEMENT


async def _get_host(url: str) -> str:
    """
    go to get the schema and hostname and port related to the given url

    param url: url of the website
    :return string 'hostname'
    """

    o = urlparse(url)
    hostname = o.scheme + '://' + o.hostname
    port = ''
    if o.port is not None and o.port != 80:
        port = ':' + str(o.port)
    hostname += port
    return hostname


async def _get_brand(url: str) -> str:
    """
    go to get the brand name related to the given url

    url: url of the website
    :return string of the Brand
    """
    brand = newspaper.build(url=await _get_host(url))
    brand.download()
    brand.parse()
    return brand.brand


async def _drop_image_node(content: str) -> tuple:
    """
    drop the image node if found

    content: content of the html possibly containing the img
    return the first found image and the content
    """
    my_image = ''
    soup = BeautifulSoup(content, 'html.parser')
    if soup.find_all('img', src=True):
        image = soup.find_all('img', src=True)[0]
        my_image = copy.copy(image['src'])
        # if not using copy.copy(image) before
        # image.decompose(), it drops content of the 2 vars
        # image and my_image
        image.decompose()
    return my_image, soup


async def get_article(url: str) -> tuple:
    """
        get the complete article page from the URL
        url: URL of the article to get
        return title text image video or the URL in case of ArticleException
    """
    # get the complete article
    r = newspaper.Article(url, keep_article_html=True)
    try:
        r.download()
        r.parse()
        article_html = r.article_html
        video = r.movies[0] if len(r.movies) > 0 else ''
        image = ''
        # check if there is a top_image
        if r.top_image:
            # go to check image in the article_html and grab the first one found in article_html
            # it may happened that top_image is not the same in the content of article_html
            # so go pickup this one and remove it in the the content of article_html
            # image, article_html = await _drop_image_node(article_html)
            dropped = await _drop_image_node(article_html)
            image, article_html = dropped
        # convert into markdown
        text = pypandoc.convert_text(article_html, 'md', format='html')
        title = r.title + ' - ' + await _get_brand(url)

        return title, text, image, video
    except newspaper.article.ArticleException:
        return url, "", "", ""
