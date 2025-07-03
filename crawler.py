import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
import io
from PIL import Image
from pathlib import Path
import hashlib
import os

# Initialize the Chrome driver with options
def get_content_from_url(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    driver.get(url)
    page_content = driver.page_source
    driver.quit()
    with open("page_content.html", "w", encoding="utf-8") as file:
        file.write(page_content)
    return page_content

def parse_image_urls(page_content, header, image, source, location, type):
    results = []
    soup = BeautifulSoup(page_content, 'html.parser')

    for a in soup.find_all(location, class_=header):

        if type == "class":
            name = a.get(source)
            if name not in results:
                results.append(name)

        elif type == "style":
            name = a.get(type)
            
            if "url(" in name:
                start = name.find("url(") + 4
                end = name.find(")", start)
                url = name[start:end].strip('"')

                if url not in results:
                    results.append(url)
        else:
            name = a.find(image)
            if name not in results:
                results.append(name.get(source))

    return results

def save_to_csv(image_urls):
    df = pd.DataFrame({"Results": image_urls})
    df.to_csv("image_urls.csv", index=False, mode='a', encoding='utf-8')

# def resize_and_optimize_image(image_path, output_path, size=(800, 600), quality = 80):
#     with Image.open(image_path) as img:
#         img = img.convert("RGB")
#         img.thumbnail(size)
#         img.save(output_path, "JPEG", quality=80)

def download_image_to_file(image_url, output_dir):
    image_content = requests.get(image_url).content
    image_file  = io.BytesIO(image_content)
    image = Image.open(image_file).convert("RGB")
    filename = hashlib.sha1(image_content).hexdigest() + ".jpg"
    file_path = Path(output_dir) / filename
    image.save(file_path, "JPEG")

def main():
    url = "https://www.loaded.gg/"
    content = get_content_from_url(url)
    image_urls = []
    image_urls += parse_image_urls(content, "hero__bg", "img", "style", "div", "style")
    image_urls += parse_image_urls(content, "work-section__slide", "img", "src", "div", "wrapper")
    image_urls += parse_image_urls(content, "partners-section__img", "img", "src", "img", "class")
    image_urls += parse_image_urls(content, "creators-block", "img", "src", "a", "wrapper")
    image_urls += parse_image_urls(content, "service-section__image", "img", "src", "div", "wrapper")
    
    save_to_csv(image_urls)

    for image_url in image_urls:
        download_image_to_file(
            image_url, output_dir=Path("/Users/manakaogura/Desktop/Loaded/image-resizing-crawler/Images"))

if __name__ == "__main__":
    results = main()
        