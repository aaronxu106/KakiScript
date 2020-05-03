import General
import time
import pyautogui


if __name__ == "__main__":
    start_time = time.time()
    title = 'KakiRaid'
    window = General.get_window_coordinate(title)  # x, y, w, h
    window.append(start_time)  # add start time to window parameters
    count = 0
    current_floor = 0
    stat = dict()
    stat['Total_Resources'] = 0
    stat['Total_Monster'] = 0
    stat['Total_Loot_Curse'] = 0
    stat['Total_Loot_Other'] = 0
    stat['Total_Camp'] = 0
    stat['Total_Ruin'] = 0
    window.append(stat)
    # General.map_management(window)

    while count < 200:
        temp_start_time = time.time()
        if count != 0:
            if current_floor > 500:
                time.sleep(140)
            elif current_floor > 400:
                time.sleep(125)
            elif current_floor > 300:
                time.sleep(100)
            elif current_floor > 200:
                time.sleep(90)
            else:
                time.sleep(80)
        pyautogui.moveTo(window[0] + window[2] // 2, window[1] + window[3] // 2)
        curse_images = General.get_curse_image(window)
        curses = General.parse_curse_image(curse_images)
        General.select_curse(window, curses, 0)
        General.map_management(window)
        elapsed_time = time.time() - temp_start_time
        count += 1
        print("Curse " + str(count) + " selected!")
        print('time elapsed: ' + str(elapsed_time) + ' seconds.')
        time.sleep(10)
        if current_floor == 0:
            current_floor = General.floor_detection(window)
        else:
            current_floor += 5
            print('Current Floor: ' + str(current_floor) + '\n')
    print('Quit with time out')

    #  For auto-upgrading weapons
    # General.auto_legend(window, 30)

# try:
#     while True:
#         x, y = pyautogui.position()
#         positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
#         print(positionStr, end='')
#         print('\b' * len(positionStr), end='', flush=True)
# except KeyboardInterrupt:
#     print('\n')
