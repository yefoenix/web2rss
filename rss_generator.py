import yaml
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time as time_module
from soupsieve.util import SelectorSyntaxError  # 导入 SelectorSyntaxError

def load_config(config_path='config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def fetch_blog_posts(config):
    print(f"Fetching posts from: {config['url']}")
    print(f"Using selectors: title={config['title_css']}, description={config['description_css']}, time={config['time_css']}")

    if config['use_headless_browser']:
        # Set up headless browser
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        
        driver.get(config['url'])
        time_module.sleep(3)  # 等待页面加载
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
    else:
        response = requests.get(config['url'])
        soup = BeautifulSoup(response.content, 'html.parser')

    # 获取标题和描述
    titles = soup.select(config['title_css'])
    descriptions = soup.select(config['description_css'])

    # 尝试获取时间，处理可能的异常
    try:
        times = soup.select(config['time_css'])
    except SelectorSyntaxError as e:
        print(f"CSS Selector error for time: {e}")
        times = []  # 如果发生错误，返回空列表

    posts = []
    for title, description in zip(titles, descriptions):
        post_time = times[0].get_text(strip=True) if times else "Unknown Time"  # 如果没有时间，设置为 "Unknown Time"
        posts.append({
            'title': title.get_text(strip=True),
            'description': description.get_text(strip=True),
            'pub_date': post_time,
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
        if not posts:  # 如果没有文章，跳过生成 RSS
            print(f"No posts found for {site['url']}, skipping RSS generation.")
            continue
            
        rss_feed = generate_rss(posts, site['url'])
        
        file_name = f"rss_feed_{site['url'].replace('https://', '').replace('/', '_')}.xml"
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(rss_feed)
        print(f"Generated RSS feed for {site['url']} -> {file_name}")

if __name__ == '__main__':
    main()
