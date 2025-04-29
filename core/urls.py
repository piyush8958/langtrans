from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('translate/', views.translate_text, name='translate'),
    path('text-to-speech/', views.text_to_speech, name='text_to_speech'),
   # ✅ Correct
path('speech-to-text/', views.speech_to_text_view, name='speech_to_text')

]
