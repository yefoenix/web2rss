import yaml
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from playwright.sync_api import sync_playwright
import time as time_module
from datetime import datetime
from urllib.parse import urljoin

def create_playwright_browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        return browser

def load_config(config_path='config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def fetch_blog_posts(config):
    print(f"Fetching posts from: {config['url']}")
    print(f"Using selectors: block={config['block_css']}, title={config['title_css']}, description={config['description_css']}, link={config['link_css']}")

    if config['use_headless_browser']:
        browser = create_playwright_browser()
        page = browser.new_page()
        page.goto(config['url'])
        page.wait_for_timeout(10000)
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        browser.close()
    else:
        response = requests.get(config['url'])
        soup = BeautifulSoup(response.content, 'html.parser')

    # 基于文本块选择器获取所有相关块
    blocks = soup.select(config['block_css'])

    posts = []
    for block in blocks:
        title = block.select_one(config['title_css'])
        description = block.select_one(config['description_css'])
        link = block.select_one(config['link_css']) if config['link_css'] else block

        if title and description and link:
            posts.append({
                'title': title.get_text(strip=True),
                'description': description.get_text(strip=True),
                'link': link['href'] if link['href'].startswith('http') else urljoin(config['url'], link['href'])
            })

    return posts

def generate_rss(posts, site_url):
    feed = FeedGenerator()
    feed.id(site_url)
    feed.title(site_url)
    feed.link(href=site_url)
    feed.description("Latest posts from " + site_url)

    for post in posts:
        entry = feed.add_entry()
        entry.title(post['title'])
        entry.link(href=post['link'])
        entry.description(post['description'])

    return feed.rss_str(pretty=True).decode('utf-8')  # 确保返回字符串

def main():
    config = load_config()
    for site in config['sites']:
        posts = fetch_blog_posts(site)
        if not posts:
            print(f"No posts found for {site['url']}, skipping RSS generation.")
            continue
            
        rss_feed = generate_rss(posts, site['url'])
        
        file_name = f"rss/rss_feed_{site['url'].replace('https://', '').replace('/', '_')}.xml"
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(rss_feed)  # 确保写入的是字符串
        print(f"Generated RSS feed for {site['url']} -> {file_name}")

if __name__ == '__main__':
    main()