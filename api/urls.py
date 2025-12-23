from django.urls import path
from .views import SignUpView, UserView, CloseUserView

urlpatterns = [
    path("signup/", SignUpView.as_view()),
    path("users/<str:user_id>/", UserView.as_view()),
    path("close/", CloseUserView.as_view()),
]
