import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

from .services import format_indian_price, get_historical_data


class PriceLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


def prepare_data(df, window_size=60):
    closes = df["Close"].values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(closes)

    sequences = []
    labels = []
    for index in range(window_size, len(scaled_data)):
        sequences.append(scaled_data[index - window_size : index, 0])
        labels.append(scaled_data[index, 0])

    x = np.array(sequences)
    y = np.array(labels)

    if len(x) == 0:
        return None, None, scaler

    x = np.reshape(x, (x.shape[0], x.shape[1], 1))
    return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32), scaler


def predict(ticker):
    df = get_historical_data(ticker, period="6mo")
    if df.empty or "Close" not in df.columns:
        return {
            "ticker": ticker,
            "predicted_price": 0.0,
            "predicted_price_display": format_indian_price(0),
            "direction": "HOLD",
            "confidence": 50.0,
        }

    x, _, scaler = prepare_data(df)
    close_values = df["Close"].dropna().values
    if x is None or len(close_values) < 2:
        last_price = float(close_values[-1]) if len(close_values) else 0.0
        return {
            "ticker": ticker,
            "predicted_price": round(last_price, 2),
            "predicted_price_display": format_indian_price(last_price),
            "direction": "HOLD",
            "confidence": 52.0,
        }

    model = PriceLSTM(input_size=1, hidden_size=64, num_layers=2)
    model.eval()

    # TODO: integrate trained LSTM checkpoint here
    with torch.no_grad():
        last_sequence = x[-1].unsqueeze(0)
        pred_scaled = model(last_sequence).numpy()
    predicted_price = scaler.inverse_transform(pred_scaled)[0][0]

    latest_close = float(close_values[-1])
    change_pct = ((predicted_price - latest_close) / latest_close) * 100 if latest_close else 0

    if change_pct > 1.0:
        direction = "BUY"
    elif change_pct < -1.0:
        direction = "SELL"
    else:
        direction = "HOLD"

    confidence = float(min(95, max(50, abs(change_pct) * 10 + 50)))

    return {
        "ticker": ticker,
        "predicted_price": round(float(predicted_price), 2),
        "predicted_price_display": format_indian_price(predicted_price),
        "direction": direction,
        "confidence": round(confidence, 2),
    }
