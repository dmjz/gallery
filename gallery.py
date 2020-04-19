import os
import json
import uuid
import PySimpleGUI as sg
from utils import \
    to_grid, list_images, make_thumbnails, THUMBNAIL_SIZES, \
    image_size


sg.theme('Dark Blue')

def get_folder_id_map():
    try:
        with open('.metadata\\folder_id_map.json') as f: 
            folderIdMap = json.load(f)
    except FileNotFoundError:
        folderIdMap = {}
    return folderIdMap


class WindowManager():
    """ Keep track of when we need to remake the window """

    selectFolderKey = 'select_folder'
    thumbsSubDir = '.thumbnails'
    thumbSize = 'S'
    imgDim = THUMBNAIL_SIZES[thumbSize]
    gridCols = 4
    folderIdMap = get_folder_id_map()

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
                if self.folderPath:
                    self.setup_thumbnails()
                return event
            #  We may have more interesting events in the future...
            if event == sg.TIMEOUT_KEY:
                continue

    def setup_thumbnails(self):
        if not self.folderPath:
            raise AttributeError('Set folderPath before setup_thumbnails()')
        if self.folderPath not in self.folderIdMap:
            self.folderIdMap[self.folderPath] = str(uuid.uuid4())
        folderId = self.folderIdMap[self.folderPath]
        self.thumbnailFolder = os.path.join(
            '.metadata', folderId, self.thumbsSubDir
        )
        try:
            os.makedirs(self.thumbnailFolder, exist_ok=False)
        except FileExistsError:
            pass
        else:
            make_thumbnails(self.folderPath, self.thumbnailFolder, makeDest=False)

    def thumbnail_path(self, img):
        return os.path.join(
            self.thumbnailFolder,
            f'{ self.thumbSize }_{ os.path.splitext(img)[0] }.png',
        )

    def thumbnail_paths(self):
        return [
            self.thumbnail_path(f)
            for f in list_images(self.folderPath)
        ]

    def menu_layout(self):
        return [
            sg.InputText(key=self.selectFolderKey, enable_events=True, visible=False), 
            sg.FolderBrowse('Open gallery', target=self.selectFolderKey),
            sg.Text(f'Folder: { self.folderShortName }', size=(60,1)),
        ]

    def gallery_element(self, elemData):
        title = os.path.basename(elemData['img'])
        if len(title) > 50:
            title = '...' + title[-47:]
        imgSize = image_size(elemData['thumb'])
        xPad = (self.imgDim - imgSize[0])//2
        yPad = (self.imgDim - imgSize[1])//2
        layout = [
            [   
                sg.Image('imgs/empty_star.png'),
                sg.Image('imgs/empty_star.png'),
                sg.Image('imgs/empty_star.png'),
                sg.Image('imgs/empty_star.png'),
            ],
            [sg.Image(elemData['thumb'], pad=(xPad, yPad))],
        ]
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
                'thumb': data['thumb'],
            })
            for col, data in enumerate(rowData['imageDatas'])
            if data
        ]

    def image_data_grid(self):
        thumbs = self.thumbnail_paths()
        names = list_images(self.folderPath)
        return to_grid(
            [{'thumb': t, 'name': n} for t, n in zip(thumbs, names)], 
            numCols = self.gridCols,
        )

    def gallery_layout(self):
        if self.folderPath:
            thumbs = self.thumbnail_paths()
            names = list_images(self.folderPath)
            rowDataDicts = [
                {'row': row, 'imageDatas': imageDatas}
                for row, imageDatas in enumerate(self.image_data_grid())
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
                size = (self.gridCols*self.imgDim + 100, 2*self.imgDim), 
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