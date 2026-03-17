from django.contrib import admin

from .models import LSTMPrediction, PriceHistory, Watchlist


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("user", "ticker", "exchange", "added_at")
    search_fields = ("user__username", "ticker", "exchange")


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("ticker", "exchange", "date", "open", "high", "low", "close", "volume")
    search_fields = ("ticker", "exchange")
    list_filter = ("exchange", "date")


@admin.register(LSTMPrediction)
class LSTMPredictionAdmin(admin.ModelAdmin):
    list_display = ("ticker", "direction", "confidence", "created_at")
    search_fields = ("ticker", "direction")
    list_filter = ("direction", "created_at")
