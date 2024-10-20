import yaml
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

def load_config(config_path='config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def fetch_blog_posts(config):
    if config['use_headless_browser']:
        # Set up headless browser
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        
        driver.get(config['url'])
        time.sleep(3)  # 等待页面加载
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
    else:
        response = requests.get(config['url'])
        soup = BeautifulSoup(response.content, 'html.parser')

    titles = soup.select(config['title_css'])
    descriptions = soup.select(config['description_css'])
    times = soup.select(config['time_css'])

    posts = []
    for title, description, time in zip(titles, descriptions, times):
        posts.append({
            'title': title.get_text(strip=True),
            'description': description.get_text(strip=True),
            'pub_date': time.get_text(strip=True),
            'link': title.find('a')['href']
        })
    return posts

def generate_rss(posts, site_url):
    feed = FeedGenerator()
    feed.id(site_url)
    feed.title("RSS Feed for " + site_url)
    feed.link(href=site_url)
    feed.description("Latest posts from " + site_url)

    for post in posts:
        entry = feed.add_entry()
        entry.title(post['title'])
        entry.link(href=post['link'])
        entry.description(post['description'])
        entry.pubDate(post['pub_date'])
    
    return feed.rss_str(pretty=True)

def main():
    config = load_config()
    for site in config['sites']:
        posts = fetch_blog_posts(site)
        rss_feed = generate_rss(posts, site['url'])
        
        file_name = f"rss_feed_{site['url'].replace('https://', '').replace('/', '_')}.xml"
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(rss_feed)
        print(f"Generated RSS feed for {site['url']} -> {file_name}")

if __name__ == '__main__':
    main()
