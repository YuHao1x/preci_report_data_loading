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
local_temp_dir = '/home/stm_preci'

if not os.path.exists(local_temp_dir):
    os.makedirs(local_temp_dir)

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mydb"]
collection = db["stm_preci"]
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

# def check_and_update_interp(folder_path, report_name, existing_record):
#     interp_path = os.path.join(folder_path, "interp")
#     if os.path.exists(interp_path) and os.path.isdir(interp_path):
#         for file_name in os.listdir(interp_path):
#             if file_name == "result":  # 跳过 result 文件
#                 continue
#             file_path = os.path.join(interp_path, file_name)
#             if file_name not in existing_record["test_type"]["interp"]:
#                 with open(file_path, 'r') as f:
#                     content = f.read()
#                     collection.update_one(
#                         {"report_name": report_name},
#                         {"$set": {f"test_type.interp.{file_name}": content}}
#                     )
#                     logging.info(f"新增文件: {file_path} 到数据库中的 interp 文件夹")


def check_and_update_interp(folder_path, report_name, existing_record):
    interp_path = os.path.join(folder_path, "interp")
    
    if os.path.exists(interp_path) and os.path.isdir(interp_path):
        result_detail = {}
        result_info = None
        result = "PASS"
        for file_name in os.listdir(interp_path):
            file_path = os.path.join(interp_path, file_name)
            
            # 处理 result 文件
            if file_name == "result":
                with open(file_path, 'r') as f:
                    result_info = f.read()
                    collection.update_one(
                        {"report_name": report_name},
                        {"$set": {"test_type.interp.result_info": result_info}}
                    )
                    logging.info(f"更新 result 文件内容到数据库: {file_path}")
                continue
            if "fail" in file_name.lower():
                result = "FAIL"
            # 处理其他文件
            if file_name not in existing_record["test_type"]["interp"]:
                with open(file_path, 'r') as f:
                    content = f.read()
                    result_detail[file_name] = content
                    collection.update_one(
                        {"report_name": report_name},
                        {"$set": {f"test_type.interp.result_detail.{file_name}": content}}
                    )
                    logging.info(f"新增文件: {file_path} 到数据库中的 interp 文件夹")
        
        # 更新 result_detail 字段
        if result_detail:
            collection.update_one(
                {"report_name": report_name},
                {"$set": {"test_type.interp.result_detail": result_detail}}
            )
        collection.update_one(
            {"report_name": report_name},
            {"$set": {"test_type.interp.result": result}}
        )

# def check_and_update_translator(folder_path, report_name, existing_record):
#     translator_path = os.path.join(folder_path, "translator")
#     if os.path.exists(translator_path) and os.path.isdir(translator_path):
#         for file_name in os.listdir(translator_path):
#             if file_name == "result":  # 跳过 result 文件
#                 continue
#             file_path = os.path.join(translator_path, file_name)
#             if file_name not in existing_record["test_type"]["translator"]:
#                 with open(file_path, 'r') as f:
#                     content = f.read()
#                     collection.update_one(
#                         {"report_name": report_name},
#                         {"$set": {f"test_type.translator.{file_name}": content}}
#                     )
#                     logging.info(f"新增文件: {file_path} 到数据库中的 translator 文件夹")




def check_and_update_translator(folder_path, report_name, existing_record):
    translator_path = os.path.join(folder_path, "translator")
    
    if os.path.exists(translator_path) and os.path.isdir(translator_path):
        result_detail = {}
        result_info = None
        result = "PASS"  # 默认结果为 PASS

        for file_name in os.listdir(translator_path):
            file_path = os.path.join(translator_path, file_name)
            
            # 处理 result 文件
            if file_name == "result":
                with open(file_path, 'r') as f:
                    result_info = f.read()
                    collection.update_one(
                        {"report_name": report_name},
                        {"$set": {"test_type.translator.result_info": result_info}}
                    )
                    logging.info(f"更新 result 文件内容到数据库: {file_path}")
                continue
            
            # 检查文件名是否包含 "fail"
            if "fail" in file_name.lower():
                result = "FAIL"  # 如果文件名包含 "fail"，将结果标记为 FAIL
            
            # 处理其他文件
            if file_name not in existing_record.get("test_type", {}).get("translator", {}):
                with open(file_path, 'r') as f:
                    content = f.read()
                    result_detail[file_name] = content
                    collection.update_one(
                        {"report_name": report_name},
                        {"$set": {f"test_type.translator.result_detail.{file_name}": content}}
                    )
                    logging.info(f"新增文件: {file_path} 到数据库中的 translator 文件夹")
        
        # 更新 result_detail 字段
        if result_detail:
            collection.update_one(
                {"report_name": report_name},
                {"$set": {"test_type.translator.result_detail": result_detail}}
            )
        
        # 更新结果字段
        collection.update_one(
            {"report_name": report_name},
            {"$set": {"test_type.translator.result": result}}
        )











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

# def process_interp_files(interp_path, data):
#     if os.path.exists(interp_path) and os.path.isdir(interp_path):
#         for file_name in os.listdir(interp_path):
#             file_path = os.path.join(interp_path, file_name)
#             with open(file_path, 'r') as f:
#                 data["test_type"]["interp"][file_name] = f.read()
#                 logging.info(f"读取interp文件: {file_path}")

# def process_interp_files(interp_path, data):
#     if os.path.exists(interp_path) and os.path.isdir(interp_path):
#         result = "PASS"
#         for file_name in os.listdir(interp_path):
#             if file_name == "result":  # 跳过 result 文件
#                 continue
#             file_path = os.path.join(interp_path, file_name)
#             with open(file_path, 'r') as f:
#                 content = f.read()
#                 data["test_type"]["interp"][file_name] = content
#                 logging.info(f"读取 interp 文件: {file_path}")
#                 if "fail" in file_name.lower() or "fail" in content.lower():
#                     result = "FAIL"
#         data["test_type"]["interp"]["result"] = result

# def process_interp_files(interp_path, data):
#     if os.path.exists(interp_path) and os.path.isdir(interp_path):
#         result = "PASS"
#         # folder_name = os.path.basename(interp_path)  # 获取文件夹名
#         # data["test_type"]["interp"]["type"] = f"{folder_name}_spec"  # 添加 type 字段
#         data["test_type"]["interp"]["type"] = f"interp_spec"
#         for file_name in os.listdir(interp_path):
#             if file_name == "result":  # 跳过 result 文件
#                 continue
#             file_path = os.path.join(interp_path, file_name)
#             with open(file_path, 'r') as f:
#                 content = f.read()
#                 data["test_type"]["interp"][file_name] = content
#                 logging.info(f"读取 interp 文件: {file_path}")
#                 if "fail" in file_name.lower() or "fail" in content.lower():
#                     result = "FAIL"
        
#         data["test_type"]["interp"]["result"] = result

# def process_interp_files(interp_path, data):
#     if "interp" not in data["test_type"]:
#         data["test_type"]["interp"] = {}
#     data["test_type"]["interp"]["type"] = "interp_spec"  # 初始化 type 字段

#     if os.path.exists(interp_path) and os.path.isdir(interp_path):
#         result = "PASS"
#         for file_name in os.listdir(interp_path):
#             if file_name == "result":  # 跳过 result 文件
#                 continue
#             file_path = os.path.join(interp_path, file_name)
#             with open(file_path, 'r') as f:
#                 content = f.read()
#                 data["test_type"]["interp"][file_name] = content
#                 logging.info(f"读取 interp 文件: {file_path}")
#                 if "fail" in file_name.lower() or "fail" in content.lower():
#                     result = "FAIL"
        
#         data["test_type"]["interp"]["result"] = result

def process_interp_files(interp_path, data):
    # 初始化 `interp` 字段
    if "interp" not in data["test_type"]:
        data["test_type"]["interp"] = {}
    interp_data = data["test_type"]["interp"]
    interp_data["type"] = "interp_spec"  # 初始化 type 字段

    # 检查路径是否存在且为目录
    if os.path.exists(interp_path) and os.path.isdir(interp_path):
        result = "PASS"
        result_detail = {}  # 用于存储文件名和内容
        result_info = None  # 用于存储 result 文件的内容

        # 遍历目录中的文件
        for file_name in os.listdir(interp_path):
            file_path = os.path.join(interp_path, file_name)

            # 如果是 result 文件
            if file_name == "result":
                with open(file_path, 'r') as f:
                    result_info = f.read()  # 读取 result 文件内容
                    logging.info(f"读取 result 文件: {file_path}")
                continue  # 跳过后续处理，直接进入下一个文件

            # 处理其他文件
            with open(file_path, 'r') as f:
                content = f.read()
                result_detail[file_name] = content  # 将文件内容存储到 result_detail
                logging.info(f"读取 interp 文件: {file_path}")

                # 如果文件名或内容中包含 "fail"，将结果标记为 FAIL
                if "fail" in file_name.lower() or "fail" in content.lower():
                    result = "FAIL"
                
        # 更新 `interp` 数据结构
        interp_data["result"] = result
        interp_data["result_info"] = result_info
        interp_data["result_detail"] = result_detail


# def process_translator_files(translator_path, data):
#     if os.path.exists(translator_path) and os.path.isdir(translator_path):
#         for file_name in os.listdir(translator_path):
#             file_path = os.path.join(translator_path, file_name)
#             with open(file_path, 'r') as f:
#                 data["test_type"]["translator"][file_name] = f.read()
#                 logging.info(f"读取translator文件: {file_path}")

# def process_translator_files(translator_path, data):
#     if os.path.exists(translator_path) and os.path.isdir(translator_path):
#         result = "PASS"
#         for file_name in os.listdir(translator_path):
#             if file_name == "result":  # 跳过 result 文件
#                 continue
#             file_path = os.path.join(translator_path, file_name)
#             with open(file_path, 'r') as f:
#                 content = f.read()
#                 data["test_type"]["translator"][file_name] = content
#                 logging.info(f"读取 translator 文件: {file_path}")
#                 if "fail" in file_name.lower() or "fail" in content.lower():
#                     result = "FAIL"
#         data["test_type"]["translator"]["result"] = result


# def process_translator_files(translator_path, data):
#     if "translator" not in data["test_type"]:
#         data["test_type"]["translator"] = {}
#     data["test_type"]["translator"]["type"] = "translator_spec"  # 初始化 type 字段

#     if os.path.exists(translator_path) and os.path.isdir(translator_path):
#         result = "PASS"
#         for file_name in os.listdir(translator_path):
#             if file_name == "result":  # 跳过 result 文件
#                 continue
#             file_path = os.path.join(translator_path, file_name)
#             with open(file_path, 'r') as f:
#                 content = f.read()
#                 data["test_type"]["translator"][file_name] = content
#                 logging.info(f"读取 translator 文件: {file_path}")
#                 if "fail" in file_name.lower() or "fail" in content.lower():
#                     result = "FAIL"
        
#         data["test_type"]["translator"]["result"] = result

def process_translator_files(translator_path, data):
    # 初始化 `translator` 字段
    if "translator" not in data["test_type"]:
        data["test_type"]["translator"] = {}
    translator_data = data["test_type"]["translator"]
    translator_data["type"] = "translator_spec"  # 初始化 type 字段

    # 检查路径是否存在且为目录
    if os.path.exists(translator_path) and os.path.isdir(translator_path):
        result = "PASS"
        result_detail = {}  # 用于存储文件名和内容
        result_info = None  # 用于存储 result 文件的内容

        # 遍历目录中的文件
        for file_name in os.listdir(translator_path):
            file_path = os.path.join(translator_path, file_name)

            # 如果是 result 文件
            if file_name == "result":
                with open(file_path, 'r') as f:
                    result_info = f.read()  # 读取 result 文件内容
                    logging.info(f"读取 result 文件: {file_path}")
                continue  # 跳过后续处理，直接进入下一个文件

            # 处理其他文件
            with open(file_path, 'r') as f:
                content = f.read()
                result_detail[file_name] = content  # 将文件内容存储到 result_detail
                logging.info(f"读取 interp 文件: {file_path}")

                # 如果文件名或内容中包含 "fail"，将结果标记为 FAIL
                if "fail" in file_name.lower() or "fail" in content.lower():
                    result = "FAIL"
                

        # 更新 `interp` 数据结构
        translator_data["result"] = result
        translator_data["result_info"] = result_info
        translator_data["result_detail"] = result_detail


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
    report_name_match = re.search(r'(^|[^a-zA-Z0-9])\d+_main_.*$', folder_name)
    # report_name_match = re.search(r'^|[^a-zA-Z0-9])\d+_main_\d.*$', folder_name)
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

def should_copy_folder(folder_name):
    return re.search(r'_main_', folder_name) is not None
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
        # should_copy_main_folder = re.search(r'_main_', folder_name)
        # 检查文件夹名称包含 "main"，并且不以 "2024" 开头
        if "main" in folder_name and not folder_name.startswith("2024") and should_copy_folder(folder_name):
            logging.info("复制report_name %s", remote_folder)
            local_folder = os.path.join(local_temp_dir, folder_name)
            
            if not os.path.exists(local_folder):
                os.makedirs(local_folder)
            # 复制远程文件夹到本地
            # copy_remote_folder_to_local(sftp, remote_folder, local_folder)
            # copy_remote_folder_to_local_rsync(remote_folder, local_folder, hostname, username)
            process_folder(local_folder, folder_name)

    
    sftp.close()
    ssh.close()
    # subprocess.run(f"rm -rf {local_temp_dir}", shell=True, check=True)
if __name__ == '__main__':
    main()
