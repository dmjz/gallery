import os
import glob
import math
import PySimpleGUI as sg
from PIL import Image
from multiprocessing import Pool

sg.theme('Dark Blue')
IMG_GLOBS = ('*.jpg', '*.jpeg', '*.png')
THUMBNAIL_SIZES = (
    ('M' , 768 ), 
    ('S' , 400 ),
)

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
    for prefix, size in THUMBNAIL_SIZES:
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
            values=[os.path.basename(name) for name in  list_images(folder)], 
            bind_return_key=True,
            key='Image List',
            size=(30,40),
        )
    ]]
    buttonLayout = [[sg.Button('Cancel')]]
    layout = imageTextLayout + buttonLayout
    folderName = os.path.basename(folder)
    title = f'Folder: { folderName }'
    window = sg.Window(title, layout)
    windowResult = window_event_loop(window, {'folder': folder})
    print(windowResult)
    window.close(); del window

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

def gallery_window_event_loop(window):
    """ Handle window events and return result """

    def open_folder(values):
        folder = values['select_folder']
        print('Open folder:', folder)
        folderName = os.path.basename(folder)
        window['folder_name'].update(folderName)
        show_window(folder)

    def image_grid(folder):
        [os.path.basename(name) for name in list_images(folder)]

    while True:
        event, values = window.read()
        print(event, values)
        if event is None:
            return 'close_window'
        if event == 'select_folder':
            open_folder(values)
        if event == sg.TIMEOUT_KEY:
            continue
            
def show_main_window():
    """ Select folder and view image grid """

    layout = [
        [
            sg.InputText(key='select_folder', enable_events=True, visible=False), 
            sg.FolderBrowse('Open gallery', target='select_folder'),
            sg.Text('Folder: ', key='folder_name', size=(60,1)),
        ],
        [
            sg.Column()
        ]
        [sg.Debug()],
    ]
    window = sg.Window('Gallery', layout)
    windowResult = gallery_window_event_loop(window)
    print(windowResult)
    window.close(); del window


class WindowManager():
    """ Keep track of when we need to remake the window """

    selectFolderKey = 'select_folder'
    thumbsSubDir = '.thumbnails'

    def __init__(self):
        self.folderPath = None
        self.window = None

    @property
    def folderShortName(self):
        if not self.folderPath:
            return ''
        return os.path.basename(self.folderPath)

    def window_event_loop(self):
        while True:
            event, values = self.window.read()
            print(event, values)
            if event is None:
                return event
            if event is self.selectFolderKey:
                self.folderPath = values[self.selectFolderKey]
                return event
            #  We may have more interesting events in the future...
            if event == sg.TIMEOUT_KEY:
                continue

    def thumbnail_path(self, size, img):
        return os.path.join(
            self.folderPath, 
            self.thumbsSubDir, 
            f'{ size }_{ os.path.splitext(img)[0] }.png'
        )

    def get_thumbnails(self, size='S'):
        if self.thumbsSubDir in os.listdir(self.folderPath):
            return [
                self.thumbnail_path(size, img)
                for img in list_images(self.folderPath)
            ]
        else:
            make_thumbnails(
                src=self.folderPath, 
                dest=os.path.join(self.folderPath, self.thumbsSubDir),
            )
            return self.get_thumbnails(size)

    def menu_layout(self):
        return [
            sg.InputText(key=self.selectFolderKey, enable_events=True, visible=False), 
            sg.FolderBrowse('Open gallery', target=self.selectFolderKey),
            sg.Text(f'Folder: { self.folderShortName }', size=(60,1)),
        ]

    def gallery_element(self, data):
        return sg.Image(data)

    def gallery_row_element(self, rowData):
        return [self.gallery_element(rd) for rd in rowData]

    def gallery_layout(self):
        if self.folderPath:
            thumbs = self.get_thumbnails()
            imageNameGrid = to_grid(thumbs, numCols=4)
            return [self.gallery_row_element(rowData) for rowData in imageNameGrid]
        else:
            displayText = 'Gallery will go here...'
            return [[ sg.Text(displayText, size=(100,40)) ]]

    def layout(self):
        return [
            self.menu_layout(),
            [sg.Column(
                self.gallery_layout(), 
                size=(1700,800), 
                scrollable=True,
                vertical_scroll_only=True,
            )],
            [sg.Debug()],
        ]

    def remake_window(self):
        newWindow = sg.Window('Gallery', self.layout())

    def close_window(self):
        if self.window:
            self.window.close()
            del self.window

    def run_window(self):
        eventLoopResult = True
        while eventLoopResult:
            newWindow = sg.Window('Gallery', self.layout())
            self.close_window()
            self.window = newWindow
            eventLoopResult = self.window_event_loop()
