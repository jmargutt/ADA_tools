# data_processing
scripts to download/transform/upload pre- and post-disaster images

1. get_images_Maxar.py
```
Usage: python get_images_Maxar.py [OPTIONS]

Options:
  --disaster TEXT    name of the disaster
  --country TEXT     country in which the disaster happened [OPTIONAL]
  --dest TEXT        destination folder [OPTIONAL]
  --ntl TEXT         filter images by night-time lights (True/False) [DEFAULT: False]
  --bbox TEXT        filter images by bounding box (CSV format) [OPTIONAL]
  --maxpre INTEGER   max number of pre-disaster images [OPTIONAL]
  --maxpost INTEGER  max number of post-disaster images [OPTIONAL]
  --help             Show this message and exit.
```
