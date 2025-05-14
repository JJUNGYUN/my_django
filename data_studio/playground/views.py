from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Playground
from models.models import LM_models
from .form import PlaygroundForm
from datetime import timedelta
import paramiko
from django.urls import reverse

# Create your views here.
def index(request):
    page = request.GET.get('page','1')  
    q = request.GET.get('q', '')  # 검색어 가져오기

    playground_list = Playground.objects.order_by('-id')
    if q:
       playground_list = playground_list.filter(llm_model_icontains=q)
    print(q)
    print(playground_list)
    paginator = Paginator(playground_list, 20)
    page_obj = paginator.get_page(page)

    context = {
        'playground_list': page_obj,
        "q": request.GET.get("q", ""),
        "reset_url": reverse('datasets:index'),
        "filter_options": {
            "all": "전체",
            "title": "제목",
            "owner": "작성자",
        }
    }


    return render(request, 'playground/playground_list.html', context)

SERVER_LIST = ['10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.4']
STATUS_PENDING = '0'
STATUS_RUNNING = '1'
STATUS_FAILED = '2'

def detail(request, pk):
    return render(request, 'playground/playground_list.html')

def get_available_gpu_index(ssh):
    try:
        # GPU별로 어떤 프로세스가 붙어있는지 확인
        cmd = "nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader,nounits"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        used_gpus = stdout.read().decode().strip().splitlines()

        # 전체 GPU 수 파악
        stdin, stdout, stderr = ssh.exec_command("nvidia-smi -L")
        all_gpus = stdout.read().decode().strip().splitlines()

        # 사용 중인 UUID 목록에서 index 제외
        available_gpu_indices = []
        for idx, line in enumerate(all_gpus):
            # 예시: GPU 0: A100-SXM4-40GB (UUID: GPU-a1b2c3d4-e5f6-7890-abcd-12345678abcd)
            uuid = line.split("UUID:")[1].strip(") ")
            if uuid not in used_gpus:
                available_gpu_indices.append(idx)

        if available_gpu_indices:
            return available_gpu_indices[0]  # 가장 먼저 비어있는 GPU
        else:
            return None
    except Exception as e:
        print(f"Error checking GPU availability: {e}")
        return None


def find_available_port(ssh, start=8001, end=9000):
    for port in range(start, end):
        command = f"netstat -tuln | grep :{port}"
        stdin, stdout, stderr = ssh.exec_command(command)
        if not stdout.read().decode().strip():  # 포트가 사용 중이 아니면
            return port
    return None


def search_server():
    for server in SERVER_LIST:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(server, username='your_user', password='your_password')

            gpu_index = get_available_gpu_index(ssh)
            if gpu_index is not None:
                port = find_available_port(ssh)
                if port:
                    docker_name = f"triton_{port}"
                    ssh.close()
                    return server, port, docker_name, gpu_index

            ssh.close()
        except Exception as e:
            print(f"Error connecting to {server}: {e}")
            continue
    return None, None, None, None




def create_triton_docker(ssh, port, docker_name, gpu_index):
    try:
        # 이미지 이름 예상 (실제 이름 알고 있다면 하드코딩도 OK)
        image_name = "nvcr.io/nvidia/tritonserver:latest"

        # 이미지 존재 여부 확인
        stdin, stdout, stderr = ssh.exec_command(f"docker images -q {image_name}")
        image_id = stdout.read().decode().strip()

        # 이미지 없으면 로드
        if not image_id:
            print("[INFO] 이미지가 없으므로 로드 시작")
            stdin, stdout, stderr = ssh.exec_command("docker load -i /tmp/docker/triton_api.tar")
            image_load_output = stdout.read().decode().strip()
            print("[이미지 로드 결과]", image_load_output)

            # 다시 이미지 이름 파싱 (혹시 이름이 다를 경우 대비)
            for line in image_load_output.splitlines():
                if "Loaded image:" in line:
                    image_name = line.split(":", 1)[1].strip()
                    break

        else:
            print(f"[INFO] 이미 이미지 존재: {image_name}")

        # Docker run
        docker_run_cmd = (
            f"docker run -d --rm "
            f"--gpus device={gpu_index} "
            f"-p {port}:8000 "
            f"--name {docker_name} "
            f"{image_name} tritonserver"
        )

        print("[컨테이너 실행 명령]", docker_run_cmd)
        ssh.exec_command(docker_run_cmd)

    except Exception as e:
        print(f"[ERROR] Docker 실행 실패: {e}")


def async_start_docker(playground, model_obj):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(playground.server, username='your_user', password='your_password')

        create_triton_docker(
            ssh=ssh,
            port=playground.triton_port,
            docker_name=playground.docker_name,
            gpu_index=playground.gpu_index
        )

        # ✅ 컨테이너 성공적으로 생성 후 status_code 업데이트
        playground.status_code = '1'
        playground.save(update_fields=['status_code'])

        ssh.close()

    except Exception as e:
        print(f"[ERROR] 비동기 docker 실행 실패: {e}")
        # 실패 시 실패 상태코드 등도 지정할 수 있음
        playground.status = '2'  # 예: 실패 상태
        playground.save(update_fields=['status_code'])


from django.utils import timezone
from datetime import timedelta
import threading

def new_playground(request):
    if request.method == 'POST':
        form = PlaygroundForm(request.POST)
        if form.is_valid() :
            try:
                # server, port, docker_name, gpu_index = search_server()

                # create_triton_docker(server, port, docker_name, gpu_index)
                server, port, docker_name, gpu_index = "10.0.0.1", "8234", "test", "0"
                playground = form.save(commit=False)
                # playground.llm_model = model_obj
                playground.author = request.user
                playground.server = server
                playground.triton_port = port
                playground.gpu_index = gpu_index
                playground.docker_name = docker_name
                playground.start_time = timezone.now()
                playground.end_time = timezone.now() + timedelta(hours=2)
                playground.status = '0'
                playground.save()

                # threading.Thread(target=async_start_docker, args=(playground, model_obj)).start()


                return redirect('playground:index')
            except Exception as e:
                form.add_error(None, str(e))
        else:
            print(form.errors)
    else:
        form = PlaygroundForm()
    context = {'form':form}
    return render(request, 'playground/new_playground.html',context)






def delete_playground(request, pk):
    playground = get_object_or_404(Playground, pk=pk)
    print(playground.docker_name)
    print(playground.server)

    if request.method == 'POST':
        playground.delete()
    
    return redirect('playground:index')

@require_GET
def model_autocomplete(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('term', '')
        results = LM_models.objects.filter(name__icontains=query).values_list('name', flat=True)
        return JsonResponse(list(results), safe=False)
    return JsonResponse([], safe=False)