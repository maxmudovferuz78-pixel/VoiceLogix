from django.shortcuts import render
from core import translate


def home(request):
    result = None
    original_text = ""
    direction = "uz_to_en"

    if request.method == "POST":
        original_text = request.POST.get("text", "").strip()
        direction = request.POST.get("direction", "uz_to_en")

        if original_text:
            result = translate(original_text, direction=direction)

    context = {
        "result": result,
        "original_text": original_text,
        "direction": direction,
    }
    return render(request, "translator_app/home.html", context)
