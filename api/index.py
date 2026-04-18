import os
import random
import json
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# 加載環境變數
load_dotenv()

app = Flask(__name__)

# LINE Bot 設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 讀取塔羅牌資料 (使用相對路徑)
def load_tarot_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # index.py 在 /api/ 資料夾內，tarot_data.json 在上一層根目錄
    json_path = os.path.join(current_dir, '..', 'tarot_data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

tarot_deck = load_tarot_data()

@app.route("/", methods=['GET'])
def index():
    return "Tarot Bot is running!", 200

# ✅ 修正：同時接受 GET 和 POST，GET 直接回傳 200
@app.route("/callback", methods=['GET', 'POST'])
def callback():
    # LINE 有時會用 GET 驗證，直接回傳 200
    if request.method == 'GET':
        return 'OK', 200

    # 取得 X-Line-Signature 標頭值
    signature = request.headers.get('X-Line-Signature', '')

    # 取得請求內容
    body = request.get_data(as_text=True)

    # 處理 webhook 本體
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK', 200  # ✅ 明確回傳 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    if "占卜" in user_message or "抽牌" in user_message or "塔羅" in user_message:
        # 隨機抽取一張牌
        card = random.choice(tarot_deck)
        # 隨機決定正位或逆位
        is_upright = random.choice([True, False])

        orientation = "正位" if is_upright else "逆位"
        meaning = card['upright'] if is_upright else card['reversed']

        reply_text = f"【{card['name']}】 - {orientation}\n\n"
        reply_text += f"🌟 牌面描述：\n{card['description']}\n\n"
        reply_text += f"🔮 {orientation}含義：\n{meaning}\n\n"
        reply_text += f"元素：{card['element']} | 序號：{card['numeral']}"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="您好！我是您的塔羅占卜師。請輸入「占卜」或「抽牌」來開始您的每日指引。")
        )