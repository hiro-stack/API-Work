from django.urls import path
from .views import index, SignUpView, UserView, CloseUserView

urlpatterns = [
    path("", index),
    path("signup/", SignUpView.as_view()),
    path("users/<str:user_id>/", UserView.as_view()),
    path("close/", CloseUserView.as_view()),
]
