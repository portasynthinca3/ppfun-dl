#!/usr/bin/env python3

# PixelPlanet downloader by portasynthinca3
# Distributed under WTFPL

import requests
import time
import numpy as np, cv2
from colorama import Fore, Back, Style, init

me = {}

# gets raw chunk data from the server
def get_chunk(d, x, y):
    # get data from the server
    successful = False
    data = None
    while not successful:
        try:
            response = requests.get(f'https://pixelplanet.fun/chunks/{d}/{x}/{y}.bmp')
            data = response.content
            if response.status_code == 200:
                successful = True
            else:
                print(f'{Fore.YELLOW}Got status code {Fore.RED}{response.status_code}{Fore.YELLOW} from the server. Waiting{Style.RESET_ALL}')
                time.sleep(3)
        except:
            print(f'{Fore.YELLOW}Error while retrieving data. Waiting{Style.RESET_ALL}')
            time.sleep(3)
    # construct a numpy array from it
    arr = np.zeros((256, 256), np.uint8)
    if len(data) != 65536: #wtf? sometimes PPFun API returns images that are 0 bytes in size
        return arr
    for i in range(65536):
        c = data[i]
        # protected pixels are shifted up by 128
        if c >= 128:
            c = c - 128
        arr[i // 256, i % 256] = c
    return arr

# gets several map chunks from the server
def get_chunks(d, xs, ys, w, h):
    # the final image
    data = np.zeros((0, w * 256), np.uint8)
    # go through the chunks
    for y in range(h):
        # the row
        row = np.zeros((256, 0), np.uint8)
        for x in range(w):
            print(f'{Fore.YELLOW}Getting chunk {Fore.GREEN}{(y * w) + x + 1}{Fore.YELLOW} (out of {w * h} total){Style.RESET_ALL}')
            # append the chunk to the row
            row = np.concatenate((row, get_chunk(d, x + xs, y + ys)), axis=1)
        # append the row to the image
        data = np.concatenate((data, row), axis=0)
    return data

# renders map data into a colored CV2 image
def render_map(d, data):
    global me
    img = np.zeros((data.shape[0], data.shape[1], 3), np.uint8)
    colors = me['canvases'][str(d)]['colors']
    # go through the data
    for y in range(data.shape[0]):
        for x in range(data.shape[1]):
            r, g, b = colors[data[y, x]]
            img[y, x] = (b, g, r)
    return img

def main():
    global me

    # initialize colorama
    init()

    # get canvas info list and user identifier
    print(f'{Fore.YELLOW}Requesting initial data{Style.RESET_ALL}')
    me = requests.get('https://pixelplanet.fun/api/me').json()

    canv_id = -1
    while str(canv_id) not in me['canvases']:
        print(Fore.YELLOW + '\n'.join(['[' + (Fore.GREEN if ("v" not in me["canvases"][k]) else Fore.RED) + f'{k}{Fore.YELLOW}] ' +
                                           me['canvases'][k]['title'] for k in me['canvases']]))
        print(f'Select the canvas [0-{len(me["canvases"]) - 1}]:{Style.RESET_ALL} ', end='')
        canv_id = input()
        if 0 <= int(canv_id) <= len(me['canvases']) - 1:
            if 'v' in me['canvases'][canv_id]:
                print(Fore.RED + 'This canvas is not supported, only 2D canvases are supported' + Style.RESET_ALL)
                canv_id = -1

    canv_desc = me['canvases'][canv_id]
    canv_id = int(canv_id)

    # get chunk data
    data = get_chunks(canv_id, 0, 0, canv_desc['size'] // 256, canv_desc['size'] // 256)
    print(f'{Fore.YELLOW}Rendering chunks{Style.RESET_ALL}')

    img = render_map(canv_id, data)
    
    print(f'{Fore.YELLOW}Saving the image{Style.RESET_ALL}')
    cv2.imwrite(canv_desc['title'] + '.png', img)

if __name__ == "__main__":
    main()