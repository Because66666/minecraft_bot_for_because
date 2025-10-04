import time
from my_logger import logger
import subprocess
from datetime import datetime
import requests

n = 1  # 登陆次数

ria_bbs_map_session = requests.Session()
ria_bbs_map_session.headers = {
    'authority': 'satellite.ria.red',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99"',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36 HBPC/12.1.3.310',
    'sec-ch-ua-platform': '"Windows"',
    'accept': '*/*',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://satellite.ria.red/map/zth',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

start_time = time.time()
program_counter = 0
while True:
    p = subprocess.Popen(['python', 'mc.py'], stdout=subprocess.PIPE, text=True)
    # readline()会阻塞直到有一行数据可读或文件结束

    # 循环检查子进程状态
    while p.poll() is None:
        # readline()会阻塞直到有一行数据可读或文件结束
        line = p.stdout.readline()

        if line:
            today = datetime.today().__str__()
            delta = time.time() - start_time

            print(f"[{today}]读取到的行:", line.strip())
            if '程序结束...' in line.strip():
                break
            if program_counter <= 120:
                pass
            elif delta < 600:
                pass
            elif program_counter > 120:
                query = ria_bbs_map_session.get('https://satellite.ria.red/map/_zth/up/world/world')
                program_counter = -1
                if query.status_code != 200:
                    pass
                elif query.status_code == 200:
                    names = [obj['account'] for obj in query.json()['players']]
                    if 'Because66666' not in names:
                        break
        # 检查子进程是否已经结束
        if p.poll() is not None:
            break  # 如果子进程已经结束，跳出循环

        # 如果子进程还在运行，等待一段时间再检查
        time.sleep(5)
        program_counter += 1

    p.terminate()  # 结束子进程
    # 子进程已经结束
    print("子进程已结束，返回码:", p.returncode)
    print('捕捉到程序退出。等待10分钟...')
    time.sleep(600)
    n += 1
    logger.info(f'正在尝试第{n}次重连...')
