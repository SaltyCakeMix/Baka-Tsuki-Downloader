import requests
import codecs
import shutil
import string
import os
from bs4 import BeautifulSoup
from PIL import Image

# Inputs
volumes = range(1, 26)
title = 'Chrome Shelled Regios'
hostURL = 'https://www.baka-tsuki.org'
pageExtension = '/project/index.php?title=Chrome_Shelled_Regios:Volume'
idealImageWidth = 1200
maxImageDLWidth = 1920

for volume in volumes:
    # Page loading
    filePath = f'{title} - Volume {volume}'
    print(f'Downloading {filePath}...')
    
    fullURL = f'{hostURL}{pageExtension}{volume}'
    page = requests.get(fullURL)
    soup = BeautifulSoup(page.content, 'html.parser')
    mainText = soup.find('div', class_='mw-parser-output')
    
    # Removing unecessary elements
    fluff = []
    fluff += mainText.find_all('table')
    fluff += mainText.find_all('div', class_='printfooter')
    fluff += mainText.find_all('span', class_='mw-editsection')
    for i in fluff:
        i.decompose()
    
    # Creating directories
    if not os.path.exists(filePath):
        os.mkdir(filePath)
    if not os.path.exists(f'{filePath}/images'):
        os.mkdir(f'{filePath}/images')
    
    # Reconstructs html file
    soup = BeautifulSoup()
    mainText.name = 'body'
    del mainText['class']
    soup.body.replace_with(mainText)
    
    # Adds header
    soup.head.append(soup.new_tag('style')) # A little bit of CSS trickery goes on here
    soup.head.style.string = '''
        body {
            background-color: rgb(20, 20, 20);
            font-family: sans-serif;
            margin: 50px 15% 50px;
            line-height: 2;
            overflow-x: hidden;
            width: 70%;
        }
        
        h3 {color: white}
        h2 {color: white}
        h1 {color: white}
        p {
            color: white;
            margin: 0px;
            overflow-x: hidden;
        }
        center {    color: white}
        ::marker {  color: rgb(20, 20, 20)}
        a:link {    color: rgb(228, 172, 255)}
        a:visited { color: rgb(169, 126, 225)}
        .reference-text {color: white}
        img {
            object-fit: cover;
            max-width: 100%;
            height: auto;
            margin: 1em 0em;
        }
        '''
    meta = soup.new_tag('meta')
    meta['charset'] = 'utf-8'
    soup.head.append(meta)
    
    # Adds title
    h1 = soup.new_tag('h1')
    h1.string = filePath
    soup.body.insert(0, h1)
    
    # Modifying images in html
    dls = []
    i = 0
    blocks = soup('li', class_='gallerybox')
    blocks += soup('div', class_='thumb tright')
    for block in blocks:
        # Unwraps images
        image = block.find('img')
        block.replace_with(image.parent)
        
        # Getting highest resolution image url
        ext = image['src']
        if image.has_attr('data-file-width'):
            newWidth = min(int(image['data-file-width']) - 1, maxImageDLWidth)
            ext = f'{ext.rstrip(string.digits)}{newWidth}'
        url = f'{hostURL}{ext}'
        
        # Check for duplicates
        failedToDL = False
        if url in dls:
            index = dls.index(url)
            imagePath = f'images/{index}.jpg'
        else:
            # Downloading image
            imagePath = f'images/{i}.jpg'
            if not os.path.isfile(f'{filePath}/{imagePath}'):
                print(f'\tDownloading image {url}')
                r = requests.get(url, stream=True)
                if r.status_code == 200:
                    with open(f'{filePath}/{imagePath}', 'wb') as f: 
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)
                else:
                    print(f'\tFailed to download {url}')
                    print(f'\tError code {r.status_code}')
                    failedToDL = True
            dls.append(url)
            i += 1
            
        # Rewriting link in html
        if not failedToDL:
            im = Image.open(f'{filePath}/{imagePath}')
            width, height = im.size
            im.close()
            width = min(width, idealImageWidth)
        
            image['src'] = imagePath
            image['width'] = width
            image['height'] = 'auto'
            image.parent['href'] = imagePath
            if image.has_attr('srcset'):
                del image['srcset']
        
    # Writing to html file
    outputFile = codecs.open(f'{filePath}/{filePath}.html', 'w', 'utf-8')
    outputFile.write(str(soup))
    outputFile.close()
    print(f'Finished downloading {filePath}\n')