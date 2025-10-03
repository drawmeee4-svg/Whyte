from python-telegram-bot import Bot
from python-telegram-bot.ext 
import Updater, CommandHandler
import requests
import schedule
import time
from datetime import datetime
import os

TELEGRAM_TOKEN = os.getenv('8430879836:AAHt_h3EhSPmmy4FA47opz5NPYOE1jC7ymU')
CHAT_ID = os.getenv('7753187984')
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']

bot = bot(token=TELEGRAM_TOKEN)

def calculate_rsi(closes, period=14):
    if len(closes) < period:
        return None
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(diff if diff > 0 else 0)
        losses.append(-diff if diff < 0 else 0)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    rs = avg_gain / avg_loss if avg_loss != 0 else 100
    return 100 - (100 / (1 + rs))

def get_futures_data(symbol):
    url = f'https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}'
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        price = float(data['lastPrice'])
        price_change_24h = float(data['priceChangePercent'])
        return price, price_change_24h, None
    except Exception as e:
        return None, None, str(e)

def get_simple_signal(symbol):
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1d&limit=15'
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        closes = [float(kline[4]) for kline in data]
        moving_average = sum(closes[-7:]) / 7
        rsi = calculate_rsi(closes, 14)
        current_price, _, error = get_futures_data(symbol)
        if error:
            return f"Error: {error}"
        signal = "Hold: Price is within normal range."
        if current_price > moving_average * 1.03 and rsi and rsi < 70:
            signal = "Long Signal: Price above 7-day MA and RSI not overbought."
        elif current_price < moving_average * 0.97 and rsi and rsi > 30:
            signal = "Short Signal: Price below 7-day MA and RSI not oversold."
        return signal
    except Exception as e:
        return f"Error: {str(e)}"

def send_daily_signal():
    try:
        message = f"🚀 Daily Futures Signals ({datetime.now().strftime('%Y-%m-%d %H:%M')} WAT):\n"
        for symbol in SYMBOLS:
            price, change_24h, error = get_futures_data(symbol)
            signal = get_simple_signal(symbol)
            if error:
                message += f"\n{symbol}:\n⚠️ Error: {error}\n"
            else:
                message += f"\n{symbol}:\n💰 Price: ${price:.2f}\n📈 24h Change: {change_24h:.2f}%\n🔔 Signal: {signal}\n"
        bot.send_message(chat_id=CHAT_ID, text=message)
        print("Signals sent successfully!")
    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"Error fetching data: {str(e)}")
        print(f"Error: {str(e)}")

def start(update, context):
    update.message.reply_text("Crypto Futures Signal Bot started! Daily signals at 8:00 AM WAT.")
    send_daily_signal()

schedule.every().day.at("07:00").do(send_daily_signal)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main()
