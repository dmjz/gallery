import os
import glob
import PySimpleGUI as sg
from PIL import Image
from multiprocessing import Pool

sg.theme('Dark Blue')
IMG_GLOBS = ('*.jpg', '*.jpeg', '*.png')
THUMBNAIL_SIZES = (1280, 1024, 768, 512)

def list_images(folder):
    """ Return list of image filenames in folder """

    return [
        f for g in IMG_GLOBS 
        for f in glob.glob(os.path.join(folder, g))
    ]

def open_image(folder, image):
    """ Display the image """

    im = Image.open(os.path.join(folder, image))
    im.show()

def thumbnails(imgDestPair):
    """ Save thumbnails in decreasing sizes """

    image, dest = imgDestPair
    im = Image.open(image)
    name = os.path.basename(image)
    for size in THUMBNAIL_SIZES:
        im.thumbnail((size, size))
        im.copy()
        im.save(os.path.join(dest, f'{ size }_{ name }'))

def make_thumbnails(src, dest):
    """ Make thumbnails from src images in the dest folder 
        Return number of images processed
    """

    images = list_images(src)
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

def window_event_loop(window, context):
    """ Handle window events and return result """

    while True:
        event, values = window.read()
        if event is None:
            return 'Close Window'
        if event == 'Cancel':
            return 'Cancel'
        if event == 'Image List':
            image = values['Image List'][0]
            open_image(context['folder'], image)

def show_window(folder):
    """ Open a GUI to open folder images """

    imageTextLayout = [[
        sg.Listbox(
            values=list_images(folder), 
            bind_return_key=True,
            key='Image List',
            size=(30,40),
        )
    ]]
    buttonLayout = [[sg.Button('Cancel')]]
    layout = imageTextLayout + buttonLayout
    title = f'Folder: { folder }'
    window = sg.Window(title, layout)
    windowResult = window_event_loop(window, {'folder': folder})
    print(windowResult)
    window.close(); del window

def gallery_window_event_loop(window):
    """ Handle window events and return result """

    while True:
        event, values = window.read()
        print(event, values)
        if event is None:
            return 'Close Window'
        if event == 'Cancel':
            return 'Cancel'
        if event == 'Open':
            folder = values['input']
            print('Open folder:', folder)
            show_window(folder)

def show_gallery_window():
    """ Show thumbnails in a gallery """

    layout = [
        [
            sg.Text('Open folder:', size=(20,1)), 
            sg.InputText(key='input', visible=False), 
            sg.FolderBrowse(target='input'),
        ],
        [sg.Button('Open'), sg.Button('Cancel')]
    ]
    window = sg.Window('Gallery', layout)
    windowResult = gallery_window_event_loop(window)
    print(windowResult)
    window.close(); del window