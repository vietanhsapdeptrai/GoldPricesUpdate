import json
import os
import urllib.parse
import urllib.request
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

DATA_FILE = 'data.json'
CONFIG_FILE = 'config.json'

# ===================================================
# THÔNG TIN BẢO MẬT & KẾT NỐI
# ===================================================
# 1. Pushover Credentials (Dành cho iPhone)
PUSHOVER_USER_KEY = 'urkreqgfxzi1vxj6cya3vhfdkiiqq6'
PUSHOVER_APP_TOKEN = 'akp3knry9sbuubxumifqbu21etmux6'

# 2. Telegram Credentials
BOT_TOKEN = '8359797934:AAGE5fnJ7GYya_cmNuSVcSXjeF_FlaRIbiA'
ALLOWED_CHAT_ID = '5333698491'


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


def save_data(assets, config):
  with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(assets, f, ensure_ascii=False, indent=2)
  with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)


def generate_reports():
  assets, config = load_data()
  if not assets:
    msg_short = '⚠️ Chưa có dữ liệu mua vàng nào trong danh mục.'
    return msg_short, msg_short

  current_price = config.get('manual_price', 0)
  if current_price <= 0:
    current_price = 14270000

  total_qty = sum(item['quantity'] for item in assets)
  total_cost = sum(item['quantity'] * item['buy_price'] for item in assets)
  total_val = total_qty * current_price
  total_profit = total_val - total_cost
  margin = (total_profit / total_cost * 100) if total_cost > 0 else 0

  # Dạng văn bản có Markdown (cho Telegram)
  details_md = ''
  # Dạng văn bản thuần (cho Pushover)
  details_plain = ''

  for item in assets:
    cost = item['quantity'] * item['buy_price']
    val = item['quantity'] * current_price
    profit = val - cost
    icon = '🟢' if profit >= 0 else '🔴'

    details_md += (
        f"▫️ *{item['date']}*: `{item['quantity']} chỉ`\n   • Lời/Lãi: {icon}"
        f' *{profit:+,.0f} đ*\n'
    )
    details_plain += (
        f"▫️ {item['date']}: {item['quantity']} chỉ\n   Lời/Lãi: {icon}"
        f' {profit:+,.0f} đ\n'
    )

  icon_total = '🎉' if total_profit >= 0 else '📉'

  # Message Telegram
  msg_telegram = (
      '🏆 *BÁO CÁO TÀI SẢN VÀNG 9999* 🏆\n'
      '───────────────────────\n'
      f'💵 *Giá hiện tại:* `{current_price:,.0f} VNĐ/chỉ`\n\n'
      f'📋 *CHI TIẾT:*\n{details_md}'
      '───────────────────────\n'
      '💼 *TỔNG KẾT DANH MỤC:*\n'
      f'• Tổng số lượng: *{total_qty:.1f} chỉ*\n'
      f'• Tổng vốn đầu tư: `{total_cost:,.0f} VNĐ`\n'
      f'• Giá trị hiện tại: `{total_val:,.0f} VNĐ`\n'
      f'• Tổng Lời/Lãi: {icon_total} *{total_profit:+,.0f} VNĐ*'
      f' (`{margin:+.2f}%`)\n'
  )

  # Message Pushover
  msg_pushover = (
      f'💵 Giá hiện tại: {current_price:,.0f} đ/chỉ\n\n'
      f'📋 CHI TIẾT:\n{details_plain}'
      f'───────────────────────\n'
      f'💼 TỔNG KẾT DANH MỤC:\n'
      f'• Số lượng: {total_qty:.1f} chỉ\n'
      f'• Tổng vốn: {total_cost:,.0f} VNĐ\n'
      f'• Giá trị hiện tại: {total_val:,.0f} VNĐ\n'
      f'• Lời/Lãi: {icon_total} {total_profit:+,.0f} VNĐ ({margin:+.2f}%)'
  )

  return msg_telegram, msg_pushover


# GỬI PUSHOVER
def send_pushover(title, text):
  try:
    url = 'https://api.pushover.net/1/messages.json'
    payload = urllib.parse.urlencode({
        'token': PUSHOVER_APP_TOKEN,
        'user': PUSHOVER_USER_KEY,
        'title': title,
        'message': text,
        'sound': 'cashregister',
        'url': 'https://goldpricesupdate.onrender.com',
        'url_title': 'Mở Web Quản Lý Vàng',
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload)
    with urllib.request.urlopen(req, timeout=10) as res:
      pass
  except Exception as e:
    print(f'Lỗi gửi Pushover: {e}')


# GỬI TELEGRAM
def send_telegram(chat_id_to_send, text):
  try:
    tele_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = json.dumps({
        'chat_id': chat_id_to_send,
        'text': text,
        'parse_mode': 'Markdown',
    }).encode('utf-8')
    tele_req = urllib.request.Request(
        tele_url, data=payload, headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(tele_req, timeout=10) as res:
      pass
  except Exception as e:
    print(f'Lỗi gửi Telegram: {e}')


# HTML TEMPLATE
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quản Lý Tài Sản Vàng 9999</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-100 min-h-screen p-4 md:p-8 font-sans">
    <div class="max-w-5xl mx-auto space-y-6">
        <div class="bg-white rounded-xl shadow-sm p-6 flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
                <h1 class="text-2xl font-bold text-slate-800">🏆 Quản Lý Tài Sản Vàng 9999</h1>
                <p class="text-slate-500 text-sm mt-1">Đồng bộ theo đơn vị <b>CHỈ</b> & Tùy chỉnh giá thị trường</p>
            </div>
            
            <div class="flex flex-col items-end gap-2">
                <div class="bg-amber-50 border border-amber-200 rounded-lg p-3 text-right w-full md:w-auto">
                    <span class="text-xs text-amber-700 font-semibold block">GIÁ VÀNG ĐANG ÁP DỤNG</span>
                    <span class="text-2xl font-black text-amber-600">{{ "{:,.0f}".format(current_price) }} VNĐ</span>
                    <span class="text-xs text-slate-500 font-medium block">/ chỉ</span>
                </div>

                <form action="/update_price" method="POST" class="flex items-center gap-2 text-xs">
                    <input type="number" name="custom_price" placeholder="Nhập giá mới (VNĐ/chỉ)..." 
                           class="border rounded-lg px-2 py-1 text-slate-700 w-44 focus:outline-blue-500" required>
                    <button type="submit" class="bg-slate-800 text-white font-medium px-3 py-1 rounded-lg">Set Giá</button>
                    {% if config.manual_price > 0 %}
                        <a href="/reset_price" class="text-rose-500 font-semibold ml-1">Dùng giá tự động</a>
                    {% endif %}
                </form>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 border-blue-500">
                <span class="text-xs font-semibold text-slate-400 uppercase">Tổng số lượng</span>
                <p class="text-2xl font-bold text-slate-800 mt-1">{{ "{:,.1f}".format(total_qty) }} <span class="text-sm font-normal text-slate-500">chỉ</span></p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 border-slate-500">
                <span class="text-xs font-semibold text-slate-400 uppercase">Tổng vốn đầu tư</span>
                <p class="text-2xl font-bold text-slate-800 mt-1">{{ "{:,.0f}".format(total_cost) }} <span class="text-xs text-slate-500">đ</span></p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 border-indigo-500">
                <span class="text-xs font-semibold text-slate-400 uppercase">Giá trị hiện tại</span>
                <p class="text-2xl font-bold text-slate-800 mt-1">{{ "{:,.0f}".format(total_val) }} <span class="text-xs text-slate-500">đ</span></p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 {% if total_profit >= 0 %}border-emerald-500{% else %}border-rose-500{% endif %}">
                <span class="text-xs font-semibold text-slate-400 uppercase">Tổng Lời / Lãi</span>
                <p class="text-2xl font-bold {% if total_profit >= 0 %}text-emerald-600{% else %}text-rose-600{% endif %} mt-1">
                    {% if total_profit >= 0 %}+{% endif %}{{ "{:,.0f}".format(total_profit) }} <span class="text-xs">đ</span>
                </p>
                <span class="text-xs {% if total_profit >= 0 %}text-emerald-600{% else %}text-rose-600{% endif %} font-semibold">
                    ({{ "{:+.2f}".format(margin) }}%)
                </span>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="bg-white p-6 rounded-xl shadow-sm h-fit">
                <h2 class="text-lg font-bold text-slate-800 mb-4 pb-2 border-b">➕ Thêm Lượt Mua Vàng</h2>
                <form action="/add" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Ngày mua</label>
                        <input type="date" name="date" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-blue-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Số lượng (Chỉ)</label>
                        <input type="number" step="0.1" name="quantity" placeholder="Ví dụ: 1 hoặc 0.5" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-blue-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Giá mua / 1 chỉ (VNĐ)</label>
                        <input type="number" name="buy_price" placeholder="Ví dụ: 18510000" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-blue-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Ghi chú (Tùy chọn)</label>
                        <input type="text" name="note" placeholder="Ví dụ: Mua nhẫn Doji..." class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-blue-500">
                    </div>
                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg text-sm transition">
                        Lưu Thông Tin
                    </button>
                </form>
            </div>

            <div class="lg:col-span-2 bg-white rounded-xl shadow-sm p-6">
                <h2 class="text-lg font-bold text-slate-800 mb-4 pb-2 border-b">📋 Chi Tiết Lịch Sử Mua</h2>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-slate-50 text-slate-500 uppercase text-[11px]">
                            <tr>
                                <th class="p-3">Ngày</th>
                                <th class="p-3">Số lượng</th>
                                <th class="p-3">Giá mua/Chỉ</th>
                                <th class="p-3">Lời / Lãi</th>
                                <th class="p-3 text-center">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y">
                            {% if not assets %}
                                <tr>
                                    <td colspan="5" class="text-center p-6 text-slate-400">Chưa có dữ liệu. Hãy nhập lượt mua đầu tiên!</td>
                                </tr>
                            {% else %}
                                {% for item in assets %}
                                    {% set cost = item.quantity * item.buy_price %}
                                    {% set val = item.quantity * current_price %}
                                    {% set profit = val - cost %}
                                    <tr class="hover:bg-slate-50">
                                        <td class="p-3">
                                            <span class="font-medium text-slate-800">{{ item.date }}</span>
                                            {% if item.note %}<span class="block text-xs text-slate-400">{{ item.note }}</span>{% endif %}
                                        </td>
                                        <td class="p-3 font-semibold text-slate-800">{{ item.quantity }} chỉ</td>
                                        <td class="p-3">{{ "{:,.0f}".format(item.buy_price) }} đ</td>
                                        <td class="p-3 font-semibold {% if profit >= 0 %}text-emerald-600{% else %}text-rose-600{% endif %}">
                                            {% if profit >= 0 %}+{% endif %}{{ "{:,.0f}".format(profit) }} đ
                                        </td>
                                        <td class="p-3 text-center">
                                            <a href="/delete/{{ loop.index0 }}" class="text-rose-500 font-semibold text-xs">Xóa</a>
                                        </td>
                                    </tr>
                                {% endfor %}
                            {% endif %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def home():
  assets, config = load_data()
  current_price = config.get('manual_price', 0)
  if current_price <= 0:
    current_price = 14270000

  total_qty = sum(item['quantity'] for item in assets)
  total_cost = sum(item['quantity'] * item['buy_price'] for item in assets)
  total_val = total_qty * current_price
  total_profit = total_val - total_cost
  margin = (total_profit / total_cost * 100) if total_cost > 0 else 0

  return render_template_string(
      HTML_TEMPLATE,
      assets=assets,
      config=config,
      current_price=current_price,
      total_qty=total_qty,
      total_cost=total_cost,
      total_val=total_val,
      total_profit=total_profit,
      margin=margin,
  )


@app.route('/add', methods=['POST'])
def add_asset():
  assets, config = load_data()
  new_asset = {
      'date': request.form.get('date'),
      'quantity': float(request.form.get('quantity', 0)),
      'buy_price': float(request.form.get('buy_price', 0)),
      'note': request.form.get('note', ''),
  }
  if new_asset['quantity'] > 0 and new_asset['buy_price'] > 0:
    assets.append(new_asset)
    save_data(assets, config)
  return redirect(url_for('home'))


@app.route('/delete/<int:index>')
def delete_asset(index):
  assets, config = load_data()
  if 0 <= index < len(assets):
    assets.pop(index)
    save_data(assets, config)
  return redirect(url_for('home'))


@app.route('/update_price', methods=['POST'])
def update_price():
  assets, config = load_data()
  config['manual_price'] = float(request.form.get('custom_price', 0))
  save_data(assets, config)
  return redirect(url_for('home'))


@app.route('/reset_price')
def reset_price():
  assets, config = load_data()
  config['manual_price'] = 0
  save_data(assets, config)
  return redirect(url_for('home'))


# TELEGRAM WEBHOOK
@app.route('/webhook', methods=['POST'])
def telegram_webhook():
  try:
    update = request.get_json(force=True, silent=True) or {}
    if 'message' in update:
      message = update['message']
      text = message.get('text', '').strip()
      chat_id = str(message.get('chat', {}).get('id'))

      if chat_id != ALLOWED_CHAT_ID:
        send_telegram(
            chat_id, '⚠️ Rất tiếc, bạn không có quyền truy cập bot này!'
        )
        return 'OK', 200

      if text.startswith('/'):
        msg_tg, _ = generate_reports()
        send_telegram(chat_id, msg_tg)
  except Exception as e:
    print(f'Lỗi Webhook: {e}')

  return 'OK', 200


# CRON CHẠY TỰ ĐỘNG HÀNG NGÀY (GỬI SONG SONG CẢ PUSHOVER & TELEGRAM)
@app.route('/cron')
def cron_send():
  msg_tg, msg_push = generate_reports()

  # 1. Gửi qua Pushover (về iPhone)
  send_pushover('🏆 BÁO CÁO TÀI SẢN VÀNG', msg_push)

  # 2. Gửi qua Telegram
  send_telegram(ALLOWED_CHAT_ID, msg_tg)

  return '✅ Đã gửi báo cáo song song tới cả Pushover và Telegram thành công!'


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)
