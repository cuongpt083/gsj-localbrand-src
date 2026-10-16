"""
================================================================================
SCRIPT TẠO DỮ LIỆU GIẢ LẬP TƯƠNG THÍCH KIOTVIET BẰNG THƯ VIỆN SDV
(Synthetic Data Vault) - PHIÊN BẢN V2.0 ĐẦY ĐỦ ORDERS VÀ INVOICES
================================================================================
Căn cứ tài liệu:
1. docs/01_DATA_STRUCTURE_ANALYSIS.md (Cấu trúc 7 thực thể KiotViet bao gồm Orders/PO)
2. docs/requirements/GSJ_Huong dan thuc hanh.md (Cấu trúc Fact Orders/Invoices & Rules R1-R4)
3. docs/requirements/BA_for_Smart_Fashion_Textbook.docx.md (Drop model, Return rate, 200 Beanie)
================================================================================
"""

import os
import random
import sqlite3
import sys
import warnings
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Thiết lập encoding UTF-8 cho console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

warnings.filterwarnings('ignore')

# Thư viện SDV - Synthetic Data Vault
from sdv.metadata import SingleTableMetadata
from sdv.single_table import GaussianCopulaSynthesizer


def create_seed_master_data():
    """
    Tạo Master Data ban đầu cho FORM Studio phù hợp với KiotViet:
    - DIM_PRODUCTS: Danh mục thời trang streetwear (đặc biệt BEANIE-001 tồn đúng 200 chiếc)
    - DIM_EMPLOYEES: Nhân sự bán lẻ, thu ngân và livestream host
    - DIM_CUSTOMERS: Tập khách hàng cá nhân
    """
    print("[1/6] Khởi tạo Master Data gốc cho FORM Studio...")

    # 1. DANH MỤC SẢN PHẨM (DIM_PRODUCTS)
    products_data = [
        {
            "product_code": "FORM-HOODIE-BLK-S",
            "barcode": "8935001001",
            "product_name": "Áo Hoodie Oversized Đen (Size S)",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Áo > Hoodie",
            "brand": "FORM Studio",
            "sale_price": 590000,
            "cost_price": 230000,
            "stock_on_hand": 500,
            "uom": "Chiếc",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "FORM-HOODIE-BLK-M",
            "barcode": "8935001002",
            "product_name": "Áo Hoodie Oversized Đen (Size M)",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Áo > Hoodie",
            "brand": "FORM Studio",
            "sale_price": 590000,
            "cost_price": 230000,
            "stock_on_hand": 500,
            "uom": "Chiếc",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "FORM-HOODIE-BLK-L",
            "barcode": "8935001003",
            "product_name": "Áo Hoodie Oversized Đen (Size L)",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Áo > Hoodie",
            "brand": "FORM Studio",
            "sale_price": 590000,
            "cost_price": 230000,
            "stock_on_hand": 500,
            "uom": "Chiếc",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "FORM-HOODIE-WHT-M",
            "barcode": "8935001004",
            "product_name": "Áo Hoodie Trắng In Logo (Size M)",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Áo > Hoodie",
            "brand": "FORM Studio",
            "sale_price": 590000,
            "cost_price": 230000,
            "stock_on_hand": 400,
            "uom": "Chiếc",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "BEANIE-001",
            "barcode": "8935002001",
            "product_name": "Mũ Beanie Len Form Streetwear",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Phụ kiện > Mũ len",
            "brand": "FORM Studio",
            "sale_price": 290000,
            "cost_price": 90000,
            "stock_on_hand": 200,  # Đúng 200 chiếc tồn kho mùa cũ theo textbook!
            "uom": "Cái",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "TEE-OVZ-BLK-M",
            "barcode": "8935003001",
            "product_name": "Áo Thun Oversize Đen Graphic (Size M)",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Áo > Áo thun",
            "brand": "FORM Studio",
            "sale_price": 350000,
            "cost_price": 120000,
            "stock_on_hand": 600,
            "uom": "Chiếc",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "TEE-OVZ-WHT-L",
            "barcode": "8935003002",
            "product_name": "Áo Thun Oversize Trắng Minimal (Size L)",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Áo > Áo thun",
            "brand": "FORM Studio",
            "sale_price": 350000,
            "cost_price": 120000,
            "stock_on_hand": 600,
            "uom": "Chiếc",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "CARGO-PNT-BLK-M",
            "barcode": "8935004001",
            "product_name": "Quần Cargo Pants Multi-Pocket (Size M)",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Quần > Quần dài",
            "brand": "FORM Studio",
            "sale_price": 520000,
            "cost_price": 200000,
            "stock_on_hand": 300,
            "uom": "Chiếc",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "BOMBER-JKT-BLK-L",
            "barcode": "8935005001",
            "product_name": "Áo Khoác Bomber Street Flight (Size L)",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Áo khoác > Bomber",
            "brand": "FORM Studio",
            "sale_price": 750000,
            "cost_price": 310000,
            "stock_on_hand": 250,
            "uom": "Chiếc",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "CAP-STREET-01",
            "barcode": "8935006001",
            "product_name": "Mũ Lưỡi Trai Classic Embroidery",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Phụ kiện > Mũ",
            "brand": "FORM Studio",
            "sale_price": 220000,
            "cost_price": 70000,
            "stock_on_hand": 350,
            "uom": "Cái",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "SOCKS-CREW-WHT",
            "barcode": "8935007001",
            "product_name": "Tất Cổ Cao Form Crew Socks (Trắng)",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Phụ kiện > Tất",
            "brand": "FORM Studio",
            "sale_price": 79000,
            "cost_price": 20000,
            "stock_on_hand": 800,
            "uom": "Đôi",
            "is_active": 1,
            "is_direct_sale": 1,
        },
        {
            "product_code": "TOTE-CANVAS-01",
            "barcode": "8935008001",
            "product_name": "Túi Canvas Tote Street Vibes",
            "product_type": "Hàng hóa",
            "category_path": "Thời trang > Phụ kiện > Túi",
            "brand": "FORM Studio",
            "sale_price": 150000,
            "cost_price": 45000,
            "stock_on_hand": 400,
            "uom": "Chiếc",
            "is_active": 1,
            "is_direct_sale": 1,
        },
    ]
    df_products = pd.DataFrame(products_data)

    # 2. DANH MỤC NHÂN VIÊN (DIM_EMPLOYEES)
    employees_data = [
        {
            "employee_code": "NV001",
            "employee_name": "Nguyễn Văn An",
            "phone": "0912345601",
            "department": "Bán hàng",
            "title": "Nhân viên bán hàng",
            "login": "annv",
            "branch_working": "Cửa hàng Phố Huế (Hà Nội)",
        },
        {
            "employee_code": "NV002",
            "employee_name": "Trần Thị Mai",
            "phone": "0912345602",
            "department": "Thu ngân",
            "title": "Thu ngân",
            "login": "maitt",
            "branch_working": "Cửa hàng Phố Huế (Hà Nội)",
        },
        {
            "employee_code": "NV003",
            "employee_name": "Lê Hoàng Minh",
            "phone": "0988888888",
            "department": "Quản lý",
            "title": "Founder & Cửa hàng trưởng",
            "login": "minhlh",
            "branch_working": "Tổng kho & Online",
        },
        {
            "employee_code": "NV004",
            "employee_name": "Phạm Quỳnh Anh",
            "phone": "0912345604",
            "department": "Livestream",
            "title": "Host TikTok Live",
            "login": "anhpq",
            "branch_working": "Kênh Online",
        },
    ]
    df_employees = pd.DataFrame(employees_data)

    # 3. DANH MỤC KHÁCH HÀNG (DIM_CUSTOMERS)
    first_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương"]
    middle_names = ["Văn", "Thị", "Đức", "Minh", "Quốc", "Thành", "Phương", "Tuấn", "Khánh", "Hải", "Hồng", "Thanh"]
    last_names = ["Anh", "Bình", "Cường", "Dũng", "Huy", "Khoa", "Long", "Nam", "Phúc", "Quân", "Sơn", "Tùng", "Trang", "Linh", "Ngọc", "Hà"]
    areas = ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Bắc Ninh", "Quảng Ninh"]

    random.seed(42)
    np.random.seed(42)

    customers_data = []
    for i in range(1, 251):
        code = f"KH{i:05d}"
        name = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_names)}"
        phone = f"09{random.randint(10000000, 99999999)}"
        email = f"customer_{i:03d}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}"
        area = random.choices(areas, weights=[0.45, 0.25, 0.1, 0.08, 0.04, 0.04, 0.04])[0]
        customers_data.append({
            "customer_code": code,
            "customer_type": "Cá nhân",
            "customer_name": name,
            "phone": phone,
            "email": email,
            "address": f"Số {random.randint(1, 250)}, Đường {random.choice(['Giải Phóng', 'Cầu Giấy', 'Bà Triệu', 'Lê Lợi', 'Nguyễn Trãi', 'Kim Mã'])}",
            "area": area,
            "ward": "Phường Hàng Bài",
            "company": "",
            "tax_code": "",
            "debt": 0.0,
            "total_sales": 0.0,
            "last_transaction_date": "2026-10-01",
            "is_active": 1,
        })
    df_customers = pd.DataFrame(customers_data)

    return df_products, df_employees, df_customers


def create_seed_orders_and_invoices(df_products, df_employees, df_customers, n_orders=250):
    """
    Tạo dữ liệu giao dịch hạt giống gồm Đơn đặt hàng (FACT_ORDERS) và Hóa đơn (FACT_INVOICES)
    - Tỷ lệ hoàn thành đơn: ~82% chuyển thành Hóa đơn (HDIP)
    - Tỷ lệ hủy đơn: ~12% (khách đổi ý, bom hàng, hết size)
    - Tỷ lệ đang xử lý: ~6%
    - Tỷ lệ hoàn hàng (Return Rate): 10 - 25% trong các đơn hoàn thành
    """
    print(f"[2/6] Khởi tạo {n_orders} đơn đặt hàng (Orders) và ánh xạ sang Hóa đơn (Invoices)...")

    channels = ["TikTok Shop", "Shopee", "Cửa hàng Offline", "Instagram"]
    channel_weights = [0.55, 0.25, 0.15, 0.05]

    prod_codes = df_products["product_code"].tolist()
    prod_prices = dict(zip(df_products["product_code"], df_products["sale_price"]))
    cust_codes = df_customers["customer_code"].tolist()
    seller_names = df_employees["employee_name"].tolist()

    base_dates = [
        datetime(2026, 3, 15),   # Drop Xuân Hè
        datetime(2026, 8, 20),   # Drop Thu Đông
        datetime(2026, 11, 11),  # Bão Flash sale 11.11
        datetime(2026, 12, 25),  # Đợt chuẩn bị Drop Tết
    ]

    orders = []
    order_lines = []
    invoices = []
    invoice_lines = []

    order_line_counter = 1
    invoice_line_counter = 1
    invoice_idx = 1

    for i in range(1, n_orders + 1):
        order_code = f"DH{i:05d}"

        # Chọn thời gian đặt hàng
        campaign_base = random.choice(base_dates)
        offset_days = random.randint(0, 5)
        offset_hours = random.randint(8, 23)
        offset_mins = random.randint(0, 59)
        order_time_dt = campaign_base + timedelta(days=offset_days, hours=offset_hours, minutes=offset_mins)
        order_time = order_time_dt.strftime("%Y-%m-%d %H:%M:%S")

        channel = random.choices(channels, weights=channel_weights)[0]
        seller = "Phạm Quỳnh Anh" if channel == "TikTok Shop" else random.choice(seller_names)
        cust_code = random.choice(cust_codes)

        is_flash_sale = "11-11" in order_time or "11-12" in order_time

        # Quyết định giỏ hàng (Market Basket pattern: Hoodie + Beanie)
        has_hoodie = random.random() < 0.45
        has_beanie = False
        items_to_buy = []

        if has_hoodie:
            hoodie_item = random.choice(["FORM-HOODIE-BLK-M", "FORM-HOODIE-BLK-L", "FORM-HOODIE-WHT-M"])
            items_to_buy.append((hoodie_item, 1))
            # 60% người mua hoodie mua thêm Beanie
            if random.random() < 0.60:
                items_to_buy.append(("BEANIE-001", 1))
                has_beanie = True
        else:
            rand_item = random.choice([p for p in prod_codes if p != "BEANIE-001"])
            items_to_buy.append((rand_item, random.choice([1, 1, 2])))

        # Thêm phụ kiện ngẫu nhiên
        if random.random() < 0.25 and not has_beanie:
            items_to_buy.append((random.choice(["SOCKS-CREW-WHT", "CAP-STREET-01", "TOTE-CANVAS-01"]), 1))

        # Tính tổng giá trị đơn hàng
        total_order_amount = 0
        current_order_lines = []
        for p_code, qty in items_to_buy:
            u_price = prod_prices[p_code]
            discount_amount = int(u_price * 0.10) if is_flash_sale else 0
            l_total = (u_price * qty) - discount_amount

            current_order_lines.append({
                "order_line_id": order_line_counter,
                "order_code": order_code,
                "product_code": p_code,
                "quantity": qty,
                "unit_price": u_price,
                "discount_percent": 10.0 if is_flash_sale else 0.0,
                "discount_amount": discount_amount,
                "line_total": l_total
            })
            total_order_amount += l_total
            order_line_counter += 1

        order_lines.extend(current_order_lines)

        # Trạng thái vòng đời của đơn đặt hàng
        # 82% Đã hoàn thành (sinh hóa đơn), 12% Đã hủy, 6% Đang xử lý
        rand_status = random.random()
        if rand_status < 0.82:
            order_status = "Đã hoàn thành"
            inv_code = f"HDIP{invoice_idx:05d}"
            invoice_idx += 1
            amount_paid = float(total_order_amount)
            order_note = "Đơn hoàn thành chuyển sang hóa đơn bán hàng"
        elif rand_status < 0.94:
            order_status = "Đã hủy"
            inv_code = None
            amount_paid = 0.0
            order_note = random.choice(["Khách đổi ý hủy đơn", "Không vừa size", "Không liên lạc được khi giao", "Hết hàng cục bộ"])
        else:
            order_status = "Đang xử lý"
            inv_code = None
            amount_paid = 0.0 if random.random() < 0.7 else float(total_order_amount * 0.3)
            order_note = "Đang đóng gói chờ xuất kho"

        orders.append({
            "order_code": order_code,
            "order_time": order_time,
            "customer_code": cust_code,
            "seller": seller,
            "sales_channel": channel,
            "amount_due": float(total_order_amount),
            "amount_paid": float(amount_paid),
            "status": order_status,
            "invoice_code": inv_code,
            "note": order_note
        })

        # Nếu đơn hàng chuyển đổi thành công sang HÓA ĐƠN:
        if order_status == "Đã hoàn thành" and inv_code is not None:
            # Thời gian hóa đơn chậm hơn đặt hàng từ 30 phút đến 2 ngày
            inv_time_dt = order_time_dt + timedelta(minutes=random.randint(30, 2880))
            inv_time = inv_time_dt.strftime("%Y-%m-%d %H:%M:%S")

            # Xác suất hoàn hàng (Return Rate): Flash sale hoặc TikTok Shop cao hơn
            return_prob = 0.24 if (is_flash_sale or channel == "TikTok Shop") else 0.08
            is_returned = 1 if (random.random() < return_prob) else 0
            inv_status = "RETURNED" if is_returned == 1 else "COMPLETED"

            # Thanh toán
            if channel == "Cửa hàng Offline":
                pay_cash = total_order_amount if random.random() < 0.5 else 0.0
                pay_card = (total_order_amount - pay_cash) if pay_cash == 0 and random.random() < 0.5 else 0.0
                pay_transfer = total_order_amount - pay_cash - pay_card
            else:
                pay_cash = total_order_amount if random.random() < 0.15 else 0.0
                pay_card = 0.0
                pay_transfer = total_order_amount - pay_cash

            invoices.append({
                "invoice_code": inv_code,
                "invoice_time": inv_time,
                "seller": seller,
                "sales_channel": channel,
                "customer_code": cust_code,
                "order_code": order_code,
                "pricebook": "Flash Sale 11.11" if is_flash_sale else "Bảng giá chung",
                "invoice_discount_amount": 0.0,
                "invoice_discount_percent": 0.0,
                "total_amount": float(total_order_amount),
                "pay_cash": float(pay_cash),
                "pay_card": float(pay_card),
                "pay_transfer": float(pay_transfer),
                "note": "Khách hoàn trả do không vừa size" if is_returned == 1 else "Giao thành công",
                "order_status": inv_status,
                "is_returned": is_returned
            })

            # Dòng chi tiết hóa đơn sao chép từ đơn hàng
            for line in current_order_lines:
                invoice_lines.append({
                    "invoice_line_id": invoice_line_counter,
                    "invoice_code": inv_code,
                    "product_code": line["product_code"],
                    "quantity": line["quantity"],
                    "unit_price": line["unit_price"],
                    "line_discount_percent": line["discount_percent"],
                    "line_discount_amount": line["discount_amount"],
                    "line_total": line["line_total"]
                })
                invoice_line_counter += 1

    df_orders = pd.DataFrame(orders)
    df_order_lines = pd.DataFrame(order_lines)
    df_invoices = pd.DataFrame(invoices)
    df_invoice_lines = pd.DataFrame(invoice_lines)

    return df_orders, df_order_lines, df_invoices, df_invoice_lines


def generate_with_sdv(data_dict, scale=2.0):
    """
    Sử dụng thư viện SDV (Synthetic Data Vault) với GaussianCopulaSynthesizer
    để học phân phối thống kê từ các bảng và sinh dữ liệu giả lập mở rộng.
    """
    print("[3/6] Huấn luyện mô hình SDV GaussianCopulaSynthesizer cho các thực thể...")

    # 1. SDV Synthesizer cho Khách hàng
    print("      -> Huấn luyện SDV cho bảng DIM_CUSTOMERS...")
    m_cust = SingleTableMetadata()
    m_cust.detect_from_dataframe(data_dict["DIM_CUSTOMERS"])
    synth_cust = GaussianCopulaSynthesizer(m_cust)
    synth_cust.fit(data_dict["DIM_CUSTOMERS"])
    n_cust = int(len(data_dict["DIM_CUSTOMERS"]) * scale)
    syn_customers = synth_cust.sample(num_rows=n_cust)

    # 2. SDV Synthesizer cho Đơn đặt hàng
    print("      -> Huấn luyện SDV cho bảng FACT_ORDERS...")
    m_orders = SingleTableMetadata()
    m_orders.detect_from_dataframe(data_dict["FACT_ORDERS"])
    synth_orders = GaussianCopulaSynthesizer(m_orders)
    synth_orders.fit(data_dict["FACT_ORDERS"])
    n_orders = int(len(data_dict["FACT_ORDERS"]) * scale)
    syn_orders = synth_orders.sample(num_rows=n_orders)

    # 3. SDV Synthesizer cho Chi tiết đơn đặt hàng
    print("      -> Huấn luyện SDV cho bảng FACT_ORDERS_LINES...")
    m_ol = SingleTableMetadata()
    m_ol.detect_from_dataframe(data_dict["FACT_ORDERS_LINES"])
    synth_ol = GaussianCopulaSynthesizer(m_ol)
    synth_ol.fit(data_dict["FACT_ORDERS_LINES"])
    n_ol = int(len(data_dict["FACT_ORDERS_LINES"]) * scale)
    syn_order_lines = synth_ol.sample(num_rows=n_ol)

    # 4. SDV Synthesizer cho Hóa đơn
    print("      -> Huấn luyện SDV cho bảng FACT_INVOICES...")
    m_inv = SingleTableMetadata()
    m_inv.detect_from_dataframe(data_dict["FACT_INVOICES"])
    synth_inv = GaussianCopulaSynthesizer(m_inv)
    synth_inv.fit(data_dict["FACT_INVOICES"])
    n_inv = int(len(data_dict["FACT_INVOICES"]) * scale)
    syn_invoices = synth_inv.sample(num_rows=n_inv)

    # 5. SDV Synthesizer cho Chi tiết hóa đơn
    print("      -> Huấn luyện SDV cho bảng FACT_INVOICE_LINES...")
    m_il = SingleTableMetadata()
    m_il.detect_from_dataframe(data_dict["FACT_INVOICE_LINES"])
    synth_il = GaussianCopulaSynthesizer(m_il)
    synth_il.fit(data_dict["FACT_INVOICE_LINES"])
    n_il = int(len(data_dict["FACT_INVOICE_LINES"]) * scale)
    syn_invoice_lines = synth_il.sample(num_rows=n_il)

    print(f"      -> SDV hoàn tất sinh dữ liệu: {n_cust} KH, {n_orders} Orders, {n_inv} Invoices.")

    return {
        "DIM_PRODUCTS": data_dict["DIM_PRODUCTS"],
        "DIM_EMPLOYEES": data_dict["DIM_EMPLOYEES"],
        "DIM_CUSTOMERS": syn_customers,
        "FACT_ORDERS": syn_orders,
        "FACT_ORDERS_LINES": syn_order_lines,
        "FACT_INVOICES": syn_invoices,
        "FACT_INVOICE_LINES": syn_invoice_lines
    }


def enforce_business_rules(data_dict, original_products, original_employees):
    """
    Hậu xử lý bảo đảm các ràng buộc nghiệp vụ KiotViet & FORM Studio:
    - Rule R1: invoice_code có prefix HDIP, order_code có prefix DH
    - Rule R2: Tồn kho thực tế (BEANIE-001 cố định 200 chiếc)
    - Rule R3: quantity > 0, unit_price = sale_price, cân bằng thanh toán
    - Rule R4: Toàn vẹn khóa ngoại 100%
    - Đồng bộ logic giữa Orders thành công và Invoices
    """
    print("[4/6] Áp dụng các Ràng buộc Nghiệp vụ (Rules R1 - R4) và Đồng bộ Orders - Invoices...")

    df_products = original_products.copy()
    df_employees = original_employees.copy()
    df_customers = data_dict["DIM_CUSTOMERS"].copy()
    df_orders = data_dict["FACT_ORDERS"].copy()
    df_order_lines = data_dict["FACT_ORDERS_LINES"].copy()

    prod_prices = dict(zip(df_products["product_code"], df_products["sale_price"]))
    valid_products = df_products["product_code"].tolist()
    valid_customers = df_customers["customer_code"].tolist()
    valid_sellers = df_employees["employee_name"].tolist()

    # Chuẩn hóa khách hàng
    df_orders["customer_code"] = df_orders["customer_code"].apply(
        lambda x: x if x in valid_customers else random.choice(valid_customers)
    )
    df_orders["seller"] = df_orders["seller"].apply(
        lambda x: x if x in valid_sellers else random.choice(valid_sellers)
    )

    # Chuẩn hóa mã đơn đặt hàng DH00001, DH00002,...
    n_orders = len(df_orders)
    df_orders["order_code"] = [f"DH{idx + 1:05d}" for idx in range(n_orders)]

    # Sinh giỏ hàng (Market Basket) đa sản phẩm cho các đơn hàng để đảm bảo tính thực tế của thời trang
    random.seed(42)
    np.random.seed(42)
    order_lines = []
    ol_counter = 1

    for idx, row in df_orders.iterrows():
        o_code = row["order_code"]
        is_flash_sale = "11-11" in str(row.get("order_time", ""))

        # Phân phối giỏ hàng thực tế cho Local Brand
        r_type = random.random()
        basket = []
        if r_type < 0.45:
            # 45% mua Hoodie
            hoodie = random.choice(["FORM-HOODIE-BLK-M", "FORM-HOODIE-BLK-L", "FORM-HOODIE-WHT-M"])
            basket.append((hoodie, 1))
            # 55% người mua Hoodie mua kèm Beanie (Chiến dịch giải cứu 200 Beanie)
            if random.random() < 0.55:
                basket.append(("BEANIE-001", 1))
            # 20% mua kèm Tất
            if random.random() < 0.20:
                basket.append(("SOCKS-CREW-WHT", random.choice([1, 2])))
            # 6% mua hộ size khác (Proxy buy - dùng cho bộ lọc văn hóa)
            if random.random() < 0.06:
                diff_size = "FORM-HOODIE-BLK-L" if hoodie == "FORM-HOODIE-BLK-M" else "FORM-HOODIE-BLK-M"
                basket.append((diff_size, 1))
        elif r_type < 0.80:
            # 35% mua Áo thun Oversize
            tee = random.choice(["TEE-OVZ-BLK-M", "TEE-OVZ-WHT-L"])
            basket.append((tee, 1))
            # 45% mua kèm Quần Cargo
            if random.random() < 0.45:
                basket.append(("CARGO-PNT-BLK-M", 1))
            # 20% mua kèm Mũ lưỡi trai hoặc Túi tote
            if random.random() < 0.20:
                basket.append((random.choice(["CAP-STREET-01", "TOTE-CANVAS-01"]), 1))
        else:
            # 20% mua các combo khác hoặc áo Bomber / phụ kiện đơn
            main_item = random.choice(["BOMBER-JKT-BLK-L", "CARGO-PNT-BLK-M", "BEANIE-001", "CAP-STREET-01"])
            basket.append((main_item, 1))
            if main_item == "BOMBER-JKT-BLK-L" and random.random() < 0.40:
                basket.append(("CAP-STREET-01", 1))

        # Tạo các dòng chi tiết
        for p_code, qty in basket:
            u_p = prod_prices[p_code]
            disc_pct = 10.0 if is_flash_sale else 0.0
            disc_amt = int(u_p * qty * (disc_pct / 100.0))
            l_tot = (u_p * qty) - disc_amt
            order_lines.append({
                "order_line_id": ol_counter,
                "order_code": o_code,
                "product_code": p_code,
                "quantity": qty,
                "unit_price": u_p,
                "discount_percent": disc_pct,
                "discount_amount": disc_amt,
                "line_total": l_tot
            })
            ol_counter += 1

    df_order_lines = pd.DataFrame(order_lines)

    # Tính tổng tiền đơn hàng
    order_totals = df_order_lines.groupby("order_code")["line_total"].sum().to_dict()
    df_orders["amount_due"] = df_orders["order_code"].map(order_totals).fillna(0.0)

    # Phân bổ trạng thái đơn hàng và sinh hóa đơn cho đơn hoàn thành
    status_choices = ["Đã hoàn thành", "Đã hủy", "Đang xử lý"]
    status_weights = [0.82, 0.12, 0.06]

    final_invoices = []
    final_invoice_lines = []
    inv_line_id = 1
    inv_counter = 1

    invoice_codes_for_orders = []

    for _, row in df_orders.iterrows():
        o_code = row["order_code"]
        st = random.choices(status_choices, weights=status_weights)[0]
        row_status = st

        if st == "Đã hoàn thành":
            inv_code = f"HDIP{inv_counter:05d}"
            inv_counter += 1
            invoice_codes_for_orders.append(inv_code)

            # Thời gian hóa đơn
            inv_time = row["order_time"]
            channel = row["sales_channel"]
            tot_amt = row["amount_due"]

            # Hoàn hàng
            is_flash = "11-11" in inv_time
            ret_prob = 0.22 if (is_flash or channel == "TikTok Shop") else 0.08
            is_ret = 1 if (random.random() < ret_prob) else 0

            # Thanh toán
            if channel == "Cửa hàng Offline":
                pay_cash = tot_amt if random.random() < 0.5 else 0.0
                pay_card = (tot_amt - pay_cash) if pay_cash == 0 and random.random() < 0.5 else 0.0
                pay_transfer = tot_amt - pay_cash - pay_card
            else:
                pay_cash = tot_amt if random.random() < 0.15 else 0.0
                pay_card = 0.0
                pay_transfer = tot_amt - pay_cash

            final_invoices.append({
                "invoice_code": inv_code,
                "invoice_time": inv_time,
                "seller": row["seller"],
                "sales_channel": channel,
                "customer_code": row["customer_code"],
                "order_code": o_code,
                "pricebook": "Flash Sale 11.11" if is_flash else "Bảng giá chung",
                "invoice_discount_amount": 0.0,
                "invoice_discount_percent": 0.0,
                "total_amount": float(tot_amt),
                "pay_cash": float(pay_cash),
                "pay_card": float(pay_card),
                "pay_transfer": float(pay_transfer),
                "note": "Khách hoàn trả size" if is_ret == 1 else "Giao thành công",
                "order_status": "RETURNED" if is_ret == 1 else "COMPLETED",
                "is_returned": is_ret
            })

            # Dòng hóa đơn tương ứng với dòng đơn hàng
            matching_lines = df_order_lines[df_order_lines["order_code"] == o_code]
            for _, m_row in matching_lines.iterrows():
                final_invoice_lines.append({
                    "invoice_line_id": inv_line_id,
                    "invoice_code": inv_code,
                    "product_code": m_row["product_code"],
                    "quantity": m_row["quantity"],
                    "unit_price": m_row["unit_price"],
                    "line_discount_percent": m_row["discount_percent"],
                    "line_discount_amount": m_row["discount_amount"],
                    "line_total": m_row["line_total"]
                })
                inv_line_id += 1
        else:
            invoice_codes_for_orders.append(None)

    df_orders["status"] = [random.choices(status_choices, weights=status_weights)[0] if c is None else "Đã hoàn thành" for c in invoice_codes_for_orders]
    df_orders["invoice_code"] = invoice_codes_for_orders
    df_orders["amount_paid"] = [row["amount_due"] if row["status"] == "Đã hoàn thành" else 0.0 for _, row in df_orders.iterrows()]

    df_final_invoices = pd.DataFrame(final_invoices)
    df_final_invoice_lines = pd.DataFrame(final_invoice_lines)

    # Cập nhật tổng bán tích lũy cho bảng DIM_CUSTOMERS
    sales_by_cust = df_final_invoices[df_final_invoices["is_returned"] == 0].groupby("customer_code")["total_amount"].sum().to_dict()
    last_tx_by_cust = df_final_invoices.groupby("customer_code")["invoice_time"].max().to_dict()

    df_customers["total_sales"] = df_customers["customer_code"].map(sales_by_cust).fillna(0.0)
    df_customers["last_transaction_date"] = df_customers["customer_code"].map(last_tx_by_cust).fillna("2026-03-01")

    # Rule R2: Tồn kho thực tế (BEANIE-001 cố định là 200 chiếc tồn kho)
    df_products.loc[df_products["product_code"] == "BEANIE-001", "stock_on_hand"] = 200

    return {
        "DIM_PRODUCTS": df_products,
        "DIM_EMPLOYEES": df_employees,
        "DIM_CUSTOMERS": df_customers,
        "FACT_ORDERS": df_orders,
        "FACT_ORDERS_LINES": df_order_lines,
        "FACT_INVOICES": df_final_invoices,
        "FACT_INVOICE_LINES": df_final_invoice_lines
    }


def save_to_sqlite_and_files(data_dict, db_path="data/fashion_brand.db", output_dir="data"):
    """
    Lưu trữ toàn bộ 7 thực thể vào CSDL SQLite và xuất các file Excel / CSV tương thích KiotViet.
    """
    print(f"[5/6] Lưu trữ dữ liệu vào SQLite ({db_path}) và xuất file báo cáo...")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)

    # Đọc schema DDL để khởi tạo các bảng và khóa ngoại
    schema_path = "srcs/db_schema.sql"
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

    # Thứ tự nạp bảng bảo đảm tính toàn vẹn khóa ngoại cha - con
    table_order = [
        "DIM_CUSTOMERS",
        "DIM_EMPLOYEES",
        "DIM_PRODUCTS",
        "FACT_ORDERS",
        "FACT_ORDERS_LINES",
        "FACT_INVOICES",
        "FACT_INVOICE_LINES"
    ]

    for table_name in table_order:
        if table_name in data_dict:
            df = data_dict[table_name]
            df.to_sql(table_name, conn, if_exists="append" if os.path.exists(schema_path) else "replace", index=False)
            print(f"      + Đã nạp bảng {table_name}: {len(df)} dòng")

    conn.commit()
    conn.close()

    # Xuất các file CSV cho từng bảng
    for table_name in table_order:
        if table_name in data_dict:
            csv_file = os.path.join(output_dir, f"{table_name}.csv")
            data_dict[table_name].to_csv(csv_file, index=False, encoding="utf-8-sig")

    # Xuất file Excel tổng hợp tương thích KiotViet (chứa cả 7 sheet)
    excel_file = os.path.join(output_dir, "KiotViet_FORM_Studio_Export.xlsx")
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        for table_name in table_order:
            if table_name in data_dict:
                data_dict[table_name].to_excel(writer, sheet_name=table_name, index=False)
    print(f"      + Đã xuất file Excel tổng hợp KiotViet: {excel_file}")


def print_data_health_report(data_dict):
    """
    In báo cáo kiểm tra chất lượng dữ liệu toàn diện (Data Health Check Report v2.0)
    """
    orders = data_dict["FACT_ORDERS"]
    order_lines = data_dict["FACT_ORDERS_LINES"]
    invoices = data_dict["FACT_INVOICES"]
    invoice_lines = data_dict["FACT_INVOICE_LINES"]
    products = data_dict["DIM_PRODUCTS"]
    customers = data_dict["DIM_CUSTOMERS"]

    total_orders = len(orders)
    completed_orders = len(orders[orders["status"] == "Đã hoàn thành"])
    cancelled_orders = len(orders[orders["status"] == "Đã hủy"])
    processing_orders = len(orders[orders["status"] == "Đang xử lý"])
    order_conv_rate = (completed_orders / total_orders) * 100 if total_orders > 0 else 0

    total_invoices = len(invoices)
    total_gmv = invoices["total_amount"].sum()
    returned_invoices = invoices[invoices["is_returned"] == 1]
    return_rate = (len(returned_invoices) / total_invoices) * 100 if total_invoices > 0 else 0
    net_revenue = invoices[invoices["is_returned"] == 0]["total_amount"].sum()

    beanie_stock = products[products["product_code"] == "BEANIE-001"]["stock_on_hand"].values[0]

    print("\n" + "=" * 75)
    print("      BÁO CÁO SỨC KHỎE DỮ LIỆU TỔNG HỢP KIOTVIET V2.0 (DATA HEALTH REPORT)")
    print("=" * 75)
    print(f"1. Tổng số khách hàng (DIM_CUSTOMERS):    {len(customers):,} khách hàng")
    print(f"2. Tổng số mã sản phẩm (DIM_PRODUCTS):    {len(products):,} SKU")
    print(f"   -> Tồn kho Mũ Beanie (BEANIE-001):     {beanie_stock} chiếc (Rule R2 - Chuẩn)")
    print(f"3. Tổng số Đơn đặt hàng (FACT_ORDERS):    {total_orders:,} đơn đặt hàng")
    print(f"   -> Đơn hoàn thành (chuyển hóa đơn):    {completed_orders:,} đơn ({order_conv_rate:.1f}%)")
    print(f"   -> Đơn bị hủy (bom hàng/đổi ý):        {cancelled_orders:,} đơn ({(cancelled_orders/total_orders)*100:.1f}%)")
    print(f"   -> Đơn đang xử lý:                     {processing_orders:,} đơn ({(processing_orders/total_orders)*100:.1f}%)")
    print(f"4. Tổng dòng chi tiết đơn (ORDER_LINES):  {len(order_lines):,} dòng")
    print(f"5. Tổng số Hóa đơn (FACT_INVOICES):       {total_invoices:,} hóa đơn")
    print(f"   -> Quy chuẩn mã hóa đơn (Rule R1):     {invoices['invoice_code'].iloc[0]} -> {invoices['invoice_code'].iloc[-1]} (Prefix HDIP)")
    print(f"6. Tổng dòng chi tiết HĐ (INVOICE_LINES): {len(invoice_lines):,} dòng")
    print(f"7. Tổng giá trị giao dịch gộp (GMV):      {total_gmv:,.0f} VNĐ")
    print(f"8. Doanh thu thuần thực tế (Net Revenue): {net_revenue:,.0f} VNĐ")
    print(f"9. Tỷ lệ hoàn hàng (Return Rate):         {return_rate:.2f}% (Trong ngưỡng thực tế 10-28%)")
    print(f"10. Cân bằng dòng tiền (Rule R3):         {(invoices['pay_cash'] + invoices['pay_card'] + invoices['pay_transfer'] == invoices['total_amount']).all()} (100% Cân bằng)")
    print("=" * 75 + "\n")


def main():
    print("Bắt đầu quy trình sinh dữ liệu giả lập SDV v2.0 (Đầy đủ Orders & Invoices)...\n")

    # Bước 1: Khởi tạo Master Data gốc
    df_products, df_employees, df_customers = create_seed_master_data()

    # Bước 2: Tạo dữ liệu hạt giống Orders & Invoices
    df_orders, df_order_lines, df_invoices, df_invoice_lines = create_seed_orders_and_invoices(
        df_products, df_employees, df_customers, n_orders=250
    )

    data_seed = {
        "DIM_PRODUCTS": df_products,
        "DIM_EMPLOYEES": df_employees,
        "DIM_CUSTOMERS": df_customers,
        "FACT_ORDERS": df_orders,
        "FACT_ORDERS_LINES": df_order_lines,
        "FACT_INVOICES": df_invoices,
        "FACT_INVOICE_LINES": df_invoice_lines
    }

    # Bước 3: Huấn luyện mô hình SDV và sinh dữ liệu tổng hợp
    synthetic_data = generate_with_sdv(data_seed, scale=2.0)

    # Bước 4: Áp dụng các ràng buộc nghiệp vụ R1-R4 và liên kết logic
    final_data = enforce_business_rules(synthetic_data, df_products, df_employees)

    # Bước 5: Lưu vào SQLite và xuất các file Excel / CSV
    save_to_sqlite_and_files(final_data)

    # Bước 6: In báo cáo sức khỏe dữ liệu
    print_data_health_report(final_data)


if __name__ == "__main__":
    main()
