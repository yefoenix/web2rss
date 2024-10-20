import yaml
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time as time_module
from soupsieve.util import SelectorSyntaxError
from datetime import datetime

def load_config(config_path='config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def fetch_blog_posts(config):
    print(f"Fetching posts from: {config['url']}")
    print(f"Using selectors: block={config['block_css']}, title={config['title_css']}, description={config['description_css']}, time={config['time_css']}, link={config['link_css']}")

    if config['use_headless_browser']:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.binary_location = "/usr/bin/chromium-browser"

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

        driver.get(config['url'])
        time_module.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
    else:
        response = requests.get(config['url'])
        soup = BeautifulSoup(response.content, 'html.parser')

    # 基于文本块选择器获取所有相关块
    blocks = soup.select(config['block_css'])

    posts = []
    post_time = None
    if config['time_css']:
        try:
            times = soup.select(config['time_css'])
            post_time = times[0].get_text(strip=True) if times else None
        except SelectorSyntaxError as e:
            print(f"CSS Selector error for time: {e}")

    for block in blocks:
        title = block.select_one(config['title_css'])
        description = block.select_one(config['description_css'])
        link = block.select_one(config['link_css'])

        if title and description and link:
            # 如果没有获取到有效时间，则使用今天的日期
            if post_time is None:
                post_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

            posts.append({
                'title': title.get_text(strip=True),
                'description': description.get_text(strip=True),
                'pub_date': post_time,
                'link': link['href']
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
        entry.pubDate(post['pub_date'])

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
