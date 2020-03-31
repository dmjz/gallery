import os
import glob
import PySimpleGUI as sg
from PIL import Image
from multiprocessing import Pool

sg.theme('Dark Blue')
FILE_EXTENSIONS = [
    '.jpg', '.jpeg', '.png',
]
THUMBNAIL_SIZES = (1280, 1024, 768, 512)

def list_images(folder):
    """ Return list of image filenames in folder """

    return [
        f for f in os.listdir(folder) 
        if os.path.splitext(f)[-1] in FILE_EXTENSIONS
    ]

def open_image(folder, image):
    """ Display the image """

    im = Image.open(os.path.join(folder, image))
    im.show()

def thumbnails(image):
    """ Yield thumbnails in decreasing sizes """

    im = Image.open(image)
    for size in THUMBNAIL_SIZES:
        im.thumbnail((size, size))
        yield im.copy()

def make_thumbnails(src, dest):
    """ Make thumbnails from src images in the dest folder """

    pass

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