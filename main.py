import json
import os
import urllib.request
from flask import Flask

app = Flask(__name__)


def send_gold_report():
  bot_token = '8359797934:AAGE5fnJ7GYya_cmNuSVcSXjeF_FlaRIbiA'
  chat_id = '5333698491'
  data_url = 'https://hatrerost.free.nf/giaVang.php?get_json=1'

  try:
    # 1. Lấy dữ liệu từ InfinityFree
    req = urllib.request.Request(
        data_url, headers={'User-Agent': 'Mozilla/5.0'}
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode())

    assets = data.get('assets', [])
    config = data.get('config', {})

    if not assets:
      return '⚠️ Chưa có dữ liệu mua vàng.'

    # 2. Lấy giá hiện tại
    current_price = config.get('manual_price', 0)
    if current_price <= 0:
      current_price = 14270000  # Giá mặc định

    # 3. Tính toán
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

    # 4. Soạn tin nhắn Telegram
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

    # 5. Gửi sang Telegram
    tele_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = json.dumps(
        {'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'}
    ).encode('utf-8')
    tele_req = urllib.request.Request(
        tele_url, data=payload, headers={'Content-Type': 'application/json'}
    )
    urllib.request.urlopen(tele_req)
    return '✅ Đã gửi báo cáo giá vàng tới Telegram thành công!'
  except Exception as e:
    return f'❌ Lỗi: {str(e)}'


@app.route('/')
def home():
  return send_gold_report()


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)
