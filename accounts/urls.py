from django.urls import path
from . import views


urlpatterns = [
    path("auth/signup", views.SignupUser.as_view(), name="signup"),
    path("auth/login", views.LoginUser.as_view(), name="login"),
    path("auth/profile", views.CurrentUser.as_view(), name="user"),
    path("auth/profile/update", views.UpdateUser.as_view(), name="updateuser"),
    path("auth/connect-to-discord", views.Discord.as_view(), name="connect-to-discord"),
    path("enroll", views.NewEnroll.as_view(), name="enrollment"),
    path("enrollments", views.MyEnrolls.as_view(), name="myenrollments"),
    path("enrollments/query", views.QueryEnrollments.as_view(), name="myenrollments"),
    path('enrollments/<int:id>/check-payze-subscription-status', views.CheckPayzeSubscriptionStatusView.as_view(), name='check-payze-status'),
    path("enrollments/<int:id>", views.UpdateEnroll.as_view()),
    path("kids/newprofile", views.NewKidsProfile.as_view()),
    path("kids/getprofiles", views.GetKidsProfile.as_view()),
    path("kids/deleteprofile", views.DeleteKidsProfile.as_view())
]
