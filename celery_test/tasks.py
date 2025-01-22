# celery -A tasks worker --loglevel=info
# celery -A tasks beat --loglevel=info


# import os,sys
# import logging
# from celery import Celery,signals
# from celery.schedules import crontab
# import subprocess
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from test_new_update import main


# app = Celery('tasks', broker='redis://localhost:6379/0')

# @app.task(name='tasks.test_new_update')
# def test_new_update_task():
#     main()  

# app.conf.beat_schedule = {
#     'run-my-script-task-every-minute': {
#         'task': 'tasks.test_new_update',
#         'schedule': 500.0,  
#         # 'schedule': crontab(hour=14, minute=0),
#     },
# }

# app.conf.timezone = 'UTC'




import os
import sys
import logging
from celery import Celery
from celery.schedules import crontab
import subprocess


local_script_dir = '/root/ibt_preci/'


app = Celery('tasks', broker='redis://localhost:6379/0')

# 定义任务
@app.task(name='tasks.run_test_script')
def run_test_script_task():
    script_path = os.path.join(local_script_dir, 'local_test_with_sshfs.py')
    try:
       
        result = subprocess.run(['python', script_path], check=True, capture_output=True, text=True)
        logging.info(f"Script output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Script failed with error: {e.stderr}")

app.conf.beat_schedule = {
    'run-test-script-every-night': {
        'task': 'tasks.run_test_script',
        'schedule': crontab(hour=13, minute=40),
    },
}

app.conf.timezone = 'Asia/Shanghai'