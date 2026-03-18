from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.decorators.http import require_POST, require_GET
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.views import APIView

from .lstm_predictor import predict
from .models import LSTMPrediction, Watchlist
from .services import (
    INDIAN_STOCKS,
    format_indian_price,
    get_historical_data,
    get_live_price,
    get_market_indices,
    get_market_sentiment,
    get_top_gainers,
    get_top_losers,
)


# Health check endpoint for Render - lightweight, no data loading
@require_GET
def health_check(request):
    """Simple health check endpoint without loading any data."""
    return JsonResponse({"status": "ok"}, status=200)


class DashboardView(View):
    @method_decorator(login_required)
    def get(self, request):
        watchlist_items = Watchlist.objects.filter(user=request.user)
        holdings = []
        total_value = 0
        total_invested = 0

        for item in watchlist_items:
            live = get_live_price(item.ticker, item.exchange)
            shares = 10
            invested_per_share = live["price"] * 0.92
            current_value = live["price"] * shares
            invested_value = invested_per_share * shares
            pnl = current_value - invested_value
            pnl_pct = (pnl / invested_value * 100) if invested_value else 0

            total_value += current_value
            total_invested += invested_value
            holdings.append(
                {
                    "ticker": item.ticker,
                    "shares": shares,
                    "current_value": current_value,
                    "current_value_display": format_indian_price(current_value),
                    "pnl": pnl,
                    "pnl_display": format_indian_price(pnl),
                    "pnl_pct": round(pnl_pct, 2),
                    "is_up": pnl >= 0,
                }
            )

        if not holdings:
            for ticker in ["RELIANCE", "INFY", "TCS"]:
                live = get_live_price(ticker)
                shares = 8
                current_value = live["price"] * shares
                invested_value = current_value * 0.95
                pnl = current_value - invested_value
                total_value += current_value
                total_invested += invested_value
                holdings.append(
                    {
                        "ticker": ticker,
                        "shares": shares,
                        "current_value": current_value,
                        "current_value_display": format_indian_price(current_value),
                        "pnl": pnl,
                        "pnl_display": format_indian_price(pnl),
                        "pnl_pct": round((pnl / invested_value) * 100, 2),
                        "is_up": pnl >= 0,
                    }
                )

        total_returns = total_value - total_invested
        total_returns_pct = (total_returns / total_invested * 100) if total_invested else 0

        predictions = []
        for ticker in [item["ticker"] for item in holdings[:4]]:
            pred = predict(ticker)
            LSTMPrediction.objects.create(
                ticker=ticker,
                predicted_price=pred["predicted_price"],
                direction=pred["direction"],
                confidence=pred["confidence"],
            )
            predictions.append(pred)

        context = {
            "indices": get_market_indices(),
            "holdings": holdings,
            "predictions": predictions,
            "total_value_display": format_indian_price(total_value),
            "total_returns_display": format_indian_price(total_returns),
            "total_returns_pct": round(total_returns_pct, 2),
            "invested_value_display": format_indian_price(total_invested),
            "active_tab": "dashboard",
        }
        return render(request, "stocks/dashboard.html", context)


class ExploreView(View):
    @method_decorator(login_required)
    def get(self, request):
        news_items = [
            {
                "source": "ET Markets",
                "time_ago": "2h ago",
                "headline": "Infrastructure stocks rally as order inflows improve for Q4.",
                "stock": "L&T",
                "change": "+2.84%",
                "is_up": True,
            },
            {
                "source": "Moneycontrol",
                "time_ago": "4h ago",
                "headline": "IT majors slip amid global tech guidance caution.",
                "stock": "INFY",
                "change": "-1.22%",
                "is_up": False,
            },
            {
                "source": "LiveMint",
                "time_ago": "6h ago",
                "headline": "Banking counters steady ahead of RBI policy commentary.",
                "stock": "HDFCBANK",
                "change": "+0.67%",
                "is_up": True,
            },
        ]
        context = {
            "indices": get_market_indices(),
            "gainers": get_top_gainers(),
            "losers": get_top_losers(),
            "news_items": news_items,
            "active_tab": "explore",
        }
        return render(request, "stocks/explore.html", context)


class StockDetailView(View):
    @method_decorator(login_required)
    def get(self, request, ticker):
        ticker = ticker.upper()
        live = get_live_price(ticker)
        history = get_historical_data(ticker, period="3mo")
        prediction = predict(ticker)
        sentiment = get_market_sentiment(ticker)

        close_series = [round(float(item), 2) for item in history["Close"].dropna().tail(60).tolist()]
        day_low = min(close_series) if close_series else live["price"]
        day_high = max(close_series) if close_series else live["price"]
        low_52 = min(close_series) * 0.8 if close_series else live["price"] * 0.8
        high_52 = max(close_series) * 1.2 if close_series else live["price"] * 1.2

        context = {
            "ticker": ticker,
            "stock_name": ticker,
            "exchange": "NSE",
            "sector": "Construction",
            "live": live,
            "prediction": prediction,
            "sentiment": sentiment,
            "day_low": format_indian_price(day_low),
            "day_high": format_indian_price(day_high),
            "week52_low": format_indian_price(low_52),
            "week52_high": format_indian_price(high_52),
            "day_range_pct": 50,
            "week52_range_pct": 58,
            "active_tab": "watchlist",
        }
        return render(request, "stocks/stock_detail.html", context)


class WatchlistView(View):
    @method_decorator(login_required)
    def get(self, request):
        items = Watchlist.objects.filter(user=request.user)
        stocks = []
        for item in items:
            live = get_live_price(item.ticker, item.exchange)
            stocks.append(
                {
                    "ticker": item.ticker,
                    "exchange": item.exchange,
                    "price": live["price"],
                    "price_display": live["price_display"],
                    "change_percent": live["change_percent"],
                    "is_up": live["is_up"],
                    "series": live["series"],
                }
            )
        return render(request, "stocks/watchlist.html", {"stocks": stocks, "active_tab": "watchlist"})


class MoreView(View):
    @method_decorator(login_required)
    def get(self, request):
        return render(request, "stocks/more.html", {"active_tab": "more"})


@require_POST
@login_required
def watchlist_add_view(request):
    ticker = request.POST.get("ticker", "").upper().strip()
    exchange = request.POST.get("exchange", "NSE").upper().strip()
    if not ticker:
        return JsonResponse({"status": "error", "message": "Ticker is required"}, status=400)
    if exchange not in ["NSE", "BSE"]:
        exchange = "NSE"
    Watchlist.objects.get_or_create(user=request.user, ticker=ticker, exchange=exchange)
    return JsonResponse({"status": "ok", "message": f"{ticker} added to watchlist"})


@require_POST
@login_required
def watchlist_remove_view(request):
    ticker = request.POST.get("ticker", "").upper().strip()
    exchange = request.POST.get("exchange", "NSE").upper().strip()
    entry = get_object_or_404(Watchlist, user=request.user, ticker=ticker, exchange=exchange)
    entry.delete()
    return JsonResponse({"status": "ok", "message": f"{ticker} removed from watchlist"})


class LivePriceAPIView(APIView):
    def get(self, request, ticker):
        period_map = {
            "1d": "1d",
            "1w": "5d",
            "1m": "1mo",
            "1y": "1y",
            "3y": "3y",
            "all": "3y",
        }
        period_key = request.GET.get("period", "1m").lower()
        period = period_map.get(period_key, "1mo")
        exchange = request.GET.get("exchange", "NSE").upper()

        live = get_live_price(ticker.upper(), exchange)
        history = get_historical_data(ticker.upper(), period=period, exchange=exchange)
        closes = [round(float(item), 2) for item in history["Close"].dropna().tolist()]

        return Response(
            {
                "ticker": ticker.upper(),
                "exchange": exchange,
                "price": live["price"],
                "price_display": live["price_display"],
                "change": live["change"],
                "change_percent": live["change_percent"],
                "is_up": live["is_up"],
                "series": closes,
            }
        )


class PredictAPIView(APIView):
    def get(self, request, ticker):
        result = predict(ticker.upper())
        return Response(result)


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully. Welcome to StockPulse.")
            return redirect("dashboard")
        messages.error(request, "Could not create account. Please fix the errors below.")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})
