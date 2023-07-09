from django.urls import path
from .views import *
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register('devices', FCMDeviceAuthorizedViewSet)

urlpatterns = [
	path("ping/", ping, name="ping"),
    path("search_place/<str:name>/", search_place, name="search_place"),
    path("register", register_view, name = "register_view"),
    path("whatsapp_auth/", whatsapp_auth, name="whatsapp_auth"),
    path("check_code/", check_code, name="check_code"),
    path("get_stp/", get_register_stp, name="get_register_stp"),
    path("get_interests/", get_interests, name="get_interests"),
    path("create_stories/", create_stories, name = "create_stories"),
    path("get_professions/", get_professions, name="get_professions"),
    path("get_home/", get_home, name="get_home"),
    path('get_home_from_slug/<str:slug>/', get_home_from_slug, name="get_home_from_slug"),
    path('post_post/', post_post, name="post_post"),
    path('get_preuve/', get_preuve, name="get_preuve"),
    path('upload_preuve/', upload_preuve, name="upload_preuve"),
    path('set_checked/', set_checked, name="set_checked"),
    path("get_payments/", get_payments, name="get_payments"),
    path("retire_all/", retire_all, name="retire_all"),
    path('add_momo/', add_momo, name="add_momo"),
    path("get_params/", get_params, name="get_params"),
    path('get_details/', get_details, name="get_details"),
    path('get_my_company/', get_my_company, name="get_my_company"),
    path('get_posts/', get_posts, name= "get_posts"),
    path('get_update/', get_update, name="get_update"),
    path('get_my_post/', get_my_post, name="get_my_post"),
    path('set_budget/', set_budget, name = "set_budget"),
    path('submit_media/', submit_media, name = "submit_media"),
    path('get_campaigns/', get_campaigns, name = "get_campaigns"),
    path('create_campaign/', create_campaign, name="create_campaign"),
    path('set_campaign/', set_campaign, name = "set_campaign"),
    path('create_post/', create_post, name = "create_post"),
    path("get_min_pay/", get_min_pay, name="get_min_pay"),
    path('make_payment/', make_payment, name="make_payment"),
    path('duplicate_data/', duplicate_data, name="duplicate_data"),
    path('get_notifs/', get_notifs, name="get_notifs"),
    path('get_stats/', get_stats, name="get_stats"),
    path('get_cpays/', get_cpays, name="get_cpays"),
    path('get_cparams/', get_cparams, name="get_cparams"),
    path('delete_post/<int:id>/', delete_post, name="delete_post")
]