if __name__ == '__main__':

    import os
    import secrets
    import random
    from gallery import *

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
    