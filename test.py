if __name__ == '__main__':

    import os
    import shutil
    import secrets
    import random
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
        src = os.path.join(testDir, 'src')
        dest = os.path.join(testDir, 'dest')
        try: shutil.rmtree(dest);
        except FileNotFoundError: pass;
        os.makedirs(dest)
        for image in glob.glob(os.path.join(src, '*.jpeg')):
            thumbs = thumbnails(image)
            imageName = os.path.basename(image)
            for size, thumb in zip(THUMBNAIL_SIZES, thumbs):
                saveName = f'{ size }_{ imageName }'
                thumb.save(os.path.join(dest, saveName))


    # test_show_window()
    # test_gallery_window()
    test_thumbnails()