
"""
{
    "report_name":"main_547_1ea0edd9",
    "test_type":{
        "rit":{
            "502":"/root/ibt_preci/preci_report/12045347808_main_547_1ea0edd9/502/CPU2017.353.intrate.test.html",
            "503":"/root/ibt_preci/preci_report/12045347808_main_547_1ea0edd9/503/CPU2017.334.fprate.test.html",
    },
        "interp":{
            "ADC_LOCK_FAIL":"ADC_LOCK-MEMb_GPR8 PASS ADC_LOCK-MEMb_IMMb_80r2 PASS ADC_LOCK-MEMv_IMMz FAIL"
        },
        "translator":{
            "ADC_LOCK_FAIL":"ADC_LOCK-MEMb_GPR8 PASS ADC_LOCK-MEMb_IMMb_80r2 PASS"
        }

    }
    
}
"""

import os
import pymongo
import re
import logging



logging.basicConfig(filename='/root/ibt_preci/preci_report/process_log.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


client = pymongo.MongoClient("mongodb://10.239.178.14:27017/")
db = client["mydb"]
collection = db["stm_preci"]
root_dir = "/root/ibt_preci/preci_report/"

# 统计信息
total_html_files = 0
processed_folders = 0

for folder_name in os.listdir(root_dir):
    folder_path = os.path.join(root_dir, folder_name)
    if os.path.isdir(folder_path) and "main" in folder_name:
        # 提取report_name字段
        report_name_match = re.search(r'main_.*', folder_name)
        if report_name_match:
            report_name = report_name_match.group(0)
        
        # 初始化数据结构
        data = {
            "report_name": report_name,
            "test_type": {
                "rit": {},
                "interp": {},
                "translator": {}
            }
        }
        
        # 遍历文件夹下的文件
        for subdir_name in os.listdir(folder_path):
            subdir_path = os.path.join(folder_path, subdir_name)
            if os.path.isdir(subdir_path) and subdir_name.isdigit():
                # 只处理以数字命名的子文件夹
                for file_name in os.listdir(subdir_path):
                    file_path = os.path.join(subdir_path, file_name)
                    if file_name.endswith(".html"):
                        # 提取rit字段
                        data["test_type"]["rit"][subdir_name] = file_path
                        total_html_files += 1
                        print(f"找到HTML文件: {file_path}")
                        logging.info(f"找到HTML文件: {file_path}")
        # 读取interp文件夹下的文件
        interp_path = os.path.join(folder_path, "interp")
        if os.path.exists(interp_path) and os.path.isdir(interp_path):
            for file_name in os.listdir(interp_path):
                file_path = os.path.join(interp_path, file_name)
                with open(file_path, 'r') as f:
                    data["test_type"]["interp"][file_name] = f.read()
                    logging.info(f"读取interp文件: {file_path}")
        # 读取translator文件夹下的文件
        translator_path = os.path.join(folder_path, "translator")
        if os.path.exists(translator_path) and os.path.isdir(translator_path):
            for file_name in os.listdir(translator_path):
                file_path = os.path.join(translator_path, file_name)
                with open(file_path, 'r') as f:
                    data["test_type"]["translator"][file_name] = f.read()
                    logging.info(f"读取translator文件: {file_path}")
        # 将数据写入MongoDB
        collection.insert_one(data)
        processed_folders += 1
        print(f"已处理文件夹: {folder_name}, 写入数据库")
        logging.info(f"已处理文件夹: {folder_name}, 写入数据库")

print(f"总共找到 {total_html_files} 个 HTML 文件")
print(f"已处理 {processed_folders} 个文件夹")
print("数据已成功写入MongoDB")
logging.info(f"总共找到 {total_html_files} 个 HTML 文件")
logging.info(f"已处理 {processed_folders} 个文件夹")
logging.info("数据已成功写入MongoDB")
