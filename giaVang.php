<?php
// File lưu dữ liệu
$dataFile = 'data.json';
$configFile = 'config.json';

// Tự động khởi tạo các file dữ liệu nếu chưa có
if (!file_exists($dataFile)) {
    file_put_contents($dataFile, json_encode([]));
}
if (!file_exists($configFile)) {
    file_put_contents($configFile, json_encode(['manual_price' => 0]));
}

// Đọc dữ liệu
$assets = json_decode(file_get_contents($dataFile), true) ?? [];
$config = json_decode(file_get_contents($configFile), true) ?? ['manual_price' => 0];

// Lấy đường dẫn chính file này để redirect không bị về trang chủ Resort
$currentUrl = $_SERVER['PHP_SELF'];

// ===================================================
// 1. XỬ LÝ FORM: CẬP NHẬT GIÁ VÀNG THỦ CÔNG
// ===================================================
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'update_custom_price') {
    $customPrice = (float)($_POST['custom_price'] ?? 0);
    $config['manual_price'] = $customPrice;
    file_put_contents($configFile, json_encode($config, JSON_PRETTY_PRINT));
    header('Location: ' . $currentUrl);
    exit;
}

// Xóa giá tùy chỉnh (Quay lại dùng giá tự động)
if (isset($_GET['reset_price'])) {
    $config['manual_price'] = 0;
    file_put_contents($configFile, json_encode($config, JSON_PRETTY_PRINT));
    header('Location: ' . $currentUrl);
    exit;
}

// ===================================================
// 2. XỬ LÝ FORM: THÊM TÀI SẢN MỚI (ĐƠN VỊ: CHỈ)
// ===================================================
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'add') {
    $newAsset = [
        'id' => time(),
        'date' => $_POST['date'] ?? date('Y-m-d'),
        'quantity' => (float)($_POST['quantity'] ?? 0),   // Số lượng (CHỈ)
        'buy_price' => (float)($_POST['buy_price'] ?? 0), // Giá mua / 1 CHỈ (VNĐ)
        'note' => htmlspecialchars($_POST['note'] ?? '')
    ];
    
    if ($newAsset['quantity'] > 0 && $newAsset['buy_price'] > 0) {
        $assets[] = $newAsset;
        file_put_contents($dataFile, json_encode($assets, JSON_PRETTY_PRINT));
    }
    header('Location: ' . $currentUrl);
    exit;
}

// ===================================================
// 3. XỬ LÝ FORM: XÓA TÀI SẢN
// ===================================================
if (isset($_GET['delete'])) {
    $deleteId = (int)$_GET['delete'];
    $assets = array_filter($assets, fn($item) => $item['id'] !== $deleteId);
    file_put_contents($dataFile, json_encode(array_values($assets), JSON_PRETTY_PRINT));
    header('Location: ' . $currentUrl);
    exit;
}

// ===================================================
// 4. HÀM XÁC ĐỊNH GIÁ VÀNG HIỆN TẠI (CHỈ)
// ===================================================
function getGold9999PricePerChi($manualPrice) {
    if ($manualPrice > 0) {
        return $manualPrice;
    }

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
                            if ($priceVal > 10000000) { 
                                return $priceVal / 10;
                            }
                        }
                    }
                }
            }
        }
    } catch (Exception $e) {}

    return 14270000; 
}

$currentPricePerChi = getGold9999PricePerChi($config['manual_price']);
$isManual = $config['manual_price'] > 0;

// ===================================================
// 5. TÍNH TỔNG DANH MỤC
// ===================================================
$totalQuantityChi = 0;
$totalCost = 0;

foreach ($assets as $item) {
    $totalQuantityChi += $item['quantity'];
    $totalCost += ($item['quantity'] * $item['buy_price']);
}

$totalValue = $totalQuantityChi * $currentPricePerChi;
$totalProfit = $totalValue - $totalCost;
$profitMargin = $totalCost > 0 ? ($totalProfit / $totalCost) * 100 : 0;
?>

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quản Lý Tài Sản Vàng 9999</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-100 min-h-screen p-4 md:p-8 font-sans">
    <div class="max-w-5xl mx-auto space-y-6">
        
        <!-- HEADER & CÀI ĐẶT GIÁ -->
        <div class="bg-white rounded-xl shadow-sm p-6 flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
                <h1 class="text-2xl font-bold text-slate-800">🏆 Quản Lý Tài Sản Vàng 9999</h1>
                <p class="text-slate-500 text-sm mt-1">Đồng bộ theo đơn vị <b>CHỈ</b> & Tùy chỉnh giá thị trường</p>
            </div>
            
            <div class="flex flex-col items-end gap-2">
                <div class="bg-amber-50 border border-amber-200 rounded-lg p-3 text-right w-full md:w-auto">
                    <div class="flex items-center justify-end gap-2">
                        <span class="text-xs text-amber-700 font-semibold block">GIÁ VÀNG ĐANG ÁP DỤNG</span>
                        <?php if ($isManual): ?>
                            <span class="bg-amber-200 text-amber-800 text-[10px] font-bold px-1.5 py-0.5 rounded">Thủ công</span>
                        <?php else: ?>
                            <span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-1.5 py-0.5 rounded">Tự động</span>
                        <?php endif; ?>
                    </div>
                    <span class="text-2xl font-black text-amber-600"><?= number_format($currentPricePerChi) ?> VNĐ</span>
                    <span class="text-xs text-slate-500 font-medium block">/ chỉ</span>
                </div>

                <!-- Form điều chỉnh giá thủ công -->
                <form action="<?= $currentUrl ?>" method="POST" class="flex items-center gap-2 text-xs">
                    <input type="hidden" name="action" value="update_custom_price">
                    <input type="number" name="custom_price" placeholder="Nhập giá mới (VNĐ/chỉ)..." 
                           class="border rounded-lg px-2 py-1 text-slate-700 w-44 focus:outline-blue-500" required>
                    <button type="submit" class="bg-slate-800 hover:bg-slate-900 text-white font-medium px-3 py-1 rounded-lg transition">
                        Set Giá
                    </button>
                    <?php if ($isManual): ?>
                        <a href="<?= $currentUrl ?>?reset_price=1" class="text-rose-500 hover:underline font-semibold ml-1">Dùng giá tự động</a>
                    <?php endif; ?>
                </form>
            </div>
        </div>

        <!-- BẢNG TỔNG QUAN TÀI SẢN -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 border-blue-500">
                <span class="text-xs font-semibold text-slate-400 uppercase">Tổng số lượng</span>
                <p class="text-2xl font-bold text-slate-800 mt-1"><?= number_format($totalQuantityChi, 2) ?> <span class="text-sm font-normal text-slate-500">chỉ</span></p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 border-slate-500">
                <span class="text-xs font-semibold text-slate-400 uppercase">Tổng vốn đầu tư</span>
                <p class="text-2xl font-bold text-slate-800 mt-1"><?= number_format($totalCost) ?> <span class="text-xs text-slate-500">đ</span></p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 border-indigo-500">
                <span class="text-xs font-semibold text-slate-400 uppercase">Giá trị hiện tại</span>
                <p class="text-2xl font-bold text-slate-800 mt-1"><?= number_format($totalValue) ?> <span class="text-xs text-slate-500">đ</span></p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border-l-4 <?= $totalProfit >= 0 ? 'border-emerald-500' : 'border-rose-500' ?>">
                <span class="text-xs font-semibold text-slate-400 uppercase">Tổng Lời / Lãi</span>
                <p class="text-2xl font-bold <?= $totalProfit >= 0 ? 'text-emerald-600' : 'text-rose-600' ?> mt-1">
                    <?= $totalProfit >= 0 ? '+' : '' ?><?= number_format($totalProfit) ?> <span class="text-xs">đ</span>
                </p>
                <span class="text-xs <?= $totalProfit >= 0 ? 'text-emerald-600' : 'text-rose-600' ?> font-semibold">
                    (<?= sprintf("%+.2f", $profitMargin) ?>%)
                </span>
            </div>
        </div>

        <!-- FORM NHẬP LIỆU & DANH SÁCH -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            <!-- FORM THÊM MỚI (BÊN TRÁI) -->
            <div class="bg-white p-6 rounded-xl shadow-sm h-fit">
                <h2 class="text-lg font-bold text-slate-800 mb-4 pb-2 border-b">➕ Thêm Lượt Mua Vàng</h2>
                <form action="<?= $currentUrl ?>" method="POST" class="space-y-4">
                    <input type="hidden" name="action" value="add">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Ngày mua</label>
                        <input type="date" name="date" value="<?= date('Y-m-d') ?>" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-blue-500" required>
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

            <!-- BẢNG DANH SÁCH TÀI SẢN (BÊN PHẢI) -->
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
                            <?php if (empty($assets)): ?>
                                <tr>
                                    <td colspan="5" class="text-center p-6 text-slate-400">Chưa có dữ liệu. Hãy nhập lượt mua đầu tiên!</td>
                                </tr>
                            <?php else: ?>
                                <?php foreach ($assets as $item): 
                                    $cost = $item['quantity'] * $item['buy_price'];
                                    $valNow = $item['quantity'] * $currentPricePerChi;
                                    $profit = $valNow - $cost;
                                ?>
                                    <tr class="hover:bg-slate-50">
                                        <td class="p-3">
                                            <span class="font-medium text-slate-800"><?= date('d/m/Y', strtotime($item['date'])) ?></span>
                                            <?php if (!empty($item['note'])): ?>
                                                <span class="block text-xs text-slate-400"><?= $item['note'] ?></span>
                                            <?php endif; ?>
                                        </td>
                                        <td class="p-3 font-semibold text-slate-800"><?= $item['quantity'] ?> chỉ</td>
                                        <td class="p-3"><?= number_format($item['buy_price']) ?> đ</td>
                                        <td class="p-3 font-semibold <?= $profit >= 0 ? 'text-emerald-600' : 'text-rose-600' ?>">
                                            <?= $profit >= 0 ? '+' : '' ?><?= number_format($profit) ?> đ
                                        </td>
                                        <td class="p-3 text-center">
                                            <a href="<?= $currentUrl ?>?delete=<?= $item['id'] ?>" onclick="return confirm('Bạn có chắc muốn xóa lượt mua này?')" class="text-rose-500 hover:text-rose-700 text-xs font-semibold">Xóa</a>
                                        </td>
                                    </tr>
                                <?php endforeach; ?>
                            <?php endif; ?>
                        </tbody>
                    </table>
                </div>
            </div>

        </div>

    </div>
</body>
</html>
