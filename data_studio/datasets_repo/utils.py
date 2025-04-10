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

    return file_info_list

def get_sample_dataset(dataset_path):
    for path, _, files in os.walk(dataset_path):
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
            

    dataset = load_dataset(d_type, data_files=sample_data, split="train")

    sample_data = [dataset[d] for d in range(50)]

    return sample_data