import win32gui
import win32api
import win32con
import pyautogui
from PIL import Image, ImageGrab
from aip import AipOcr
import time
import re
import cv2
from sklearn.cluster import KMeans
import os
import os.path
from os import path
import imagehash
import copy
import ctypes
import configparser
import sys
import smtplib


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
        config.read('config.ini', encoding='utf-8')
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


def parse_curse_image(curses, keys):
    try:
        curse1 = baidu_ocr(curses[0], keys)
        curse2 = baidu_ocr(curses[1], keys)
        curse3 = baidu_ocr(curses[2], keys)
    except:
        time.sleep(5)  # in case parse failed
        curse1 = parse_curse_image(curses, keys)[0]
        curse2 = parse_curse_image(curses, keys)[1]
        curse3 = parse_curse_image(curses, keys)[2]
    return [curse1, curse2, curse3]


def curse_page_detect(window, count=0):
    f = window[7]
    while count < 400:
        curse_page_diff = [692-274, 177-46, 1285-274, 278-46]
        curse_page_image = ImageGrab.grab(bbox=(window[0] + curse_page_diff[0], window[1] + curse_page_diff[1],
                                                window[0] + curse_page_diff[2], window[1] + curse_page_diff[3]))
        if path.exists('curse_page_image.jpg'):
            os.remove('curse_page_image.jpg')
        time.sleep(0.1)
        curse_page_image.save('curse_page_image.jpg', 'JPEG')
        im1_hash = imagehash.average_hash(Image.open('curse_page_image.jpg'))
        im2_hash = imagehash.average_hash(Image.open('Ref\\curse_page_image_ref.jpg'))
        if abs(im1_hash - im2_hash) <= 3:
            return True
        time.sleep(1)
        count += 1
    curse_page_diff = [692 - 274, 177 - 46, 1285 - 274, 278 - 46]
    curse_page_image = ImageGrab.grab(bbox=(window[0] + curse_page_diff[0], window[1] + curse_page_diff[1],
                                            window[0] + curse_page_diff[2], window[1] + curse_page_diff[3]))
    curse_page_image.save('curse_page_image.jpg', 'JPEG')
    im1_hash = imagehash.average_hash(Image.open('curse_page_image.jpg'))
    im2_hash = imagehash.average_hash(Image.open('Ref\\curse_page_image_ref.jpg'))

    if abs(im1_hash - im2_hash) <= 3:
        return True
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
    time.sleep(1.2)
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
    toggle_auto_path_finding(window)
    print("Total map management time consumed: " + str(map_elapsed_time) + " seconds!", file=f)
    f.flush()


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


def resource_completion_detect(window, count=0):
    time.sleep(1)
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
    if abs(im1_hash - im1_hash_ref) <= 3 or abs(im2_hash - im2_hash_ref) <= 3:  # fail here?
        pyautogui.click(window[0] + window[2] // 2, window[1] + window[3] // 8 * 7, duration=0.25)
        count += 1
        if count < 2:
            resource_completion_detect(window, count)
        return True
    else:
        return False


def send_email(message):
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')

    gmail_user = config['Email']['username']

    sent_from = "aaron.luke927@gmail.com"
    to = [gmail_user]
    subject = 'KakiScript Failed'
    body = message

    email_text = """From: %s\nTo: %s\nSubject: %s\n\n%s
                 """ % (sent_from, ", ".join(to), subject, body)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login("aaron.luke927@gmail.com", "Asdfasdf2345!!!")
        server.sendmail(sent_from, to, email_text)
        server.close()
    except Exception as e:
        pass

#
# def doClick(cx, cy):
#     hwnd = win32gui.FindWindowEx(None, None, None, 'Calculator')
#     time.sleep(0.2)
#     # win32gui.SetForegroundWindow(hwnd)
#     long_position = win32api.MAKELONG(cx, cy)  # 模拟鼠标指针 传送到指定坐标
#     win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_position)  # 模拟鼠标按下
#     win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, long_position)  # 模拟鼠标弹起
