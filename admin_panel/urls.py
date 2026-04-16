from django.urls import path

from . import views

urlpatterns = [
    path('tests/', views.ListTestsView.as_view()),
    path('tests/run/', views.RunTestsView.as_view()),
]
