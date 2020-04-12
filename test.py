if __name__ == '__main__':

    import os
    import shutil
    import secrets
    import random
    from timeit import default_timer as timer
    from gallery import *

    def sample_gallery_folder():
        source = secrets.galleryPath
        for folder in os.listdir(source):
            for f in os.listdir(os.path.join(source, folder)):
                return os.path.join(source, folder, f)

    def test_show_window():
        """ Test the window (the first, super-basic one) """

        source = secrets.galleryPath
        galleryFolders = [
            os.path.join(source, folder, f) 
            for folder in os.listdir(source) 
            for f in os.listdir(os.path.join(source, folder))
        ]
        folder = galleryFolders[0]
        images = list_images(folder)
        print(images[:10])
        image = random.choice(images)
        #open_image(folder, image)
        show_window(folder)

    def test_gallery_window():
        """ Test the gallery_window """

        show_gallery_window()

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
            numImages = make_thumbnails(src, dest)
            end = timer()
            print(f'Thumbnail test runtime for { srcLeaf }:')
            print(f'{ end-start } seconds, { (end-start)/numImages } sec/file')

    def test_main_window():
        """ Test the main_window """

        show_main_window()

    def test_WindowManager():
        """ Test WindowManager class """

        wm = WindowManager()
        wm.run_window()



    # test_show_window()
    # test_gallery_window()
    # test_thumbnails()
    # test_main_window()
    test_WindowManager()