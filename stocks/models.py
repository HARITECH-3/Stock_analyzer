from django.contrib.auth.models import User
from django.db import models


class Watchlist(models.Model):
    EXCHANGE_CHOICES = (("NSE", "NSE"), ("BSE", "BSE"))

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist_items")
    ticker = models.CharField(max_length=20)
    exchange = models.CharField(max_length=3, choices=EXCHANGE_CHOICES, default="NSE")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "ticker", "exchange")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} - {self.ticker} ({self.exchange})"


class PriceHistory(models.Model):
    EXCHANGE_CHOICES = (("NSE", "NSE"), ("BSE", "BSE"))

    ticker = models.CharField(max_length=20)
    exchange = models.CharField(max_length=3, choices=EXCHANGE_CHOICES, default="NSE")
    date = models.DateField()
    open = models.DecimalField(max_digits=12, decimal_places=2)
    high = models.DecimalField(max_digits=12, decimal_places=2)
    low = models.DecimalField(max_digits=12, decimal_places=2)
    close = models.DecimalField(max_digits=12, decimal_places=2)
    volume = models.BigIntegerField(default=0)

    class Meta:
        ordering = ["-date"]
        unique_together = ("ticker", "exchange", "date")

    def __str__(self):
        return f"{self.ticker} {self.date}"


class LSTMPrediction(models.Model):
    DIRECTION_CHOICES = (("BUY", "BUY"), ("SELL", "SELL"), ("HOLD", "HOLD"))

    ticker = models.CharField(max_length=20)
    predicted_price = models.DecimalField(max_digits=12, decimal_places=2)
    direction = models.CharField(max_length=4, choices=DIRECTION_CHOICES)
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticker} - {self.direction} ({self.confidence:.2f}%)"
