import win32gui
import pyautogui
from PIL import Image, ImageGrab, ImageDraw
from aip import AipOcr
import time
import re
import cv2
from sklearn.cluster import KMeans
import os
import os.path
import numpy as np
from os import path
import imagehash
import copy
import configparser
import sys
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

# version 1.8.2, By Signal


class MapTile:
    def __init__(self, value=None, coordinate=None):
        self.value = value
        self.coordinate = coordinate
        self.children = []

    def add_child(self, map_tiles):
        for item in map_tiles:
            self.children.append(item)


class Solution:
    def __init__(self):
        self.tile_dict = dict()
        self.map_dict_to_value()
        self.max_weight = -999
        self.max_path = list()

    def path_max_weight(self, start, end):
        self.dfs(start, end, 0, [])
        return self.max_path

    def dfs(self, start, end, partial_weight, partial_path):
        if start == end:
            if partial_weight > self.max_weight:
                self.max_weight = partial_weight
                self.max_path = copy.deepcopy(partial_path)
        for child in start.children:
            partial_path.append(child)
            partial_weight += self.tile_dict[child.value]
            self.dfs(child, end, partial_weight, partial_path)
            partial_path.pop()
            partial_weight -= self.tile_dict[child.value]

    def map_dict_to_value(self):
        config = configparser.ConfigParser()
        try:
            config.read('config.ini', encoding='utf-8')
        except:
            config.read('config.ini', encoding='utf-8-sig')
        self.tile_dict['start'] = 0
        self.tile_dict['shop'] = 0
        self.tile_dict['secret'] = 1
        self.tile_dict['mystery'] = 1
        self.tile_dict['resource_sos'] = -500
        self.tile_dict['resource_wood'] = -500
        self.tile_dict['resource_ore'] = -500
        self.tile_dict['resource_pelt'] = -500
        self.tile_dict['resource_fish'] = -500
        self.tile_dict['resource_food'] = -500
        self.tile_dict['resource_herb'] = -500
        self.tile_dict['camp'] = 500
        self.tile_dict['loot_adv'] = 3
        self.tile_dict['loot_curse'] = 3
        self.tile_dict['loot_normal'] = 1
        self.tile_dict['ruin'] = 2
        self.tile_dict['monster_adv'] = 10
        self.tile_dict['monster_elite'] = -999
        self.tile_dict['monster_normal'] = 10
        self.tile_dict['end'] = 0
        self.tile_dict['unknown'] = -3
        config_weight_dict = config._sections['Map_Weight']
        for key, value in config_weight_dict.items():
            if key in self.tile_dict.keys() and value:
                self.tile_dict[key] = int(value)


def get_window_coordinate(title):
    hwnd = win32gui.FindWindowEx(None, None, None, title)
    try:
        win32gui.SetForegroundWindow(hwnd)
    finally:
        if not (hwnd == 0):
            rect = win32gui.GetWindowRect(hwnd)
            x = rect[0]
            y = rect[1]
            w = rect[2] - x
            h = rect[3] - y
            return [x, y, w, h]


def adjust_window(title, coordinate):
    hwnd = win32gui.FindWindowEx(None, None, None, title)
    try:
        win32gui.SetForegroundWindow(hwnd)
    finally:
        win32gui.MoveWindow(hwnd, coordinate[0], coordinate[1], 1429, 834, True)


def floor_detection(window, skip_level=150):
    skip_until = skip_level
    f = window[7]
    window_ref = [235, 84]
    floor_position_1 = [867, 116]
    floor_position_2 = [1054, 176]
    floor_diff_1 = [floor_position_1[0] - window_ref[0], floor_position_1[1] - window_ref[1]]
    floor_diff_2 = [floor_position_2[0] - window_ref[0], floor_position_2[1] - window_ref[1]]
    floor_image = ImageGrab.grab(bbox=(window[0]+floor_diff_1[0], window[1]+floor_diff_1[1],
                                       window[0]+floor_diff_2[0], window[1]+floor_diff_2[1]))
    floor_image.save('floor_image.jpg', 'JPEG')
    keys = [window[6]['Baidu_API']['API_ID'], window[6]['Baidu_API']['API_KEY'], window[6]['Baidu_API']['SECRET_KEY']]
    try:
        parsed_floor_image = baidu_ocr('floor_image.jpg', keys)
        floor = re.findall(r"\d+", parsed_floor_image[1]['words'])
        if floor and int(floor[0]):
            print('Current Floor: ' + floor[0] + '\n', file=f)
            f.flush()
            return int(floor[0])
        else:
            print('Failed to detect floor level. \n', file=f)
            f.flush()
            return 0
    except:
        print('Failed to detect floor level. \n', file=f)
        f.flush()
        return 0
        # if floor and int(floor[0]) < skip_until:
        #     print('Current Floor: ' + floor[0] + ', Skipped!')
        #     time.sleep(max(20*(skip_until - int(floor[0])), 0.1))  # assume 20s to clear 1 floor, wait until 150 floor
        #     return False
        # else:
        #     return True
    # else:
    #     time.sleep(5)  # if cannot find floor info, wait 5 sec and do again.
    #     floor_detection(window, skip_level)


def failure_detect(window):
    window_ref = [235, 84]
    fail_position_1 = [1317, 672]
    fail_position_2 = [1508, 771]
    fail_diff_1 = [fail_position_1[0] - window_ref[0], fail_position_1[1] - window_ref[1]]
    fail_diff_2 = [fail_position_2[0] - window_ref[0], fail_position_2[1] - window_ref[1]]
    fail_image = ImageGrab.grab(bbox=(window[0] + fail_diff_1[0], window[1] + fail_diff_1[1],
                                       window[0] + fail_diff_2[0], window[1] + fail_diff_2[1]))
    fail_image.save('fail_image.jpg', 'JPEG')
    im1_hash = imagehash.average_hash(Image.open('fail_image.jpg'))
    im2_hash = imagehash.average_hash(Image.open('Ref\\fail_image_ref.jpg'))
    f = window[7]
    if abs(im1_hash - im2_hash) <= 2:
        print('Battle Failed, Quitting Program...', file=f)
        print('Total Resource Tiles selected: ' + str(window[5]['Total_Resources']), file=f)
        print('Total Monster Tiles selected: ' + str(window[5]['Total_Monster']), file=f)
        print('Total Loot Curse Tiles selected: ' + str(window[5]['Total_Loot_Curse']), file=f)
        print('Total Loot Other selected: ' + str(window[5]['Total_Loot_Other']), file=f)
        print('Total Camp selected: ' + str(window[5]['Total_Camp']), file=f)
        print('Total Ruin selected: ' + str(window[5]['Total_Ruin']), file=f)
        elapsed_time = int(time.time() - window[4])
        print('Time elapsed:', file=f)
        print('{:02d}:{:02d}:{:02d}'.format(elapsed_time // 3600, (elapsed_time % 3600 // 60), elapsed_time % 60),
              file=f)
        # ctypes.windll.user32.MessageBoxW(0, 'Battle Failed, Quitting Program..', 'Message', 0x1000)
        time.sleep(1)
        send_email('Kaki battle failed, quit program.')
        sys.exit()
        #  [1205, 723] 继续, [1412, 716] 离开
        # To be added, auto-save and re-start a new session?


def confirm_detect(window):
    confirm_diff = [969 - 245, 635 - 123, 1123 - 245, 695 - 123]
    confirm_img_1 = ImageGrab.grab(bbox=(window[0] + confirm_diff[0], window[1] + confirm_diff[1],
                                         window[0] + confirm_diff[2], window[1] + confirm_diff[3]))
    confirm_img_1.save('confirm_img_1.jpg', 'JPEG')
    time.sleep(0.2)
    im1_hash = imagehash.average_hash(Image.open('confirm_img_1.jpg'))
    im2_hash = imagehash.average_hash(Image.open('Ref\\confirm_img_1_ref.jpg'))
    if abs(im1_hash - im2_hash) <= 3:
        pyautogui.click(x=1045 - 245 + window[0], y=668 - 123 + window[1], duration=0.8)
        return True
    else:
        return False


def get_curse_image(window):
    curse_1_coordinate_diff = [20, 270, 482, 677]
    curse_2_coordinate_diff = [503, 270, 920, 677]
    curse_3_coordinate_diff = [938, 270, 1348, 677]
    curse_img_1 = ImageGrab.grab(bbox=(window[0]+curse_1_coordinate_diff[0], window[1]+curse_1_coordinate_diff[1],
                                       window[0]+curse_1_coordinate_diff[2], window[1]+curse_1_coordinate_diff[3]))
    curse_img_2 = ImageGrab.grab(bbox=(window[0]+curse_2_coordinate_diff[0], window[1]+curse_2_coordinate_diff[1],
                                       window[0]+curse_2_coordinate_diff[2], window[1]+curse_2_coordinate_diff[3]))
    curse_img_3 = ImageGrab.grab(bbox=(window[0] + curse_3_coordinate_diff[0], window[1] + curse_3_coordinate_diff[1],
                                       window[0] + curse_3_coordinate_diff[2], window[1] + curse_3_coordinate_diff[3]))
    curse_img_1.save('curse_img_1.jpg', 'JPEG')
    curse_img_2.save('curse_img_2.jpg', 'JPEG')
    curse_img_3.save('curse_img_3.jpg', 'JPEG')
    return ['curse_img_1.jpg', 'curse_img_2.jpg', 'curse_img_3.jpg']


def auto_route_detect(window):
    auto_route_diff = [1570 - 245, 773 - 123, 1645 - 245, 846 - 123]
    auto_route_img = ImageGrab.grab(bbox=(window[0] + auto_route_diff[0],
                                          window[1] + auto_route_diff[1],
                                          window[0] + auto_route_diff[2],
                                          window[1] + auto_route_diff[3]))
    auto_route_img.save('auto_route.jpg', 'JPEG')
    time.sleep(0.01)

    in_battle_diff = [1594 - 245, 177 - 123, 1630 - 245, 215 - 123]
    in_battle_img = ImageGrab.grab(bbox=(window[0] + in_battle_diff[0],
                                         window[1] + in_battle_diff[1],
                                         window[0] + in_battle_diff[2],
                                         window[1] + in_battle_diff[3]))
    in_battle_img.save('in_battle.jpg', 'JPEG')

    ref_off = circle_mask("Ref//auto_route_off.jpg")
    real_time = circle_mask("auto_route.jpg")
    average_color_off = np.average(np.average(ref_off, axis=0), axis=0)
    average_color_real_time = np.average(np.average(real_time, axis=0), axis=0)

    im_hash = imagehash.average_hash(Image.open('in_battle.jpg'))
    im_ref_hash = imagehash.average_hash(Image.open('Ref\\in_battle_ref.jpg'))

    sum_off = 1
    for i in range(3):
        # sum_on += abs(average_color_real_time[i] - average_color_on[i])
        if abs(average_color_real_time[i] - average_color_off[i]) > 6:  # auto_route on
            # print('Auto_route check: ' + str(i) + 'th')
            # print(abs(average_color_real_time[i] - average_color_off[i]))
            sum_off = 0
    if sum_off == 1 and abs(im_ref_hash - im_hash) > 2:  # not in combat
        # print('combat diff (in combat less than 2)')
        # print(abs(im_ref_hash - im_hash))
        # print('auto_path on')
        return False
    else:
        return True


def parse_curse_image(curses, keys, count=2):
    try:
        curse1 = baidu_ocr(curses[0], keys)
        curse2 = baidu_ocr(curses[1], keys)
        curse3 = baidu_ocr(curses[2], keys)
    except:
        time.sleep(5)  # in case parse failed
        if count > 0:
            curses = parse_curse_image(curses, keys, count-1)
            curse1 = curses[0]
            curse2 = curses[1]
            curse3 = curses[2]
        else:
            return [0, 0, 0]
    return [curse1, curse2, curse3]


def crop_circle_image(filename, destination_name):
    img = Image.open(filename).convert("RGB")
    npImage = np.array(img)
    h, w = img.size

    # Create same size alpha layer with circle
    alpha = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(alpha)
    draw.pieslice([0, 0, h, w], 0, 360, fill=255)

    # Convert alpha Image to numpy array
    npAlpha = np.array(alpha)

    # Add alpha layer to RGB
    npImage = np.dstack((npImage, npAlpha))

    # Save with alpha
    Image.fromarray(npImage).save(destination_name)


def circle_mask(filename):
    im = cv2.imread(filename)
    height, width, depth = im.shape
    circle_img = np.zeros((height, width), np.uint8)
    cv2.circle(circle_img, (width // 2, height // 2), 37, 1, thickness=-1)

    masked_data = cv2.bitwise_and(im, im, mask=circle_img)
    return masked_data


def curse_page_detect(window, count=0):
    f = window[7]
    while count < 400:
        curse_page_diff = [692-274, 177-46, 1285-274, 278-46]
        curse_page_image = ImageGrab.grab(bbox=(window[0] + curse_page_diff[0], window[1] + curse_page_diff[1],
                                                window[0] + curse_page_diff[2], window[1] + curse_page_diff[3]))
        curse_page_image.save('curse_page_image.jpg', 'JPEG')
        time.sleep(0.5)
        im1_hash = imagehash.average_hash(Image.open('curse_page_image.jpg'))
        im2_hash = imagehash.average_hash(Image.open('Ref\\curse_page_image_ref.jpg'))
        if abs(im1_hash - im2_hash) <= 3:
            return True
        else:
            time.sleep(1)
            count += 1

    curse_page_diff = [692 - 274, 177 - 46, 1285 - 274, 278 - 46]
    curse_page_image = ImageGrab.grab(bbox=(window[0] + curse_page_diff[0], window[1] + curse_page_diff[1],
                                            window[0] + curse_page_diff[2], window[1] + curse_page_diff[3]))
    curse_page_image.save('curse_page_image.jpg', 'JPEG')
    time.sleep(0.5)
    im1_hash = imagehash.average_hash(Image.open('curse_page_image.jpg'))
    im2_hash = imagehash.average_hash(Image.open('Ref\\curse_page_image_ref.jpg'))

    if abs(im1_hash - im2_hash) <= 3:
        return True
    else:
        print('Fail to detect curse page, quitting program..', file=f)
        f.flush()
        return False


def baidu_ocr(pic_file, keys):
    APP_ID = keys[0]
    API_KEY = keys[1]
    SECRET_KEY = keys[2]
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    i = open(pic_file, 'rb')
    img = i.read()
    message = client.basicGeneral(img)  # 通用文字识别，每天 50 000 次免费
    # message = client.basicAccurate(img)   # 通用文字高精度识别，每天 800 次免费
    i.close()
    return message['words_result']


def select_curse(window, words_results, fail_count=0):  # select curse coordinate may need to be updated.
    start_time = time.time()
    f = window[7]
    keys = [window[6]['Baidu_API']['API_ID'], window[6]['Baidu_API']['API_KEY'], window[6]['Baidu_API']['SECRET_KEY']]
    try:
        if len(words_results[0]) >= 2:
            forbidden_words = window[6]['Forbidden_Curse_Affix']['forbidden_words'].split(',')
            curse_score = [0, 0, 0]
            select = [1, 1, 1]
            max_score = 0
            selected = 0
            for i in range(len(words_results)):
                try:
                    curse_score[i] = words_results[i][1]['words'].split(':')[1]  # when fail to recognize? out of range?
                except:
                    print('Failed to detect curse score!', file=f)
                    pass
                for j in range(4, len(words_results[i])):
                    temp_word = words_results[i][j]['words']
                    if any(x in temp_word for x in forbidden_words):
                        select[i] = 0
            for index in range(len(words_results)):
                if select[index] == 1:
                    if int(curse_score[index]) > max_score:
                        max_score = int(curse_score[index])
                        selected = index+1
            if selected == 1:
                print("Curse_score: " + words_results[0][1]['words'].split(':')[1], file=f)
                print("Curse_first_affix: " + words_results[0][4]['words'], file=f)
                pyautogui.click(x=window[0]+277, y=window[1]+750)  # actual - window x, y
            elif selected == 2:
                print("Curse_score: " + words_results[1][1]['words'].split(':')[1], file=f)
                print("Curse_first_affix: " + words_results[1][4]['words'], file=f)
                pyautogui.click(x=window[0]+715, y=window[1]+750)
            elif selected == 3:
                print("Curse_score: " + words_results[2][1]['words'].split(':')[1], file=f)
                print("Curse_first_affix: " + words_results[2][4]['words'], file=f)
                pyautogui.click(x=window[0]+1149, y=window[1]+750)
            else:
                print("No available curse, re-selecting...", file=f)
                pyautogui.click(x=window[0]+1356, y=window[1]+184)
                pyautogui.moveTo(window[0] + window[2]//2, window[1] + window[3]//2)
                curse_images = get_curse_image(window)
                curses = parse_curse_image(curse_images, keys)
                select_curse(window, curses)
            f.flush()
        else:
            time.sleep(2)
            print("Unknown Error Occurred, Refreshing..", file=f)
            pyautogui.click(x=window[0] + 1356, y=window[1] + 184)
            pyautogui.moveTo(window[0] + window[2] // 2, window[1] + window[3] // 2)
            curse_images = get_curse_image(window)
            curses = parse_curse_image(curse_images, keys)
            fail_count += 1  # add fail limit
            if fail_count <= 5:
                select_curse(window, curses, fail_count)
            else:
                print('Curse detection failed, quitting program..', file=f)
                f.flush()
                send_email('Kaki script failed to detect curse, quit program.')
                sys.exit()
    except:
        time.sleep(2)
        print("Unknown Error Occurred, Refreshing..", file=f)
        pyautogui.click(x=window[0] + 1356, y=window[1] + 184)
        pyautogui.moveTo(window[0] + window[2] // 2, window[1] + window[3] // 2)
        curse_images = get_curse_image(window)
        curses = parse_curse_image(curse_images, keys)
        fail_count += 1  # add fail limit
        if fail_count <= 5:
            select_curse(window, curses, fail_count)
        else:
            print('Curse detection failed, quitting program..', file=f)
            f.close()
            send_email('Kaki script failed to detect curse, quit program.')
            sys.exit()
        # else:  # detect if stuck
        #     stuck_result = stuck_detect(window)
        #     if stuck_result == 2:
        #         pyautogui.click(x=window[0] + (320 - 245), y=window[1] + (213 - 123), duration=0.1)
        #         toggle_auto_path_finding(window)
        #         print('Adventure stuck at relic augmentation, resolving..')
        #     elif stuck_result == 1:
        #         toggle_auto_path_finding(window)
        #         print('Adventure stuck at random place, resolving..')
        #     else:
        #         time.sleep(90)
        #         select_curse(window, curses, fail_count)


def city_page_detect(window):
    city_page_diff = [1571 - 245, 910 - 123, 1656 - 245, 933 - 123]
    city_page_img = ImageGrab.grab(bbox=(window[0] + city_page_diff[0],
                                         window[1] + city_page_diff[1],
                                         window[0] + city_page_diff[2],
                                         window[1] + city_page_diff[3]))
    city_page_img.save('city_page.jpg', 'JPEG')
    time.sleep(0.1)
    im_hash = imagehash.average_hash(Image.open('city_page.jpg'))
    im_ref_hash = imagehash.average_hash(Image.open('Ref\\city_page_ref.jpg'))
    if abs(im_hash - im_ref_hash) < 3:
        return True
    else:
        return False


def stuck_detect(window):
    stuck_coordinate_diff = [962 - 245, 203 - 123, 1427 - 245, 255 - 123]
    stuck_image1 = ImageGrab.grab(bbox=(window[0] + stuck_coordinate_diff[0], window[1] + stuck_coordinate_diff[1],
                                        window[0] + stuck_coordinate_diff[2], window[1] + stuck_coordinate_diff[3]))
    stuck_image1.save('stuck_image1.jpg', 'JPEG')
    time.sleep(5)
    stuck_image2 = ImageGrab.grab(bbox=(window[0] + stuck_coordinate_diff[0], window[1] + stuck_coordinate_diff[1],
                                        window[0] + stuck_coordinate_diff[2], window[1] + stuck_coordinate_diff[3]))
    stuck_image2.save('stuck_image2.jpg', 'JPEG')
    im1_hash = imagehash.average_hash(Image.open('stuck_image1.jpg'))
    im2_hash = imagehash.average_hash(Image.open('stuck_image2.jpg'))
    im_ref_hash = imagehash.average_hash(Image.open('Ref\\stuck_ref1.jpg'))
    if abs(im1_hash - im2_hash) <= 2:
        if abs(im1_hash - im_ref_hash) <= 2:
            return 2  # stuck at relic augmentation
        else:
            return 1  # general stuck
    else:
        return 0  # not stuck


def toggle_auto_path_finding(window):
    toggle_diff = [1607-236, 810-123]
    time.sleep(0.2)
    pyautogui.click(x=window[0] + toggle_diff[0], y=window[1] + toggle_diff[1])


def map_management(window):  # window [x, y, w, h, start.time, stat(dict)]
    # add check to see if at map selection page
    time.sleep(1.8)
    map_button_diff = [367-246, 889-123]
    map_coordinate = dict()
    pyautogui.moveTo(window[0] + map_button_diff[0], window[1] + map_button_diff[1], duration=0.3)
    pyautogui.click()
    time.sleep(0.7)
    map_tile_0_0_diff = [646-246, 401-123, 734-246, 549-123]
    map_coordinate[(0, 0)] = [int(map_tile_0_0_diff[0] + map_tile_0_0_diff[2]) // 2 + window[0],
                              int(map_tile_0_0_diff[1] + map_tile_0_0_diff[3]) // 2 + window[1]]
    map_tile_1_0_diff = [646-246, 556-123, 732-246, 701-123]
    map_coordinate[(1, 0)] = [int(map_tile_1_0_diff[0] + map_tile_1_0_diff[2]) // 2 + window[0],
                              int(map_tile_1_0_diff[1] + map_tile_1_0_diff[3]) // 2 + window[1]]

    map_tile_0_1_diff = [782-246, 324-123, 869-246, 470-123]
    map_coordinate[(0, 1)] = [int(map_tile_0_1_diff[0] + map_tile_0_1_diff[2]) // 2 + window[0],
                              int(map_tile_0_1_diff[1] + map_tile_0_1_diff[3]) // 2 + window[1]]
    map_tile_1_1_diff = [782-246, 478-123, 871-246, 625-123]
    map_coordinate[(1, 1)] = [int(map_tile_1_1_diff[0] + map_tile_1_1_diff[2]) // 2 + window[0],
                              int(map_tile_1_1_diff[1] + map_tile_1_1_diff[3]) // 2 + window[1]]
    map_tile_2_1_diff = [782-246, 635-123, 868-246, 781-123]
    map_coordinate[(2, 1)] = [int(map_tile_2_1_diff[0] + map_tile_2_1_diff[2]) // 2 + window[0],
                              int(map_tile_2_1_diff[1] + map_tile_2_1_diff[3]) // 2 + window[1]]

    map_tile_0_2_diff = [916-246, 245-123, 1003-246, 390-123]
    map_coordinate[(0, 2)] = [int(map_tile_0_2_diff[0] + map_tile_0_2_diff[2]) // 2 + window[0],
                              int(map_tile_0_2_diff[1] + map_tile_0_2_diff[3]) // 2 + window[1]]
    map_tile_1_2_diff = [917-246, 401-123, 1003-246, 545-123]
    map_coordinate[(1, 2)] = [int(map_tile_1_2_diff[0] + map_tile_1_2_diff[2]) // 2 + window[0],
                              int(map_tile_1_2_diff[1] + map_tile_1_2_diff[3]) // 2 + window[1]]
    map_tile_2_2_diff = [916-246, 557-123, 1002-246, 701-123]
    map_coordinate[(2, 2)] = [int(map_tile_2_2_diff[0] + map_tile_2_2_diff[2]) // 2 + window[0],
                              int(map_tile_2_2_diff[1] + map_tile_2_2_diff[3]) // 2 + window[1]]
    map_tile_3_2_diff = [917-246, 711-123, 1002-246, 857-123]
    map_coordinate[(3, 2)] = [int(map_tile_3_2_diff[0] + map_tile_3_2_diff[2]) // 2 + window[0],
                              int(map_tile_3_2_diff[1] + map_tile_3_2_diff[3]) // 2 + window[1]]

    map_tile_0_3_diff = [1052-246, 325-123, 1138-246, 469-123]
    map_coordinate[(0, 3)] = [int(map_tile_0_3_diff[0] + map_tile_0_3_diff[2]) // 2 + window[0],
                              int(map_tile_0_3_diff[1] + map_tile_0_3_diff[3]) // 2 + window[1]]
    map_tile_1_3_diff = [1053-246, 480-123, 1138-246, 623-123]
    map_coordinate[(1, 3)] = [int(map_tile_1_3_diff[0] + map_tile_1_3_diff[2]) // 2 + window[0],
                              int(map_tile_1_3_diff[1] + map_tile_1_3_diff[3]) // 2 + window[1]]
    map_tile_2_3_diff = [1053-246, 637-123, 1138-246, 779-123]
    map_coordinate[(2, 3)] = [int(map_tile_2_3_diff[0] + map_tile_2_3_diff[2]) // 2 + window[0],
                              int(map_tile_2_3_diff[1] + map_tile_2_3_diff[3]) // 2 + window[1]]

    map_tile_0_4_diff = [1186-246, 402-123, 1273-246, 546-123]
    map_coordinate[(0, 4)] = [int(map_tile_0_4_diff[0] + map_tile_0_4_diff[2]) // 2 + window[0],
                              int(map_tile_0_4_diff[1] + map_tile_0_4_diff[3]) // 2 + window[1]]
    map_tile_1_4_diff = [1187-246, 558-123, 1271-246, 703-123]
    map_coordinate[(1, 4)] = [int(map_tile_1_4_diff[0] + map_tile_1_4_diff[2]) // 2 + window[0],
                              int(map_tile_1_4_diff[1] + map_tile_1_4_diff[3]) // 2 + window[1]]

    map_tile_0_0_img = ImageGrab.grab(bbox=(window[0] + map_tile_0_0_diff[0], window[1] + map_tile_0_0_diff[1],
                                      window[0] + map_tile_0_0_diff[2], window[1] + map_tile_0_0_diff[3]))
    map_tile_1_0_img = ImageGrab.grab(bbox=(window[0] + map_tile_1_0_diff[0], window[1] + map_tile_1_0_diff[1],
                                            window[0] + map_tile_1_0_diff[2], window[1] + map_tile_1_0_diff[3]))

    map_tile_0_1_img = ImageGrab.grab(bbox=(window[0] + map_tile_0_1_diff[0], window[1] + map_tile_0_1_diff[1],
                                            window[0] + map_tile_0_1_diff[2], window[1] + map_tile_0_1_diff[3]))
    map_tile_1_1_img = ImageGrab.grab(bbox=(window[0] + map_tile_1_1_diff[0], window[1] + map_tile_1_1_diff[1],
                                            window[0] + map_tile_1_1_diff[2], window[1] + map_tile_1_1_diff[3]))
    map_tile_2_1_img = ImageGrab.grab(bbox=(window[0] + map_tile_2_1_diff[0], window[1] + map_tile_2_1_diff[1],
                                            window[0] + map_tile_2_1_diff[2], window[1] + map_tile_2_1_diff[3]))

    map_tile_0_2_img = ImageGrab.grab(bbox=(window[0] + map_tile_0_2_diff[0], window[1] + map_tile_0_2_diff[1],
                                            window[0] + map_tile_0_2_diff[2], window[1] + map_tile_0_2_diff[3]))
    map_tile_1_2_img = ImageGrab.grab(bbox=(window[0] + map_tile_1_2_diff[0], window[1] + map_tile_1_2_diff[1],
                                            window[0] + map_tile_1_2_diff[2], window[1] + map_tile_1_2_diff[3]))
    map_tile_2_2_img = ImageGrab.grab(bbox=(window[0] + map_tile_2_2_diff[0], window[1] + map_tile_2_2_diff[1],
                                            window[0] + map_tile_2_2_diff[2], window[1] + map_tile_2_2_diff[3]))
    map_tile_3_2_img = ImageGrab.grab(bbox=(window[0] + map_tile_3_2_diff[0], window[1] + map_tile_3_2_diff[1],
                                            window[0] + map_tile_3_2_diff[2], window[1] + map_tile_3_2_diff[3]))

    map_tile_0_3_img = ImageGrab.grab(bbox=(window[0] + map_tile_0_3_diff[0], window[1] + map_tile_0_3_diff[1],
                                            window[0] + map_tile_0_3_diff[2], window[1] + map_tile_0_3_diff[3]))
    map_tile_1_3_img = ImageGrab.grab(bbox=(window[0] + map_tile_1_3_diff[0], window[1] + map_tile_1_3_diff[1],
                                            window[0] + map_tile_1_3_diff[2], window[1] + map_tile_1_3_diff[3]))
    map_tile_2_3_img = ImageGrab.grab(bbox=(window[0] + map_tile_2_3_diff[0], window[1] + map_tile_2_3_diff[1],
                                            window[0] + map_tile_2_3_diff[2], window[1] + map_tile_2_3_diff[3]))

    map_tile_0_4_img = ImageGrab.grab(bbox=(window[0] + map_tile_0_4_diff[0], window[1] + map_tile_0_4_diff[1],
                                            window[0] + map_tile_0_4_diff[2], window[1] + map_tile_0_4_diff[3]))
    map_tile_1_4_img = ImageGrab.grab(bbox=(window[0] + map_tile_1_4_diff[0], window[1] + map_tile_1_4_diff[1],
                                            window[0] + map_tile_1_4_diff[2], window[1] + map_tile_1_4_diff[3]))

    map_tile_0_0_img.save('map_tile_0_0.jpg', 'JPEG')
    map_tile_1_0_img.save('map_tile_1_0.jpg', 'JPEG')

    map_tile_0_1_img.save('map_tile_0_1.jpg', 'JPEG')
    map_tile_1_1_img.save('map_tile_1_1.jpg', 'JPEG')
    map_tile_2_1_img.save('map_tile_2_1.jpg', 'JPEG')

    map_tile_0_2_img.save('map_tile_0_2.jpg', 'JPEG')
    map_tile_1_2_img.save('map_tile_1_2.jpg', 'JPEG')
    map_tile_2_2_img.save('map_tile_2_2.jpg', 'JPEG')
    map_tile_3_2_img.save('map_tile_3_2.jpg', 'JPEG')

    map_tile_0_3_img.save('map_tile_0_3.jpg', 'JPEG')
    map_tile_1_3_img.save('map_tile_1_3.jpg', 'JPEG')
    map_tile_2_3_img.save('map_tile_2_3.jpg', 'JPEG')

    map_tile_0_4_img.save('map_tile_0_4.jpg', 'JPEG')
    map_tile_1_4_img.save('map_tile_1_4.jpg', 'JPEG')

    image_list = ['map_tile_0_0.jpg', 'map_tile_1_0.jpg',
                  'map_tile_0_1.jpg', 'map_tile_1_1.jpg', 'map_tile_2_1.jpg',
                  'map_tile_0_2.jpg', 'map_tile_1_2.jpg', 'map_tile_2_2.jpg', 'map_tile_3_2.jpg',
                  'map_tile_0_3.jpg', 'map_tile_1_3.jpg', 'map_tile_2_3.jpg',
                  'map_tile_0_4.jpg', 'map_tile_1_4.jpg']
    coordinate_list = [[0, 0], [1, 0],
                       [0, 1], [1, 1], [2, 1],
                       [0, 2], [1, 2], [2, 2], [3, 2],
                       [0, 3], [1, 3], [2, 3],
                       [0, 4], [1, 4]]
    f = window[7]
    print('Map raw detection starts...', file=f)
    map_start_time = time.time()
    raw_color_list = [None] * 14
    for i in range(len(image_list)):
        temp_color = get_dominant_colors(image_list[i], 1)[0]
        if abs(temp_color[0] - 200) <= 15:
            if abs(temp_color[2] - 212) <= 22:
                raw_color_list[i] = 'mystery'
            elif abs(temp_color[2] - 81) <= 22:
                raw_color_list[i] = 'shop'
            else:
                if abs(temp_color[2] - 112) <= 22:
                    raw_color_list[i] = get_image_diff(image_list[i], 'Loot')
                else:
                    raw_color_list[i] = get_image_diff(image_list[i], 'Monster')
        elif abs(temp_color[0] - 226) <= 15:
            if abs(temp_color[2] - 112) <= 22:
                raw_color_list[i] = get_image_diff(image_list[i], 'Loot')
            else:
                raw_color_list[i] = get_image_diff(image_list[i], 'Monster')
        elif abs(temp_color[0] - 122) <= 15 and abs(temp_color[2] - 195) <= 15:
            # raw_color_list[i] = 'resources'  # add differentiation
            raw_color_list[i] = get_image_diff(image_list[i], 'Resources')
        elif abs(temp_color[0] - 155) <= 15 and abs(temp_color[2] - 93) <= 15:
            raw_color_list[i] = 'camp'
        elif abs(temp_color[0] - 143) <= 15 and abs(temp_color[2] - 157) <= 15:
            raw_color_list[i] = 'secret'
        else:
            raw_color_list[i] = 'unknown'
    print('Map raw detection complete!', file=f)
    map_elapsed_time = time.time() - map_start_time
    start, end = build_tree(raw_color_list, coordinate_list)
    map_path = find_route(start, end)
    map_path.pop()
    mark_route_diff = [524 - 246, 887 - 123]
    pyautogui.click(x=mark_route_diff[0] + window[0], y=mark_route_diff[1] + window[1], duration=0.2)

    print('Best path found:', file=f)
    for item in map_path:
        print('Tile: ' + item.value + '  coordinate: ' + str(item.coordinate), file=f)
        if item.value == 'resources':
            window[5]['Total_Resources'] += 1
        elif item.value == 'Monster_Normal' or item.value == 'Monster_Adv':
            window[5]['Total_Monster'] += 1
        elif item.value == 'Loot_Curse':
            window[5]['Total_Loot_Curse'] += 1
        elif item.value == 'camp':
            window[5]['Total_Camp'] += 1
        elif item.value == 'Ruin':
            window[5]['Total_Ruin'] += 1

        pyautogui.click(x=map_coordinate[tuple(item.coordinate)][0],
                        y=map_coordinate[tuple(item.coordinate)][1], duration=0.2)
    pyautogui.moveTo(window[0] + map_button_diff[0], window[1] + map_button_diff[1], duration=0.2)
    pyautogui.click()
    # toggle_auto_path_finding(window)
    print("Total map management time consumed: " + str(map_elapsed_time) + " seconds!", file=f)
    f.flush()


def void_map_management(window):
    map_button_diff = [367-246, 889-123]
    map_coordinate = dict()
    pyautogui.moveTo(window[0] + map_button_diff[0], window[1] + map_button_diff[1], duration=0.3)
    pyautogui.click()
    time.sleep(0.2)
    for i in range(10):
        time.sleep(0.1)
        pyautogui.vscroll(-1)
    pyautogui.moveTo(x=748-245+window[0], y=554-123+window[1], duration=0.5)
    pyautogui.mouseDown()
    time.sleep(0.5)
    pyautogui.dragRel(xOffset=-250, yOffset=369, duration=3, mouseDownUp=False)
    time.sleep(0.5)
    pyautogui.mouseUp()
    upper_map_diff = [597 - 245, 223 - 123, 1570 - 245, 825 - 123]
    upper_map_img = ImageGrab.grab(bbox=(window[0] + upper_map_diff[0],
                                         window[1] + upper_map_diff[1],
                                         window[0] + upper_map_diff[2],
                                         window[1] + upper_map_diff[3]))
    upper_map_img.save('upper_map.jpg', 'JPEG')

    pyautogui.moveTo(x=1340 - 245 + window[0], y=933 - 123 + window[1], duration=0.5)
    pyautogui.mouseDown()
    time.sleep(0.5)
    pyautogui.dragRel(xOffset=-462 - 245 + window[0], yOffset=-650 - 123 + window[1], duration=3, mouseDownUp=False)
    time.sleep(0.5)
    pyautogui.mouseUp()
    lower_map_diff = [256 - 245, 289 - 123, 1234 - 245, 947 - 123]
    lower_map_img = ImageGrab.grab(bbox=(window[0] + lower_map_diff[0],
                                         window[1] + lower_map_diff[1],
                                         window[0] + lower_map_diff[2],
                                         window[1] + lower_map_diff[3]))
    lower_map_img.save('lower_map.jpg', 'JPEG')
    upper_result = find_image('upper_map.jpg', 'Map//void_loot.jpg')
    lower_result = find_image('lower_map.jpg', 'Map//void_loot.jpg')
    if upper_result[0] > lower_result[0]:
        pyautogui.moveTo(x=1340 - 462 - 245 + window[0], y=933 - 650 - 123 + window[1], duration=0.5)
        pyautogui.mouseDown()
        time.sleep(0.5)
        pyautogui.dragRel(xOffset=462 - 245 + window[0], yOffset=650 - 123 + window[1], duration=3, mouseDownUp=False)
        time.sleep(0.5)
        pyautogui.mouseUp()
        void_loot_x = 597 - 245 + upper_result[1][0] + window[0] + 29
        void_loot_y = 223 - 123 + upper_result[1][1] + window[1] + 52

        map_start = [658 - 245 + window[0], 767 - 123 + window[1]]

        distance_x = round((void_loot_x - map_start[0]) / 95)
        distance_y = -round((void_loot_y - map_start[1]) / 54)
        mark_route_diff = [524 - 246, 887 - 123]
        pyautogui.click(x=mark_route_diff[0] + window[0], y=mark_route_diff[1] + window[1], duration=0.5)
        a = round((distance_x + distance_y) / 2)
        b = round((distance_x - distance_y) / 2)

        for i in range(a + 1):
            pyautogui.click(x=map_start[0] + 95 * i, y=map_start[1] - 54 * i, duration=0.25)
        for j in range(b):
            # print(map_start[0] + 95 * a + j + 1, map_start[1] - 54 * a + 54 * (j + 1))
            pyautogui.click(x=map_start[0] + 95 * a + 95 * (j + 1),
                            y=map_start[1] - 54 * a + 54 * (j + 1), duration=0.25)
        # close map and toggle auto
        pyautogui.moveTo(window[0] + map_button_diff[0], window[1] + map_button_diff[1], duration=0.2)
        pyautogui.click()
        time.sleep(0.5)
        # toggle_auto_path_finding(window)
    else:
        void_loot_x = 256 - 245 + lower_result[1][0] + window[0] + 29
        void_loot_y = 289 - 123 + lower_result[1][1] + window[1] + 52
        map_start = [318 - 245 + window[0], 400 - 123 + window[1]]

        distance_x = round((void_loot_x - map_start[0]) / 95)
        distance_y = round((void_loot_y - map_start[1]) / 54)
        mark_route_diff = [524 - 246, 887 - 123]
        pyautogui.click(x=mark_route_diff[0] + window[0], y=mark_route_diff[1] + window[1], duration=0.5)
        a = round((distance_x + distance_y) / 2)
        b = round((distance_x - distance_y) / 2)

        for i in range(a + 1):
            pyautogui.click(x=map_start[0] + 95 * i, y=map_start[1] + 54 * i, duration=0.5)
        for j in range(b):
            # print(map_start[0] + 95 * a + j + 1, map_start[1] + 54 * a + 54 * (j + 1))
            pyautogui.click(x=map_start[0] + 95 * a + 95 * (j + 1),
                            y=map_start[1] + 54 * a - 54 * (j + 1), duration=0.5)
        # close map and toggle auto
        pyautogui.moveTo(window[0] + map_button_diff[0], window[1] + map_button_diff[1], duration=0.2)
        pyautogui.click()
        time.sleep(0.5)
        toggle_auto_path_finding(window)
    pass


# def find_image(im_file, tpl_file):
#     im = cv2.imread(im_file)
#     tpl = cv2.imread(tpl_file)
#     im = np.atleast_3d(im)
#     tpl = np.atleast_3d(tpl)
#     H, W, D = im.shape[:3]
#     h, w = tpl.shape[:2]
#
#     # Integral image and template sum per channel
#     sat = im.cumsum(1).cumsum(0)
#     tplsum = np.array([tpl[:, :, i].sum() for i in range(D)])
#
#     # Calculate lookup table for all the possible windows
#     iA, iB, iC, iD = sat[:-h, :-w], sat[:-h, w:], sat[h:, :-w], sat[h:, w:]
#     lookup = iD - iB - iC + iA
#     # Possible matches
#     possible_match = np.where(np.logical_and.reduce([lookup[..., i] == tplsum[i] for i in range(D)]))
#     # possible_match = np.where(np.logical_and.reduce([abs(lookup[..., i] - tplsum[i]) <= 0.1*tplsum[i]
#     #                                                 for i in range(D)]))
#
#     # Find exact match
#     for y, x in zip(*possible_match):
#         if np.all(im[y+1:y+h+1, x+1:x+w+1] == tpl):
#             return y+1, x+1
#
#     return 0, 0


def find_image(im_file, tpl_file):
    im = cv2.imread(im_file)
    tpl = cv2.imread(tpl_file)
    method = cv2.TM_CCOEFF_NORMED
    result = cv2.matchTemplate(im, tpl, method)
    _, maxVal, _, maxLoc = cv2.minMaxLoc(result)
    # minVal, maxVal, minLoc, maxLoc = cv.MinMaxLoc(result)
    #  CV_TM_SQDIFF || CV_TM_SQDIFF_NORMED, match = min, other method, match = max
    return [maxVal, maxLoc]


def build_tree(map_list, coordinate_list):
    start = MapTile('start', [-1, 0])
    end = MapTile('end', [0, 5])
    tile = [None] * len(map_list)
    for i in range(len(map_list)):
        tile[i] = MapTile(map_list[i], coordinate_list[i])
    start.add_child([tile[0], tile[1]])
    tile[0].add_child([tile[2], tile[3]])
    tile[1].add_child([tile[3], tile[4]])
    tile[2].add_child([tile[5], tile[6]])
    tile[3].add_child([tile[6], tile[7]])
    tile[4].add_child([tile[7], tile[8]])
    tile[5].add_child([tile[9]])
    tile[6].add_child([tile[9], tile[10]])
    tile[7].add_child([tile[10], tile[11]])
    tile[8].add_child([tile[11]])
    tile[9].add_child([tile[12]])
    tile[10].add_child([tile[12], tile[13]])
    tile[11].add_child([tile[13]])
    tile[12].add_child([end])
    tile[13].add_child([end])
    return start, end


def find_route(start, end):
    route = Solution()
    result = route.path_max_weight(start, end)
    return result


def get_dominant_colors(image_path, clusters):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.reshape((img.shape[0] * img.shape[1], 3))
    kmeans = KMeans(n_clusters=clusters)
    kmeans.fit(img)
    colors = kmeans.cluster_centers_
    return colors.astype(int)


def get_image_diff(image1, folder_name):
    # img_ref will be a list of images
    image_ref = ['Map/' + folder_name + "/" + f for f in os.listdir('Map/' + folder_name)]
    im1_hash = imagehash.average_hash(Image.open(image1))
    dist_min = 99999999
    selection = 0
    temp_list = list()
    for i in range(len(image_ref)):
        temp_im_hash = imagehash.average_hash(Image.open(image_ref[i]))
        sum_dists = temp_im_hash - im1_hash
        temp_list.append(sum_dists)
        if sum_dists <= dist_min:
            dist_min = sum_dists
            selection = i
    best_match = image_ref[selection].split('.')[0].split('/')[2]
    return best_match


def auto_legend(window, counter):
    black_position = [1366, 632]
    reform_position = [858, 784]
    green_position = [1279, 514]
    window_ref = [235, 84]
    black_diff = [black_position[0] - window_ref[0], black_position[1] - window_ref[1]]
    reform_diff = [reform_position[0] - window_ref[0], reform_position[1] - window_ref[1]]
    green_diff = [green_position[0] - window_ref[0], green_position[1] - window_ref[1]]
    count = 0
    while count < counter:
        pyautogui.moveTo(window[0] + black_diff[0], window[1] + black_diff[1], duration=0.2)
        pyautogui.click()
        pyautogui.moveTo(window[0] + reform_diff[0], window[1] + reform_diff[1], duration=0.2)
        pyautogui.click()
        pyautogui.moveTo(window[0] + green_diff[0], window[1] + green_diff[1], duration=0.2)
        pyautogui.click()
        pyautogui.moveTo(window[0] + reform_diff[0], window[1] + reform_diff[1], duration=0.2)
        pyautogui.click()
        count += 1


def click_continue(window):
    while True:
        battle_end1_diff = [1082 - 245, 426 - 123, 1148 - 245, 491 - 123]
        battle_end1_img = ImageGrab.grab(bbox=(window[0] + battle_end1_diff[0],
                                               window[1] + battle_end1_diff[1],
                                               window[0] + battle_end1_diff[2],
                                               window[1] + battle_end1_diff[3]))
        time.sleep(0.1)
        battle_end1_img.save('battle_end1.jpg', 'JPEG')

        battle_end2_diff = [1232 - 245, 851 - 123, 1401 - 245, 926 - 123]
        battle_end2_img = ImageGrab.grab(bbox=(window[0] + battle_end2_diff[0],
                                               window[1] + battle_end2_diff[1],
                                               window[0] + battle_end2_diff[2],
                                               window[1] + battle_end2_diff[3]))
        time.sleep(0.1)
        battle_end2_img.save('battle_end2.jpg', 'JPEG')
        time.sleep(0.1)
        im_hash_1 = imagehash.average_hash(Image.open('battle_end1.jpg'))
        im_hash_2 = imagehash.average_hash(Image.open('battle_end2.jpg'))
        im_hash_ref_1 = imagehash.average_hash(Image.open('Ref\\battle_end1.jpg'))
        im_hash_ref_2 = imagehash.average_hash(Image.open('Ref\\battle_end2.jpg'))
        # im_hash_ref_3 = imagehash.average_hash(Image.open('Ref\\battle_end3.jpg'))
        # im_hash_ref_4 = imagehash.average_hash(Image.open('Ref\\battle_end4.jpg'))
        im_hash_ref_5 = imagehash.average_hash(Image.open('Ref\\battle_end5.jpg'))

        if abs(im_hash_1 - im_hash_ref_1) < 2:
            if abs(im_hash_2 - im_hash_ref_2) < 2:
                pyautogui.click(x=1316 - 245 + window[0], y=888 - 123 + window[1])
            # elif abs(im_hash_2 - im_hash_ref_3) < 3:
            #     pyautogui.click(x=1316 - 245 + window[0], y=888 - 123 + window[1])
            # elif abs(im_hash_2 - im_hash_ref_4) < 3:
            #     pyautogui.click(x=1316 - 245 + window[0], y=888 - 123 + window[1])
            elif abs(im_hash_2 - im_hash_ref_5) < 2:
                pyautogui.click(x=1316 - 245 + window[0], y=888 - 123 + window[1])
        time.sleep(0.8)


def map_page_detect(window, mode=1):
    map_button_diff = [287 - 245, 854 - 123, 441 - 245, 914 - 123]
    map_button_img = ImageGrab.grab(bbox=(window[0] + map_button_diff[0],
                                          window[1] + map_button_diff[1],
                                          window[0] + map_button_diff[2],
                                          window[1] + map_button_diff[3]))
    map_button_img.save('map_button.jpg', 'JPEG')
    time.sleep(0.2)
    im_hash = imagehash.average_hash(Image.open('map_button.jpg'))
    im_hash_ref = imagehash.average_hash(Image.open('Ref//map_button_ref.jpg'))
    im_hash_close_ref = imagehash.average_hash(Image.open('Ref//map_button_close.jpg'))
    if abs(im_hash_ref - im_hash) < 3:
        return True
    elif mode == 1 and abs(im_hash_close_ref - im_hash) < 3:  # map management check
        pyautogui.moveTo(window[0] + 367 - 246, window[1] + 889 - 123, duration=0.3)
        pyautogui.click()
        return False
    elif mode == 2 and abs(im_hash_close_ref - im_hash) < 3:  # general check
        time.sleep(2.5)
        map_button_diff = [287 - 245, 854 - 123, 441 - 245, 914 - 123]
        map_button_img = ImageGrab.grab(bbox=(window[0] + map_button_diff[0],
                                              window[1] + map_button_diff[1],
                                              window[0] + map_button_diff[2],
                                              window[1] + map_button_diff[3]))
        map_button_img.save('map_button.jpg', 'JPEG')
        time.sleep(0.2)
        im_hash = imagehash.average_hash(Image.open('map_button.jpg'))
        if abs(im_hash_close_ref - im_hash) < 3:
            pyautogui.moveTo(window[0] + 367 - 246, window[1] + 889 - 123, duration=0.3)
            pyautogui.click()
            print('map closed, outside map management')
        return False
    else:
        return False


def void_island_grind(window):
    time.sleep(1)
    f = window[5]
    config = configparser.ConfigParser()
    try:
        config.read('config.ini', encoding='utf-8')
    except:
        config.read('config.ini', encoding='utf-8-sig')
    restart = int(config['Void_Island']['Restart'])
    level = int(config['Void_Island']['Level'])
    melee_kaki_index = config['Void_Island']['Melee_Index'].split(',')
    range_kaki_index = config['Void_Island']['Range_Index'].split(',')

    if city_page_detect(window):
        adv_start_diff = [1619 - 245, 887 - 123]
        pyautogui.click(adv_start_diff[0] + window[0], adv_start_diff[1] + window[1], duration=0.25)

        # check if inventory full
        full_inventory_img_diff = [727 - 245, 351 - 123, 1190 - 245, 397 - 123]
        full_inventory_img = ImageGrab.grab(bbox=(window[0] + full_inventory_img_diff[0],
                                                  window[1] + full_inventory_img_diff[1],
                                                  window[0] + full_inventory_img_diff[2],
                                                  window[1] + full_inventory_img_diff[3]))
        full_inventory_img.save('inventory_check.jpg', 'JPEG')
        time.sleep(0.1)
        im_hash = imagehash.average_hash(Image.open('inventory_check.jpg'))
        im_hash_ref = imagehash.average_hash(Image.open('Ref\\inventory_check_ref.jpg'))
        if abs(im_hash - im_hash_ref) > 4:
            void_island_diff = [328 - 245, 560 - 123]
            pyautogui.click(void_island_diff[0] + window[0], void_island_diff[1] + window[1], duration=1)
            level_inc_diff = [1149 - 245, 716 - 123]
            time.sleep(1)
            if level > 1:
                pyautogui.click(level_inc_diff[0] + window[0], level_inc_diff[1] + window[1], clicks=level,
                                interval=0.5)
            time.sleep(0.5)
            grind_start_diff = [1103 - 245, 831 - 123]
            pyautogui.click(grind_start_diff[0] + window[0], grind_start_diff[1] + window[1], duration=1)
            team_select_diff = [859 - 245, 748 - 123]
            pyautogui.click(team_select_diff[0] + window[0], team_select_diff[1] + window[1], duration=1)

            melee_group_diff = [596 - 245, 624 - 123]
            first_kaki_diff = [365 - 245, 766 - 123]
            pyautogui.click(melee_group_diff[0] + window[0], melee_group_diff[1] + window[1], duration=1)
            time.sleep(0.5)
            move_counter = 0
            for i in range(len(melee_kaki_index)):  # max 13 kaki, in case of new kaki, need to modify the if statement
                if (int(melee_kaki_index[i]) - 6 * move_counter) > 7:
                    pyautogui.moveTo(first_kaki_diff[0] + 150 * 6 + window[0], first_kaki_diff[1] + window[1])
                    pyautogui.mouseDown()
                    time.sleep(0.5)
                    pyautogui.dragRel(xOffset=-150 * 6, yOffset=0, duration=3, mouseDownUp=False)
                    time.sleep(0.5)
                    pyautogui.mouseUp()
                    move_counter += 1
                    pyautogui.click(first_kaki_diff[0] +
                                    150 * (int(melee_kaki_index[i]) - 6 * move_counter - 1) + window[0],
                                    first_kaki_diff[1] + window[1], duration=0.8)
                elif (int(melee_kaki_index[i]) - 6 * move_counter) <= 7:
                    pyautogui.click(first_kaki_diff[0] +
                                    150 * (int(melee_kaki_index[i]) - 6 * move_counter - 1) + window[0],
                                    first_kaki_diff[1] + window[1], duration=0.8)

            range_group_diff = [797 - 245, 622 - 123]
            pyautogui.click(range_group_diff[0] + window[0], range_group_diff[1] + window[1], duration=0.8)
            for i in range(len(range_kaki_index)):  # max 17 kaki, in case of new kaki, need to modify if statement
                if (int(range_kaki_index[i]) - 6 * move_counter) > 13:
                    pyautogui.moveTo(first_kaki_diff[0] + 150 * 6 + window[0], first_kaki_diff[1] + window[1])
                    pyautogui.mouseDown()
                    time.sleep(0.5)
                    pyautogui.dragRel(xOffset=-150 * 6, yOffset=0, duration=3, mouseDownUp=False)
                    time.sleep(0.5)
                    pyautogui.mouseUp()
                    pyautogui.moveTo(first_kaki_diff[0] + 150 * 6 + window[0], first_kaki_diff[1] + window[1])
                    pyautogui.mouseDown()
                    time.sleep(0.5)
                    pyautogui.dragRel(xOffset=-150 * 6, yOffset=0, duration=3, mouseDownUp=False)
                    time.sleep(0.5)
                    pyautogui.mouseUp()
                    move_counter += 2
                    pyautogui.click(first_kaki_diff[0] +
                                    150 * (int(range_kaki_index[i]) - 6 * move_counter) + window[0] - 3,
                                    first_kaki_diff[1] + window[1], duration=0.8)
                elif (int(range_kaki_index[i]) - 6 * move_counter) > 7:
                    pyautogui.moveTo(first_kaki_diff[0] + 150 * 6 + window[0], first_kaki_diff[1] + window[1])
                    pyautogui.mouseDown()
                    time.sleep(0.5)
                    pyautogui.dragRel(xOffset=-150 * 6, yOffset=0, duration=3, mouseDownUp=False)
                    time.sleep(0.5)
                    pyautogui.mouseUp()
                    move_counter += 1
                    pyautogui.click(first_kaki_diff[0] +
                                    150 * (int(range_kaki_index[i]) - 6 * move_counter - 1) + window[0],
                                    first_kaki_diff[1] + window[1], duration=0.8)
                elif 0 < (int(range_kaki_index[i]) - 6 * move_counter) <= 7:
                    pyautogui.click(first_kaki_diff[0] +
                                    150 * (int(range_kaki_index[i]) - 6 * move_counter - 1) + window[0],
                                    first_kaki_diff[1] + window[1], duration=0.8)
                elif (int(range_kaki_index[i]) - 6 * move_counter) <= 0:
                    pyautogui.moveTo(first_kaki_diff[0] + window[0], first_kaki_diff[1] + window[1])
                    pyautogui.mouseDown()
                    time.sleep(0.5)
                    pyautogui.dragRel(xOffset=150 * 6, yOffset=0, duration=3, mouseDownUp=False)
                    time.sleep(0.5)
                    pyautogui.mouseUp()
                    move_counter -= 1
                    pyautogui.click(first_kaki_diff[0] +
                                    150 * (int(range_kaki_index[i]) - 6 * move_counter - 1) + window[0],
                                    first_kaki_diff[1] + window[1], duration=0.8)
            confirm_team_diff = [1493 - 245, 872 - 123]
            pyautogui.click(window[0] + confirm_team_diff[0], window[1] + confirm_team_diff[1], duration=0.5)
            go_button_diff = [1460 - 245, 839 - 123]
            pyautogui.click(window[0] + go_button_diff[0], window[1] + go_button_diff[1], duration=0.5)
            time.sleep(6)
            toggle_auto_path_finding(window)
            time.sleep(4.5)
            select_blessing_diff = [1047 - 245, 740 - 123]
            pyautogui.click(window[0] + select_blessing_diff[0], window[1] + select_blessing_diff[1], duration=0.5)
            time.sleep(5)
            while True:
                time.sleep(2)
                # print('loop started')  # Remove
                while confirm_detect(window):
                    # print('network turbulence, confirm button detected')  # Remove
                    time.sleep(1)
                while resource_completion_detect(window):
                    # print('resource task completed')  # Remove
                    time.sleep(2)
                    if resource_completion_detect(window):
                        resource_completion_click(window)
                    # print('resource task completed')  # Remove
                    time.sleep(1)
                if start_floor_detect(window):
                    # print('start floor detected')  # Remove

                    void_map_management(window)
                    # print('map management completed')  # Remove
                    if not auto_route_detect(window):
                        toggle_auto_path_finding(window)
                    # print('map management auto_route enabled')  # Remove
                    map_page_detect(window)
                    # print('map page closed')  # Remove
                    time.sleep(20)
                if not auto_route_detect(window):
                    time.sleep(1)
                    if not auto_route_detect(window):
                        toggle_auto_path_finding(window)
                map_page_detect(window, 2)
                void_complete_img_diff = [759 - 245, 842 - 123, 1160 - 245, 900 - 123]
                void_complete_img = ImageGrab.grab(bbox=(window[0] + void_complete_img_diff[0],
                                                         window[1] + void_complete_img_diff[1],
                                                         window[0] + void_complete_img_diff[2],
                                                         window[1] + void_complete_img_diff[3]))
                void_complete_img.save('void_complete.jpg', 'JPEG')
                time.sleep(0.2)
                im_hash_void_complete = imagehash.average_hash(Image.open('void_complete.jpg'))
                im_hash_void_complete_ref = imagehash.average_hash(Image.open('Ref\\void_complete_ref.jpg'))
                if abs(im_hash_void_complete - im_hash_void_complete_ref) < 3:
                    # print('void island completed')  # Remove
                    time.sleep(1.5)
                    success_continue_diff = [957 - 245, 874 - 123]
                    pyautogui.click(window[0] + success_continue_diff[0], window[1] + success_continue_diff[1],
                                    duration=0.5)
                    time.sleep(1.5)  # miracle_stone experience completion
                    pyautogui.click(window[0] + success_continue_diff[0], window[1] + success_continue_diff[1],
                                    duration=0.5)
                    time.sleep(1.5)  # confirm hero/god experience count down
                    pyautogui.click(window[0] + success_continue_diff[0], window[1] + success_continue_diff[1],
                                    duration=0.5)
                    time.sleep(1.5)  # confirm hero/god experience continue
                    pyautogui.click(window[0] + success_continue_diff[0], window[1] + success_continue_diff[1],
                                    duration=0.5)
                    time.sleep(1.5)  # ???
                    pyautogui.click(window[0] + success_continue_diff[0], window[1] + success_continue_diff[1],
                                    duration=0.5)
                    now = datetime.now()
                    print(now, file=f)
                    f.flush()
                    time.sleep(10)
                    break
        else:
            send_email('Inventory Full!')
            sys.exit()
    else:
        while True:
            time.sleep(2)
            # print('loop started')  # Remove
            while confirm_detect(window):
                # print('network turbulence, confirm button detected')  # Remove
                time.sleep(1)
            while resource_completion_detect(window):
                # print('resource task completed')  # Remove
                time.sleep(2)
                if resource_completion_detect(window):
                    resource_completion_click(window)
            if start_floor_detect(window):
                # print('start floor detected')  # Remove
                void_map_management(window)
                # print('map management completed')  # Remove
                if not auto_route_detect(window):
                    toggle_auto_path_finding(window)
                # print('map management auto_route enabled')  # Remove
                map_page_detect(window)
                # print('map page closed')  # Remove
                time.sleep(20)
            if not auto_route_detect(window):
                time.sleep(1)
                if not auto_route_detect(window):
                    toggle_auto_path_finding(window)
            map_page_detect(window, 2)
            void_complete_img_diff = [759 - 245, 842 - 123, 1160 - 245, 900 - 123]
            void_complete_img = ImageGrab.grab(bbox=(window[0] + void_complete_img_diff[0],
                                                     window[1] + void_complete_img_diff[1],
                                                     window[0] + void_complete_img_diff[2],
                                                     window[1] + void_complete_img_diff[3]))
            void_complete_img.save('void_complete.jpg', 'JPEG')
            time.sleep(0.2)
            im_hash_void_complete = imagehash.average_hash(Image.open('void_complete.jpg'))
            im_hash_void_complete_ref = imagehash.average_hash(Image.open('Ref\\void_complete_ref.jpg'))
            if abs(im_hash_void_complete - im_hash_void_complete_ref) < 3:
                # print('void island completed')  # Remove
                time.sleep(1.5)
                success_continue_diff = [957 - 245, 874 - 123]
                pyautogui.click(window[0] + success_continue_diff[0], window[1] + success_continue_diff[1],
                                duration=0.5)
                time.sleep(1.5)  # miracle_stone experience completion
                pyautogui.click(window[0] + success_continue_diff[0], window[1] + success_continue_diff[1],
                                duration=0.5)
                time.sleep(1.5)  # confirm hero/god experience count down
                pyautogui.click(window[0] + success_continue_diff[0], window[1] + success_continue_diff[1],
                                duration=0.5)
                time.sleep(1.5)  # confirm hero/god experience continue
                pyautogui.click(window[0] + success_continue_diff[0], window[1] + success_continue_diff[1],
                                duration=0.5)
                time.sleep(1.5)  # ???
                pyautogui.click(window[0] + success_continue_diff[0], window[1] + success_continue_diff[1],
                                duration=0.5)
                now = datetime.now()
                print(now, file=f)
                f.flush()
                time.sleep(10)
                break
    pass


def resource_completion_detect(window):
    time.sleep(0.5)
    first_track_diff = [729-245, 716-123, 794-245, 782-123]  # fail
    second_track_diff = [449-245, 716-123, 514-245, 782-123]  # success
    first_track_img = ImageGrab.grab(bbox=(window[0] + first_track_diff[0], window[1] + first_track_diff[1],
                                           window[0] + first_track_diff[2], window[1] + first_track_diff[3]))
    second_track_img = ImageGrab.grab(bbox=(window[0] + second_track_diff[0], window[1] + second_track_diff[1],
                                            window[0] + second_track_diff[2], window[1] + second_track_diff[3]))
    first_track_img.save('first_track_img.jpg', 'JPEG')
    second_track_img.save('second_track_img.jpg', 'JPEG')
    im1_hash = imagehash.average_hash(Image.open('first_track_img.jpg'))
    im1_hash_ref = imagehash.average_hash(Image.open('Ref\\first_track_img_ref.jpg'))
    im2_hash = imagehash.average_hash(Image.open('second_track_img.jpg'))
    im2_hash_ref = imagehash.average_hash(Image.open('Ref\\second_track_img_ref.jpg'))
    if abs(im1_hash - im1_hash_ref) <= 9 or abs(im2_hash - im2_hash_ref) <= 9:
        # pyautogui.click(window[0] + window[2] // 2, window[1] + window[3] // 8 * 7, duration=0.3)
        return True
    else:
        return False


def resource_completion_click(window):
    time.sleep(0.5)
    pyautogui.click(window[0] + window[2] // 2, window[1] + window[3] // 8 * 7, duration=0.3)


def start_floor_detect(window):
    map_start_diff = [922 - 245, 187 - 123, 996 - 245, 210 - 123]
    map_start_img = ImageGrab.grab(bbox=(window[0] + map_start_diff[0],
                                         window[1] + map_start_diff[1],
                                         window[0] + map_start_diff[2],
                                         window[1] + map_start_diff[3]))
    map_start_img.save('map_start.jpg', 'JPEG')
    time.sleep(0.2)
    im_hash = imagehash.average_hash(Image.open('map_start.jpg'))
    im_hash_ref = imagehash.average_hash(Image.open('Ref\\map_start.jpg'))
    if abs(im_hash - im_hash_ref) < 2:
        return True
    else:
        return False


# def send_email(message):
#     config = configparser.ConfigParser()
#     try:
#         config.read('config.ini', encoding='utf-8')
#     except:
#         config.read('config.ini', encoding='utf-8-sig')
#     gmail_user = config['Email']['email']
#
#     sent_from = "aaron.luke927@gmail.com"
#     to = [gmail_user]
#     subject = 'KakiScript Failed'
#     body = message
#
#     email_text = """From: %s\nTo: %s\nSubject: %s\n\n%s
#                  """ % (sent_from, ", ".join(to), subject, body)
#
#     try:
#         server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
#         server.ehlo()
#         server.login("aaron.luke927@gmail.com", "Asdfasdf2345!!!")
#         server.sendmail(sent_from, to, email_text)
#         server.close()
#     except Exception as e:
#         pass


def send_email(message):
    try:
        config = configparser.ConfigParser()
        try:
            config.read('config.ini', encoding='utf-8')
        except:
            config.read('config.ini', encoding='utf-8-sig')

        email_user = config['Email']['email']

        host = 'smtp.163.com'
        port = 465
        sender = 'aaron_luke927@163.com'
        # pwd = 'WWFWTEMTFYWSMOVD'
        pwd = 'UKRXHVMGYOJLSUZL'
        receiver = email_user
        body = message
        msg = MIMEText(body, 'html')
        msg['subject'] = 'KakiScript Failed!'
        msg['from'] = sender
        msg['to'] = receiver
        s = smtplib.SMTP_SSL(host, port)
        s.login(sender, pwd)
        s.sendmail(sender, receiver, msg.as_string())
    except:
        pass


#
# def doClick(cx, cy):
#     hwnd = win32gui.FindWindowEx(None, None, None, 'Calculator')
#     time.sleep(0.2)
#     # win32gui.SetForegroundWindow(hwnd)
#     long_position = win32api.MAKELONG(cx, cy)  # 模拟鼠标指针 传送到指定坐标
#     win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_position)  # 模拟鼠标按下
#     win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, long_position)  # 模拟鼠标弹起
