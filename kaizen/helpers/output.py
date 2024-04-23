import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup, Comment
import asyncio
import nest_asyncio
import subprocess
import os

logger = logging.getLogger(__name__)


PR_COLLAPSIBLE_TEMPLATE = """
<details>
<summary>{comment}</summary>

##### Reason
{reasoning}

##### Confidence
{confidence}
</details>
"""

DESC_COLLAPSIBLE_TEMPLATE = """
<details>
<summary>Original Description</summary>
{desc}
</details>
"""


def merge_topics(reviews):
    topics = {}
    for review in reviews:
        if review["topic"] in topics:
            topics[review["topic"]].append(review)
        else:
            topics[review["topic"]] = [review]
    return topics


def create_pr_review_from_json(data):
    markdown_output = "## Code Review Feedback\n\n"

    topics = merge_topics(data["review"])

    for topic, reviews in topics.items():
        markdown_output += f"### {topic}\n\n"
        for review in reviews:
            ct = PR_COLLAPSIBLE_TEMPLATE.format(
                comment=review.get("comment", "NA"),
                reasoning=review.get("reasoning", "NA"),
                confidence=review.get("confidence", "NA"),
            )
            markdown_output += ct + "\n"

    return markdown_output


def create_pr_description(data, original_desc):
    markdown_output = data["desc"]
    markdown_output += "\n\n -- Generated with love by Kaizen"
    markdown_output += "\n\n" + DESC_COLLAPSIBLE_TEMPLATE.format(desc=original_desc)
    return markdown_output


async def get_html(url):
    async with async_playwright() as p:
        subprocess.run(["playwright", "install", "--with-deps"], check=True)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        html = await page.content()
        await browser.close()
        return html


def get_web_html(url):
    nest_asyncio.apply()
    html = asyncio.run(get_html(url))
    soup = BeautifulSoup(html, "html.parser")

    for svg in soup.find_all("svg"):
        svg.decompose()
    
    # Delete each comment
    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.decompose()
    
    for style_block in soup.find_all('style'):
        style_block.decompose()
    
    pretty_html = soup.prettify()
    return pretty_html


def get_parent_folder():
    return os.getcwd()


def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger.debug(f"Folder '{folder_path}' created successfully.")
    else:
        logger.debug(f"Folder '{folder_path}' already exists.")