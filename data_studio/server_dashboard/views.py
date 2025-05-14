from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
def index(request):
    
    return render(request, 'server_dashboard/server_info.html')

def gpu_usage(request):
    gpu_data = {"GPU-1":{"memory":"80", "usage":"72"}, "GPU-2":{"memory":"80", "usage":"61"}, "GPU-3":{"memory":"80", "usage":"10"}, "GPU-4":{"memory":"80", "usage":"33"}, "GPU-5":{"memory":"80", "usage":"27"}, "GPU-6":{"memory":"80", "usage":"78"}}
    
    def get_color(percentage):
        p = float(percentage)
        if p <= 20:
            return 'rgba(75, 192, 192, 0.2)'
        elif p <= 40:
            return 'rgba(153, 102, 255, 0.2)'
        elif p <= 60:
            return 'rgba(54, 162, 235, 0.2)'
        elif p <= 80:
            return 'rgba(255, 206, 86, 0.2)'
        elif p <= 95:
            return 'rgba(255, 159, 64, 0.2)'
        else:
            return 'rgba(255, 99, 132, 0.2)'

    labels = []
    data = []
    backgroundColors = []

    for gpu, stats in gpu_data.items():
        usage_percent = (int(stats["usage"]) / int(stats["memory"])) * 100
        labels.append(gpu)
        data.append(round(usage_percent, 2))
        backgroundColors.append(get_color(usage_percent))

    return JsonResponse({
        "labels": labels,
        "data": data,
        "backgroundColors": backgroundColors
    })