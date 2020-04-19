if __name__ == '__main__':

    import os
    import shutil
    import local_secrets
    import random
    from timeit import default_timer as timer
    from gallery import *

    def sample_gallery_folder():
        source = local_secrets.galleryPath
        for folder in os.listdir(source):
            for f in os.listdir(os.path.join(source, folder)):
                return os.path.join(source, folder, f)

    def test_thumbnails():
        """ Test thumbnail creation """

        testDir = '.test_thumbnail'
        for srcLeaf in ('src_small', 'src_med', 'src_large'):
            src = os.path.join(testDir, srcLeaf)
            dest = os.path.join(testDir, 'dest')
            try: 
                shutil.rmtree(dest)
            except FileNotFoundError: 
                pass
            os.makedirs(dest)
            start = timer()
            numImages = make_thumbnails(src, dest, makeDest=False)
            end = timer()
            print(f'Thumbnail test runtime for { srcLeaf }:')
            print(f'{ end-start } seconds, { (end-start)/numImages } sec/file')

    def test_WindowManager():
        """ Test WindowManager class """

        wm = WindowManager()
        wm.run_window()

    def test_layout_components():
        """ Test WindowManager layout components """

        wm = WindowManager()
        wm.folderPath = local_secrets.testGalleryLayoutFolderPath
        return {
            'menu': wm.menu_layout(),
            'gallery': wm.gallery_layout(),
            'full': wm.layout(),
        }

    
    # test_thumbnails()
    test_WindowManager()
    # d =  test_layout_components()