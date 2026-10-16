# THIẾT KẾ CƠ SỞ DỮ LIỆU TƯƠNG THÍCH KIOTVIET & KIẾN TRÚC KỸ THUẬT (SAD)
## Software Architecture & Database Design Document
### Dự án: Smart Fashion Business Analytics Dashboard
* **Doanh nghiệp ứng dụng:** FORM Studio (Hà Nội, Việt Nam)
* **Hệ thống nguồn đối ứng:** Phần mềm Quản lý Bán lẻ KiotViet (Mô hình Bán lẻ Đa kênh Omnichannel)
* **Tài liệu tham chiếu chuẩn:** 
  * [01_DATA_STRUCTURE_ANALYSIS.md](file:///c:/Users/Admin/Workspaces/gsj-localbrand-src/docs/01_DATA_STRUCTURE_ANALYSIS.md)
  * [GSJ_Huong dan thuc hanh.md](file:///c:/Users/Admin/Workspaces/gsj-localbrand-src/docs/requirements/GSJ_Huong%20dan%20thuc%20hanh.md)
  * [BA_for_Smart_Fashion_Textbook.docx.md](file:///c:/Users/Admin/Workspaces/gsj-localbrand-src/docs/requirements/BA_for_Smart_Fashion_Textbook.docx.md)
* **Phiên bản:** v2.0 (Bổ sung đầy đủ thực thể ORDERS & ORDER_LINES) | **Ngày cập nhật:** 16/10/2026

---

## 1. TỔNG QUAN KIẾN TRÚC & PHÂN BIỆT ĐƠN HÀNG (ORDERS) VS. HÓA ĐƠN (INVOICES)

Trong nghiệp vụ bán lẻ KiotViet và đặc thù ngành thời trang Streetwear (Drop Model), quá trình bán hàng bao gồm 2 giai đoạn kế tiếp nhau với bản chất nghiệp vụ hoàn toàn khác nhau:

### 1.1. Vai trò của Đơn đặt hàng (ORDERS & ORDER_LINES)
* **Bản chất:** Giai đoạn khách hàng **dự định mua hàng hoặc đặt trước (Pre-order)**, giữ chỗ sản phẩm trong đợt Drop hoặc trên giỏ hàng sàn TMĐT (TikTok Shop, Shopee, Fanpage).
* **Đặc điểm:** Số lượng, chủng loại hàng hóa có thể bị thay đổi hoặc hủy bỏ. Lúc này **chưa phát sinh thanh toán thực tế** và **chưa ghi nhận doanh thu kế toán**.
* **Ý nghĩa phân tích cho BA:**
  * Giúp tính toán **Tỷ lệ chuyển đổi đơn hàng (Order Conversion Rate)**: Tỷ lệ đơn đặt hàng chuyển thành hóa đơn thanh toán thành công.
  * Đo lường **Tỷ lệ hủy đơn (Cancellation Rate / Drop-off Rate)**: Những khách đặt đơn nhưng sau đó hủy do phí ship, đổi ý hoặc chờ giao quá lâu.
  * Phân tích nhu cầu thị trường thực tế (Demand Forecasting) trước khi quyết định sản xuất.

### 1.2. Vai trò của Hóa đơn (INVOICES & INVOICE_LINES)
* **Bản chất:** Kết quả của giao dịch thành công khi hàng hóa đã được xuất kho, xử lý đóng gói, thanh toán và chuyển giao cho khách hàng (hoặc phát sinh đổi trả).
* **Đặc điểm:** Là cơ sở pháp lý và kế toán để **ghi nhận doanh thu thuần, dòng tiền thực nhận, và theo dõi tỷ lệ hoàn hàng (Return Rate)**.

```mermaid
flowchart LR
    A["Khách Hàng Đặt Mua (Pre-order / Cart)"] --> B["FACT_ORDERS (Mã DHxxxxx)"]
    B -->|85% Giao thành công| C["FACT_INVOICES (Mã HDIPxxxxx)"]
    B -->|10% Khách đổi ý| D["Trạng thái: Đã Hủy"]
    B -->|5% Đang đóng gói| E["Trạng thái: Đang Xử Lý"]
    C -->|Thành công| F["Doanh Thu Thực Nhận (Net Revenue)"]
    C -.->|Hoàn trả 10-25%| G["Đơn Hoàn (is_returned = 1)"]
```

---

## 2. SƠ ĐỒ THỰC THỂ QUAN HỆ TOÀN DIỆN (ERD DIAGRAM)

```mermaid
erDiagram
    DIM_CUSTOMERS ||--o{ FACT_ORDERS : "dat hang (customer_code)"
    DIM_CUSTOMERS ||--o{ FACT_INVOICES : "mua hang (customer_code)"
    DIM_EMPLOYEES ||--o{ FACT_ORDERS : "xu ly don (seller)"
    DIM_EMPLOYEES ||--o{ FACT_INVOICES : "xuat hoa don (seller)"
    DIM_PRODUCTS ||--o{ FACT_ORDERS_LINES : "chua trong (product_code)"
    DIM_PRODUCTS ||--o{ FACT_INVOICE_LINES : "chua trong (product_code)"
    FACT_ORDERS ||--|{ FACT_ORDERS_LINES : "chi tiet don (order_code)"
    FACT_ORDERS ||--o| FACT_INVOICES : "chuyen doi thanh (invoice_code)"
    FACT_INVOICES ||--|{ FACT_INVOICE_LINES : "chi tiet hoa don (invoice_code)"

    DIM_CUSTOMERS {
        string customer_code PK "Mã khách hàng (KHxxxxx)"
        string customer_type "Loại khách (Cá nhân/Đại lý)"
        string customer_name "Tên khách hàng"
        string phone "Điện thoại"
        string email "Email liên hệ"
        string address "Địa chỉ"
        string area "Khu vực giao hàng (Tỉnh/Thành phố)"
        string ward "Phường / Xã"
        real debt "Nợ cần thu hiện tại"
        real total_sales "Tổng bán (lũy kế)"
        string last_transaction_date "Ngày giao dịch cuối"
        integer is_active "Trạng thái (1: Hoạt động, 0: Khóa)"
    }

    DIM_EMPLOYEES {
        string employee_code PK "Mã nhân viên (NVxxx)"
        string employee_name "Tên nhân viên (UNIQUE)"
        string phone "Số điện thoại"
        string department "Phòng ban (Bán hàng, Thu ngân, Livestream)"
        string title "Chức danh"
        string login "Tài khoản đăng nhập"
        string branch_working "Chi nhánh làm việc"
    }

    DIM_PRODUCTS {
        string product_code PK "Mã hàng / SKU"
        string barcode "Mã vạch"
        string product_name "Tên hàng"
        string product_type "Loại hàng (Hàng hóa)"
        string category_path "Nhóm hàng (3 Cấp)"
        string brand "Thương hiệu (FORM Studio)"
        real sale_price "Giá bán niêm yết"
        real cost_price "Giá vốn (COGS)"
        integer stock_on_hand "Tồn kho thực tế (Beanie = 200 chiếc)"
        string uom "Đơn vị tính (Chiếc/Cái/Đôi)"
        integer is_active "Đang kinh doanh (1/0)"
        integer is_direct_sale "Được bán trực tiếp (1/0)"
    }

    FACT_ORDERS {
        string order_code PK "Mã đơn hàng (Prefix DHxxxxx)"
        string order_time "Thời gian đặt hàng"
        string customer_code FK "Mã khách hàng"
        string seller FK "Nhân viên phụ trách"
        string sales_channel "Kênh bán (TikTok Shop, Shopee, Offline)"
        real amount_due "Tổng tiền khách cần trả"
        real amount_paid "Tiền khách đã cọc/trả trước"
        string status "Trạng thái (Đã hoàn thành, Đang xử lý, Đã hủy)"
        string invoice_code FK "Liên kết Hóa đơn (HDIPxxxxx nếu thành công)"
        string note "Ghi chú đơn hàng"
    }

    FACT_ORDERS_LINES {
        integer order_line_id PK "ID dòng chi tiết đơn"
        string order_code FK "Mã đơn hàng (DHxxxxx)"
        string product_code FK "Mã hàng (SKU)"
        integer quantity "Số lượng đặt"
        real unit_price "Đơn giá niêm yết"
        real discount_percent "Giảm giá % dòng"
        real discount_amount "Giảm giá tiền dòng"
        real line_total "Thành tiền dòng đơn hàng"
    }

    FACT_INVOICES {
        string invoice_code PK "Mã hóa đơn (Prefix HDIPxxxxx)"
        string invoice_time "Thời gian xuất hóa đơn"
        string seller FK "Người bán đứng tên"
        string sales_channel "Kênh bán"
        string customer_code FK "Mã khách hàng"
        string order_code FK "Đơn đặt hàng gốc (nếu có)"
        string pricebook "Bảng giá áp dụng"
        real invoice_discount_amount "Giảm giá hóa đơn (VNĐ)"
        real total_amount "Tổng tiền khách thanh toán"
        real pay_cash "Tiền mặt"
        real pay_card "Thẻ"
        real pay_transfer "Chuyển khoản (Banking/QR)"
        string note "Ghi chú"
        string order_status "Trạng thái (COMPLETED, RETURNED)"
        integer is_returned "Cờ hoàn hàng (1: Hoàn trả, 0: Thành công)"
    }

    FACT_INVOICE_LINES {
        integer invoice_line_id PK "ID dòng chi tiết hóa đơn"
        string invoice_code FK "Mã hóa đơn (HDIPxxxxx)"
        string product_code FK "Mã hàng (SKU)"
        integer quantity "Số lượng mua thực tế"
        real unit_price "Đơn giá"
        real line_discount_percent "Giảm giá %"
        real line_discount_amount "Giảm giá tiền"
        real line_total "Thành tiền dòng hóa đơn"
    }
```

---

## 3. CHI TIẾT BẢNG DỮ LIỆU ORDERS & ORDER_LINES (DATA DICTIONARY)

### 3.1. Bảng `FACT_ORDERS` (Đơn đặt hàng)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- |
| `order_code` | TEXT | PRIMARY KEY | Prefix `DH` theo chuẩn KiotViet | Mã đơn đặt hàng (VD: `DH00001`, `DH00002`) |
| `order_time` | TEXT | | ISO-8601 `YYYY-MM-DD HH:MM:SS` | Thời điểm khách đặt đơn trên hệ thống |
| `customer_code` | TEXT | FOREIGN KEY | `REFERENCES DIM_CUSTOMERS(customer_code)` | Khách hàng thực hiện đặt đơn |
| `seller` | TEXT | FOREIGN KEY | `REFERENCES DIM_EMPLOYEES(employee_name)` | Nhân viên tiếp nhận đơn hoặc kênh bán |
| `sales_channel` | TEXT | | NOT NULL | Kênh đặt hàng (TikTok Shop, Shopee, Offline) |
| `amount_due` | REAL | | `>= 0` | Tổng giá trị đơn hàng khách cần thanh toán |
| `amount_paid` | REAL | | `>= 0` | Số tiền khách đã thanh toán trước (cọc) |
| `status` | TEXT | | `Đã hoàn thành`, `Đang xử lý`, `Đã hủy` | Trạng thái vòng đời của đơn đặt hàng |
| `invoice_code` | TEXT | FOREIGN KEY | `REFERENCES FACT_INVOICES(invoice_code)` | Mã hóa đơn sinh ra nếu đơn hoàn thành |
| `note` | TEXT | | | Ghi chú đơn (Lý do hủy đơn, ghi chú size) |

### 3.2. Bảng `FACT_ORDERS_LINES` (Chi tiết dòng đơn đặt hàng)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- |
| `order_line_id` | INTEGER | PRIMARY KEY | AUTOINCREMENT | Định danh duy nhất dòng đơn hàng |
| `order_code` | TEXT | FOREIGN KEY | `REFERENCES FACT_ORDERS(order_code)` | Mã đơn đặt hàng cha |
| `product_code` | TEXT | FOREIGN KEY | `REFERENCES DIM_PRODUCTS(product_code)` | Sản phẩm đặt mua |
| `quantity` | INTEGER | | `> 0` | Số lượng sản phẩm khách đặt |
| `unit_price` | REAL | | `== DIM_PRODUCTS.sale_price` | Đơn giá niêm yết tại thời điểm đặt |
| `discount_percent` | REAL | | `0 - 100` | Giảm giá theo % của chiến dịch |
| `discount_amount` | REAL | | `>= 0` | Tiền giảm giá trên dòng |
| `line_total` | REAL | | `quantity * unit_price - discount` | Thành tiền dự kiến của dòng đặt hàng |

---

## 4. QUY TẮC NGHIỆP VỤ ĐỒNG BỘ GIỮA ORDERS VÀ INVOICES

1. **Quy tắc Tiền tố Định danh (Naming Convention):**
   * Đơn đặt hàng KiotViet: Tiền tố bắt buộc **`DH`** (ví dụ: `DH00001`, `DH00002`...).
   * Hóa đơn KiotViet: Tiền tố bắt buộc **`HDIP`** (ví dụ: `HDIP00001`, `HDIP00002`...).
2. **Quy tắc Chuyển đổi Phễu Đơn hàng (Conversion Pipeline):**
   * Khi đơn đặt hàng đạt trạng thái `Đã hoàn thành` ($\approx 80\% - 85\%$): Một bản ghi `FACT_INVOICES` tương ứng được sinh ra, liên kết chéo qua cột `invoice_code`.
   * Khi đơn đặt hàng ở trạng thái `Đã hủy` ($\approx 10\% - 15\%$): Không sinh hóa đơn, ghi rõ lý do hủy trong cột `note` (khách không vừa size, bom hàng, không nghe máy).
   * Khi đơn đặt hàng ở trạng thái `Đang xử lý` ($\approx 5\%$): Đang chuẩn bị xuất kho.
3. **Quy tắc Bảo toàn Sản phẩm & Tồn kho:**
   * Các sản phẩm trong `FACT_ORDERS_LINES` của đơn hoàn thành sẽ được sao chép sang `FACT_INVOICE_LINES`.
   * Tồn kho khả dụng của sản phẩm bị tạm giữ khi đơn hàng được tạo, và chỉ thực sự trừ khỏi `stock_on_hand` khi xuất hóa đơn.

---
*(Tài liệu này là căn cứ để cập nhật `srcs/db_schema.sql` và tái cấu trúc script SDV trong `srcs/generate_synthetic_data_sdv.py`).*
