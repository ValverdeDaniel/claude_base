from django.urls import path

from . import views

urlpatterns = [
    path('tests/', views.ListTestsView.as_view()),
    path('tests/run/', views.RunTestsView.as_view()),
    path('tests/runs/', views.TestRunListView.as_view()),
    path('tests/runs/<int:pk>/status/', views.TestRunStatusView.as_view()),
    path('tests/runs/<int:pk>/cancel/', views.CancelTestRunView.as_view()),
    path('tests/runs/<int:pk>/', views.TestRunDetailView.as_view()),
]
