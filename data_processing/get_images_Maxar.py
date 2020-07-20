from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import urllib.request
import sys
import time
import click
import os
import glob
import fiona
import rasterio
from rasterio.windows import get_data_window
from tqdm import tqdm
from shapely.geometry import box
import geopandas as gpd
from fiona.crs import from_epsg
from rasterio.mask import mask


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
@click.option('--country', default='', help='country in which the disaster happened')
@click.option('--dest', default='output', help='destination folder')
@click.option('--download', default=True, help='download images (yes/no)')
@click.option('--ntl', default=False, help='filter images by night-time lights (yes/no)')
@click.option('--bbox', default='', help='filter images by bounding box (CSV format)')
@click.option('--maxpre', default=1000000, help='max number of pre-disaster images')
@click.option('--maxpost', default=1000000, help='max number of post-disaster images')
def main(disaster, country, dest, download, ntl, bbox, maxpre, maxpost):
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
    if download:
        image_elements = browser.find_elements_by_css_selector('a')
        image_urls = [el.get_attribute('text') for el in image_elements]
        count_pre, count_post = 0, 0
        for url in image_urls:
            name = url.split('/')[-1]
            if not name.endswith('.tif'):
                continue
            cat = url.split('/')[-2]
            name = cat+'-'+name
            if 'pre-event' in url and count_pre < maxpre:
                urllib.request.urlretrieve(url, dest+'/pre-event/'+name, reporthook)
                print(' --> image', name, 'saved')
                count_pre += 1
            elif 'post-event' in url and count_post < maxpost:
                urllib.request.urlretrieve(url, dest+'/post-event/'+name, reporthook)
                print(' --> image', name, 'saved')
                count_post += 1

    # filter rasters

    print('filtering rasters')
    image_label = ''

    # filter by bounding box (if provided)
    if bbox != '':
        bbox_tuple = [float(x) for x in bbox.split(',')]
        bbox = box(bbox_tuple[0], bbox_tuple[1], bbox_tuple[2], bbox_tuple[3])
        geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=from_epsg(4326))
        coords = getFeatures(geo)
        print('filtering on bbox:')
        print(coords)
        image_label = '-bbox'

        # loop over images and filter
        for raster in tqdm(glob.glob(dest + '/*/*.tif')):
            raster = raster.replace('\\', '/')
            raster_or = raster
            out_name = raster.split('.')[0] + image_label +'.tif'
            with rasterio.open(raster) as src:
                print('cropping on bbox')

                try:
                    out_img, out_transform = mask(dataset=src, shapes=coords, crop=True)
                    out_meta = src.meta.copy()
                    out_meta.update({
                        'height': out_img.shape[1],
                        'width': out_img.shape[2],
                        'transform': out_transform})

                    print('saving', out_name)
                    with rasterio.open(out_name, 'w', **out_meta) as dst:
                        dst.write(out_img)
                except:
                    print('empty raster, discard')

            os.remove(raster_or)

    # filter by nighttime lights

    # load nighttime light mask
    ntl_shapefile = 'input/ntl_mask_extended.shp'
    if ntl:
        # filter mask by country (if provided)
        if country != '':
            country_ntl_shapefile = ntl_shapefile.split('.')[0] + '_' + country.lower() + '.shp'
            if not os.path.exists(country_ntl_shapefile):
                ntl_world = gpd.read_file(ntl_shapefile)
                ntl_world.crs = {'init': 'epsg:4326'}
                ntl_world = ntl_world.to_crs("EPSG:4326")
                world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
                country_shape = world[world.name == country]
                country_shape = country_shape.reset_index()
                country_shape.at[0, 'geometry'] = box(*country_shape.at[0, 'geometry'].bounds)
                country_shape.geometry = country_shape.geometry.scale(xfact=1.1, yfact=1.1)
                ntl_country = gpd.clip(ntl_world, country_shape)
                ntl_country.to_file(country_ntl_shapefile)
            with fiona.open(country_ntl_shapefile, "r") as shapefile:
                shapes = [feature["geometry"] for feature in shapefile]
        else:
            with fiona.open(ntl_shapefile, "r") as shapefile:
                shapes = [feature["geometry"] for feature in shapefile]

        # loop over images and filter
        for raster in tqdm(glob.glob(dest+'/*/*'+image_label+'.tif')):
            raster = raster.replace('\\', '/')
            raster_or = raster
            out_name = raster.split('.')[0] + '-ntl.tif'
            if 'ntl' in raster:
                continue
            crop_next = True

            print('processing', raster)
            out_name_ntl = raster.split('.')[0] + '-ntl-mask.tif'
            with rasterio.open(raster) as src:
                shapes_r = [x for x in shapes if not rasterio.coords.disjoint_bounds(src.bounds, rasterio.features.bounds(x))]
                if len(shapes_r) == 0:
                    print('no ntl present, discard')
                    crop_next = False
                else:
                    print('ntl present, creating mask')
                    out_image, out_transform = rasterio.mask.mask(src, shapes_r, crop=True)
                    out_meta = src.meta

                    out_meta.update({"driver": "GTiff",
                                     "height": out_image.shape[1],
                                     "width": out_image.shape[2],
                                     "transform": out_transform})
                    # save temporary ntl file
                    print('saving mask', out_name_ntl)
                    with rasterio.open(out_name_ntl, "w", **out_meta) as dst:
                        dst.write(out_image)
                    crop_next = True
                raster = out_name_ntl
            if crop_next:
                with rasterio.open(raster) as src:
                    print('cropping nan on', raster)
                    window = get_data_window(src.read(1, masked=True))

                    kwargs = src.meta.copy()
                    kwargs.update({
                        'height': window.height,
                        'width': window.width,
                        'transform': rasterio.windows.transform(window, src.transform)})

                    print('saving', out_name)
                    try:
                        with rasterio.open(out_name, 'w', **kwargs) as dst:
                            dst.write(src.read(window=window))
                    except:
                        print('empty raster, discard')

                # remove temporary ntl file
                os.remove(raster)

            # remove original raster
            # os.remove(raster_or)


if __name__ == "__main__":
    main()