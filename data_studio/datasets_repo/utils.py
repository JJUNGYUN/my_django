import os
from django.utils import timezone
from datasets import load_dataset


def get_file_info_from_dir(directory_path):
    file_info_list = []

    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path) or os.path.isdir(file_path):
                stat = os.stat(file_path)
                file_size = round(stat.st_size / (1024 * 1024), 2)  # MB
                modified_time = timezone.datetime.fromtimestamp(stat.st_mtime, tz=timezone.get_current_timezone())
                if os.path.isdir(os.path.join(directory_path, filename)):
                    filetype = '📁'
                else:
                    filetype = '📄'
                    
                file_info_list.append({
                    'file_type' : filetype,
                    'name': filename,
                    'size': f"{file_size} MB",
                    'modified': modified_time
                })
    file_info_list = sorted(file_info_list, key=lambda x: (x['file_type'], x['name']))
    return file_info_list



def get_sample_dataset(dataset_path, MAX_DEPTH = 2):
    d_type = None
    sample_data = None
    for path, _, files in os.walk(dataset_path):
        rel_path = os.path.relpath(path, dataset_path)
        depth = rel_path.count(os.sep)
        
        if depth > MAX_DEPTH:
            continue  # skip deeper folders

        for file in files:
            if 'parquet' in file:
                d_type = 'parquet'
                sample_data = os.path.join(path, file)
                break
            if 'json' in file:
                d_type = 'json'
                sample_data = os.path.join(path, file)
                break
            if 'jsonl' in file:
                d_type = 'jsonl'
                sample_data = os.path.join(path, file)
                break    
            if 'csv' in file:
                d_type = 'jsonl'
                sample_data = os.path.join(path, file)
                break 

    if not sample_data:
        return {"현재 읽기 지원하는 데이터는 csv, json, jsonl, parquet입니다."}

    dataset = load_dataset(d_type, data_files=sample_data, split="train[:50]")

    sample_data = [dataset[d] for d in range(50)]

    return sample_data