import os
import glob
import math
from PIL import Image
from multiprocessing import Pool


IMG_GLOBS = ('*.jpg', '*.jpeg', '*.png')
THUMBNAIL_SIZES = {'S': 400}
THUMBNAIL_SIZE_ITEMS = list(THUMBNAIL_SIZES.items())

def to_grid(arr, numCols):
    """ Convert list to grid (list of lists) """

    L = len(arr)
    numRows = math.ceil(L/numCols)
    return [
        [
            arr[row*numCols + col] if row*numCols + col < L else None
            for col in range(numCols)
        ]
        for row in range(numRows)
    ]

def list_images(folder):
    """ Return list of image filenames in folder """
    
    return [
        os.path.basename(f) 
        for g in IMG_GLOBS 
        for f in glob.glob(os.path.join(folder, g))
    ]

def open_image(folder, image):
    """ Display the image """

    im = Image.open(os.path.join(folder, image))
    im.show()

def thumbnails(imgDestPair):
    """ Save PNG thumbnails in decreasing sizes """

    image, dest = imgDestPair
    im = Image.open(image)
    name = os.path.basename(image)
    name = os.path.splitext(name)[0] + '.png'
    for prefix, size in THUMBNAIL_SIZE_ITEMS:
        im.thumbnail((size, size))
        im.copy()
        im.save(os.path.join(dest, f'{ prefix }_{ name }'))

def make_thumbnails(src, dest, makeDest=True):
    """ Make thumbnails from src images in the dest folder 
        Return number of images processed
    """

    if makeDest:
        os.makedirs(dest)
    images = [os.path.join(src, img) for img in list_images(src)]
    L = len(images)
    if L < 8:
        # No multithreading
        for img in images:
            thumbnails((img, dest))
    else:
        # Yes multithreading
        numThreads = 4 if L < 64 else 8
        pool = Pool(numThreads)
        pool.map(thumbnails, [(img, dest) for img in images])
    return L

def image_size(filepath):
    return Image.open(filepath).size