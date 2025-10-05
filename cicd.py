import time
from functions.my_logger import logger
import subprocess
from datetime import datetime
import requests
from mc import GameUtils
n = 1  # 登陆次数



def check_online():
    t = int(time.time()*1000)
    players, success = GameUtils.fetch_online_player_by_map_api()
    if not success:
        return True
    names = [obj['account'] for obj in players]
    if 'Because66666' not in names:
        return False
    return True

def main():
    p = None
    start_time = None
    while True:
        if p is None:
            logger.info("Starting mc.py")
            p = subprocess.Popen(['python', 'mc.py'])
            start_time = datetime.now()
            logger.info(f"mc.py started at {start_time}")

        time_elapsed = (datetime.now() - start_time).total_seconds() / 60

        if time_elapsed >= 10:
            if not check_online():
                logger.warning("mc.py is not online after 10 minutes. Restarting...")
                if p.poll() is None:  # Process is still running
                    p.terminate()
                    p.wait()
                p = None
                logger.info("Waiting for 10 minutes before restarting mc.py...")
                time.sleep(600)  # Wait 10 minutes
            else:
                logger.info("mc.py is online.")
        else:
            logger.info(f"Waiting for 10 minutes initial startup. {10 - time_elapsed:.1f} minutes remaining.")

        time.sleep(60)  # Check every 1 minute

def main_without_check():
    p = None
    start_time = None
    while True:
        if p is None:
            logger.info("Starting mc.py")
            p = subprocess.Popen(['python', 'mc.py'])
            start_time = datetime.now()
            logger.info(f"mc.py started at {start_time}")

        time_elapsed = (datetime.now() - start_time).total_seconds() / 60

        if time_elapsed < 10:
            pass
        else:
            # 检查p进程是否结束
            if p.poll() is not None:
                logger.info(f"mc.py exited with return code {p.returncode}")
                p = None
                logger.info("Waiting for 10 minutes before restarting mc.py...")
                time.sleep(540)  # Wait 10 minutes
        time.sleep(60)  # Check every 1 minute

if __name__ == '__main__':
    main()
