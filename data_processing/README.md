# data_processing
scripts to download/transform/upload pre- and post-disaster images

1. get_images_Maxar.py
```
Usage: python get_images_Maxar.py [OPTIONS]

Options:
  --disaster TEXT    name of the disaster
  --country TEXT     country in which the disaster happened
  --dest TEXT        destination folder
  --ntl TEXT         filter images by night-time lights (yes/no)
  --bbox TEXT        filter images by bounding box (CSV format)
  --maxpre INTEGER   max number of pre-disaster images
  --maxpost INTEGER  max number of post-disaster images
  --help             Show this message and exit.
```
