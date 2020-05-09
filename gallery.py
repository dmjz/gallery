import os
import json
import uuid
import queue
import time
from collections import namedtuple
import threading
import concurrent.futures
# mutex = threading.Lock()
import PySimpleGUI as sg
from utils import \
    to_grid, list_images, make_thumbnails, THUMBNAIL_SIZES, \
    image_size, thumbnails

sg.theme('Dark Blue')


ImageUpdateRecord = namedtuple('ImageUpdateRecord', 'image, folder')
ImageKey = namedtuple('ImageKey', 'image, element')


class FolderData():
    """ Load, edit, save folder metadata """

    thumbsSubDir = '.t'
    allFolderDataPath = os.path.join('.metadata', 'all_folder_data.json')
    allFolderData = None

    def __init__(self):
        self.openFolderPath = None
        self.openFolderData = None
        self.settings = None
        if self.allFolderData is None:
            self.load_all_data()

    def load_all_data(self):
        try:
            with open(self.allFolderDataPath, encoding='utf-8') as file:
                self.allFolderData = json.load(file)
        except FileNotFoundError:
            self.allFolderData = {}

    def open_folder(self, folderPath, settings, windowManager):
        self.openFolderPath = folderPath
        self.settings = settings
        self.openFolderData = self.get_folder_data(self.openFolderPath)
        ### Doing this in the WindowManager...
        ### self.make_folder_thumbs(windowManager)
        return True

    def get_folder_data(self, folderPath):
        if folderPath in self.allFolderData:
            return self.allFolderData[folderPath]
        return self.new_folder_data(folderPath)
    
    def new_folder_data(self, folderPath):
        new_uid = str(uuid.uuid4())
        folderData = {
            'path': folderPath,
            'uid':  new_uid,
            'thumbnailFolder': os.path.join('.metadata', new_uid, self.thumbsSubDir),
            'shortName': os.path.basename(folderPath),
            'imageData': { 
                    os.path.basename(img): self.new_image_data(img)
                    for img in list_images(folderPath)
                },
        }
        # Make new thumbnail dir
        try:
            os.makedirs(folderData['thumbnailFolder'], exist_ok=False)
        except FileExistsError:
            pass
        self.update_save_folder_data(folderPath, folderData)
        return folderData

    def make_folder_thumbs(self, windowManager):
        """ Make thumbs as necessary and populate wm image update queue """

        src = self.openFolderPath
        dest = self.openFolderData['thumbnailFolder']
        destFiles = os.listdir(dest)

        def make_thumb_thread(img):
            thumbPath = self.thumb_path(img)
            if thumbPath in destFiles:
                print('Thumb already made:', img)
            else:
                print('Make thumb:', img)
                thumbnails((os.path.join(src, img), dest))
            record = ImageUpdateRecord(image=img, folder=self.openFolderPath)
            mutex.acquire()
            windowManager.put_image_update(record)
            mutex.release()

        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(make_thumb_thread, list_images(src))


    def thumb_path(self, img):
        return os.path.join(
            self.openFolderData['thumbnailFolder'],
            f"{ self.settings['thumbSize'] }_{ os.path.splitext(img)[0] }.png",
        )
        

    def update_save_folder_data(self, fpath=None, fdata=None):
        """ If fpath, fdata are None, update open folder entry """

        if fpath and fdata:
            self.allFolderData[fpath] = fdata
        elif not fpath and not fdata:
            self.allFolderData[self.openFolderPath] = self.openFolderData
        else:
            raise ValueError('Cannot specify one of fpath, fdata without the other')
        with open(self.allFolderDataPath, 'w', encoding='utf-8') as f:
            json.dump(self.allFolderData, f)

    def new_image_data(self, img):
        return {
            'path': img,
            'name': os.path.basename(img),
            'rating': None,
        }

    @property
    def folderShortName(self):
        return self.openFolderData['shortName'] if self.openFolderData else ''

    def thumbnail_paths(self):
        thumbnailFolder = self.openFolderData['thumbnailFolder']
        size = self.settings['thumbSize']
        return [
            os.path.join(
                thumbnailFolder,
                f'{ size }_{ os.path.splitext(img)[0] }.png',
            )
            for img in self.images()
        ]

    def images(self):
        return list_images(self.openFolderPath)

    def set_rating(self, image, rating):
        self.openFolderData['imageData'][image]['rating'] = rating

    def get_rating(self, image):
        return self.openFolderData['imageData'][image]['rating']


class ThreadedThumbApp(threading.Thread):
    def __init__(self, windowManager, thumbData):
        super().__init__()
        self._stop_event = threading.Event()
        self.wm = windowManager
        self.thumbData = thumbData

    def run(self):
        folder = self.wm.folderData.openFolderPath
        for img, src, dest in self.thumbData:
            print('Make thumb:', img)
            thumbnails((os.path.join(src, img), dest))
            record = ImageUpdateRecord(image=img, folder=folder)
            # mutex.acquire()
            self.wm.put_image_update(record)
            # mutex.release()        

    def stop(self):
        self._stop_event.set()


class WindowManager():
    """ Keep track of when we need to remake the window """

    selectFolderKey = 'select_folder'
    thumbSize = 'S'
    imgDim = THUMBNAIL_SIZES[thumbSize]
    gridCols = 4
    folderData = FolderData()
    folderSettings = {
        'thumbSize': thumbSize,
    }
    imageUpdateQueue = queue.Queue()

    def __init__(self):
        self.folder = None
        self.window = None

    @property
    def folderShortName(self):
        return self.folderData.folderShortName if self.folder else ''

    def put_image_update(self, img):
        self.imageUpdateQueue.put(img)

    def window_event_loop(self):
        while True:
            event, values = self.window.read(timeout=100)
            if event and event != '__TIMEOUT__':
                print('-- Event:\n', event, values)

            # Handle events
            if event is None:
                # Event: close main window
                self.folderData.update_save_folder_data()
                return event
            if event == self.selectFolderKey:
                # Event: close folder select window
                if not values[self.selectFolderKey]:
                    continue
                self.folder = self.folderData.open_folder(
                    folderPath = values[self.selectFolderKey],
                    settings   = self.folderSettings,
                    windowManager = self,
                )

                ### ???
                ### Launch get_thumbnail threads here?
                print('Kick off thumbnail threads')
                src = self.folderData.openFolderPath
                dest = self.folderData.openFolderData['thumbnailFolder']
                thumbData = [
                    (img, src, dest)
                    for img in list_images(src)
                ]
                ThreadedThumbApp(self, thumbData).start()
                ### ???
                ### ???

                return event
            if isinstance(event, ImageKey):
                # Event: user clicked part of an image frame
                if event.element[:4] == 'star':
                    rating = int(event.element[-1])
                    self.folderData.set_rating(event.image, rating)
                    self.update_star_display(event.image)
                if event.element == 'img':
                    # User clicked image itself
                    pass

            # Poll image update queue
            try:
                record = self.imageUpdateQueue.get(block=False)
            except queue.Empty:
                pass
            else:
                print('Retrieved image update record:')
                print(str(record))
                self.update_image(record)

            # Place at very end of event loop for debug window
            if event == sg.TIMEOUT_KEY:
                continue

    def make_thumb_thread(self, data):
        print('thumb thread:', data)
        src, dest = data
        thumbPath = self.thumb_path(img)
        print('Make thumb:', img)
        thumbnails((os.path.join(src, img), dest))
        record = ImageUpdateRecord(image=img, folder=self.openFolderPath)
        # mutex.acquire()
        self.put_image_update(record)
        # mutex.release()

    def update_image(self, imageUpdateRecord):
        image, folder = imageUpdateRecord
        if folder != self.folderData.openFolderPath:
            print('Folder no longer open:', folder)
            return
        key = ImageKey(image, 'img')
        thumb = self.folderData.thumb_path(image)
        elem = self.window[key]
        if not elem:
            print('Image not found:', image)
            pass
        else:
            print('Updated:', thumb)
            self.window[key].update(thumb)
            ###
            ### TODO: also update padding, or not...
            ###
            

    def update_star_display(self, image):
        # Note: imageKey = ImageKey obj obtained as event in event loop
        rating = self.folderData.get_rating(image)
        for i in range(4):
            ik = ImageKey(image, f'star{ i }')
            if rating >= i:
                self.window[ik].update('imgs/full_star.png')
            else:
                self.window[ik].update('imgs/empty_star.png')

    def menu_layout(self):
        return [
            sg.InputText(key=self.selectFolderKey, enable_events=True, visible=False), 
            sg.FolderBrowse('Open gallery', target=self.selectFolderKey),
            sg.Text(f'Folder: { self.folderShortName }', size=(60,1)),
        ]

    def gallery_element(self, elemData):
        # print('Received gallery element elem data:')
        # print(elemData)
        image = os.path.basename(elemData['img'])
        title = image
        imgSize = image_size(elemData['thumb'])
        rating = self.folderData.get_rating(image)
        if rating is None: 
            rating = -1
        xPad = (self.imgDim - imgSize[0])//2
        yPad = (self.imgDim - imgSize[1])//2
        layout = [
            [   
                sg.Image(
                    'imgs/full_star.png' if i <= rating else 'imgs/empty_star.png',
                    enable_events=True,
                    key=ImageKey(image, element=f'star{ i }'),
                )
                for i in range(4)
            ],
            [
                sg.Image(
                    elemData['thumb'],
                    pad=(xPad, yPad), 
                    enable_events=True,
                    key=ImageKey(image, element='img'),
                )
            ],
        ]
        if len(title) > 50:
            title = '...' + title[-47:]
        return sg.Frame(
            title, layout, 
            element_justification = 'center'
        )

    def gallery_row_element(self, rowData):
        return [
            self.gallery_element(elemData={
                'row': rowData['row'],
                'col': col,
                'img': data['name'],
                'thumb': 'imgs/loading_thumb.png', #data['thumb'],
            })
            for col, data in enumerate(rowData['imageDatas'])
            if data
        ]

    def image_data_grid(self, thumbs, imgNames):
        return to_grid(
            arr = [{'thumb': t, 'name': n} for t, n in zip(thumbs, imgNames)], 
            numCols = self.gridCols,
        )

    def gallery_layout(self):
        if self.folder:
            thumbs = self.folderData.thumbnail_paths()
            names = self.folderData.images()
            imgDataGrid = self.image_data_grid(thumbs=thumbs, imgNames=names)
            rowDataDicts = [
                {'row': row, 'imageDatas': imageDatas}
                for row, imageDatas in enumerate(imgDataGrid)
            ]
            return [
                self.gallery_row_element(rowData)
                for row, rowData in enumerate(rowDataDicts)
            ]
        else:
            displayText = 'Gallery will go here...'
            return [[ sg.Text(displayText, size=(100,40)) ]]

    def layout(self):
        return [
            self.menu_layout(),
            [sg.Column(
                self.gallery_layout(), 
                size = (self.gridCols*(self.imgDim + 40), 2*self.imgDim), 
                scrollable = True,
                vertical_scroll_only = True,
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


if __name__ == '__main__':
    wm = WindowManager()
    wm.run_window()