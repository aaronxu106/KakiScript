import General
import time
import pyautogui
import configparser
import sys
from datetime import datetime
import threading

from PIL import Image, ImageGrab

# import imagehash

# version 1.8.2, By Signal


def main():
    start_time = time.time()
    f = open('Kakilog.log', 'a+', encoding='utf-8')
    now = datetime.now()
    print("Log started: ", now, file=f)
    # read config file
    config = configparser.ConfigParser()
    try:
        config.read('config.ini', encoding='utf-8')
    except:
        config.read('config.ini', encoding='utf-8-sig')

    title = 'KakiRaid'
    if int(config['DEFAULT']['AdjustWindow']) == 1:
        General.adjust_window(title, [0, 0])
        time.sleep(0.2)
    elif int(config['DEFAULT']['AdjustWindow']) == 2:
        General.adjust_window(title, [245, 123])
        time.sleep(0.2)
    window = General.get_window_coordinate(title)  # x, y, w, h
    time.sleep(0.2)
    window.append(start_time)  # index 4

    auto_legend_count = int(config['DEFAULT']['AutoLegendCount'])
    if int(config['DEFAULT']['ModeSelection']) == 0:
        count = 0
        max_count = int(config['DEFAULT']['MainLoopCount'])
        current_floor = 0
        stat = dict()
        stat['Total_Resources'] = 0
        stat['Total_Monster'] = 0
        stat['Total_Loot_Curse'] = 0
        stat['Total_Loot_Other'] = 0
        stat['Total_Camp'] = 0
        stat['Total_Ruin'] = 0
        window.append(stat)  # index 5
        window.append(config)  # index 6
        window.append(f)
        keys = [window[6]['Baidu_API']['API_ID'], window[6]['Baidu_API']['API_KEY'],
                window[6]['Baidu_API']['SECRET_KEY']]
        # while count < max_count:
        thread_1 = threading.Thread(target=General.click_continue, args=(window,))
        thread_1.start()
        while True:
            print('\n', file=f)
            f.flush()
            temp_start_time = time.time()
            General.failure_detect(window)  # thread
            curse_page_result = General.curse_page_detect(window, 400)  # thread
            if not curse_page_result:
                while General.confirm_detect(window):
                    time.sleep(1)
                time.sleep(0.5)
            else:
                curse_images = General.get_curse_image(window)
                curses = General.parse_curse_image(curse_images, keys)
                if curses != [0, 0, 0]:
                    General.select_curse(window, curses)
                    time.sleep(2.5)
                    while General.resource_completion_detect(window):
                        time.sleep(1.5)
                        General.resource_completion_click(window)
                else:
                    print("Baidu ocr failed!", file=f)
                    sys.exit()
            time.sleep(0.2)

            if General.start_floor_detect(window):
                # General.map_page_detect(window)  # thread
                # while General.resource_completion_detect(window):
                #     time.sleep(1)
                General.map_management(window)
                General.toggle_auto_path_finding(window)
                General.map_page_detect(window)
                elapsed_time = time.time() - temp_start_time
                print("Curse " + str(count) + " selected!", file=f)
                print('time elapsed: ' + str(elapsed_time) + ' seconds.', file=f)
                time.sleep(7)
            General.map_page_detect(window, 2)
            if not General.auto_route_detect(window):
                time.sleep(1.5)
                if not General.auto_route_detect(window):
                    General.toggle_auto_path_finding(window)

            count += 1

            if current_floor == 0:
                current_floor = General.floor_detection(window)
            else:
                current_floor += 5
                print('Current Floor: ' + str(current_floor) + '\n', file=f)
                f.flush()
            time.sleep(1)
    elif int(config['DEFAULT']['ModeSelection']) == 1:
        General.auto_legend(window, auto_legend_count)
    elif int(config['DEFAULT']['ModeSelection']) == 2:
        thread_1 = threading.Thread(target=General.click_continue, args=(window,))
        thread_1.start()
        grind_count = int(config['Void_Island']['Count'])
        if grind_count == 0:
            grind_count = 9999
        window.append(f)
        while grind_count > 0:
            General.void_island_grind(window)
            print('Void Island Completed', file=f)
            f.flush()
            grind_count -= 1


if __name__ == "__main__":
    main()

    # title = 'KakiRaid'
    # window = General.get_window_coordinate(title)

    # General.crop_circle_image('Ref\\auto_route_on.jpg', 'Ref\\auto_route_on_circle.png')
    # city_page = General.city_page_detect(window)
    # print(city_page)
    # print(window)
    # General.auto_route_detect(window)
    # pyautogui.press('space', presses=3, interval=3)
    # General.void_map_management(window)
    # General.circle_mask('auto_route.jpg')
    # General.click_continue(window)

    # pyautogui.moveTo(x=597 - 245 + location[0] + window[0], y=223 - 123 + location[1] + window[1], duration=0.5)
    # pyautogui.moveTo(x=1322, y=606, duration=0.5)
    # x = round((1322 - 658) / 95)
    # print(x)
    # confirm_counter = 8
    # confirm_flag = 0
    # toggle_flag = 0
    # while confirm_counter > 0:
    #     time.sleep(5)
    #     confirm_flag = General.confirm_detect(window)
    #     if confirm_flag is True:
    #         toggle_flag = 1
    #     confirm_counter -= 1
    # time.sleep(60)  # wait for battle finish
    # if confirm_flag == 0 and toggle_flag == 1:
    #     General.toggle_auto_path_finding(window)

    # upper_map_diff = [1594 - 245, 177 - 123, 1630 - 245, 215 - 123]
    # upper_map_img = ImageGrab.grab(bbox=(window[0] + upper_map_diff[0],
    #                                      window[1] + upper_map_diff[1],
    #                                      window[0] + upper_map_diff[2],
    #                                      window[1] + upper_map_diff[3]))
    # upper_map_img.save('in_battle.jpg', 'JPEG')
    #
    # upper_map_diff = [1232 - 245, 851 - 123, 1401 - 245, 926 - 123]
    # upper_map_img = ImageGrab.grab(bbox=(window[0] + upper_map_diff[0],
    #                                      window[1] + upper_map_diff[1],
    #                                      window[0] + upper_map_diff[2],
    #                                      window[1] + upper_map_diff[3]))
    # upper_map_img.save('battle_end2.jpg', 'JPEG')
    #
    # im_hash_void_complete = imagehash.average_hash(Image.open('void_complete.jpg'))
    # im_hash_void_complete_ref = imagehash.average_hash(Image.open('Ref\\void_complete_ref.jpg'))
    # print(abs(im_hash_void_complete - im_hash_void_complete_ref))

    # try:
    #     while True:
    #         x, y = pyautogui.position()
    #         positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
    #         print(positionStr, end='')
    #         print('\b' * len(positionStr), end='', flush=True)
    # except KeyboardInterrupt:
    #     print('\n')
