import General
import time
import pyautogui
import configparser
import sys
from datetime import datetime


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
    elif int(config['DEFAULT']['AdjustWindow']) == 2:
        General.adjust_window(title, [245, 123])
    window = General.get_window_coordinate(title)  # x, y, w, h
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
        while count < max_count:
            print('\n', file=f)
            f.flush()
            temp_start_time = time.time()
            if count != 0:
                if current_floor > 500:
                    time.sleep(130)
                elif current_floor > 400:
                    time.sleep(120)
                elif current_floor > 300:
                    time.sleep(95)
                elif current_floor > 200:
                    time.sleep(85)
                else:
                    time.sleep(75)
            General.failure_detect(window)
            curse_page_result = General.curse_page_detect(window)
            if not curse_page_result:
                stuck_result = General.stuck_detect(window)
                curse_page_result = General.curse_page_detect(window, 400)  # 400 as count to bypass repeated detect
                while stuck_result != 0 and not curse_page_result:
                    if stuck_result == 1:
                        # To add support for network turbulence and portal stuck?
                        print('Progress stuck at unknown, quitting program..', file=f)
                        f.close()
                        General.send_email('Kaki script stuck, quit program.')
                        sys.exit()
                    elif stuck_result == 2:
                        print('Progress stuck at relic augmentation, try resolving..', file=f)
                        pyautogui.click(x=window[0] + (320 - 245), y=window[1] + (213 - 123), duration=0.1)
                        stuck_result = General.stuck_detect(window)
                        if stuck_result == 1:
                            General.toggle_auto_path_finding(window)
                            stuck_result = General.stuck_detect(window)
                        else:
                            stuck_result = 0
            else:
                curse_images = General.get_curse_image(window)
                curses = General.parse_curse_image(curse_images, keys)
                General.select_curse(window, curses)
            General.resource_completion_detect(window)
            General.map_management(window)
            elapsed_time = time.time() - temp_start_time
            count += 1
            print("Curse " + str(count) + " selected!", file=f)
            print('time elapsed: ' + str(elapsed_time) + ' seconds.', file=f)
            time.sleep(10)
            if current_floor == 0:
                current_floor = General.floor_detection(window)
            else:
                current_floor += 5
                print('Current Floor: ' + str(current_floor) + '\n', file=f)
        f.close()
        General.send_email('Kaki script quit with time out')
        print('Quit with time out')
    elif int(config['DEFAULT']['ModeSelection']) == 1:
        General.auto_legend(window, auto_legend_count)
    elif int(config['DEFAULT']['ModeSelection']) == 2:
        grind_count = int(config['Void_Island']['Count'])
        if grind_count == 0:
            grind_count = 9999
        while grind_count > 0:
            General.void_island_grind(window)
            print('Void Island Completed', file=f)
            f.flush()
            grind_count -= 1


if __name__ == "__main__":
    main()

    # General.doClick(367 - 246, 889 - 123)
    # General.doClick(100, 700)

    # start_time = time.time()
    # f = open('Kakilog.log', 'a+', encoding='utf-8')
    # now = datetime.now()
    # print("Log started: ", now, file=f)
    # # read config file
    # config = configparser.ConfigParser()
    # config.read('config.ini', encoding='utf-8')
    # title = 'KakiRaid'
    # window = General.get_window_coordinate(title)
    # print(window)
    # if int(config['DEFAULT']['AdjustWindow']) == 1:
    #     General.adjust_window(title, [0, 0])
    # elif int(config['DEFAULT']['AdjustWindow']) == 2:
    #     General.adjust_window(title, [245, 123])
    # window = General.get_window_coordinate(title)  # x, y, w, h
    # window.append(start_time)  # index 4
    #
    # auto_legend_count = int(config['DEFAULT']['AutoLegendCount'])
    # if int(config['DEFAULT']['ModeSelection']) == 0:
    #     count = 0
    #     max_count = int(config['DEFAULT']['MainLoopCount'])
    #     current_floor = 0
    #     stat = dict()
    #     stat['Total_Resources'] = 0
    #     stat['Total_Monster'] = 0
    #     stat['Total_Loot_Curse'] = 0
    #     stat['Total_Loot_Other'] = 0
    #     stat['Total_Camp'] = 0
    #     stat['Total_Ruin'] = 0
    #     window.append(stat)  # index 5
    #     window.append(config)  # index 6
    #     window.append(f)
    # General.curse_page_detect(window)
    # General.map_management(window)
    # General.resource_completion_detect(window)
    # try:
    #     while True:
    #         x, y = pyautogui.position()
    #         positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
    #         print(positionStr, end='')
    #         print('\b' * len(positionStr), end='', flush=True)
    # except KeyboardInterrupt:
    #     print('\n')
