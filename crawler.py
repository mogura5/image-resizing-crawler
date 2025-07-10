import PIL
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import requests
import io
from PIL import Image
from pathlib import Path
import hashlib
import argparse

def argument_parser():
    parser = argparse.ArgumentParser(description="Image scraping crawler for loaded.gg")
    parser.add_argument(
        '--output',
        default='Images',
        help='Output directory for downloaded images'
    )
    args = parser.parse_args()
    return args
def get_content_from_url(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    driver.get(url)
    return driver
def is_valid_loaded_link(link):
    if link.startswith("https://www.loaded.gg/privacy-policy/"):
        return False
    if link.startswith("https://www.loaded.gg/"):
        return True
    return False
def scrape_links_and_visit(driver, url):        
    driver.get(url)
    links = driver.find_elements(By.TAG_NAME, "a")
    raw_links = [link.get_attribute("href") for link in links]
    available_links = [link for link in raw_links if is_valid_loaded_link(link)]
    all_image_urls = []
    visited_links = set()

    print(f"\n * Found {len(available_links)} valid links to visit. *\n")

    for idx, link in enumerate(available_links):
        if link in visited_links:
            continue
        visited_links.add(link)
        print(f"+ Visiting link {idx+1}/{len(available_links)}: {link} +\n")
        
        try:
            driver.get(link)
            all_image_urls += find_images_urls(link, driver, all_image_urls)
            print(f"Found {len(all_image_urls)} <img> elements\n")
            
            if link == "https://www.loaded.gg/": # only on main page
                for _ in range(4):

                    bg_url = get_background_image_url(driver)

                    if bg_url and bg_url not in all_image_urls:
                        all_image_urls.append(bg_url)

                    driver.refresh()
            else:
                bg_url = get_background_image_url(driver)

                if bg_url and bg_url not in all_image_urls:
                    all_image_urls.append(bg_url)

            driver.back()

        except Exception as e:
            print(f"Error accessing link {link}: {e}")

    return all_image_urls
def find_images_urls(url, driver, visited_image_urls):
    driver.get(url)
    images = driver.find_elements(By.CSS_SELECTOR, "img")

    new_image_urls = []

    for image in images:
        image_url = image.get_attribute("src")

        if image_url.lower().endswith(".svg") :
            continue

        if image_url.startswith("data:"):
            continue
        
        if image_url not in visited_image_urls:
            new_image_urls.append(image_url)

    return new_image_urls
def get_background_image_url(driver):

    bg_element = driver.find_element(By.ID, "heroBackground")

    style = bg_element.get_attribute("style")
    
    if "url(" in style:
        start = style.find('url("') + 5
        end = style.find('")', start)
        return style[start:end] 
    return None
def download_images_locally(urls, output_dir):
    paths = {}

    for image_url in urls:
        filename = image_url.split("/")[-1]
        label = filename.split(".")[0]
        image_path = image_to_file(
            image_url,
            output_dir,
            label=label
        )
        if image_path:
            paths[image_url] = image_path

    return paths
def image_to_file(image_url, output_dir, label):
    image_content = requests.get(image_url, stream=True).content

    image_file = io.BytesIO(image_content)
    try:
        image = Image.open(image_file).convert("RGB")
    except PIL.UnidentifiedImageError:
        print(f"Error: Unable to identify image file {image_url}")
        return None

    if label is not None:
        filename = f"{label}.jpg"
    else:
        filename = hashlib.sha1(image_content).hexdigest() + ".jpg"

    file_path = Path(output_dir) / filename
    image.save(file_path, "JPEG")
    return file_path
def check_image_info(path):
    with Image.open(path) as img:
        return {
            "format": img.format,
            "size": img.size,
            "mode": img.mode,
            "file_size_kb": Path(path).stat().st_size / 1024
        }
def print_info_to_txt(image_url_to_path):

    with open("image_urls.txt", "r") as f:
        existing_urls = f.read().splitlines()

    with open("image_urls.txt", "a") as f:
        for url, path in image_url_to_path.items():
            if url not in existing_urls:
                image_info = check_image_info(path)
                f.write(f"Image URL: {url}\n")
                f.write(f"Image Info: {image_info}\n\n")
def main():
    args = argument_parser()

    output_dir=Path(args.output).resolve() # replace if it doesn't work

    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        
    url = "https://www.loaded.gg/"
    driver = get_content_from_url(url)

    all_image_urls = scrape_links_and_visit(driver, url)

    image_paths = download_images_locally(
        all_image_urls,
        output_dir)
    
    print_info_to_txt(image_paths)
    
    driver.quit()

if __name__ == "__main__":
    results = main()
        