import os
import json
import uuid
import PySimpleGUI as sg
from utils import \
    to_grid, list_images, make_thumbnails, THUMBNAIL_SIZES, \
    image_size

sg.theme('Dark Blue')


class FolderData():
    """ Load, edit, save folder metadata """

    thumbsSubDir = '.t'
    ###
    ### TODO: load all folder data right away
    ###
    allFolderData = {}
    ###

    def __init__(self):
        self.openFolderPath = None
        self.openFolderData = None
        self.settings = None

    def open_folder(self, folderPath, settings):
        # For now, just set up thumbnails
        self.openFolderPath = folderPath
        self.settings = settings
        self.openFolderData = self.get_folder_data(self.openFolderPath)
        return True

    def get_folder_data(self, folderPath):
        if folderPath in self.allFolderData:
            ###
            ### TODO: "data completeness checks", e.g. are there thumbnails
            ### of the right size (based on settings) for each image...
            ###
            return allFolderData[folderPath]
        return self.new_folder_data(folderPath)
    
    def new_folder_data(self, folderPath):
        folderData = {}
        folderData['path'] = folderPath
        folderData['uid'] = str(uuid.uuid4())
        folderData['thumbnailFolder'] = os.path.join(
            '.metadata', folderData['uid'], self.thumbsSubDir
        )
        folderData['shortName'] = os.path.basename(folderPath)
        folderData['ratings'] = {
            img: None for img in list_images(folderPath)
        }
        try:
            os.makedirs(folderData['thumbnailFolder'], exist_ok=False)
        except FileExistsError:
            pass
        make_thumbnails(folderPath, folderData['thumbnailFolder'], makeDest=False)
        return folderData

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

    def __init__(self):
        self.folder = None
        self.window = None

    @property
    def folderShortName(self):
        return self.folderData.folderShortName if self.folder else ''

    def window_event_loop(self):
        while True:
            event, values = self.window.read()
            print(event, values)
            if event is None:
                return event
            if event is self.selectFolderKey:
                self.folder = self.folderData.open_folder(
                    folderPath = values[self.selectFolderKey],
                    settings   = self.folderSettings,
                )
                return event
            #  We may have more interesting events in the future...
            if event == sg.TIMEOUT_KEY:
                continue

    def menu_layout(self):
        return [
            sg.InputText(key=self.selectFolderKey, enable_events=True, visible=False), 
            sg.FolderBrowse('Open gallery', target=self.selectFolderKey),
            sg.Text(f'Folder: { self.folderShortName }', size=(60,1)),
        ]

    def gallery_element(self, elemData):
        # print('Received gallery element elem data:')
        # print(elemData)
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