import os
import PySimpleGUI as sg
from PIL import Image

FILE_EXTENSIONS = [
    '.jpg', '.jpeg', '.png',
]

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
    """ Open a GUI displaying folder images """

    sg.theme('Dark Blue')
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