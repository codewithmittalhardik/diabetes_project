from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .services import ai_service

def index(request):
    return render(request, 'index.html')

def severity_guide(request):
    return render(request, 'severity.html')

def tech_stack(request):
    return render(request, 'tech_stack.html')

def food_checker(request):
    return render(request, 'food_checker.html')

def dataset_info(request):
    return render(request, 'dataset_info.html')

@csrf_exempt
def predict(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            result, status = ai_service.predict(data)
            return JsonResponse(result, status=status)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "POST required"}, status=405)

@csrf_exempt
def check_food(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            food_name = data.get('food_name')
            result, status = ai_service.check_food(food_name)
            return JsonResponse(result, status=status)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "POST required"}, status=405)


def custom_permission_denied(request, exception=None):
    return render(request, '403.html', status=403)


def custom_csrf_failure(request, reason=""):
    return render(request, '403.html', status=403)
