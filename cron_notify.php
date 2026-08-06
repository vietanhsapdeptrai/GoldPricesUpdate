<?php
// Tắt hiển thị lỗi thô ra màn hình
ini_set('display_errors', 0);
error_reporting(0);

// ===================================================
// 1. THÔNG TIN BOT TELEGRAM CỦA BẠN
// ===================================================
$botToken = "8359797934:AAGE5fnJ7GYya_cmNuSVcSXjeF_FlaRIbiA";
$chatId   = "5333698491";

// Đường dẫn file dữ liệu
$dataFile   = __DIR__ . '/data.json';
$configFile = __DIR__ . '/config.json';

// Kiểm tra dữ liệu
$assets = file_exists($dataFile) ? (json_decode(file_get_contents($dataFile), true) ?? []) : [];
$config = file_exists($configFile) ? (json_decode(file_get_contents($configFile), true) ?? ['manual_price' => 0]) : ['manual_price' => 0];

if (empty($assets)) {
    exit("⚠️ Chưa có dữ liệu mua vàng nào trong file data.json!");
}

// ===================================================
// 2. TÍNH GIÁ VÀNG HIỆN TẠI (ĐƠN VỊ: CHỈ)
// ===================================================
function getGoldPricePerChi($manualPrice) {
    if ($manualPrice > 0) return $manualPrice;

    try {
        $sources = [
            'https://vnexpress.net/rss/gia-vang.rss',
            'https://sjc.com.vn/xml/tygia.xml'
        ];

        foreach ($sources as $url) {
            $opts = [
                'http' => [
                    'method' => "GET",
                    'header' => "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n",
                    'timeout' => 3
                ]
            ];
            $context = stream_context_create($opts);
            $content = @file_get_contents($url, false, $context);
            
            if ($content) {
                $xml = @simplexml_load_string($content);
                if ($xml) {
                    foreach ($xml->xpath('//item') as $item) {
                        $sellAttr = (string)$item['sell'];
                        if (!empty($sellAttr)) {
                            $priceVal = (float)str_replace([',', '.'], '', $sellAttr);
                            if ($priceVal > 10000000) return $priceVal / 10;
                        }
                    }
                }
            }
        }
    } catch (Exception $e) {}

    return 14270000; // Giá mặc định sát thực tế
}

$currentPrice = getGoldPricePerChi($config['manual_price']);
$isManual = $config['manual_price'] > 0;

// ===================================================
// 3. TỔNG HỢP BÁO CÁO TÀI SẢN
// ===================================================
$totalQty = 0;
$totalCost = 0;
$detailsText = "";

foreach ($assets as $item) {
    $qty = (float)$item['quantity'];
    $buyP = (float)$item['buy_price'];
    $cost = $qty * $buyP;
    $valNow = $qty * $currentPrice;
    $profit = $valNow - $cost;

    $totalQty += $qty;
    $totalCost += $cost;

    $itemIcon = $profit >= 0 ? "🟢" : "🔴";
    $dateStr = date('d/m/Y', strtotime($item['date']));
    $noteStr = !empty($item['note']) ? " ({$item['note']})" : "";

    $detailsText .= "▫️ *{$dateStr}*{$noteStr}: `{$qty} chỉ`\n";
    $detailsText .= "   • Lời/Lãi: {$itemIcon} *" . ($profit >= 0 ? '+' : '') . number_format($profit) . " đ*\n";
}

$totalValue = $totalQty * $currentPrice;
$totalProfit = $totalValue - $totalCost;
$profitMargin = $totalCost > 0 ? ($totalProfit / $totalCost) * 100 : 0;

$statusIcon = $totalProfit >= 0 ? "🎉" : "📉";
$priceTypeStr = $isManual ? "(Thủ công)" : "(Tự động)";

// Soạn tin nhắn Telegram
$msg  = "🏆 *BÁO CÁO TÀI SẢN VÀNG 9999* 🏆\n";
$msg .= "───────────────────────\n";
$msg .= "💵 *Giá hiện tại:* `" . number_format($currentPrice) . " VNĐ/chỉ` _{$priceTypeStr}_\n\n";
$msg .= "📋 *CHI TIẾT:*\n{$detailsText}";
$msg .= "───────────────────────\n";
$msg .= "💼 *TỔNG KẾT DANH MỤC:*\n";
$msg .= "• Tổng số lượng: *" . number_format($totalQty, 1) . " chỉ*\n";
$msg .= "• Tổng vốn đầu tư: `" . number_format($totalCost) . " VNĐ`\n";
$msg .= "• Giá trị hiện tại: `" . number_format($totalValue) . " VNĐ`\n";
$msg .= "• Tổng Lời/Lãi: {$statusIcon} *" . ($totalProfit >= 0 ? '+' : '') . number_format($totalProfit) . " VNĐ* (`" . sprintf("%+.2f", $profitMargin) . "%`)\n";

// ===================================================
// 4. GỬI TELEGRAM (TỰ ĐỘNG CHUYỂN PROXY NẾU BỊ CHẶN)
// ===================================================
$endpoints = [
    "https://api.telegram.org/bot{$botToken}/sendMessage",
    "https://telegram-bot-api.vercel.app/bot{$botToken}/sendMessage",
    "https://tele.m3o.app/bot{$botToken}/sendMessage"
];

$success = false;
$lastError = "";

foreach ($endpoints as $url) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query([
        'chat_id' => $chatId,
        'text' => $msg,
        'parse_mode' => 'Markdown'
    ]));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 8);

    $response = curl_exec($ch);
    $err = curl_error($ch);
    curl_close($ch);

    if ($response && empty($err)) {
        $resData = json_decode($response, true);
        if (isset($resData['ok']) && $resData['ok'] === true) {
            $success = true;
            break;
        }
    }
    $lastError = $err ?: "Proxy không phản hồi";
}

if ($success) {
    echo "✅ Đã gửi báo cáo giá vàng tới Telegram thành công!";
} else {
    echo "❌ Lỗi kết nối: " . $lastError;
}
