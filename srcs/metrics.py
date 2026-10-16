"""
================================================================================
MODULE TÍNH TOÁN CHỈ SỐ KINH DOANH & VẬN HÀNH (METRICS ENGINE)
Dự án: Smart Fashion Business Analytics Dashboard (FORM Studio)
Phân hệ: SF-02 Executive 90s Cockpit
================================================================================
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime


def load_database_tables(db_path="data/fashion_brand.db"):
    """
    Tải toàn bộ các bảng dữ liệu từ CSDL SQLite vào các DataFrame của Pandas
    """
    conn = sqlite3.connect(db_path)
    
    df_customers = pd.read_sql_query("SELECT * FROM DIM_CUSTOMERS", conn)
    df_employees = pd.read_sql_query("SELECT * FROM DIM_EMPLOYEES", conn)
    df_products = pd.read_sql_query("SELECT * FROM DIM_PRODUCTS", conn)
    df_orders = pd.read_sql_query("SELECT * FROM FACT_ORDERS", conn)
    df_order_lines = pd.read_sql_query("SELECT * FROM FACT_ORDERS_LINES", conn)
    df_invoices = pd.read_sql_query("SELECT * FROM FACT_INVOICES", conn)
    df_invoice_lines = pd.read_sql_query("SELECT * FROM FACT_INVOICE_LINES", conn)
    
    conn.close()
    
    # Ép kiểu thời gian
    if not df_invoices.empty and "invoice_time" in df_invoices.columns:
        df_invoices["invoice_time"] = pd.to_datetime(df_invoices["invoice_time"])
    if not df_orders.empty and "order_time" in df_orders.columns:
        df_orders["order_time"] = pd.to_datetime(df_orders["order_time"])
        
    return {
        "customers": df_customers,
        "employees": df_employees,
        "products": df_products,
        "orders": df_orders,
        "order_lines": df_order_lines,
        "invoices": df_invoices,
        "invoice_lines": df_invoice_lines
    }


def calculate_executive_kpis(
    df_invoices,
    df_lines,
    df_products,
    channel="Tất cả",
    fee_platform_pct=7.0,
    fee_koc_pct=18.0,
    shipping_return_fee=30000
):
    """
    Tính toán 3 Thẻ Chỉ số Sống còn và các chỉ số Unit Economics:
    - GMV: Tổng giá trị giao dịch gộp
    - Net Revenue: Doanh thu thuần thực nhận (loại bỏ đơn RETURNED)
    - Return Rate (%): Tỷ lệ đơn bị hoàn trả
    - COGS: Giá vốn hàng bán của các đơn thành công
    - Net Margin (VNĐ và %): Lợi nhuận ròng sau trừ phí sàn, KOC và phí hoàn
    """
    if df_invoices.empty:
        return {}

    inv = df_invoices.copy()
    if channel != "Tất cả":
        inv = inv[inv["sales_channel"] == channel]
        
    if inv.empty:
        return {
            "gmv": 0, "net_revenue": 0, "return_rate": 0, "total_invoices": 0,
            "completed_invoices": 0, "returned_invoices": 0, "cogs": 0,
            "fee_platform": 0, "fee_koc": 0, "fee_return_shipping": 0,
            "net_margin": 0, "net_margin_pct": 0, "aov": 0
        }

    total_invoices = len(inv)
    gmv = inv["total_amount"].sum()

    # Phân loại đơn hoàn trả và đơn thành công
    completed_inv = inv[inv["is_returned"] == 0]
    returned_inv = inv[inv["is_returned"] == 1]

    completed_count = len(completed_inv)
    returned_count = len(returned_inv)
    return_rate = (returned_count / total_invoices * 100) if total_invoices > 0 else 0.0

    net_revenue = completed_inv["total_amount"].sum()
    aov = (net_revenue / completed_count) if completed_count > 0 else 0.0

    # Tính toán Giá vốn hàng bán (COGS) dựa trên dòng chi tiết của đơn thành công
    completed_codes = set(completed_inv["invoice_code"])
    comp_lines = df_lines[df_lines["invoice_code"].isin(completed_codes)].copy()

    # Ghép giá vốn từ bảng sản phẩm
    prod_cost_map = dict(zip(df_products["product_code"], df_products["cost_price"]))
    comp_lines["cost_price"] = comp_lines["product_code"].map(prod_cost_map).fillna(0)
    cogs = (comp_lines["cost_price"] * comp_lines["quantity"]).sum()

    # Chi phí biến đổi (Unit Economics)
    fee_platform = net_revenue * (fee_platform_pct / 100.0)
    fee_koc = net_revenue * (fee_koc_pct / 100.0)
    fee_return_shipping = returned_count * shipping_return_fee

    # Lợi nhuận ròng thực tế
    net_margin = net_revenue - cogs - fee_platform - fee_koc - fee_return_shipping
    net_margin_pct = (net_margin / net_revenue * 100) if net_revenue > 0 else 0.0

    return {
        "gmv": gmv,
        "net_revenue": net_revenue,
        "return_rate": return_rate,
        "total_invoices": total_invoices,
        "completed_invoices": completed_count,
        "returned_invoices": returned_count,
        "aov": aov,
        "cogs": cogs,
        "fee_platform": fee_platform,
        "fee_koc": fee_koc,
        "fee_return_shipping": fee_return_shipping,
        "net_margin": net_margin,
        "net_margin_pct": net_margin_pct
    }


def generate_ccr_narrative(kpis, channel="Tất cả"):
    """
    Sinh văn bản nhận định điều hành tự động theo công thức CCR:
    - Context (Bối cảnh): Doanh thu gộp và khối lượng giao dịch
    - Complication (Điểm nghẽn): Mức độ thất thoát do hoàn hàng và chi phí sàn/KOC
    - Resolution (Hành động chiến lược): Quyết định tức thời cho Founder Minh
    """
    if not kpis or kpis.get("total_invoices", 0) == 0:
        return {
            "context": "Chưa có đủ dữ liệu giao dịch cho bộ lọc được chọn.",
            "complication": "Không thể phân tích điểm nghẽn tài chính.",
            "resolution": "Vui lòng mở rộng phạm vi thời gian hoặc chọn tất cả kênh bán."
        }

    gmv = kpis["gmv"]
    net_rev = kpis["net_revenue"]
    ret_rate = kpis["return_rate"]
    net_margin = kpis["net_margin"]
    margin_pct = kpis["net_margin_pct"]
    fee_koc = kpis["fee_koc"]
    fee_plat = kpis["fee_platform"]
    cash_gap = gmv - net_rev

    # 1. Context
    channel_txt = f"trên kênh {channel}" if channel != "Tất cả" else "trên toàn bộ kênh phân phối"
    context = (
        f"FORM Studio ghi nhận tổng giá trị giao dịch gộp (GMV) đạt **{gmv:,.0f} VNĐ** "
        f"từ **{kpis['total_invoices']:,} đơn hàng** {channel_txt}. "
        f"Giá trị trung bình mỗi đơn (AOV) đạt **{kpis['aov']:,.0f} VNĐ**."
    )

    # 2. Complication
    if ret_rate > 15.0:
        comp_status = "báo động đỏ"
        comp_reason = (
            f"Tỷ lệ hoàn hàng đang ở mức **{ret_rate:.1f}% ({comp_status})**, "
            f"khiến **{cash_gap:,.0f} VNĐ** doanh thu bị bốc hơi và gánh thêm chi phí vận chuyển hoàn hai chiều. "
            f"Cùng với chi phí hoa hồng KOC ({fee_koc:,.0f} VNĐ) và phí sàn ({fee_plat:,.0f} VNĐ), "
            f"biên lợi nhuận ròng thực tế co hẹp chỉ còn **{margin_pct:.1f}%** ({net_margin:,.0f} VNĐ)."
        )
    else:
        comp_reason = (
            f"Tỷ lệ hoàn hàng kiểm soát ở mức **{ret_rate:.1f}%**. "
            f"Tuy nhiên, khoảng chênh lệch dòng tiền GMV vs. Thực nhận vẫn là **{cash_gap:,.0f} VNĐ**. "
            f"Biên lợi nhuận ròng đạt **{margin_pct:.1f}%** ({net_margin:,.0f} VNĐ)."
        )

    # 3. Resolution
    if ret_rate > 15.0:
        resolution = (
            "**Hành động ngay:**\n"
            "1. Tạm dừng các đợt Flash Sale giảm sâu -70% trên TikTok Shop để cắt giảm nhóm Discount Hunter có tỷ lệ hoàn cao.\n"
            "2. Cập nhật lại Bảng kích cỡ (Size Chart) chi tiết cho mẫu Áo Hoodie để giảm tình trạng mua nhầm size.\n"
            "3. Kích hoạt gói bán kèm (Bundle) **Hoodie + Beanie** để tăng AOV bù đắp chi phí vận hành và giải phóng 200 chiếc Beanie tồn đọng."
        )
    else:
        resolution = (
            "**Hành động tiếp theo:**\n"
            "1. Tiếp tục duy trì chuẩn dịch vụ và chuẩn bị mở bán sớm (Early Access) cho nhóm 200 khách Fan ruột (VIP).\n"
            "2. Triển khai thử nghiệm combo Tết Streetwear để giải phóng triệt để 200 mũ Beanie trong kho."
        )

    return {
        "context": context,
        "complication": comp_reason,
        "resolution": resolution
    }


def get_timeline_cash_gap(df_invoices, channel="Tất cả"):
    """
    Tổng hợp dữ liệu theo ngày phục vụ Biểu đồ đường kép (GMV vs. Net Revenue)
    """
    if df_invoices.empty:
        return pd.DataFrame()

    inv = df_invoices.copy()
    if channel != "Tất cả":
        inv = inv[inv["sales_channel"] == channel]

    inv["date"] = inv["invoice_time"].dt.date

    # Tính GMV theo ngày
    gmv_by_date = inv.groupby("date")["total_amount"].sum().reset_index(name="gmv")

    # Tính Net Revenue theo ngày (chỉ tính đơn hoàn thành)
    completed_inv = inv[inv["is_returned"] == 0]
    net_by_date = completed_inv.groupby("date")["total_amount"].sum().reset_index(name="net_revenue")

    # Merge lại
    timeline = pd.merge(gmv_by_date, net_by_date, on="date", how="left").fillna(0)
    timeline["cash_gap"] = timeline["gmv"] - timeline["net_revenue"]
    timeline["date"] = pd.to_datetime(timeline["date"])
    timeline = timeline.sort_values("date")

    return timeline


def get_inventory_alerts(df_products, df_lines):
    """
    Widget cảnh báo tồn kho:
    Xác định các sản phẩm có tồn kho cao nhưng tốc độ bán chậm (đặc biệt BEANIE-001)
    """
    if df_products.empty:
        return pd.DataFrame()

    prod = df_products.copy()

    # Tính tổng số lượng đã bán từ invoice_lines
    if not df_lines.empty:
        sold_qty = df_lines.groupby("product_code")["quantity"].sum().to_dict()
    else:
        sold_qty = {}

    prod["sold_qty"] = prod["product_code"].map(sold_qty).fillna(0).astype(int)
    prod["turnover_ratio"] = prod.apply(
        lambda r: (r["sold_qty"] / (r["stock_on_hand"] + r["sold_qty"])) if (r["stock_on_hand"] + r["sold_qty"]) > 0 else 0,
        axis=1
    )

    # Đánh giá cảnh báo
    def evaluate_alert(row):
        code = row["product_code"]
        stock = row["stock_on_hand"]
        sold = row["sold_qty"]
        if code == "BEANIE-001":
            return "CẢNH BÁO TỒN ĐỌNG (Mùa cũ: 200 chiếc -> Cần đóng Bundle ngay!)"
        elif stock <= 20 and sold >= 30:
            return "CẢNH BÁO SẮP HẾT HÀNG (Cần nhập thêm vải)"
        elif stock > 300 and sold < 15:
            return "Cảnh báo bán chậm"
        else:
            return "Bình thường"

    prod["alert_status"] = prod.apply(evaluate_alert, axis=1)
    return prod[["product_code", "product_name", "stock_on_hand", "sold_qty", "sale_price", "alert_status"]]


def get_order_conversion_funnel(df_orders, df_invoices):
    """
    Thống kê phễu chuyển đổi: Đặt hàng -> Hóa đơn -> Hoàn thành -> Hoàn trả
    """
    total_orders = len(df_orders) if not df_orders.empty else 0
    cancelled_orders = len(df_orders[df_orders["status"] == "Đã hủy"]) if not df_orders.empty else 0
    completed_orders = len(df_orders[df_orders["status"] == "Đã hoàn thành"]) if not df_orders.empty else 0
    
    total_invoices = len(df_invoices) if not df_invoices.empty else 0
    returned_invoices = len(df_invoices[df_invoices["is_returned"] == 1]) if not df_invoices.empty else 0
    success_invoices = total_invoices - returned_invoices

    return {
        "total_orders": total_orders,
        "cancelled_orders": cancelled_orders,
        "completed_orders": completed_orders,
        "total_invoices": total_invoices,
        "success_invoices": success_invoices,
        "returned_invoices": returned_invoices
    }
