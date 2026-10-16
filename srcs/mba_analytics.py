"""
================================================================================
FORM STUDIO - PHÂN HỆ SF-04: KHÁM PHÁ GIỎ HÀNG & GỢI Ý BUNDLE (MARKET BASKET)
Thuật toán: Apriori Association Rule Mining kết hợp Ma trận 4 Tầng lọc
Tài liệu SRS: docs/03_Dac_ta_Yeu_cau_Phan_mem_SRS.md
================================================================================
"""

import sqlite3
from itertools import combinations
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np


def load_mba_data(db_path: str = "data/fashion_brand.db") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Nạp dữ liệu chi tiết hóa đơn, đơn hàng và sản phẩm phục vụ Market Basket Analysis.
    """
    conn = sqlite3.connect(db_path)
    
    # Bảng chi tiết hóa đơn (chỉ lấy các hóa đơn hoàn thành, không lấy hàng hoàn)
    query_invoices = """
        SELECT 
            il.invoice_code,
            il.product_code,
            p.product_name,
            p.category_path,
            p.cost_price,
            p.sale_price,
            p.stock_on_hand,
            i.customer_code,
            i.sales_channel,
            i.invoice_time
        FROM FACT_INVOICE_LINES il
        JOIN FACT_INVOICES i ON il.invoice_code = i.invoice_code
        JOIN DIM_PRODUCTS p ON il.product_code = p.product_code
        WHERE i.is_returned = 0
    """
    df_lines = pd.read_sql(query_invoices, conn)
    
    # Bảng sản phẩm
    df_products = pd.read_sql("SELECT * FROM DIM_PRODUCTS", conn)
    
    # Bảng hóa đơn
    df_invoices = pd.read_sql("SELECT * FROM FACT_INVOICES WHERE is_returned = 0", conn)
    
    conn.close()
    return df_lines, df_products, df_invoices


def calculate_basket_kpis(df_lines: pd.DataFrame, df_invoices: pd.DataFrame) -> Dict[str, Any]:
    """
    Tính toán các chỉ số KPI giỏ hàng tổng quan của FORM Studio:
    - Tổng số giao dịch
    - Tỷ lệ mua kèm (Cross-sell Rate / Multi-item Basket %)
    - Kích thước giỏ hàng trung bình (Items per Basket)
    - Giá trị đơn hàng trung bình (AOV)
    """
    total_tx = df_invoices["invoice_code"].nunique()
    if total_tx == 0:
        return {
            "total_transactions": 0,
            "multi_item_rate": 0.0,
            "avg_items_per_basket": 0.0,
            "aov": 0.0,
            "cross_sell_count": 0
        }
    
    # Đếm số SKU trong mỗi hóa đơn
    items_per_invoice = df_lines.groupby("invoice_code")["product_code"].nunique()
    multi_item_invoices = (items_per_invoice > 1).sum()
    multi_item_rate = (multi_item_invoices / total_tx) * 100.0
    
    # Tổng số lượng sản phẩm mỗi hóa đơn (kể cả quantity)
    total_items_per_invoice = df_lines.groupby("invoice_code")["product_code"].count()
    avg_items = total_items_per_invoice.mean()
    
    # AOV
    aov = df_invoices["total_amount"].mean() if "total_amount" in df_invoices.columns else 0.0
    
    return {
        "total_transactions": total_tx,
        "multi_item_invoices": int(multi_item_invoices),
        "multi_item_rate": float(multi_item_rate),
        "avg_items_per_basket": float(avg_items),
        "aov": float(aov)
    }


def mine_association_rules(
    df_lines: pd.DataFrame,
    min_support: float = 0.02,
    min_confidence: float = 0.20,
    min_lift: float = 1.0
) -> pd.DataFrame:
    """
    Thuật toán Apriori thuần Python để khai phá luật kết hợp (Association Rules):
    Support(A -> B) = P(A & B) = count(A & B) / N
    Confidence(A -> B) = P(B|A) = count(A & B) / count(A)
    Lift(A -> B) = Confidence(A -> B) / Support(B) = P(A & B) / (P(A) * P(B))
    """
    # Gom các sản phẩm theo từng giỏ hàng (invoice_code)
    baskets = df_lines.groupby("invoice_code")["product_code"].apply(lambda s: sorted(list(set(s)))).tolist()
    n_transactions = len(baskets)
    
    if n_transactions == 0:
        return pd.DataFrame()

    # 1. Tần suất xuất hiện của từng sản phẩm đơn lẻ (1-itemsets)
    item_counts: Dict[str, int] = {}
    for basket in baskets:
        for item in basket:
            item_counts[item] = item_counts.get(item, 0) + 1
            
    # Lọc 1-itemsets đạt min_support
    freq_items = {item: cnt for item, cnt in item_counts.items() if (cnt / n_transactions) >= min_support}

    # 2. Tần suất xuất hiện của các cặp sản phẩm (2-itemsets)
    pair_counts: Dict[Tuple[str, str], int] = {}
    for basket in baskets:
        valid_items_in_basket = [item for item in basket if item in freq_items]
        if len(valid_items_in_basket) >= 2:
            for pair in combinations(valid_items_in_basket, 2):
                pair_counts[pair] = pair_counts.get(pair, 0) + 1

    # 3. Tạo các luật kết hợp (Association Rules: A -> B và B -> A)
    rules = []
    for (item_a, item_b), count_ab in pair_counts.items():
        support_ab = count_ab / n_transactions
        if support_ab < min_support:
            continue

        # Luật 1: item_a -> item_b
        support_a = item_counts[item_a] / n_transactions
        support_b = item_counts[item_b] / n_transactions
        
        conf_a_to_b = support_ab / support_a if support_a > 0 else 0
        lift_a_to_b = conf_a_to_b / support_b if support_b > 0 else 0
        
        if conf_a_to_b >= min_confidence and lift_a_to_b >= min_lift:
            rules.append({
                "antecedent": item_a,
                "consequent": item_b,
                "pair_count": count_ab,
                "support": round(support_ab, 4),
                "confidence": round(conf_a_to_b, 4),
                "lift": round(lift_a_to_b, 3)
            })

        # Luật 2: item_b -> item_a
        conf_b_to_a = support_ab / support_b if support_b > 0 else 0
        lift_b_to_a = conf_b_to_a / support_a if support_a > 0 else 0
        
        if conf_b_to_a >= min_confidence and lift_b_to_a >= min_lift:
            rules.append({
                "antecedent": item_b,
                "consequent": item_a,
                "pair_count": count_ab,
                "support": round(support_ab, 4),
                "confidence": round(conf_b_to_a, 4),
                "lift": round(lift_b_to_a, 3)
            })

    df_rules = pd.DataFrame(rules)
    if not df_rules.empty:
        df_rules = df_rules.sort_values(by=["lift", "confidence"], ascending=[False, False]).reset_index(drop=True)
    return df_rules


def apply_four_layer_filter(
    df_rules: pd.DataFrame,
    df_products: pd.DataFrame,
    enable_inventory_filter: bool = True,
    min_stock_consequent: int = 20,
    enable_cultural_filter: bool = True
) -> pd.DataFrame:
    """
    ÁP DỤNG MA TRẬN 4 TẦNG LỌC ĐỘT PHÁ CỦA FORM STUDIO:
    - Tầng 1: Lọc Thống Kê (Support, Confidence, Lift) - đã xử lý ở Apriori
    - Tầng 2: Lọc Tồn Kho (Consequent có tồn kho >= min_stock_consequent, bảo đảm không bị hủy đơn)
    - Tầng 3: Lọc Văn Hóa Streetwear (Loại bỏ Proxy Buy - mua hộ cùng loại áo khác size S+M)
    - Tầng 4: Gắn nhãn Phân khúc Khách hàng mục tiêu (VIP Early Access, Newbie, At-Risk)
    """
    if df_rules.empty:
        return df_rules

    # Merge thông tin sản phẩm
    prod_dict = df_products.set_index("product_code").to_dict(orient="index")
    
    enriched_rules = []
    for _, row in df_rules.iterrows():
        a_code = row["antecedent"]
        b_code = row["consequent"]
        
        a_info = prod_dict.get(a_code, {})
        b_info = prod_dict.get(b_code, {})
        
        a_name = a_info.get("product_name", a_code)
        b_name = b_info.get("product_name", b_code)
        
        a_stock = a_info.get("stock_on_hand", 0)
        b_stock = b_info.get("stock_on_hand", 0)
        
        a_price = a_info.get("sale_price", 0.0)
        b_price = b_info.get("sale_price", 0.0)
        
        a_cost = a_info.get("cost_price", 0.0)
        b_cost = b_info.get("cost_price", 0.0)
        
        # --- TẦNG 2: LỌC TỒN KHO ---
        # Consequent phải còn đủ hàng để bán kèm
        pass_stock_filter = True
        if enable_inventory_filter and b_stock < min_stock_consequent:
            pass_stock_filter = False

        # --- TẦNG 3: LỌC VĂN HÓA STREETWEAR (CULTURAL & OUTFIT FILTER) ---
        # Phát hiện Proxy Buy: Nếu cả A và B cùng là Hoodie hoặc cùng là T-shirt (chỉ khác size)
        is_proxy_buy = False
        is_same_model_diff_size = False
        
        a_is_hoodie = "HOODIE" in a_code
        b_is_hoodie = "HOODIE" in b_code
        a_is_tee = "TEE" in a_code
        b_is_tee = "TEE" in b_code
        
        if (a_is_hoodie and b_is_hoodie) or (a_is_tee and b_is_tee):
            is_same_model_diff_size = True
            is_proxy_buy = True

        pass_cultural_filter = True
        if enable_cultural_filter and is_proxy_buy:
            pass_cultural_filter = False

        # --- TẦNG 4: ĐỊNH HƯỚNG PHÂN KHÚC MỤC TIÊU (RFM TARGETING) ---
        # Phân loại Bundle dựa trên bản chất sản phẩm và giá trị
        combo_price = a_price + b_price
        
        if "BEANIE" in b_code or "BEANIE" in a_code:
            target_segment = "Giải Cứu Tồn Kho (Đề xuất Flash Sale / Toàn bộ KH)"
            bundle_theme = "Combo Streetwear Mùa Đông (Tết Duo Set)"
        elif combo_price >= 1000000 or "BOMBER" in a_code or "BOMBER" in b_code:
            target_segment = "VIP Early Access & Khách Thân Thiết"
            bundle_theme = "Premium Streetwear Combo (Outerwear Set)"
        elif "TEE" in a_code and "CARGO" in b_code:
            target_segment = "Khách Hàng Mới (Newbie Onboarding)"
            bundle_theme = "Streetwear Outfit Toàn Diện (Tee + Cargo)"
        elif "SOCKS" in b_code or "CAP" in b_code or "TOTE" in b_code:
            target_segment = "Khách Hàng Có Nguy Cơ Rời Bỏ & Khách Vãng Lai"
            bundle_theme = "Gợi Ý Mua Kèm Phụ Kiện (Add-on Essentials)"
        else:
            target_segment = "Đại Chúng (Mass Segment)"
            bundle_theme = "Mix & Match Phong Cách Tự Do"

        enriched_rules.append({
            "antecedent_code": a_code,
            "antecedent_name": a_name,
            "consequent_code": b_code,
            "consequent_name": b_name,
            "pair_count": row["pair_count"],
            "support": row["support"],
            "confidence": row["confidence"],
            "lift": row["lift"],
            "consequent_stock": b_stock,
            "combo_original_price": combo_price,
            "combo_cost": a_cost + b_cost,
            "is_proxy_buy": is_proxy_buy,
            "pass_stock_filter": pass_stock_filter,
            "pass_cultural_filter": pass_cultural_filter,
            "target_segment": target_segment,
            "bundle_theme": bundle_theme
        })

    df_enriched = pd.DataFrame(enriched_rules)
    
    # Lọc theo các cờ đã kích hoạt
    filtered_df = df_enriched.copy()
    if enable_inventory_filter:
        filtered_df = filtered_df[filtered_df["pass_stock_filter"] == True]
    if enable_cultural_filter:
        filtered_df = filtered_df[filtered_df["pass_cultural_filter"] == True]
        
    return filtered_df.reset_index(drop=True)


def calculate_beanie_liquidation_case(
    beanie_code: str = "BEANIE-001",
    hoodie_code: str = "FORM-HOODIE-BLK-M",
    bundle_selling_price: float = 799000.0,
    df_products: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    MÔ PHỎNG CHI TIẾT CHIẾN DỊCH GIẢI CỨU 200 MŨ BEANIE TỒN KHO:
    - Giá bán lẻ Hoodie: 590,000 VNĐ (Cost: 280,000 VNĐ)
    - Giá bán lẻ Beanie: 290,000 VNĐ (Cost: 110,000 VNĐ)
    - Tổng giá niêm yết: 880,000 VNĐ
    - Giá Bundle đề xuất: 799,000 VNĐ (Ưu đãi ~ 9.2%)
    - Đánh giá AOV Uplift, Lợi nhuận gộp, và Tiền mặt giải phóng
    """
    if df_products is not None:
        p_dict = df_products.set_index("product_code").to_dict(orient="index")
        beanie_info = p_dict.get(beanie_code, {})
        hoodie_info = p_dict.get(hoodie_code, {})
        
        beanie_sale = beanie_info.get("sale_price", 290000.0)
        beanie_cost = beanie_info.get("cost_price", 110000.0)
        beanie_stock = beanie_info.get("stock_on_hand", 200)
        
        hoodie_sale = hoodie_info.get("sale_price", 590000.0)
        hoodie_cost = hoodie_info.get("cost_price", 280000.0)
    else:
        beanie_sale, beanie_cost, beanie_stock = 290000.0, 110000.0, 200
        hoodie_sale, hoodie_cost = 590000.0, 280000.0

    original_total = hoodie_sale + beanie_sale
    bundle_discount_amt = original_total - bundle_selling_price
    bundle_discount_pct = (bundle_discount_amt / original_total) * 100.0
    
    total_cost = hoodie_cost + beanie_cost
    gross_profit_per_bundle = bundle_selling_price - total_cost
    gross_margin_pct = (gross_profit_per_bundle / bundle_selling_price) * 100.0
    
    # AOV Uplift: So với việc khách chỉ mua Hoodie
    aov_uplift_pct = ((bundle_selling_price - hoodie_sale) / hoodie_sale) * 100.0
    
    # Kịch bản giải phóng toàn bộ số mũ Beanie tồn kho
    total_revenue_potential = beanie_stock * bundle_selling_price
    total_gross_profit_potential = beanie_stock * gross_profit_per_bundle
    trapped_capital_recovered = beanie_stock * beanie_cost  # 200 * 110k = 22 triệu

    return {
        "beanie_code": beanie_code,
        "beanie_stock": beanie_stock,
        "hoodie_sale_price": hoodie_sale,
        "beanie_sale_price": beanie_sale,
        "original_total_price": original_total,
        "bundle_selling_price": bundle_selling_price,
        "bundle_discount_amt": bundle_discount_amt,
        "bundle_discount_pct": bundle_discount_pct,
        "total_cost": total_cost,
        "gross_profit_per_bundle": gross_profit_per_bundle,
        "gross_margin_pct": gross_margin_pct,
        "aov_uplift_pct": aov_uplift_pct,
        "trapped_capital_recovered": trapped_capital_recovered,
        "total_revenue_potential": total_revenue_potential,
        "total_gross_profit_potential": total_gross_profit_potential
    }


def generate_cross_sell_matrix(df_lines: pd.DataFrame, df_products: pd.DataFrame) -> pd.DataFrame:
    """
    Sinh ma trận tương quan mua kèm (Co-occurrence / Affinity Matrix) giữa các SKU:
    Hàng i và Cột j biểu thị số lượng hóa đơn mua cùng giữa sản phẩm i và j.
    """
    # Lấy danh sách sản phẩm xuất hiện trong hóa đơn
    valid_codes = sorted(df_lines["product_code"].unique().tolist())
    matrix = pd.DataFrame(0, index=valid_codes, columns=valid_codes)
    
    # Gom sản phẩm theo từng hóa đơn
    baskets = df_lines.groupby("invoice_code")["product_code"].apply(lambda s: list(set(s))).tolist()
    
    for basket in baskets:
        if len(basket) >= 2:
            for item1, item2 in combinations(basket, 2):
                if item1 in matrix.index and item2 in matrix.columns:
                    matrix.loc[item1, item2] += 1
                    matrix.loc[item2, item1] += 1
        elif len(basket) == 1:
            item = basket[0]
            if item in matrix.index:
                matrix.loc[item, item] += 1

    # Tạo nhãn tên sản phẩm gọn gàng
    name_map = dict(zip(df_products["product_code"], df_products["product_name"]))
    short_labels = [f"{c} ({name_map.get(c, c)[:12]}..)" for c in valid_codes]
    
    matrix.index = short_labels
    matrix.columns = short_labels
    return matrix
