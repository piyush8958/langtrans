import os
import uuid
import tempfile
from django.shortcuts import render
from django.http import FileResponse
from googletrans import Translator
from gtts import gTTS
import speech_recognition as sr
import sounddevice as sd
from scipy.io.wavfile import write
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import subprocess
from django.http import JsonResponse
from django.utils.translation import gettext as _




# views.py






translator = Translator()


def home(request):
    return render(request, 'home.html')


def translate_text(request):
    translated_text = None
    if request.method == "POST":
        text = request.POST.get("text")
        lang = request.POST.get("lang")

        if text and lang:
            translator = Translator()
            if lang == "en":
                dest = "hi"
            else:
                dest = "en"

            try:
                translated = translator.translate(text, dest=dest)
                translated_text = translated.text
            except Exception as e:
                translated_text = f"Error: {str(e)}"

    return render(request, "translate_text.html", {"translated_text": translated_text})


def text_to_speech(request):
    original_audio_url = None
    translated_audio_url = None
    text = ''
    translated_text = ''
    lang = ''
    
    if request.method == "POST":
        text = request.POST.get("text")
        action = request.POST.get("action")
        translator = Translator()
        
        # Detect original language
        lang = "en" if all(ord(c) < 128 for c in text) else "hi"
        static_dir = os.path.join(settings.BASE_DIR, "static")
        os.makedirs(static_dir, exist_ok=True)

        # Generate original speech
        if action == "generate":
            tts = gTTS(text=text, lang=lang)
            file_name = f"tts_{lang}_{uuid.uuid4().hex}.mp3"
            file_path = os.path.join(static_dir, file_name)
            tts.save(file_path)
            original_audio_url = f"/static/{file_name}"

        # Translate and generate translated speech
        elif action == "translate":
            translated_text = translator.translate(text, src="en" if lang == "en" else "hi", dest="hi" if lang == "en" else "en").text
            translated_lang = "hi" if lang == "en" else "en"
            tts = gTTS(text=translated_text, lang=translated_lang)
            file_name = f"tts_translated_{translated_lang}_{uuid.uuid4().hex}.mp3"
            file_path = os.path.join(static_dir, file_name)
            tts.save(file_path)
            translated_audio_url = f"/static/{file_name}"
            original_audio_url = request.POST.get("original_audio_url")  # Keep original audio

    return render(request, "text_to_speech.html", {
        "original_audio_url": original_audio_url,
        "translated_audio_url": translated_audio_url,
        "text": text,
        "translated_text": translated_text,
        "lang": lang,
    })





@csrf_exempt
def speech_to_text_view(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        for chunk in audio_file.chunks():
            temp_audio.write(chunk)
        temp_audio.close()

        recognizer = sr.Recognizer()
        translator = Translator()
        try:
            with sr.AudioFile(temp_audio.name) as source:
                audio = recognizer.record(source)

            # Try Hindi first, fallback to English
            try:
                text = recognizer.recognize_google(audio, language='hi-IN')
                translated = translator.translate(text, src='hi', dest='en').text
            except sr.UnknownValueError:
                text = recognizer.recognize_google(audio, language='en-IN')
                translated = translator.translate(text, src='en', dest='hi').text

            os.remove(temp_audio.name)
            return JsonResponse({"text": text, "translated": translated})

        except Exception as e:
            os.remove(temp_audio.name)
            return JsonResponse({"error": str(e)})

    return render(request, "core/speech_to_text.html")
