import re
import json
import threading
import time
import os
import shutil
import subprocess
import requests
import PySimpleGUI as sg
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import mixer

# 窗口配置和对象
VIDEO_URL = "https://www.bilibili.com/video/BV1e84y1T7jp"
MP3_LIST = ["暂无歌单"]

DEFAULT_SINGER_DICT = {
    "btn_jay": ("周杰伦", "https://www.bilibili.com/video/BV1e84y1T7jp"),
    "btn_beyond": ("Beyond", "https://www.bilibili.com/video/BV1f8411S7AJ"),
    "btn_zxy": ("张学友", "https://www.bilibili.com/video/BV1GM411e7iZ"),
    "btn_fhcq": ("凤凰传奇", "https://www.bilibili.com/video/BV1Ap4y1S7Gg"),
    "btn_zdlg": ("经典老歌", "https://www.bilibili.com/video/BV1ws4y1j7jY"),
    "btn_2023": ("2003年", "https://www.bilibili.com/video/BV1jz4y1i76P"),
}

LAYOUT = [
    [sg.Button(group[0], key=key) for key, group in DEFAULT_SINGER_DICT.items()],
    [
        sg.Input(VIDEO_URL, expand_x=True, key="txt_video_url"),
        sg.Button('获取歌单', key="btn_fetch")
    ],
    [
        sg.Button('暂停', key="btn_pause"),
        sg.Button('播放', key="btn_play"),
        sg.Button('上一首', key="btn_prev"),
        sg.Button('下一首', key="btn_next"),
    ],
    [sg.ProgressBar(100, orientation="h", expand_x=True, key="process_bar")],
    [sg.Listbox(MP3_LIST, key='song_list', expand_x=True, expand_y=True, enable_events=True)]
]

WINDOW = sg.Window(
    '音乐播放器',
    LAYOUT,
    size=(500, 600),
    # 图片获取到base64编码
    icon=b'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'
)

# 所有歌单
PLAY_VIDEO_BASE_URL = None
PLAY_TOTAL_NAME_DICT = {}
PLAY_TOTAL_NAME_LIST = []

# 暂定
PLAY_USER_PAUSE = False

# 正在播放的音乐（用于歌单循环）
PLAY_VIDEO_URL = None
PLAY_CHOICE_INT_NUM = None
PLAY_CLOSE = False


def fetch_name_list(video_url):
    """ 获取歌曲列表 """
    res = requests.get(
        url=video_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
    )
    res.close()
    data_list = re.findall(r'__INITIAL_STATE__=(.+);\(function', res.text)
    data_dict = json.loads(data_list[0])
    page_list = data_dict["videoData"]['pages']

    global PLAY_VIDEO_BASE_URL
    PLAY_VIDEO_BASE_URL = video_url.split("?")[0]

    global PLAY_TOTAL_NAME_DICT
    PLAY_TOTAL_NAME_DICT = {item['page']: item['part'] for item in page_list}
    global PLAY_TOTAL_NAME_LIST
    PLAY_TOTAL_NAME_LIST = ["{page} {part}".format(**item) for item in page_list]


def download_m4s(video_url, download_folder):
    """ 下载m4s文件 """
    session = requests.Session()
    session.headers.update({
        # "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Referer": video_url,
        "Accept-Language": "zh-CN,zh;q=0.9"
    })

    # 1.访问首页
    res = session.get(video_url)

    play_list = re.findall(r'__playinfo__=(.+?)</script', res.text)
    play_dict = json.loads(play_list[0])
    audio_list = play_dict['data']['dash']['audio']
    for item in audio_list:
        base_url = item['baseUrl']
        audio_file_name = base_url.split("?", maxsplit=1)[0].split("/")[-1]
        res = session.get(url=item['baseUrl'], )
        if res.status_code != 200:
            continue

        folder = os.path.join(download_folder, str(int(time.time() * 1000)))
        if not os.path.exists(folder):
            os.makedirs(folder)

        m4s_file_path = os.path.join(folder, audio_file_name)
        with open(m4s_file_path, mode='wb') as f:
            f.write(res.content)
        res.close()
        return True, m4s_file_path
    return False, None


def convert_to_mp3(m4s_file_path, mp3_path):
    """ 转换m4s成mp3文件"""
    os.environ['PATH'] = os.path.join("ffmpeg-win64-gpl-shared", 'bin')

    cmd_string = f'ffmpeg -loglevel quiet -i "{m4s_file_path}" -y "{mp3_path}"'
    subprocess.check_output(cmd_string, shell=True)


def music_end_event():
    """ 不断检测，音乐是否播放完，播放完则单曲循环"""
    while True:
        time.sleep(1)

        # 关闭，则退出
        if PLAY_CLOSE:
            return

        # 暂停，则不选播放下一首
        if PLAY_USER_PAUSE:
            continue

        if mixer.music.get_busy():
            pass  # print("播放中")
        else:
            global PLAY_CHOICE_INT_NUM

            if not PLAY_CHOICE_INT_NUM:
                continue
            if PLAY_CHOICE_INT_NUM < len(PLAY_TOTAL_NAME_DICT):
                PLAY_CHOICE_INT_NUM += 1
            else:
                PLAY_CHOICE_INT_NUM = 1
            index = PLAY_CHOICE_INT_NUM - 1
            WINDOW.Element("song_list").Update(PLAY_TOTAL_NAME_LIST, scroll_to_index=index, set_to_index=index)
            play_task()  # 播放完5s，用户未选择其他，则默认下一首；如果已播完，则重新开始


def play_task():
    base_url = PLAY_VIDEO_BASE_URL
    num = PLAY_CHOICE_INT_NUM

    if not num or not base_url:
        return

    name = PLAY_TOTAL_NAME_DICT.get(num)
    if not name:
        return

    mixer.pause()
    WINDOW.set_title(f"{name} 加载中")
    bv_id = base_url.strip("/").split("/")[-1]
    video_url = f"{base_url}?p={num}"
    download_folder = os.path.join("Download", bv_id)
    mp3_path = os.path.join(download_folder, f"{name}.mp3")

    if os.path.exists(mp3_path):
        WINDOW.set_title(f"{name} 播放中")
        mixer.music.load(mp3_path)
        mixer.music.play()
        return

    status, m4s_file_path = download_m4s(video_url, download_folder)
    if not status:
        WINDOW.set_title(f"{name} 加载失败")
        return

    WINDOW.set_title(f"{name} 转码中")

    convert_to_mp3(m4s_file_path, mp3_path)

    shutil.rmtree(os.path.dirname(m4s_file_path))

    WINDOW.set_title(f"{name} 播放中")
    mixer.music.load(f"{mp3_path}")
    mixer.music.play()


def run():
    global PLAY_USER_PAUSE
    global PLAY_CHOICE_INT_NUM

    mixer.init()

    # 线程，检测是否已播放完（播完自动单曲循环）
    end_event_thread = threading.Thread(target=music_end_event)
    end_event_thread.start()

    while True:
        # 监听窗体中的事件：点击获取歌单 、 选中歌曲
        event, value_dict = WINDOW.read()

        if event in DEFAULT_SINGER_DICT:
            _, url = DEFAULT_SINGER_DICT[event]
            WINDOW.Element("txt_video_url").update(url)

        if event == "btn_pause":
            mixer.music.pause()
            PLAY_USER_PAUSE = True

        if event == "btn_play":
            if PLAY_USER_PAUSE:
                mixer.music.unpause()
                PLAY_USER_PAUSE = False
                continue

            if PLAY_TOTAL_NAME_DICT and not PLAY_CHOICE_INT_NUM:
                PLAY_CHOICE_INT_NUM = 1

                index = PLAY_CHOICE_INT_NUM - 1
                WINDOW.Element("song_list").Update(PLAY_TOTAL_NAME_LIST, scroll_to_index=index, set_to_index=index)
                t = threading.Thread(target=play_task)
                t.start()

        if event == "btn_next":
            if not PLAY_CHOICE_INT_NUM or not PLAY_TOTAL_NAME_DICT:
                continue
            PLAY_USER_PAUSE = False
            if PLAY_CHOICE_INT_NUM < len(PLAY_TOTAL_NAME_DICT):
                PLAY_CHOICE_INT_NUM += 1
            else:
                PLAY_CHOICE_INT_NUM = 1

            index = PLAY_CHOICE_INT_NUM - 1
            WINDOW.Element("song_list").Update(PLAY_TOTAL_NAME_LIST, scroll_to_index=index, set_to_index=index)
            t = threading.Thread(target=play_task)
            t.start()

        if event == "btn_prev":
            if not PLAY_CHOICE_INT_NUM or not PLAY_TOTAL_NAME_DICT:
                continue
            PLAY_USER_PAUSE = False
            if PLAY_CHOICE_INT_NUM < 2:
                PLAY_CHOICE_INT_NUM = 1
            else:
                PLAY_CHOICE_INT_NUM -= 1

            index = PLAY_CHOICE_INT_NUM - 1
            WINDOW.Element("song_list").Update(PLAY_TOTAL_NAME_LIST, scroll_to_index=index, set_to_index=index)
            t = threading.Thread(target=play_task)
            t.start()

        if event == "btn_fetch":
            # 点击获取歌单
            video_url = value_dict['txt_video_url']
            fetch_name_list(video_url)
            WINDOW.Element("song_list").Update(PLAY_TOTAL_NAME_LIST)

            PLAY_CHOICE_INT_NUM = None

        if event == "song_list":
            # 选择歌曲+播放发
            choice_string = value_dict['song_list'][0]
            if choice_string == "暂无歌单":
                continue

            if not PLAY_TOTAL_NAME_DICT:
                continue

            # 用户如果暂定
            PLAY_USER_PAUSE = False

            # 当前播放歌曲，字符串格式的序号
            PLAY_CHOICE_INT_NUM = int(choice_string.split(maxsplit=1)[0])

            # 创建线程去播放
            t = threading.Thread(target=play_task)
            t.start()

        if not event:
            break

    # 关闭监听单曲循环的线程
    global PLAY_CLOSE
    PLAY_CLOSE = True

    # 关闭播放器
    mixer.music.stop()
    WINDOW.close()


if __name__ == '__main__':
    run()
