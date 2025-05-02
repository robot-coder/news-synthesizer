import asyncio
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from llama_index import GPTIndex  # Assuming llama_index provides summarization
import spacy
from mcp_server_library import MCPClient  # Placeholder for MCP server interactions
from typing import List, Dict, Any

# Load NLP model for summarization
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

NEWS_SOURCES = [
    "https://example-news-site.com",
    # Add more news site URLs here
]

MIN_POPULARITY_THRESHOLD = 1000  # Example threshold for popularity filtering

async def fetch_dynamic_content(url: str, playwright) -> str:
    """
    Uses Playwright to fetch dynamic content from a URL.
    """
    try:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        content = await page.content()
        await browser.close()
        return content
    except Exception as e:
        print(f"Error fetching dynamic content from {url}: {e}")
        return ""

def scrape_static_content(url: str) -> str:
    """
    Fetches static content from a URL using requests.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching static content from {url}: {e}")
        return ""

def parse_articles(html_content: str) -> List[Dict[str, Any]]:
    """
    Parses HTML content to extract articles with title, link, relevance, and popularity.
    """
    articles = []
    soup = BeautifulSoup(html_content, 'html.parser')
    # Placeholder parsing logic; should be adapted to actual site structure
    for item in soup.find_all('article'):
        title_tag = item.find('h2')
        link_tag = item.find('a', href=True)
        popularity_tag = item.find('span', class_='popularity')
        relevance_score = evaluate_relevance(item)
        popularity = int(popularity_tag.text) if popularity_tag else 0
        if title_tag and link_tag:
            articles.append({
                'title': title_tag.text.strip(),
                'link': link_tag['href'],
                'relevance': relevance_score,
                'popularity': popularity
            })
    return articles

def evaluate_relevance(article_html) -> float:
    """
    Placeholder function to evaluate relevance of an article.
    """
    # Implement relevance scoring logic here
    return 1.0  # Default relevance

def filter_articles(articles: List[Dict[str, Any]], relevance_threshold: float, popularity_threshold: int) -> List[Dict[str, Any]]:
    """
    Filters articles based on relevance and popularity thresholds.
    """
    return [
        article for article in articles
        if article['relevance'] >= relevance_threshold and article['popularity'] >= popularity_threshold
    ]

def summarize_text(text: str) -> str:
    """
    Summarizes the given text using spaCy.
    """
    try:
        doc = nlp(text)
        sentences = list(doc.sents)
        # Simple heuristic: return first 3 sentences
        summary = ' '.join([sent.text for sent in sentences[:3]])
        return summary
    except Exception as e:
        print(f"Error during summarization: {e}")
        return text

async def extract_dynamic_content_from_articles(articles: List[Dict[str, Any]], playwright) -> List[Dict[str, Any]]:
    """
    Uses Playwright to fetch dynamic content for articles with dynamic pages.
    """
    tasks = []
    for article in articles:
        url = article['link']
        tasks.append(fetch_dynamic_content(url, playwright))
    contents = await asyncio.gather(*tasks)
    for idx, content in enumerate(contents):
        articles[idx]['content'] = content
    return articles

def compile_news(articles: List[Dict[str, Any]]) -> str:
    """
    Compiles articles into a newsletter string with summaries.
    """
    newsletter = ""
    for article in articles:
        content = article.get('content', '')
        if not content:
            # Fetch static content if dynamic content not available
            content = scrape_static_content(article['link'])
        summary = summarize_text(content)
        newsletter += f"Title: {article['title']}\nLink: {article['link']}\nSummary: {summary}\n\n"
    return newsletter

def send_newsletter_via_mcp(newsletter: str) -> None:
    """
    Sends the compiled newsletter via MCP server.
    """
    try:
        mcp_client = MCPClient()
        mcp_client.send_message("daily_newsletter", newsletter)
    except Exception as e:
        print(f"Error sending newsletter via MCP: {e}")

async def main() -> None:
    """
    Main orchestration function to develop the daily newsletter.
    """
    all_articles = []

    # Fetch and parse articles from each news source
    for url in NEWS_SOURCES:
        html_content = scrape_static_content(url)
        if not html_content:
            # If static fetch fails, try dynamic
            async with async_playwright() as playwright:
                html_content = await fetch_dynamic_content(url, playwright)
        articles = parse_articles(html_content)
        all_articles.extend(articles)

    # Filter articles based on relevance and popularity
    filtered_articles = filter_articles(all_articles, relevance_threshold=0.5, popularity_threshold=MIN_POPULARITY_THRESHOLD)

    # Fetch dynamic content for articles with dynamic pages
    async with async_playwright() as playwright:
        enriched_articles = await extract_dynamic_content_from_articles(filtered_articles, playwright)

    # Compile newsletter
    newsletter = compile_news( enriched_articles)

    # Send newsletter via MCP
    send_newsletter_via_mcp(newsletter)

if __name__ == "__main__":
    asyncio.run(main())