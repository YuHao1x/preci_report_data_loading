import os
import pymongo
import re
import datetime
import subprocess
import logging
import paramiko
import stat


timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

log_filename = f'/log/process_log_{timestamp}.log'

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = os.path.join(log_dir, f'process_log_{timestamp}.log')

logging.basicConfig(filename=log_filename, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

hostname = '10.239.176.143'
username = 'root'
password = "openEuler12#$"
remote_root_dir = '/root/ibt_preci/preci_report/'
local_temp_dir = '/root/ibt_preci/preci_report_test'

if not os.path.exists(local_temp_dir):
    os.makedirs(local_temp_dir)

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["test_preci_report_data"]
collection = db["preci_report"]
# root_dir = "/root/ibt_preci/preci_report/"


def check_and_update_rit(folder_path, report_name, existing_record):
    for subdir_name in os.listdir(folder_path):
        subdir_path = os.path.join(folder_path, subdir_name)
        if os.path.isdir(subdir_path) and subdir_name.isdigit():
            if subdir_name not in existing_record["test_type"]["rit"]:
                for file_name in os.listdir(subdir_path):
                    file_path = os.path.join(subdir_path, file_name)
                    if file_name.endswith(".html"):
                        collection.update_one(
                            {"report_name": report_name},
                            {"$set": {f"test_type.rit.{subdir_name}": file_path}}
                        )
                        logging.info(f"新增HTML文件: {file_path} 到数据库中的 rit 文件夹")

def check_and_update_interp(folder_path, report_name, existing_record):
    interp_path = os.path.join(folder_path, "interp")
    if os.path.exists(interp_path) and os.path.isdir(interp_path):
        for file_name in os.listdir(interp_path):
            file_path = os.path.join(interp_path, file_name)
            if file_name not in existing_record["test_type"]["interp"]:
                with open(file_path, 'r') as f:
                    content = f.read()
                    collection.update_one(
                        {"report_name": report_name},
                        {"$set": {f"test_type.interp.{file_name}": content}}
                    )
                    logging.info(f"新增文件: {file_path} 到数据库中的 interp 文件夹")

def check_and_update_translator(folder_path, report_name, existing_record):
    translator_path = os.path.join(folder_path, "translator")
    if os.path.exists(translator_path) and os.path.isdir(translator_path):
        for file_name in os.listdir(translator_path):
            file_path = os.path.join(translator_path, file_name)
            if file_name not in existing_record["test_type"]["translator"]:
                with open(file_path, 'r') as f:
                    content = f.read()
                    collection.update_one(
                        {"report_name": report_name},
                        {"$set": {f"test_type.translator.{file_name}": content}}
                    )
                    logging.info(f"新增文件: {file_path} 到数据库中的 translator 文件夹")

def process_rit_files(folder_path, data):
    for subdir_name in os.listdir(folder_path):
        subdir_path = os.path.join(folder_path, subdir_name)
        if os.path.isdir(subdir_path) and subdir_name.isdigit():
            # 只处理以数字命名的子文件夹
            for file_name in os.listdir(subdir_path):
                file_path = os.path.join(subdir_path, file_name)
                if file_name.endswith(".html"):
                    # 提取rit字段
                    data["test_type"]["rit"][subdir_name] = file_path
                    logging.info(f"找到HTML文件: {file_path}")

def process_interp_files(interp_path, data):
    if os.path.exists(interp_path) and os.path.isdir(interp_path):
        for file_name in os.listdir(interp_path):
            file_path = os.path.join(interp_path, file_name)
            with open(file_path, 'r') as f:
                data["test_type"]["interp"][file_name] = f.read()
                logging.info(f"读取interp文件: {file_path}")

def process_translator_files(translator_path, data):
    if os.path.exists(translator_path) and os.path.isdir(translator_path):
        for file_name in os.listdir(translator_path):
            file_path = os.path.join(translator_path, file_name)
            with open(file_path, 'r') as f:
                data["test_type"]["translator"][file_name] = f.read()
                logging.info(f"读取translator文件: {file_path}")

def insert_data(folder_path, report_name):
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
    process_rit_files(folder_path, data)
    
    # 读取 interp 文件夹下的文件
    interp_path = os.path.join(folder_path, "interp")
    process_interp_files(interp_path, data)
    
    # 读取 translator 文件夹下的文件
    translator_path = os.path.join(folder_path, "translator")
    process_translator_files(translator_path, data)
    
    # 将数据插入MongoDB
    collection.insert_one(data)
    logging.info(f"已处理文件夹: {folder_path}, 数据已插入数据库")
    print(f"已处理文件夹: {folder_path}, 数据已插入数据库")

def process_folder(folder_path, folder_name):
    # 提取report_name字段
    report_name_match = re.search(r'main_.*', folder_name)
    if report_name_match:
        report_name = report_name_match.group(0)
        
        # 检查数据库中是否已经存在相同的 report_name
        existing_record = collection.find_one({"report_name": report_name})
        if existing_record:
            logging.info(f"检查文件夹: {folder_name}，数据库中已存在相同的 report_name: {report_name}")
            print(f"检查文件夹: {folder_name}，数据库中已存在相同的 report_name: {report_name}")
            check_and_update_rit(folder_path, report_name, existing_record)
            check_and_update_interp(folder_path, report_name, existing_record)
            check_and_update_translator(folder_path, report_name, existing_record)
        else:
            insert_data(folder_path, report_name)

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
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)
    rsync_command = f"rsync -avz -e 'ssh -i ~/.ssh/id_rsa' {username}@{hostname}:{remote_folder} {local_folder}"
    logging.info(f"Executing rsync command: {rsync_command}")
    try:
        subprocess.run(rsync_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"rsync command failed with error: {e}")


def main():
    

    # 使用 paramiko 连接到远程服务器
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)

    # 获取远程服务器上的文件夹列表
    # stdin, stdout, stderr = ssh.exec_command(f'ls -d {remote_root_dir} */')
    # remote_folders = stdout.read().decode().splitlines()
    # print("11111111111111111111111111111",remote_folders)
    sftp = ssh.open_sftp()
    remote_folders = sftp.listdir(remote_root_dir)
    # print(1111111111111111111111111111111,remote_folders)
    for folder_name in remote_folders:
        remote_folder = os.path.join(remote_root_dir, folder_name)
        local_folder = os.path.join(local_temp_dir, folder_name)

        # 检查文件夹名称包含 "main"，并且不以 "2024" 开头
        if "main" in folder_name and not folder_name.startswith("2024"):
            logging.info("复制report_name %s", remote_folder)
            local_folder = os.path.join(local_temp_dir, folder_name)
            
            if not os.path.exists(local_folder):
                os.makedirs(local_folder)
            # 复制远程文件夹到本地
            copy_remote_folder_to_local(sftp, remote_folder, local_folder)
            # copy_remote_folder_to_local_rsync(remote_folder, local_folder, hostname, username)
            process_folder(local_folder, folder_name)

    
    sftp.close()
    ssh.close()
    subprocess.run(f"rm -rf {local_temp_dir}", shell=True, check=True)
if __name__ == '__main__':
    main()
