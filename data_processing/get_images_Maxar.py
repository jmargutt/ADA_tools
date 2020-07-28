from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import urllib.request
import sys
import time
import click
import os
from tqdm import tqdm


def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = max(time.time() - start_time, 1)
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = min(int(count * block_size * 100 / total_size), 100)
    sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds passed" %
                    (percent, progress_size / (1024 * 1024), speed, duration))
    sys.stdout.flush()

@click.command()
@click.option('--disaster', default='typhoon-mangkhut', help='name of the disaster')
@click.option('--dest', default='output', help='destination folder')
@click.option('--maxpre', default=1000000, help='max number of pre-disaster images')
@click.option('--maxpost', default=1000000, help='max number of post-disaster images')
def main(disaster, dest, maxpre, maxpost):

    # initialize webdriver
    opts = Options()
    opts.headless = True
    assert opts.headless  # operating in headless mode

    # binary = r'C:\Program Files\Mozilla Firefox\firefox.exe'
    options = Options()
    options.headless = True
    # options.binary = binary
    cap = DesiredCapabilities().FIREFOX
    cap["marionette"] = True  # optional
    browser = Firefox(options=options, capabilities=cap)#, executable_path="C:\\geckodriver\\geckodriver.exe")
    print("Headless Firefox Initialized")
    disaster = disaster.lower().replace(' ', '-')
    base_url = 'view-source:https://www.digitalglobe.com/ecosystem/open-data/'+disaster
    try:
        browser.get(base_url)
    except:
        print('ERROR:', base_url, 'not found')

    os.makedirs(dest, exist_ok=True)
    os.makedirs(dest+'/pre-event', exist_ok=True)
    os.makedirs(dest+'/post-event', exist_ok=True)

    # find & download images
    image_elements = browser.find_elements_by_css_selector('a')
    urls = [el.get_attribute('text') for el in image_elements]
    images = [x for x in urls if x.split('/')[-1].endswith('.tif')]
    images_pre = [x for x in images if 'pre-' in x.split('/')[-4]]
    images_post = [x for x in images if 'post-' in x.split('/')[-4]]
    print('total pre-disaster images:', len(images_pre))
    print('total post-disaster images:', len(images_post))
    print('selecting intersection of pre- and post-disaster sets (images that are in both)')
    images_pre_selected = [x for x in images_pre if x.split('/')[-1] in [x.split('/')[-1] for x in images_post]]
    images_post_selected = [x for x in images_post if x.split('/')[-1] in [x.split('/')[-1] for x in images_pre]]
    print('selected pre-disaster images:', len(images_pre_selected))
    print('selected post-disaster images:', len(images_post_selected))
    print('downloading pre-disaster images')
    for url in tqdm(images_pre_selected[:min(len(images_pre_selected), maxpre)]):
        name = url.split('/')[-1]
        cat = url.split('/')[-2]
        name = cat+'-'+name
        urllib.request.urlretrieve(url, dest+'/pre-event/'+name, reporthook)
    print('downloading post-disaster images')
    for url in tqdm(images_post_selected[:min(len(images_post_selected), maxpost)]):
        name = url.split('/')[-1]
        cat = url.split('/')[-2]
        name = cat + '-' + name
        urllib.request.urlretrieve(url, dest + '/post-event/' + name, reporthook)


if __name__ == "__main__":
    main()