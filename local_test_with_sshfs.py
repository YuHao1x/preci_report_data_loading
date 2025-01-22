import os
import pymongo
import re
import datetime,time
import logging


def configure_global_logging():
    log_dir = '/root/ibt_preci/logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(log_dir, f'process_log_{timestamp}.log')
    logger = logging.getLogger('global_logger')
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(file_handler)
    return logger

global_logger = configure_global_logging()
hostname = '10.239.176.143'
username = 'root'
password = "openEuler12#$"
local_temp_dir = '/home/ibt_preci/preci_report/'



client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mydb"]
collection = db["stm_preci"]


def check_and_update_interp(folder_path, report_name, existing_record):
    # logger = logging.getLogger('global_logger')
    interp_path = os.path.join(folder_path, "interp")
    # print("interp",interp_path)
    result_detail = {}
    interp_regression = []  
    result = "PASS" 
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) and file_name.lower().startswith("regression") and file_name.lower().endswith("interp"):
            result = "FAIL"             
            with open(file_path, 'r') as f:
                content = f.read()
                for line in content.strip().split("\n"):

                    parts = line.split()
                    if len(parts) >= 5: 
                        interp_regression.append({
                            "sub_test_suite": parts[0],
                            "result": parts[1],
                            "test_banner": parts[2],
                            "date": parts[3],
                            "time": parts[4], 
                        
                        })

    
    if os.path.exists(interp_path) and os.path.isdir(interp_path):
        for file_name in os.listdir(interp_path):
            file_path = os.path.join(interp_path, file_name)
            if file_name == "result":  
                continue
            if file_name not in existing_record.get("test_type", {}).get("interp", {}):
                with open(file_path, 'r') as f:
                    content = f.read()
                    result_detail[file_name] = content
                    collection.update_one(
                        {"report_name": report_name},
                        {"$set": {f"test_type.interp.result_detail.{file_name}": content}}
                    )
                    global_logger.info(f"Rewrite file: {file_path} to the interp folder in the database")

        if result_detail:
            collection.update_one(
                {"report_name": report_name},
                {"$set": {"test_type.interp.result_detail": result_detail or {}}}
            )

    if interp_regression:
        collection.update_one(
            {"report_name": report_name},
            {"$set": {"test_type.interp.interp_regression": interp_regression or []}}
        )

    collection.update_one(
        {"report_name": report_name},
        {"$set": {"test_type.interp.result": result}}
    )


def check_and_update_translator(folder_path, report_name, existing_record):
    # logger = logging.getLogger('global_logger')
    translator_path = os.path.join(folder_path, "translator")
    result_detail = {}
    translator_regression = [] 
    result = "PASS"  

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) and file_name.lower().startswith("regression") and file_name.lower().endswith("translator"):
            result = "FAIL"  
            with open(file_path, 'r') as f:
                content = f.read()
                for line in content.strip().split("\n"):                 
                    parts = line.split()
                    if len(parts) >= 5:  
                        translator_regression.append({
                            "sub_test_suite": parts[0],
                            "result": parts[1],
                            "test_banner": parts[2],
                            "date": parts[3],
                            "time": parts[4], 
                        
                        })

    if os.path.exists(translator_path) and os.path.isdir(translator_path):
        for file_name in os.listdir(translator_path):
            file_path = os.path.join(translator_path, file_name)
            if file_name == "result": 
                continue
            if file_name not in existing_record.get("test_type", {}).get("translator", {}):
                with open(file_path, 'r') as f:
                    content = f.read()
                    result_detail[file_name] = content
                    
                    collection.update_one(
                        {"report_name": report_name},
                        {"$set": {f"test_type.translator.result_detail.{file_name}": content}}
                    )
                    global_logger.info(f"New file: {file_path} 到数据库中的 translator 文件夹")

        if result_detail:
            collection.update_one(
                {"report_name": report_name},
                {"$set": {"test_type.translator.result_detail": result_detail or {}}}
            )
    if translator_regression:
        collection.update_one(
            {"report_name": report_name},
            {"$set": {"test_type.translator.translator_regression": translator_regression or []}}
        )

    collection.update_one(
        {"report_name": report_name},
        {"$set": {"test_type.translator.result": result}},
        
    )


def check_and_update_spec(folder_path, report_name, existing_record):
    # logger = logging.getLogger('global_logger')
    spec_path = os.path.join(folder_path)
    new_spec_data = {"spec_detail_suite": {}}
    overall_result = "NO RUN"  
    
    for subdir_name in os.listdir(spec_path):
        subdir_path = os.path.join(spec_path, subdir_name)
        if os.path.isdir(subdir_path) and subdir_name.isdigit():
            overall_result = "PASS"  
            log_result = "PASS"
            html_file_path = None
            runtime = None
            
            for file_name in os.listdir(subdir_path):
                file_path = os.path.join(subdir_path, file_name)
                
                if file_name.endswith(".log"):
                    with open(file_path, 'r') as f:
                        # print("runtime_file", file_path)
                        content = f.read()
                        if "error" in content.lower():
                            log_result = "FAIL"
                            overall_result = "FAIL"
                        elif "success" not in content.lower():
                            log_result = "FAIL"
                            overall_result = "FAIL"
                        
                        runtime_match = re.search(r'runtime=(\d+\.\d+)', content)
                        if runtime_match:
                            runtime = runtime_match.group(1)
                
                if file_name.endswith(".html"):
                    html_file_path = file_path
            
            if html_file_path:
                new_spec_data["spec_detail_suite"][subdir_name] = {
                    "html": html_file_path,
                    "spec_type": log_result,
                    "runtime": runtime
                }
    
    new_spec_data["type"] = overall_result

    existing_spec = existing_record["test_type"]["spec"]
    updates = {}

    for key, new_data in new_spec_data["spec_detail_suite"].items():
        existing_data = existing_spec["spec_detail"]["spec_detail_suite"].get(key)
        if existing_data != new_data:
            updates[f"test_type.spec.spec_detail.spec_detail_suite.{key}"] = new_data

    if new_spec_data["type"] != existing_spec.get("type"):
        updates["test_type.spec.type"] = new_spec_data["type"]
    if updates:
        collection.update_one(
            {"report_name": report_name},
            {"$set": updates}
        )
        global_logger.info(f"Updated spec data for report: {report_name}")


def process_spec_files(folder_path, data):
    # logger = logging.getLogger('global_logger')
    spec_data = {"spec_detail": {"spec_detail_suite": {}}}
    overall_result = "NO RUN"  
    
    for subdir_name in os.listdir(folder_path):
        subdir_path = os.path.join(folder_path, subdir_name)
        if os.path.isdir(subdir_path) and subdir_name.isdigit():
            overall_result = "PASS" 
            log_result = "PASS"
            html_file_path = None
            runtime = None
            
            for file_name in os.listdir(subdir_path):
                file_path = os.path.join(subdir_path, file_name)
            
                if file_name.endswith(".log"):
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if "error" in content.lower():
                            log_result = "FAIL"
                            overall_result = "FAIL"
                        elif "success" not in content.lower():
                            log_result = "FAIL"
                            overall_result = "FAIL"
                        
                        runtime_match = re.search(r'runtime=(\d+\.\d+)', content)
                        if runtime_match:
                            runtime = runtime_match.group(1)
                
                if file_name.endswith(".html"):
                    html_file_path = file_path
            
            if html_file_path:
                spec_data["spec_detail"]["spec_detail_suite"][subdir_name] = {
                    "html": html_file_path,
                    "spec_type": log_result,
                    "runtime": runtime
                }  
    spec_data["type"] = overall_result
    data["test_type"]["spec"] = spec_data


def process_interp_files(interp_path, data):
    # logger = logging.getLogger('global_logger')
    if "interp" not in data["test_type"]:
        data["test_type"]["interp"] = {}
    interp_data = data["test_type"]["interp"]
    test_type_path = os.path.dirname(interp_path)
  
    if os.path.exists(interp_path) and os.path.isdir(interp_path):
        result = "PASS"
        result_detail = {}
        interp_regression = []  

        for file_name in os.listdir(test_type_path):
            if file_name.lower().startswith("regression") and file_name.lower().endswith("interp"):
                result = "FAIL"  
                file_path = os.path.join(test_type_path, file_name)
                with open(file_path, 'r') as f:
                    content = f.read()

                    for line in content.strip().split("\n"):
                        parts = line.split()
                        if len(parts) >= 5:  
                            interp_regression.append({
                                "sub_test_suite": parts[0],
                                "result": parts[1],
                                "test_banner": parts[2],
                                "date": parts[3],
                                "time": parts[4]
                            })
                global_logger.info(f"Read regression files: {file_path}")

      
        for file_name in os.listdir(interp_path):
            file_path = os.path.join(interp_path, file_name)
            if file_name == "result":  
                continue

            with open(file_path, 'r') as f:
                content = f.read()
                result_detail[file_name] = content
                global_logger.info(f"Read interp files: {file_path}")

   
        interp_data["result"] = result
        interp_data["result_detail"] = result_detail if result_detail else {}
        interp_data["interp_regression"] = interp_regression if interp_regression else []



def process_translator_files(translator_path, data):

    if "translator" not in data["test_type"]:
        data["test_type"]["translator"] = {}
    translator_data = data["test_type"]["translator"]
    test_type_path = os.path.dirname(translator_path)
    if os.path.exists(translator_path) and os.path.isdir(translator_path):
        result = "PASS"
        result_detail = {}
        translator_regression = [] 

        for file_name in os.listdir(test_type_path):
            if file_name.lower().startswith("regression") and file_name.lower().endswith("translator"):
                result = "FAIL" 
                file_path = os.path.join(test_type_path, file_name)
                with open(file_path, 'r') as f:
                    content = f.read()
                    for line in content.strip().split("\n"):
                        parts = line.split()
                        if len(parts) >= 5:  
                            translator_regression.append({
                                "sub_test_suite": parts[0],
                                "result": parts[1],
                                "test_banner": parts[2],
                                "date": parts[3],
                                "time": parts[4]
                            })
                global_logger.info(f"Read regression files: {file_path}")

        for file_name in os.listdir(translator_path):
            file_path = os.path.join(translator_path, file_name)
            if file_name == "result": 
                continue

            with open(file_path, 'r') as f:
                content = f.read()
                result_detail[file_name] = content
                global_logger.info(f"Read translator files: {file_path}")

  
        translator_data["result"] = result
        translator_data["result_detail"] = result_detail if result_detail else {}
        
        translator_data["translator_regression"] = translator_regression if translator_regression else []

def determine_result(spec_result, interp_result, translator_result):
    if spec_result == "NO RUN":
        if interp_result == "FAIL" or translator_result == "FAIL":
            return "FAIL"
        else:
            return "PASS"
    else:
        if spec_result == "FAIL" or interp_result == "FAIL" or translator_result == "FAIL":
            return "FAIL"
        else:
            return "PASS"

def check_and_update_results(folder_path, report_name, existing_record):

    check_and_update_spec(folder_path, report_name, existing_record)
    check_and_update_interp(folder_path, report_name, existing_record)
    check_and_update_translator(folder_path, report_name, existing_record)
    updated_record = collection.find_one({"report_name": report_name})
    new_result = determine_result(
        updated_record["test_type"]["spec"].get("type", "PASS"),
        updated_record["test_type"]["interp"].get("result", "PASS"),
        updated_record["test_type"]["translator"].get("result", "PASS")
    )

    if new_result != updated_record.get("result"):
        collection.update_one(
            {"report_name": report_name},
            {"$set": {"result": new_result}}
        )
        global_logger.info(f"Updated overall result for report: {report_name}")



def insert_data(folder_path, report_name):

    data = {
        "report_name": report_name,
        "result":"",
        "test_type": {
            "spec": {},
            "interp": {},
            "translator": {}
        }
    }

    process_spec_files(folder_path, data)
    interp_path = os.path.join(folder_path, "interp")
    # print("interp_path11111",interp_path)
    process_interp_files(interp_path, data)
    translator_path = os.path.join(folder_path, "translator")
    process_translator_files(translator_path, data)

    spec_result = data["test_type"]["spec"].get("result", "PASS")
    interp_result = data["test_type"]["interp"].get("result", "PASS")
    translator_result = data["test_type"]["translator"].get("result", "PASS")

    if "FAIL" in [spec_result, interp_result, translator_result]:
        data["result"] = "FAIL"
    else:
        data["result"] = "PASS"


    collection.insert_one(data)
    global_logger.info(f"Processed folder: {folder_path}, data inserted into database")
    print(f"Processed folder: {folder_path}, data inserted into database")

def process_folder(folder_path, folder_name):

    report_name_match = re.search(r'(^|[^a-zA-Z0-9])\d+_main_\d.*$', folder_name)
    # print(report_name_match)
    if report_name_match:
        report_name = report_name_match.group(0)
        existing_record = collection.find_one({"report_name": report_name})
        if existing_record:
            global_logger.info(f"Folder: {folder_name} already exists in database with report_name: {report_name}")
            print(f"Folder: {folder_name} already exists in database with report_name: {report_name}")
            check_and_update_results(folder_path, report_name, existing_record)
        else:
            insert_data(folder_path, report_name)



def should_copy_folder(folder_name):
    return re.search(r'_main_', folder_name) is not None

def main():
    
    for folder_name in os.listdir(local_temp_dir):
        # print(folder_name)
        local_test_temp_dir = os.path.join(local_temp_dir, folder_name)

        if "main" in folder_name and not folder_name.startswith("2024") and should_copy_folder(folder_name):
            # print(folder_name)
            global_logger.info("Match report_name %s", folder_name)
          
            process_folder(local_test_temp_dir, folder_name)


if __name__ == '__main__':
    # start_time = time.time()
    main()
    # end_time = time.time()
    # print(f"处理数据耗时: {end_time - start_time:.2f} 秒")