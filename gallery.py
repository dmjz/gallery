import os
import PySimpleGUI as sg
from utils import to_grid, list_images, make_thumbnails


sg.theme('Dark Blue')

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



if __name__ == '__main__':
    wm = WindowManager()
    wm.run_window()