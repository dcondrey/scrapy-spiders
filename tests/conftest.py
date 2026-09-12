from pathlib import Path

import pytest
from scrapy.http import HtmlResponse, XmlResponse

FIXTURES = Path(__file__).parent / "fixtures"


def _body(name):
    return (FIXTURES / name).read_bytes()


@pytest.fixture
def ec_search_response():
    return HtmlResponse(
        url="https://www.entertainmentcareers.net/psearch/?zoom_query=film+editor",
        body=_body("entertainmentcareers_search.html"),
        encoding="utf-8",
    )


@pytest.fixture
def ec_detail_response():
    return HtmlResponse(
        url="https://www.entertainmentcareers.net/framestore/social-media-video-editor/job/531017/",
        body=_body("entertainmentcareers_detail.html"),
        encoding="utf-8",
    )


@pytest.fixture
def craigslist_detail_response():
    return HtmlResponse(
        url="https://www.craigslist.org/view/d/livermore-plumbing-warehouse-position/7ou63o3k7pfC5k3xhGnrCu",
        body=_body("craigslist_posting.html"),
        encoding="utf-8",
    )


@pytest.fixture
def craigslist_sitemap_response():
    return XmlResponse(
        url="https://www.craigslist.org/sitemap-postings-2026-09-11-sfo-jjj.xml",
        body=_body("craigslist_sitemap.xml"),
        encoding="utf-8",
    )


@pytest.fixture
def productionhub_detail_response():
    return HtmlResponse(
        url="https://www.productionhub.com/job/65062/producers-assistant",
        body=_body("productionhub_detail.html"),
        encoding="utf-8",
    )
