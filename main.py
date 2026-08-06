import json
import os
import urllib.request
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

DATA_FILE = 'data.json'
CONFIG_FILE = 'config.json'
BOT_TOKEN = '8359797934:AAGE5fnJ7GYya_cmNuSVcSXjeF_FlaRIbiA'
CHAT_ID = '5333698491'


def load_data():
  if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
      json.dump([], f)
  if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
      json.dump({'manual_price': 0}, f)

  with open(DATA_FILE, 'r', encoding='utf-8') as f:
    assets = json.load(f)
  with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)
  return assets, config


def generate_report():
  assets, config = load_data()
  if not assets:
    return '⚠️ Chưa có dữ liệu mua vàng nào trong danh mục.'

  current_price = config.get('manual_price', 0)
  if current_price <= 0:
    current_price = 14270000

  total_qty = sum(item['quantity'] for item in assets)
  total_cost = sum(item['quantity'] * item['buy_price'] for item in assets)
  total_val = total_qty * current_price
  total_profit = total_val - total_cost
  margin = (total_profit / total_cost * 100) if total_cost > 0 else 0

  details = ''
  for item in assets:
    cost = item['quantity'] * item['buy_price']
    val = item['quantity'] * current_price
    profit = val - cost
    icon = '🟢' if profit >= 0 else '🔴'
    details += (
        f"▫️ *{item['date']}*: `{item['quantity']} chỉ`\n   • Lời/Lãi: {icon}"
        f' *{profit:+,.0f} đ*\n'
    )

  icon_total = '🎉' if total_profit >= 0 else '📉'

  msg = (
      '🏆 *BÁO CÁO TÀI SẢN VÀNG 9999* 🏆\n'
      '───────────────────────\n'
      f'💵 *Giá hiện tại:* `{current_price:,.0f} VNĐ/chỉ`\n\n'
      f'📋 *CHI TIẾT:*\n{details}'
      '───────────────────────\n'
      '💼 *TỔNG KẾT DANH MỤC:*\n'
      f'• Tổng số lượng: *{total_qty:.1f} chỉ*\n'
      f'• Tổng vốn đầu tư: `{total_cost:,.0f} VNĐ`\n'
      f'• Giá trị hiện tại: `{total_val:,.0f} VNĐ`\n'
      f'• Tổng Lời/Lãi: {icon_total} *{total_profit:+,.0f} VNĐ*'
      f' (`{margin:+.2f}%`)\n'
  )
  return msg


def send_telegram_msg(chat_id_to_send, text_content):
  tele_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
  payload = json.dumps({
      'chat_id': chat_id_to_send,
      'text': text_content,
      'parse_mode': 'Markdown',
  }).encode('utf-8')
  tele_req = urllib.request.Request(
      tele_url, data=payload, headers={'Content-Type': 'application/json'}
  )
  with urllib.request.urlopen(tele_req, timeout=10) as res:
    pass

# WEBHOOK LẮNG NGHE LỆNH TỪ TELEGRAM (ĐÃ KHÓA BẢO MẬT)
@app.route('/webhook', methods=['POST'])
def telegram_webhook():
  try:
    update = request.get_json(force=True, silent=True) or {}

    if 'message' in update:
      message = update['message']
      text = message.get('text', '').strip()
      chat_id = str(message.get('chat', {}).get('id'))

      # 🔒 BẢO MẬT: CHỈ PHẢN HỒI NẾU CHAT_ID KHỚP VỚI ID CỦA BẠN
      ALLOWED_CHAT_ID = "5333698491"  # ID Telegram cá nhân của bạn

      if chat_id != ALLOWED_CHAT_ID:
        # Nếu người lạ nhắn tin, bot từ chối phản hồi
        send_telegram_msg(
            chat_id, "⚠️ Rất tiếc, bạn không có quyền truy cập bot này!"
        )
        return "OK", 200

      # Nếu đúng là bạn nhắn tin:
      if text.startswith('/'):
        report_msg = generate_report()
        send_telegram_msg(chat_id, report_msg)

  except Exception as e:
    print(f"Lỗi Webhook: {e}")

  return "OK", 200

# ROUTE CRON HÀNG NGÀY
@app.route('/cron')
def cron_send():
  msg = generate_report()
  try:
    send_telegram_msg(CHAT_ID, msg)
    return '✅ Đã gửi báo cáo giá vàng tới Telegram!'
  except Exception as e:
    return f'❌ Lỗi gửi Telegram: {str(e)}'


# GIAO DIỆN WEB MANAGEMENT (Giữ nguyên các route /, /add, /delete, /update_price...)
