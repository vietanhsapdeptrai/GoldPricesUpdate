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
PUSHOVER_USER_KEY = 'THAY_USER_KEY_PUSHOVER_CUA_BAN'
PUSHOVER_APP_TOKEN = 'THAY_APP_TOKEN_PUSHOVER_CUA_BAN'

BOT_TOKEN = '8359797934:AAGE5fnJ7GYya_cmNuSVcSXjeF_FlaRIbiA'
ALLOWED_CHAT_ID = '5333698491'


def load_data():
  if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
      json.dump([], f)
  if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
      json.dump({'gold_price': 14270000, 'silver_price': 1200000}, f)

  with open(DATA_FILE, 'r', encoding='utf-8') as f:
    assets = json.load(f)
  with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

  # Mặc định cấu hình giá nếu chưa có
  if 'gold_price' not in config:
    config['gold_price'] = 14270000
  if 'silver_price' not in config:
    config['silver_price'] = 1200000

  return assets, config


def save_data(assets, config):
  with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(assets, f, ensure_ascii=False, indent=2)
  with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)


def generate_reports():
  assets, config = load_data()
  if not assets:
    msg_empty = '⚠️ Chưa có dữ liệu mua tài sản nào.'
    return msg_empty, msg_empty

  gold_price = config.get('gold_price', 14270000)
  silver_price = config.get('silver_price', 1200000)

  total_cost_all = 0
  total_val_all = 0

  details_md = ''
  details_plain = ''

  for item in assets:
    asset_type = item.get('type', 'gold')
    cur_price = gold_price if asset_type == 'gold' else silver_price
    unit_name = 'chỉ' if asset_type == 'gold' else 'lượng'
    type_name = 'Vàng 9999' if asset_type == 'gold' else 'Bạc 999'

    cost = item['quantity'] * item['buy_price']
    val = item['quantity'] * cur_price
    profit = val - cost

    total_cost_all += cost
    total_val_all += val

    icon = '🟢' if profit >= 0 else '🔴'

    details_md += (
        f"▫️ *{item['date']}* ({type_name}): `{item['quantity']} {unit_name}`\n "
        f'  • Lời/Lãi: {icon} *{profit:+,.0f} đ*\n'
    )
    details_plain += (
        f"▫️ {item['date']} ({type_name}): {item['quantity']} {unit_name}\n   "
        f'Lời/Lãi: {icon} {profit:+,.0f} đ\n'
    )

  total_profit_all = total_val_all - total_cost_all
  margin_all = (
      (total_profit_all / total_cost_all * 100) if total_cost_all > 0 else 0
  )
  icon_total = '🎉' if total_profit_all >= 0 else '📉'

  # Bản tin nhắn Telegram
  msg_telegram = (
      '🏆 *BÁO CÁO TÀI SẢN VÀNG & BẠC* 🏆\n'
      '───────────────────────\n'
      f'💵 *Giá Vàng hiện tại:* `{gold_price:,.0f} đ/chỉ`\n'
      f'⚪ *Giá Bạc hiện tại:* `{silver_price:,.0f} đ/lượng`\n\n'
      f'📋 *CHI TIẾT DANH MỤC:*\n{details_md}'
      '───────────────────────\n'
      '💼 *TỔNG KẾT TOÀN BỘ:*\n'
      f'• Tổng vốn đầu tư: `{total_cost_all:,.0f} VNĐ`\n'
      f'• Giá trị hiện tại: `{total_val_all:,.0f} VNĐ`\n'
      f'• Tổng Lời/Lãi: {icon_total} *{total_profit_all:+,.0f} VNĐ*'
      f' (`{margin_all:+.2f}%`)\n'
  )

  # Bản tin nhắn Pushover
  msg_pushover = (
      f'💵 Giá Vàng: {gold_price:,.0f} đ/chỉ | ⚪ Giá Bạc:'
      f' {silver_price:,.0f} đ/lượng\n\n'
      f'📋 CHI TIẾT:\n{details_plain}'
      f'───────────────────────\n'
      f'💼 TỔNG KẾT DANH MỤC:\n'
      f'• Tổng vốn: {total_cost_all:,.0f} VNĐ\n'
      f'• Giá trị hiện tại: {total_val_all:,.0f} VNĐ\n'
      f'• Lời/Lãi: {icon_total} {total_profit_all:+,.0f} VNĐ'
      f' ({margin_all:+.2f}%)'
  )

  return msg_telegram, msg_pushover


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
        'url_title': 'Mở Web Quản Lý',
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload)
    with urllib.request.urlopen(req, timeout=10) as res:
      pass
  except Exception as e:
    print(f'Lỗi gửi Pushover: {e}')


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


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quản Lý Tài Sản Vàng & Bạc</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-100 min-h-screen p-4 md:p-8 font-sans">
    <div class="max-w-5xl mx-auto space-y-6">
        
        <div class="bg-white rounded-xl shadow-sm p-6 flex flex-col lg:flex-row justify-between items-center gap-4">
            <div>
                <h1 class="text-2xl font-bold text-slate-800">🏆 Quản Lý Tài Sản Vàng & Bạc</h1>
                <p class="text-slate-500 text-sm mt-1">Vàng (Đơn vị: <b>Chỉ</b>) | Bạc (Đơn vị: <b>Lượng</b>)</p>
            </div>
            
            <form action="/update_prices" method="POST" class="flex flex-wrap items-center gap-3">
                <div class="bg-amber-50 border border-amber-200 rounded-lg p-2 text-right">
                    <span class="text-[10px] text-amber-700 font-semibold block">GIÁ VÀNG (VNĐ/CHỈ)</span>
                    <input type="number" name="gold_price" value="{{ config.gold_price }}" class="w-28 text-right font-bold text-amber-600 bg-transparent focus:outline-none">
                </div>
                <div class="bg-slate-100 border border-slate-300 rounded-lg p-2 text-right">
                    <span class="text-[10px] text-slate-600 font-semibold block">GIÁ BẠC (VNĐ/LƯỢNG)</span>
                    <input type="number" name="silver_price" value="{{ config.silver_price }}" class="w-28 text-right font-bold text-slate-700 bg-transparent focus:outline-none">
                </div>
                <button type="submit" class="bg-slate-800 text-white font-medium px-4 py-3 rounded-lg text-xs">Cập Nhật Giá</button>
            </form>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 border-slate-500">
                <span class="text-xs font-semibold text-slate-400 uppercase">Tổng vốn đầu tư</span>
                <p class="text-2xl font-bold text-slate-800 mt-1">{{ "{:,.0f}".format(total_cost_all) }} <span class="text-xs text-slate-500">đ</span></p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 border-indigo-500">
                <span class="text-xs font-semibold text-slate-400 uppercase">Giá trị hiện tại</span>
                <p class="text-2xl font-bold text-slate-800 mt-1">{{ "{:,.0f}".format(total_val_all) }} <span class="text-xs text-slate-500">đ</span></p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 {% if total_profit_all >= 0 %}border-emerald-500{% else %}border-rose-500{% endif %}">
                <span class="text-xs font-semibold text-slate-400 uppercase">Tổng Lời / Lãi</span>
                <p class="text-2xl font-bold {% if total_profit_all >= 0 %}text-emerald-600{% else %}text-rose-600{% endif %} mt-1">
                    {% if total_profit_all >= 0 %}+{% endif %}{{ "{:,.0f}".format(total_profit_all) }} <span class="text-xs">đ</span>
                </p>
                <span class="text-xs {% if total_profit_all >= 0 %}text-emerald-600{% else %}text-rose-600{% endif %} font-semibold">
                    ({{ "{:+.2f}".format(margin_all) }}%)
                </span>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="bg-white p-6 rounded-xl shadow-sm h-fit">
                <h2 class="text-lg font-bold text-slate-800 mb-4 pb-2 border-b">➕ Thêm Lượt Mua</h2>
                <form action="/add" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Loại tài sản</label>
                        <select name="type" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-blue-500">
                            <option value="gold">🥇 Vàng 9999 (Tính theo Chỉ)</option>
                            <option value="silver">⚪ Bạc 999 (Tính theo Lượng)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Ngày mua</label>
                        <input type="date" name="date" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-blue-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Số lượng</label>
                        <input type="number" step="0.01" name="quantity" placeholder="Số chỉ (Vàng) hoặc Số lượng (Bạc)" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-blue-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Giá mua / 1 Đơn vị (VNĐ)</label>
                        <input type="number" name="buy_price" placeholder="Nhập giá mua tại thời điểm đó..." class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-blue-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Ghi chú (Tùy chọn)</label>
                        <input type="text" name="note" placeholder="Ví dụ: Mua thỏi PNJ, nhẫn..." class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-blue-500">
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
                                <th class="p-3">Ngày / Loại</th>
                                <th class="p-3">Số lượng</th>
                                <th class="p-3">Giá mua</th>
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
                                    {% set cur_p = config.gold_price if item.type == 'gold' else config.silver_price %}
                                    {% set unit = 'chỉ' if item.type == 'gold' else 'lượng' %}
                                    {% set cost = item.quantity * item.buy_price %}
                                    {% set val = item.quantity * cur_p %}
                                    {% set profit = val - cost %}
                                    <tr class="hover:bg-slate-50">
                                        <td class="p-3">
                                            <span class="font-medium text-slate-800">{{ item.date }}</span>
                                            <span class="block text-xs {% if item.type == 'gold' %}text-amber-600{% else %}text-slate-500{% endif %} font-semibold">
                                                {% if item.type == 'gold' %}🥇 Vàng 9999{% else %}⚪ Bạc 999{% endif %}
                                            </span>
                                            {% if item.note %}<span class="block text-xs text-slate-400">{{ item.note }}</span>{% endif %}
                                        </td>
                                        <td class="p-3 font-semibold text-slate-800">{{ item.quantity }} {{ unit }}</td>
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
  gold_price = config.get('gold_price', 14270000)
  silver_price = config.get('silver_price', 1200000)

  total_cost_all = 0
  total_val_all = 0

  for item in assets:
    cur_p = gold_price if item.get('type') == 'gold' else silver_price
    cost = item['quantity'] * item['buy_price']
    val = item['quantity'] * cur_p
    total_cost_all += cost
    total_val_all += val

  total_profit_all = total_val_all - total_cost_all
  margin_all = (
      (total_profit_all / total_cost_all * 100) if total_cost_all > 0 else 0
  )

  return render_template_string(
      HTML_TEMPLATE,
      assets=assets,
      config=config,
      total_cost_all=total_cost_all,
      total_val_all=total_val_all,
      total_profit_all=total_profit_all,
      margin_all=margin_all,
  )


@app.route('/add', methods=['POST'])
def add_asset():
  assets, config = load_data()
  new_asset = {
      'type': request.form.get('type', 'gold'),
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


@app.route('/update_prices', methods=['POST'])
def update_prices():
  assets, config = load_data()
  config['gold_price'] = float(request.form.get('gold_price', 0))
  config['silver_price'] = float(request.form.get('silver_price', 0))
  save_data(assets, config)
  return redirect(url_for('home'))


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


@app.route('/cron')
def cron_send():
  msg_tg, msg_push = generate_reports()

  # Gửi đồng thời Pushover & Telegram
  send_pushover('🏆 BÁO CÁO TÀI SẢN VÀNG & BẠC', msg_push)
  send_telegram(ALLOWED_CHAT_ID, msg_tg)

  return (
      '✅ Đã gửi báo cáo danh mục Vàng & Bạc tới cả Pushover và Telegram thành'
      ' công!'
  )


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)
