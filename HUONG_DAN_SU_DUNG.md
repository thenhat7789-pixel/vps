# 🎮 HƯỚNG DẪN BỘ ĐIỀU KHIỂN & AUTO ĐÁNH GAME TRÊN PC / VPS 24/7

> **TÍCH HỢP TỰ ĐỘNG KHỞI CHẠY 24/7 & TẢI GAME TRỌN GÓI TRỰC TIẾP**

---

## 📥 1. NÚT TẢI GAME TRỌN GÓI (ĐẦY ĐỦ FILE GỐC)
- Ngay trên thanh điều hướng đầu trang Web Dashboard, bạn có nút: **`📥 Tải Game Trọn Gói (HSO v403B)`**.
- Bạn cũng có thể tải trực tiếp file game tại địa chỉ:
  - `http://<dia-chi-ip-hoac-domain>:3000/download/game`
  - File tải về: **`HSO_v403B.exe`** (Bản chuẩn ~25MB sẵn sàng chơi ngay, không cần giải nén hay cài đặt thêm).

---

## ⚡ 2. CÁCH ĐỂ TỰ CHẠY 24/7 (BẬT TÊN MIỀN / VPS LÀ TỰ CHẠY, KHÔNG CẦN BẬT TAY .BAT)

Để khi mở Tên Miền / IP hoặc khi VPS tự khởi động lại mà Web Agent **vẫn tự động chạy ngầm 24/7** (không cần phải vào VPS mở file `.bat` thủ công, không có cửa sổ đen che màn hình):

### Cách 1: Chạy file cài đặt tự động 1-Click (Khuyên Dùng)
1. Trong thư mục dự án trên VPS, nhấp chuột phải vào file:
   ```text
   cai_dat_tu_khoi_dong_vps.bat
   ```
   chọn **Run as Administrator** (Chạy với quyền Quản trị).
2. Hệ thống sẽ tự động:
   - Đăng ký vào **Windows Startup** và **Windows Task Scheduler**.
   - Chạy Agent ngầm hoàn toàn bằng file `start_agent_hidden.vbs` (ẩn 100% cửa sổ CMD).
   - VPS vừa bật lên là Agent tự hoạt động ngay lập tức.
3. Từ bây giờ, bạn chỉ cần gõ **Tên miền** hoặc **IP:3000** trên điện thoại / máy tính là vào được ngay bất kỳ lúc nào!

*Nếu muốn tắt agent chạy ngầm:* chạy file `tat_agent_ngam.bat`  
*Nếu muốn gỡ tự khởi động:* chạy file `go_cai_dat_tu_khoi_dong.bat`

---

### Cách 2: Chạy qua PM2 Process Manager (Dành cho Node.js)
Nếu VPS đã có Node.js, bạn có thể chạy bằng PM2 để quản lý tiến trình chuyên nghiệp nhất:
```bash
npm install -g pm2
pm2 start agent.js --name "vps-agent"
pm2 startup
pm2 save
```

---

## 🎯 3. CÁC TÍNH NĂNG ĐIỀU KHIỂN & AUTO GAME
1. **Khởi chạy Game**: Bấm `Khởi Chạy Game Knight Age` trực tiếp từ Web.
2. **Auto Đánh & Xuất Chiêu (Phím 1, 2, 5)**: Tự động tung chiêu luân phiên theo chu kỳ mili-giây.
3. **Auto Bơm Máu (Phím 7)** & **Hồi Năng Lượng (Phím 8)**: Tự động giữ an toàn cho nhân vật.
4. **Tự Động Hồi Sinh & Quay Lại Map (Smart Teleport)**: Khi chẳng may bị quái đánh chết, tự về làng và bay lại bãi quái cày tiếp.
5. **Auto Ngầm 24/7**: Ẩn/thu nhỏ cửa sổ game xuống thanh taskbar, tắt tab web hoặc tắt máy cá nhân — nhân vật trên VPS vẫn tự cày 24/7!
