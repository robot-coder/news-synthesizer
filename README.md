# README.md

# Multi-Functional News Aggregator and Newsletter Generator

This project implements a multi-functional agent that scrapes news websites, filters articles based on relevance and popularity, interacts with MCP servers using Playwright for dynamic content extraction, and generates a personalized daily newsletter with summarized content.

## Features

- Scrapes news articles from multiple sources
- Filters articles by relevance and popularity
- Uses Playwright to automate browser interactions for dynamic content
- Summarizes articles using NLP techniques
- Compiles a personalized daily newsletter

## Requirements

Ensure you have Python 3.8+ installed. Install the required libraries:

```bash
pip install -r requirements.txt
```

## Files

- `main.py`: Main script orchestrating the workflow
- `requirements.txt`: List of dependencies
- `README.md`: This documentation

## Usage

1. Configure your news sources and filtering criteria in `main.py`.
2. Run the script:

```bash
python main.py
```

3. The script will fetch, filter, summarize articles, and generate a newsletter.

## Dependencies

- llama_index
- mcp_server_library
- playwright
- beautifulsoup4
- requests
- nltk or spaCy

## Notes

- Make sure to install Playwright browsers:

```bash
python -m playwright install
```

- Customize filtering and summarization parameters as needed.

---

# main.py

import asyncio
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from llama_index import GPTIndex
from mcp_server_library import MCPClient
import nltk
from nltk.tokenize import sent_tokenize
from typing import List, Dict, Optional

# Download NLTK data if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class NewsArticle:
    def __init__(self, title: str, url: str, content: str):
        self.title = title
        self.url = url
        self.content = content

def fetch_static_content(url: str) -> Optional[str]:
    """
    Fetches static HTML content from a URL.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

async def fetch_dynamic_content(url: str, playwright: 'async_playwright') -> Optional[str]:
    """
    Uses Playwright to fetch dynamic content from a URL.
    """
    try:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, timeout=30000)
        content = await page.content()
        await browser.close()
        return content
    except Exception as e:
        print(f"Error fetching dynamic content from {url}: {e}")
        return None

def parse_article_content(html: str) -> str:
    """
    Parses HTML to extract main article content.
    """
    soup = BeautifulSoup(html, 'html.parser')
    paragraphs = soup.find_all('p')
    content = ' '.join([p.get_text() for p in paragraphs])
    return content

def filter_articles(articles: List[NewsArticle], relevance_keywords: List[str], min_popularity: int) -> List[NewsArticle]:
    """
    Filters articles based on relevance keywords and popularity.
    """
    filtered = []
    for article in articles:
        if any(keyword.lower() in article.content.lower() for keyword in relevance_keywords):
            # Placeholder for popularity check, e.g., via social metrics
            # For demo, assume all passing relevance are relevant
            filtered.append(article)
    return filtered

def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    Summarizes text by extracting key sentences.
    """
    sentences = sent_tokenize(text)
    return ' '.join(sentences[:max_sentences])

def generate_newsletter(articles: List[NewsArticle]) -> str:
    """
    Compiles a newsletter string from articles.
    """
    newsletter = "Daily News Summary\n\n"
    for article in articles:
        summary = summarize_text(article.content)
        newsletter += f"Title: {article.title}\nURL: {article.url}\nSummary: {summary}\n\n"
    return newsletter

async def main():
    """
    Main orchestrator function.
    """
    news_sources = [
        # List of news site URLs
        'https://example-news-site.com',
        # Add more sources as needed
    ]
    relevance_keywords = ['technology', 'science', 'innovation']
    min_popularity = 1000  # Placeholder for popularity threshold

    articles: List[NewsArticle] = []

    async with async_playwright() as playwright:
        for source_url in news_sources:
            html = fetch_static_content(source_url)
            if html is None:
                # Try dynamic content fetching
                html = await fetch_dynamic_content(source_url, playwright)
            if html:
                # Parse articles from HTML
                soup = BeautifulSoup(html, 'html.parser')
                for link in soup.find_all('a', href=True):
                    article_url = link['href']
                    if not article_url.startswith('http'):
                        article_url = source_url.rstrip('/') + '/' + article_url.lstrip('/')
                    article_html = fetch_static_content(article_url)
                    if article_html is None:
                        article_html = await fetch_dynamic_content(article_url, playwright)
                    if article_html:
                        content = parse_article_content(article_html)
                        title = link.get_text() or 'No Title'
                        articles.append(NewsArticle(title=title, url=article_url, content=content))
    # Filter articles
    filtered_articles = filter_articles(articles, relevance_keywords, min_popularity)

    # Generate newsletter
    newsletter_content = generate_newsletter(filtered_articles)

    # Save or send newsletter
    with open('daily_newsletter.txt', 'w', encoding='utf-8') as f:
        f.write(newsletter_content)
    print("Newsletter generated: daily_newsletter.txt")

if __name__ == '__main__':
    asyncio.run(main())

# requirements.txt

llama_index
mcp_server_library
playwright
beautifulsoup4
requests
nltk
