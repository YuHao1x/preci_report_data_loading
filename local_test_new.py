import os
import pymongo
import re
import datetime
import subprocess
import logging
import paramiko
import stat
import time

timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = os.path.join(log_dir, f'process_log_{timestamp}.log')

logging.basicConfig(filename=log_filename, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 远程服务器信息
hostname = '10.239.176.143'
username = 'root'
password = "openEuler12#$"
remote_root_dir = '/root/ibt_preci/preci_report/'
local_temp_dir = '/root/ibt_preci/preci_report_async_test'

if not os.path.exists(local_temp_dir):
    os.makedirs(local_temp_dir)

# MongoDB连接设置
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["test_preci_report_data"]
collection = db["preci_report"]

def connect_to_remote_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)
    sftp = ssh.open_sftp()
    return ssh, sftp

def check_and_update_rit(folder_path, report_name, existing_record, sftp=None):
    for subdir_name in os.listdir(folder_path) if sftp is None else sftp.listdir(folder_path):
        subdir_path = os.path.join(folder_path, subdir_name)
        if (os.path.isdir(subdir_path) if sftp is None else stat.S_ISDIR(sftp.stat(subdir_path).st_mode)) and subdir_name.isdigit():
            if subdir_name not in existing_record["test_type"]["rit"]:
                for file_name in os.listdir(subdir_path) if sftp is None else sftp.listdir(subdir_path):
                    file_path = os.path.join(subdir_path, file_name)
                    if file_name.endswith(".html"):
                        collection.update_one(
                            {"report_name": report_name},
                            {"$set": {f"test_type.rit.{subdir_name}": file_path}}
                        )
                        logging.info(f"新增HTML文件: {file_path} 到数据库中的 rit 文件夹")

def check_and_update_interp(folder_path, report_name, existing_record, sftp=None):
    interp_path = os.path.join(folder_path, "interp")
    if (os.path.exists(interp_path) and os.path.isdir(interp_path)) if sftp is None else stat.S_ISDIR(sftp.stat(interp_path).st_mode):
        for file_name in os.listdir(interp_path) if sftp is None else sftp.listdir(interp_path):
            file_path = os.path.join(interp_path, file_name)
            if file_name not in existing_record["test_type"]["interp"]:
                with open(file_path, 'r') if sftp is None else sftp.open(file_path, 'r') as f:
                    content = f.read().decode() if sftp else f.read()
                    collection.update_one(
                        {"report_name": report_name},
                        {"$set": {f"test_type.interp.{file_name}": content}}
                    )
                    logging.info(f"新增文件: {file_path} 到数据库中的 interp 文件夹")

def check_and_update_translator(folder_path, report_name, existing_record, sftp=None):
    translator_path = os.path.join(folder_path, "translator")
    if (os.path.exists(translator_path) and os.path.isdir(translator_path)) if sftp is None else stat.S_ISDIR(sftp.stat(translator_path).st_mode):
        for file_name in os.listdir(translator_path) if sftp is None else sftp.listdir(translator_path):
            file_path = os.path.join(translator_path, file_name)
            if file_name not in existing_record["test_type"]["translator"]:
                with open(file_path, 'r') if sftp is None else sftp.open(file_path, 'r') as f:
                    content = f.read().decode() if sftp else f.read()
                    collection.update_one(
                        {"report_name": report_name},
                        {"$set": {f"test_type.translator.{file_name}": content}}
                    )
                    logging.info(f"新增文件: {file_path} 到数据库中的 translator 文件夹")

def process_rit_files(folder_path, data, sftp=None):
    for subdir_name in os.listdir(folder_path) if sftp is None else sftp.listdir(folder_path):
        subdir_path = os.path.join(folder_path, subdir_name)
        if (os.path.isdir(subdir_path) if sftp is None else stat.S_ISDIR(sftp.stat(subdir_path).st_mode)) and subdir_name.isdigit():
            # 只处理以数字命名的子文件夹
            for file_name in os.listdir(subdir_path) if sftp is None else sftp.listdir(subdir_path):
                file_path = os.path.join(subdir_path, file_name)
                if file_name.endswith(".html"):
                    # 提取rit字段
                    data["test_type"]["rit"][subdir_name] = file_path
                    logging.info(f"找到HTML文件: {file_path}")

def process_interp_files(interp_path, data, sftp=None):
    try:
        if (os.path.exists(interp_path) and os.path.isdir(interp_path)) if sftp is None else stat.S_ISDIR(sftp.stat(interp_path).st_mode):
            for file_name in os.listdir(interp_path) if sftp is None else sftp.listdir(interp_path):
                file_path = os.path.join(interp_path, file_name)
                try:
                    with open(file_path, 'r') if sftp is None else sftp.open(file_path, 'r') as f:
                        data["test_type"]["interp"][file_name] = f.read().decode() if sftp else f.read()
                        logging.info(f"读取interp文件: {file_path}")
                except FileNotFoundError:
                    logging.warning(f"文件未找到: {file_path}")
        else:
            logging.warning(f"文件夹未找到或不是文件夹: {interp_path}")
    except FileNotFoundError:
        logging.warning(f"文件夹未找到: {interp_path}")

def process_translator_files(translator_path, data, sftp=None):
    try:
        if (os.path.exists(translator_path) and os.path.isdir(translator_path)) if sftp is None else stat.S_ISDIR(sftp.stat(translator_path).st_mode):
            for file_name in os.listdir(translator_path) if sftp is None else sftp.listdir(translator_path):
                file_path = os.path.join(translator_path, file_name)
                try:
                    with open(file_path, 'r') if sftp is None else sftp.open(file_path, 'r') as f:
                        data["test_type"]["translator"][file_name] = f.read().decode() if sftp else f.read()
                        logging.info(f"读取translator文件: {file_path}")
                except FileNotFoundError:
                    logging.warning(f"文件未找到: {file_path}")
        else:
            logging.warning(f"文件夹未找到或不是文件夹: {translator_path}")
    except FileNotFoundError:
        logging.warning(f"文件夹未找到: {translator_path}")

def copy_remote_folder_to_local(sftp, remote_folder, local_folder):
    for item in sftp.listdir_attr(remote_folder):
        remote_path = os.path.join(remote_folder, item.filename)
        local_path = os.path.join(local_folder, item.filename)
        if stat.S_ISDIR(item.st_mode):
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            copy_remote_folder_to_local(sftp, remote_path, local_path)
        else:
            sftp.get(remote_path, local_path)
            logging.info(f"Copied {remote_path} to {local_path}")


def copy_remote_folder_to_local_rsync(remote_folder, local_folder, hostname, username):
    # if not os.path.exists(local_folder):
    #     os.makedirs(local_folder)
    # ssh, sftp = connect_to_remote_server()
    # remote_folders = sftp.listdir(remote_root_dir)

    rsync_command = f"sshpass -p '{password}' rsync -avz {username}@{hostname}:{remote_folder} {local_folder}"
    logging.info(f"Executing rsync command: {rsync_command}")
    try:
        subprocess.run(rsync_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"rsync command failed with error: {e}")

def insert_data(folder_path, report_name, sftp=None):
    # 初始化数据结构
    data = {
        "report_name": report_name,
        "test_type": {
            "rit": {},
            "interp": {},
            "translator": {}
        }
    }
    
    # 处理 rit 文件夹下的文件
    process_rit_files(folder_path, data, sftp)
    
    # 读取 interp 文件夹下的文件
    interp_path = os.path.join(folder_path, "interp")
    process_interp_files(interp_path, data, sftp)
    
    # 读取 translator 文件夹下的文件
    translator_path = os.path.join(folder_path, "translator")
    process_translator_files(translator_path, data, sftp)
    
    # 将数据插入MongoDB
    collection.insert_one(data)
    logging.info(f"已处理文件夹: {folder_path}, 数据已插入数据库")
    print(f"已处理文件夹: {folder_path}, 数据已插入数据库")

def process_folder(folder_path, folder_name, sftp=None):
    # 提取report_name字段
    report_name_match = re.search(r'main_.*', folder_name)
    if report_name_match:
        report_name = report_name_match.group(0)
        
        # 检查数据库中是否已经存在相同的 report_name
        existing_record = collection.find_one({"report_name": report_name})
        if existing_record:
            logging.info(f"检查文件夹: {folder_name}，数据库中已存在相同的 report_name: {report_name}")
            print(f"检查文件夹: {folder_name}，数据库中已存在相同的 report_name: {report_name}")
            check_and_update_rit(folder_path, report_name, existing_record, sftp)
            check_and_update_interp(folder_path, report_name, existing_record, sftp)
            check_and_update_translator(folder_path, report_name, existing_record, sftp)
        else:
            insert_data(folder_path, report_name, sftp)





def process_remote_data():
    ssh, sftp = connect_to_remote_server()
    remote_folders = sftp.listdir(remote_root_dir)

    for folder_name in remote_folders:
        remote_folder = os.path.join(remote_root_dir, folder_name)

        # 检查文件夹名称包含 "main"，并且不以 "2024" 开头
        if "main" in folder_name and not folder_name.startswith("2024"):
            logging.info("处理文件夹 %s", remote_folder)
            process_folder(remote_folder, folder_name, sftp)

    sftp.close()
    ssh.close()

def copy_and_process_local_data():
    ssh, sftp = connect_to_remote_server()
    remote_folders = sftp.listdir(remote_root_dir)

    for folder_name in remote_folders:
        remote_folder = os.path.join(remote_root_dir, folder_name)
        local_folder = os.path.join(local_temp_dir, folder_name)

        # 检查文件夹名称包含 "main"，并且不以 "2024" 开头
        if "main" in folder_name and not folder_name.startswith("2024"):
            logging.info("复制文件夹 %s 到本地 %s", remote_folder, local_folder)
            if not os.path.exists(local_folder):
                os.makedirs(local_folder)
            # copy_remote_folder_to_local(sftp, remote_folder, local_folder)
            copy_remote_folder_to_local_rsync(remote_folder, local_folder, hostname, username)

            process_folder(local_folder, folder_name)

    sftp.close()
    ssh.close()

def main():
    # start_time = time.time()
    # process_remote_data()
    # end_time = time.time()
    # logging.info(f"处理远程数据耗时: {end_time - start_time:.2f} 秒")
    # print(f"处理远程数据耗时: {end_time - start_time:.2f} 秒") #193.93

    # 复制远程数据到本地并处理
    start_time = time.time()
    copy_and_process_local_data()
    end_time = time.time()
    logging.info(f"复制远程数据到本地并处理耗时: {end_time - start_time:.2f} 秒")
    print(f"复制远程数据到本地并处理耗时: {end_time - start_time:.2f} 秒") # 348.51   121.12

if __name__ == '__main__':
    main()