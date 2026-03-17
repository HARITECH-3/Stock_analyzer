from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    DashboardView,
    ExploreView,
    LivePriceAPIView,
    MoreView,
    PredictAPIView,
    StockDetailView,
    WatchlistView,
    home_redirect,
    register_view,
    watchlist_add_view,
    watchlist_remove_view,
)

urlpatterns = [
    path("", home_redirect, name="home"),
    path("explore/", ExploreView.as_view(), name="explore"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("watchlist/", WatchlistView.as_view(), name="watchlist"),
    path("more/", MoreView.as_view(), name="more"),
    path("stock/<str:ticker>/", StockDetailView.as_view(), name="stock_detail"),
    path("watchlist/add/", watchlist_add_view, name="watchlist_add"),
    path("watchlist/remove/", watchlist_remove_view, name="watchlist_remove"),
    path("api/price/<str:ticker>/", LivePriceAPIView.as_view(), name="api_price"),
    path("api/predict/<str:ticker>/", PredictAPIView.as_view(), name="api_predict"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html", redirect_authenticated_user=False),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", register_view, name="register"),
]
