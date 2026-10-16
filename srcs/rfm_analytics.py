"""
================================================================================
MODULE PHÂN TÍCH CHÂN DUNG KHÁCH HÀNG & PHÁT HIỆN RESELLER (RFM ENGINE)
Dự án: Smart Fashion Business Analytics Dashboard (FORM Studio)
Phân hệ: SF-03 Customer RFM & Reseller Hunter
================================================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime


def detect_resellers(df_invoices, df_lines):
    """
    Thuật toán phát hiện Reseller / Scalper (Thợ săn deal & con buôn gom hàng):
    Tiêu chí gắn cờ (is_reseller = True):
    1. Có ít nhất một đơn hàng mua >= 3 chiếc cùng loại sản phẩm nhưng khác size (S, M, L)
    2. Tỷ lệ mua phụ kiện (tất, mũ, túi) = 0% (chỉ tập trung mua hero items như hoodie/jacket để bán lại)
    3. Hoặc tần suất mua đột biến trong đợt flash sale nhưng tổng giá trị không kèm phụ kiện
    """
    if df_invoices.empty or df_lines.empty:
        return {}

    # Danh mục phụ kiện thời trang
    accessory_keywords = ["BEANIE", "SOCKS", "CAP", "TOTE"]

    # Ghép thông tin hóa đơn vào dòng chi tiết
    merged = pd.merge(
        df_lines,
        df_invoices[["invoice_code", "customer_code", "sales_channel", "pricebook", "invoice_time"]],
        on="invoice_code",
        how="inner"
    )

    reseller_flags = {}

    for cust_code, group in merged.groupby("customer_code"):
        is_reseller = False
        reasons = []

        # Kiểm tra 1: Mua nhiều size cùng loại sản phẩm trong 1 hóa đơn
        for inv_code, inv_group in group.groupby("invoice_code"):
            # Lấy các mã áo hoodie hoặc jacket
            hoodie_items = inv_group[inv_group["product_code"].str.contains("HOODIE", na=False)]
            if len(hoodie_items) >= 2 and hoodie_items["quantity"].sum() >= 3:
                is_reseller = True
                reasons.append(f"Mua gom {hoodie_items['quantity'].sum()} áo Hoodie khác size trong đơn {inv_code}")
                break

        # Kiểm tra 2: Mua số lượng lớn nhưng tỷ lệ phụ kiện = 0%
        has_accessories = group["product_code"].apply(
            lambda x: any(kw in str(x) for kw in accessory_keywords)
        ).any()

        total_bought = group["quantity"].sum()
        if total_bought >= 4 and not has_accessories:
            is_reseller = True
            reasons.append(f"Mua {total_bought} sản phẩm chính nhưng không mua bất kỳ phụ kiện nào (tỷ lệ phụ kiện 0%)")

        # Kiểm tra 3: Chỉ xuất hiện mua flash sale
        flash_sales_only = (group["pricebook"] == "Flash Sale 11.11").all() and len(group) >= 2
        if flash_sales_only:
            is_reseller = True
            reasons.append("Chỉ mua vào đợt Flash Sale 11.11 giảm sâu")

        if is_reseller:
            reseller_flags[cust_code] = "; ".join(reasons)

    return reseller_flags


def calculate_rfm_segments(df_invoices, df_lines, df_customers, reference_date=None):
    """
    Thuật toán tính điểm RFM thích ứng với nhịp Drop Streetwear:
    - Recency (R): Số ngày tính từ lần mua gần nhất đến mốc phân tích (Drop Tết)
    - Frequency (F): Tổng số đơn hàng thành công (không tính đơn hoàn)
    - Monetary (M): Tổng chi tiêu thực tế (không tính tiền đơn hoàn)
    - Phân vị Percentile (1 - 5 điểm) bằng rank tương đối
    - Phân loại 5 nhóm: VIP / Champions, Loyal Fans, Potential / Newbies, At-risk, Discount Hunters & Resellers
    """
    if df_invoices.empty or df_customers.empty:
        return pd.DataFrame()

    # Chỉ phân tích trên các đơn hàng thành công (loại trừ đơn hoàn trả)
    comp_inv = df_invoices[df_invoices["is_returned"] == 0].copy()

    if reference_date is None:
        reference_date = df_invoices["invoice_time"].max()
    else:
        reference_date = pd.to_datetime(reference_date)

    # 1. Tính toán Recency, Frequency, Monetary cho từng khách hàng
    rfm_table = comp_inv.groupby("customer_code").agg({
        "invoice_time": lambda x: (reference_date - x.max()).days,
        "invoice_code": "nunique",
        "total_amount": "sum"
    }).reset_index()

    rfm_table.columns = ["customer_code", "recency", "frequency", "monetary"]

    # Ghép với toàn bộ danh mục khách hàng (kể cả khách chưa có đơn thành công)
    all_cust = df_customers[["customer_code", "customer_name", "phone", "area"]].copy()
    rfm_df = pd.merge(all_cust, rfm_table, on="customer_code", how="left")

    # Điền giá trị mặc định cho khách chưa mua hoặc mới tạo
    rfm_df["recency"] = rfm_df["recency"].fillna(365)
    rfm_df["frequency"] = rfm_df["frequency"].fillna(0).astype(int)
    rfm_df["monetary"] = rfm_df["monetary"].fillna(0.0)

    # Lọc những khách hàng đã có ít nhất 1 đơn thành công để tính điểm phân vị
    active_mask = rfm_df["frequency"] > 0
    active_df = rfm_df[active_mask].copy()

    if len(active_df) >= 5:
        # 2. Tính điểm phân vị tương đối (Percentile Scoring 1 - 5)
        # Recency: Số ngày càng nhỏ thì điểm càng cao (đảo ngược thứ tự)
        active_df["r_score"] = pd.qcut(
            active_df["recency"].rank(method="first", ascending=False),
            q=5,
            labels=[1, 2, 3, 4, 5]
        ).astype(int)

        # Frequency: Tần suất càng cao thì điểm càng cao
        active_df["f_score"] = pd.qcut(
            active_df["frequency"].rank(method="first"),
            q=5,
            labels=[1, 2, 3, 4, 5]
        ).astype(int)

        # Monetary: Chi tiêu càng nhiều thì điểm càng cao
        active_df["m_score"] = pd.qcut(
            active_df["monetary"].rank(method="first"),
            q=5,
            labels=[1, 2, 3, 4, 5]
        ).astype(int)
    else:
        active_df["r_score"] = 3
        active_df["f_score"] = 3
        active_df["m_score"] = 3

    # Gán lại vào bảng tổng hợp
    rfm_df["r_score"] = active_df["r_score"].reindex(rfm_df.index).fillna(1).astype(int)
    rfm_df["f_score"] = active_df["f_score"].reindex(rfm_df.index).fillna(1).astype(int)
    rfm_df["m_score"] = active_df["m_score"].reindex(rfm_df.index).fillna(1).astype(int)
    rfm_df["rfm_score"] = rfm_df["r_score"].astype(str) + rfm_df["f_score"].astype(str) + rfm_df["m_score"].astype(str)

    # 3. Phát hiện Reseller
    reseller_dict = detect_resellers(df_invoices, df_lines)
    rfm_df["is_reseller"] = rfm_df["customer_code"].apply(lambda c: c in reseller_dict)
    rfm_df["reseller_reason"] = rfm_df["customer_code"].map(reseller_dict).fillna("")

    # 4. Gán nhãn phân khúc chiến lược (Segment Labeling) theo ngữ cảnh FORM Studio
    def assign_segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        is_reseller = row["is_reseller"]

        if is_reseller:
            return "Discount Hunters & Resellers"
        elif r >= 4 and f >= 4 and m >= 4:
            return "VIP / Champions"
        elif r >= 3 and f >= 3 and m >= 3:
            return "Loyal Customers"
        elif r >= 4 and f <= 2:
            return "Potential / Newbies"
        elif r <= 2 and f >= 3 and m >= 3:
            return "At-Risk Customers"
        else:
            return "Casual / Promising"

    rfm_df["segment"] = rfm_df.apply(assign_segment, axis=1)

    # 5. Khuyến nghị hành động tiếp thị cho từng phân khúc
    action_map = {
        "VIP / Champions": "Trao quyền Early Access Drop Tết, tặng thiệp tay, sản phẩm độc quyền (Không gửi voucher giảm giá)",
        "Loyal Customers": "Mời vào Private VIP Community, khảo sát mẫu thiết kế bộ sưu tập mới",
        "Potential / Newbies": "Gửi Brand Story qua Zalo/Email, Lookbook hướng dẫn phối đồ Streetwear",
        "At-Risk Customers": "Kích hoạt chiến dịch Win-Back trước đợt Drop 2 tuần: 'FORM nhớ bạn - Tặng quyền ưu tiên'",
        "Discount Hunters & Resellers": "Chặn khỏi danh sách Early Access; chỉ tiếp thị khi có đợt xả kho mùa cũ",
        "Casual / Promising": "Remarketing giới thiệu các sản phẩm bán chạy (Best-sellers)"
    }
    rfm_df["recommended_action"] = rfm_df["segment"].map(action_map)

    # Ẩn số điện thoại bảo mật (Phone Masking)
    rfm_df["phone_masked"] = rfm_df["phone"].apply(
        lambda p: f"{str(p)[:3]}****{str(p)[-3:]}" if pd.notna(p) and len(str(p)) >= 7 else "N/A"
    )

    return rfm_df


def get_early_access_vip_list(rfm_df, limit=200):
    """
    Trích xuất danh sách 200 suất quà Early Access sạch:
    - Chọn từ phân khúc VIP / Champions và Loyal Customers
    - Loại bỏ 100% đối tượng Reseller (is_reseller == False)
    - Sắp xếp theo Monetary và Frequency giảm dần
    """
    if rfm_df.empty:
        return pd.DataFrame()

    eligible = rfm_df[
        (rfm_df["is_reseller"] == False) &
        (rfm_df["segment"].isin(["VIP / Champions", "Loyal Customers"]))
    ].copy()

    # Sắp xếp theo giá trị đóng góp
    eligible = eligible.sort_values(by=["monetary", "frequency", "r_score"], ascending=[False, False, False])
    early_access_list = eligible.head(limit)

    return early_access_list[[
        "customer_code", "customer_name", "phone_masked", "area",
        "segment", "recency", "frequency", "monetary", "recommended_action"
    ]]
