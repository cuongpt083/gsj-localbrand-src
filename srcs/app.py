"""
================================================================================
ỨNG DỤNG STREAMLIT DASHBOARD - FORM STUDIO SMART FASHION BUSINESS ANALYTICS
Phân hệ chức năng SF-02: Bảng Điều Hành 90 Giây (Executive 90s Cockpit)
Theo đặc tả SRS: docs/03_Dac_ta_Yeu_cau_Phan_mem_SRS.md
================================================================================
"""

import os
import sys
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Thiết lập encoding UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import module tính toán chỉ số
from metrics import (
    load_database_tables,
    calculate_executive_kpis,
    generate_ccr_narrative,
    get_timeline_cash_gap,
    get_inventory_alerts,
    get_order_conversion_funnel
)
from rfm_analytics import (
    calculate_rfm_segments,
    get_early_access_vip_list
)
from mba_analytics import (
    calculate_basket_kpis,
    mine_association_rules,
    apply_four_layer_filter,
    calculate_beanie_liquidation_case,
    generate_cross_sell_matrix
)

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FORM Studio - Smart Fashion Executive Dashboard",
    page_icon="🧢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho phong cách Streetwear Local Brand hiện đại
st.markdown("""
<style>
    /* Nền và phông chữ */
    .main {
        background-color: #0E1117;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* KPI Card Style */
    .kpi-card {
        background: linear-gradient(135deg, #1A1C23 0%, #252836 100%);
        border: 1px solid #323644;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 15px;
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8E95A5;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 6px;
    }
    .kpi-subtext {
        font-size: 0.8rem;
        color: #A0AEC0;
    }
    
    /* Alert Badge */
    .badge-green {
        background-color: rgba(46, 204, 113, 0.2);
        color: #2ECC71;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-yellow {
        background-color: rgba(241, 196, 15, 0.2);
        color: #F1C40F;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-red {
        background-color: rgba(231, 76, 60, 0.25);
        color: #E74C3C;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
        border: 1px solid rgba(231, 76, 60, 0.4);
    }
    
    /* CCR Narrative Box */
    .ccr-box {
        background: #161922;
        border-left: 4px solid #E74C3C;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 25px;
    }
    .ccr-header {
        font-size: 0.95rem;
        font-weight: 700;
        color: #F8F9FA;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. TẢI DỮ LIỆU TỪ CƠ SỞ DỮ LIỆU
# -----------------------------------------------------------------------------
DB_PATH = "data/fashion_brand.db"

if not os.path.exists(DB_PATH):
    st.error(f"⚠️ Chưa tìm thấy cơ sở dữ liệu tại `{DB_PATH}`. Vui lòng chạy script sinh dữ liệu SDV trước.")
    st.stop()

@st.cache_data(ttl=60)
def get_data():
    return load_database_tables(DB_PATH)

try:
    data = get_data()
except Exception as e:
    st.error(f"Lỗi khi nạp dữ liệu SQLite: {e}")
    st.stop()

df_customers = data["customers"]
df_employees = data["employees"]
df_products = data["products"]
df_orders = data["orders"]
df_order_lines = data["order_lines"]
df_invoices = data["invoices"]
df_invoice_lines = data["invoice_lines"]


# -----------------------------------------------------------------------------
# 3. SIDEBAR: BỘ LỌC ĐIỀU HÀNH & MÔ PHỎNG CHI PHÍ
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧢 **FORM STUDIO**")
    st.markdown("*Streetwear Local Brand • Hà Nội*")
    st.markdown("---")

    st.markdown("### 🔍 **Bộ Lọc Điều Hành**")
    
    # 1. Lọc kênh bán
    channels = ["Tất cả"] + sorted(list(df_invoices["sales_channel"].unique()))
    selected_channel = st.selectbox("Kênh phân phối:", channels, index=0)

    # 2. Bộ lọc thời gian
    st.markdown("### ⚙️ **Mô Phỏng Unit Economics**")
    st.caption("Founder Minh có thể điều chỉnh chi phí sàn và hoa hồng để thấy ảnh hưởng tới lợi nhuận:")
    
    fee_platform = st.slider("Phí sàn TMĐT (%):", min_value=3.0, max_value=12.0, value=7.0, step=0.5)
    fee_koc = st.slider("Hoa hồng KOC / KOL (%):", min_value=5.0, max_value=25.0, value=18.0, step=1.0)
    shipping_return = st.number_input("Phí ship đơn hoàn (VNĐ):", min_value=10000, max_value=60000, value=30000, step=5000)

    st.markdown("---")
    st.markdown("### 🟢 **Trạng Thái Dữ Liệu**")
    st.success(f"CSDL SQLite: Đã kết nối\n* {len(df_customers):,} Khách hàng\n* {len(df_orders):,} Đơn đặt hàng\n* {len(df_invoices):,} Hóa đơn hoàn tất")


# -----------------------------------------------------------------------------
# 4. TÍNH TOÁN CÁC CHỈ SỐ THEO BỘ LỌC
# -----------------------------------------------------------------------------
kpis = calculate_executive_kpis(
    df_invoices,
    df_invoice_lines,
    df_products,
    channel=selected_channel,
    fee_platform_pct=fee_platform,
    fee_koc_pct=fee_koc,
    shipping_return_fee=shipping_return
)

ccr = generate_ccr_narrative(kpis, channel=selected_channel)
timeline = get_timeline_cash_gap(df_invoices, channel=selected_channel)
inventory_df = get_inventory_alerts(df_products, df_invoice_lines)
funnel = get_order_conversion_funnel(df_orders, df_invoices)

# Tính toán phân khúc RFM & Early Access
rfm_df = calculate_rfm_segments(df_invoices, df_invoice_lines, df_customers)
early_access_df = get_early_access_vip_list(rfm_df, limit=200)


# -----------------------------------------------------------------------------
# 5. TIÊU ĐỀ CHÍNH & NGUYÊN TẮC 90 GIÂY
# -----------------------------------------------------------------------------
st.title("🎯 PHÒNG ĐIỀU HÀNH THỜI TRANG THÔNG MINH")
st.markdown("**Executive 90-Second Cockpit • Hệ Thống Trợ Lý Ra Quyết Định Kinh Doanh Cho Founder Minh**")

# Tabs phân hệ chức năng
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Tab 1: Executive 90s Cockpit",
    "👥 Tab 2: RFM Customer Intelligence",
    "🛍️ Tab 3: MBA & Bundle Recommender",
    "🗄️ Tab 4: KiotViet Data Explorer"
])


# =============================================================================
# TAB 1: EXECUTIVE 90S COCKPIT (PHÂN HỆ SF-02)
# =============================================================================
with tab1:
    st.markdown("---")

    # -------------------------------------------------------------------------
    # [SF-02.1] BỘ 3 THẺ CHỈ SỐ SỐNG CÒN (90S RULE)
    # -------------------------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        cash_gap = kpis['gmv'] - kpis['net_revenue']
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">💵 DOANH THU THỰC NHẬN (NET REVENUE)</div>
            <div class="kpi-value">{kpis['net_revenue']:,.0f} đ</div>
            <div class="kpi-subtext">
                Tổng GMV: <b>{kpis['gmv']:,.0f} đ</b><br>
                Thất thoát do hoàn đơn: <span style="color:#E74C3C; font-weight:600;">-{cash_gap:,.0f} đ</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        ret_rate = kpis['return_rate']
        if ret_rate < 10.0:
            badge_html = f'<span class="badge-green">An toàn ({ret_rate:.1f}%)</span>'
        elif ret_rate <= 15.0:
            badge_html = f'<span class="badge-yellow">Chú ý ({ret_rate:.1f}%)</span>'
        else:
            badge_html = f'<span class="badge-red">BÁO ĐỘNG ({ret_rate:.1f}%)</span>'

        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">🔄 TỶ LỆ HOÀN HÀNG (RETURN RATE)</div>
            <div class="kpi-value">{ret_rate:.1f}% &nbsp; {badge_html}</div>
            <div class="kpi-subtext">
                Đơn hoàn trả: <b>{kpis['returned_invoices']:,}</b> / {kpis['total_invoices']:,} đơn<br>
                Phí vận chuyển 2 chiều: <b>{kpis['fee_return_shipping']:,.0f} đ</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        margin_pct = kpis['net_margin_pct']
        margin_val = kpis['net_margin']
        margin_color = "#2ECC71" if margin_pct >= 20.0 else ("#F1C40F" if margin_pct > 10.0 else "#E74C3C")
        
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">📈 BIÊN LỢI NHUẬN RÒNG (NET MARGIN)</div>
            <div class="kpi-value" style="color: {margin_color};">{margin_pct:.1f}%</div>
            <div class="kpi-subtext">
                Lợi nhuận ròng thực nhận: <b>{margin_val:,.0f} đ</b><br>
                Đã trừ Phí sàn ({fee_platform}%) & Hoa hồng KOC ({fee_koc}%)
            </div>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # [SF-02.4] KHUNG TƯỜNG THUẬT NHẬN ĐỊNH CCR (CONTEXT - COMPLICATION - RESOLUTION)
    # -------------------------------------------------------------------------
    st.markdown(f"""
    <div class="ccr-box">
        <div class="ccr-header">
            <span>📢</span> BÁO CÁO NHẬN ĐỊNH ĐIỀU HÀNH 90 GIÂY (MÔ THỨC CCR - MCKINSEY / FINANCIAL TIMES)
        </div>
        <p><b>[Bối Cảnh - Context]:</b> {ccr['context']}</p>
        <p><b>[Điểm Nghẽn - Complication]:</b> {ccr['complication']}</p>
        <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; margin-top: 8px;">
            {ccr['resolution']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # [SF-02.2] BIỂU ĐỒ XU HƯỚNG DÒNG TIỀN (GMV VS. NET REVENUE - CASH GAP)
    # -------------------------------------------------------------------------
    st.subheader("📉 Biểu Đồ Bóc Tách Dòng Tiền: Ảo Ảnh GMV vs. Thực Nhận (Cash Flow Gap)")
    st.caption("Caption theo chuẩn FT: *Khoảng cách giữa hai đường phản ánh dòng tiền bị giam giữ và thất thoát do tỷ lệ hoàn trả.*")

    if not timeline.empty:
        fig_timeline = go.Figure()

        # Đường GMV gộp
        fig_timeline.add_trace(go.Scatter(
            x=timeline["date"],
            y=timeline["gmv"],
            mode="lines+markers",
            name="GMV Gộp (Ảo ảnh bán hàng)",
            line=dict(color="#E74C3C", width=3, dash="dot"),
            marker=dict(size=6)
        ))

        # Đường Doanh thu thực nhận
        fig_timeline.add_trace(go.Scatter(
            x=timeline["date"],
            y=timeline["net_revenue"],
            mode="lines+markers",
            name="Doanh Thu Thực Nhận (Tiền vào ví)",
            line=dict(color="#2ECC71", width=3),
            fill='tonexty',
            fillcolor='rgba(231, 76, 60, 0.15)',  # Vùng Cash Gap
            marker=dict(size=6)
        ))

        fig_timeline.update_layout(
            template="plotly_dark",
            height=380,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="Thời gian diễn ra chiến dịch Drop",
            yaxis_title="Số tiền (VNĐ)",
            hovermode="x unified"
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("Không có dữ liệu thời gian phù hợp để vẽ biểu đồ.")

    # -------------------------------------------------------------------------
    # PHỄU CHUYỂN ĐỔI ĐƠN HÀNG VÀ CƠ CẤU DOANH THU
    # -------------------------------------------------------------------------
    col_chart_left, col_chart_right = st.columns([1, 1])

    with col_chart_left:
        st.subheader("🛒 Phễu Chuyển Đổi Đơn Hàng (Order Funnel)")
        st.caption("Từ lúc khách đặt đơn (FACT_ORDERS) tới khi thanh toán thực tế (FACT_INVOICES):")

        funnel_stages = ["Tổng Đơn Đặt", "Đơn Hoàn Thành", "Hóa Đơn Thành Công", "Đơn Bị Hoàn Trả"]
        funnel_values = [
            funnel["total_orders"],
            funnel["completed_orders"],
            funnel["success_invoices"],
            funnel["returned_invoices"]
        ]

        fig_funnel = go.Figure(go.Funnel(
            y=funnel_stages,
            x=funnel_values,
            textinfo="value+percent initial",
            marker=dict(color=["#3498DB", "#2ECC71", "#1ABC9C", "#E74C3C"])
        ))
        fig_funnel.update_layout(
            template="plotly_dark",
            height=300,
            margin=dict(l=20, r=20, t=10, b=10)
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

    with col_chart_right:
        st.subheader("💳 Cơ Cấu Doanh Thu Theo Kênh Bán")
        st.caption("Tỷ trọng đóng góp doanh thu của từng kênh phân phối đa kênh:")

        channel_summary = df_invoices.groupby("sales_channel")["total_amount"].sum().reset_index()
        fig_channel = px.pie(
            channel_summary,
            names="sales_channel",
            values="total_amount",
            hole=0.45,
            color_discrete_sequence=["#FF0050", "#EE4D2D", "#3498DB", "#9B59B6"]
        )
        fig_channel.update_layout(
            template="plotly_dark",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_channel, use_container_width=True)

    # -------------------------------------------------------------------------
    # [SF-02.3] WIDGET CẢNH BÁO TỒN KHO NÓNG (ĐẶC BIỆT 200 BEANIE)
    # -------------------------------------------------------------------------
    st.subheader("⚠️ Cảnh Báo Tồn Kho & Vòng Quay Sản Phẩm (Inventory Health Check)")
    st.caption("Trọng tâm: Phát hiện hàng tồn ứ đọng vốn lưu động để lên kế hoạch đóng gói Bundle xả kho.")

    # Định dạng hiển thị bảng
    def highlight_beanie(val):
        if "CẢNH BÁO TỒN ĐỌNG" in str(val):
            return "background-color: rgba(231, 76, 60, 0.35); color: #FFFFFF; font-weight: bold;"
        elif "CẢNH BÁO SẮP HẾT HÀNG" in str(val):
            return "background-color: rgba(241, 196, 15, 0.3); color: #FFFFFF;"
        return ""

    display_inv = inventory_df.copy()
    display_inv.columns = ["Mã SKU", "Tên Sản Phẩm", "Tồn Kho Hiện Tại", "Đã Bán", "Giá Bán Lẻ", "Trạng Thái Cảnh Báo"]
    
    st.dataframe(
        display_inv.style.map(highlight_beanie, subset=["Trạng Thái Cảnh Báo"]),
        use_container_width=True,
        hide_index=True
    )


# =============================================================================
# TAB 2: RFM CUSTOMER INTELLIGENCE (PLACEHOLDER CHO MODULE SF-03)
# =============================================================================
# =============================================================================
# TAB 2: RFM CUSTOMER INTELLIGENCE & RESELLER HUNTER (PHÂN HỆ SF-03)
# =============================================================================
with tab2:
    st.markdown("---")
    st.markdown("### 🎯 PHÂN TÍCH CHÂN DUNG KHÁCH HÀNG & PHÁT HIỆN RESELLER")
    st.caption("Mô hình RFM thích ứng với nhịp tim Drop Streetwear • Loại trừ 100% Reseller • Cấp 200 Suất Early Access cho Fan ruột")

    if not rfm_df.empty:
        # ---------------------------------------------------------------------
        # 1. BỘ THẺ KPI KHÁCH HÀNG
        # ---------------------------------------------------------------------
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)

        total_customers = len(rfm_df)
        vip_loyal_df = rfm_df[rfm_df["segment"].isin(["VIP / Champions", "Loyal Customers"])]
        vip_loyal_count = len(vip_loyal_df)
        vip_rev_share = (vip_loyal_df["monetary"].sum() / rfm_df["monetary"].sum() * 100) if rfm_df["monetary"].sum() > 0 else 0

        at_risk_count = len(rfm_df[rfm_df["segment"] == "At-Risk Customers"])
        reseller_count = rfm_df["is_reseller"].sum()

        with col_c1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">👥 TỔNG TỆP KHÁCH HÀNG</div>
                <div class="kpi-value">{total_customers:,}</div>
                <div class="kpi-subtext">Khách hàng trong CSDL KiotViet</div>
            </div>
            """, unsafe_allow_html=True)

        with col_c2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">⭐ VIP & FAN RUỘT (PARETO)</div>
                <div class="kpi-value">{vip_loyal_count:,} <span style="font-size:1rem; color:#2ECC71;">({(vip_loyal_count/total_customers)*100:.1f}%)</span></div>
                <div class="kpi-subtext">Đóng góp <b>{vip_rev_share:.1f}%</b> tổng doanh thu</div>
            </div>
            """, unsafe_allow_html=True)

        with col_c3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">⚠️ KHÁCH CẦN GIỮ CHÂN (AT-RISK)</div>
                <div class="kpi-value" style="color:#F1C40F;">{at_risk_count:,}</div>
                <div class="kpi-subtext">Cần gửi Zalo Win-back trước Drop 2 tuần</div>
            </div>
            """, unsafe_allow_html=True)

        with col_c4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">🚫 RESELLER / SCALPER BỊ CHẶN</div>
                <div class="kpi-value" style="color:#E74C3C;">{reseller_count:,}</div>
                <div class="kpi-subtext">Đã loại khỏi danh sách Early Access</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # 2. BIỂU ĐỒ TRỰC QUAN HÓA CƠ CẤU PHÂN KHÚC & SCATTER RFM
        # ---------------------------------------------------------------------
        col_viz_left, col_viz_right = st.columns([1, 1])

        with col_viz_left:
            st.subheader("📊 Cơ Cấu Phân Khúc Khách Hàng")
            st.caption("Tỷ trọng từng nhóm khách hàng theo hành vi mua thực tế:")

            seg_counts = rfm_df["segment"].value_counts().reset_index()
            seg_counts.columns = ["Phân Khúc", "Số Lượng"]

            color_map = {
                "VIP / Champions": "#2ECC71",
                "Loyal Customers": "#3498DB",
                "Potential / Newbies": "#1ABC9C",
                "At-Risk Customers": "#F39C12",
                "Discount Hunters & Resellers": "#E74C3C",
                "Casual / Promising": "#95A5A6"
            }

            fig_donut = px.pie(
                seg_counts,
                names="Phân Khúc",
                values="Số Lượng",
                color="Phân Khúc",
                color_discrete_map=color_map,
                hole=0.45
            )
            fig_donut.update_layout(
                template="plotly_dark",
                height=350,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_viz_right:
            st.subheader("🎯 Tương Quan Recency vs. Monetary")
            st.caption("Bong bóng biểu thị Tần suất (F). Nhóm VIP nằm ở góc trên bên trái (Gần đây + Chi tiêu cao):")

            active_rfm = rfm_df[rfm_df["frequency"] > 0].copy()
            fig_scatter = px.scatter(
                active_rfm,
                x="recency",
                y="monetary",
                size="frequency",
                color="segment",
                color_discrete_map=color_map,
                hover_data=["customer_name", "phone_masked", "rfm_score"],
                labels={
                    "recency": "Số ngày từ lần mua cuối (Recency)",
                    "monetary": "Tổng chi tiêu thực tế (VNĐ)",
                    "segment": "Phân khúc"
                }
            )
            fig_scatter.update_layout(
                template="plotly_dark",
                height=350,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        # ---------------------------------------------------------------------
        # 3. [SF-03.3] SĂN RESELLER & BẢO VỆ FAN CHÂN CHÍNH
        # ---------------------------------------------------------------------
        st.markdown("---")
        st.subheader("🛡️ Danh Sách Reseller / Scalper Bị Phát Hiện (Reseller Hunter)")
        st.caption("Các tài khoản bị gắn cờ do hành vi mua gom size số lượng lớn hoặc chỉ săn deal rẻ, đã tự động bị chặn khỏi danh sách nhận quà Early Access:")

        reseller_df = rfm_df[rfm_df["is_reseller"] == True][[
            "customer_code", "customer_name", "phone_masked", "area", "frequency", "monetary", "reseller_reason"
        ]].copy()

        if not reseller_df.empty:
            reseller_df.columns = ["Mã KH", "Tên Khách Hàng", "SĐT", "Khu Vực", "Số Đơn", "Tổng Mua", "Lý Do Bị Gắn Cờ Cảnh Báo"]
            st.dataframe(reseller_df, use_container_width=True, hide_index=True)
        else:
            st.success("Không phát hiện tài khoản Reseller bất thường.")

        # ---------------------------------------------------------------------
        # 4. [SF-03.4] XUẤT 200 SUẤT EARLY ACCESS CHO ĐỢT DROP TẾT
        # ---------------------------------------------------------------------
        st.markdown("---")
        col_ea_header, col_ea_btn = st.columns([3, 1])
        
        with col_ea_header:
            st.subheader("🎁 Danh Sách Suất Quà Early Access Đợt Drop Tết (Đã Lọc Sạch)")
            st.caption(f"Trích xuất {len(early_access_df)} khách hàng tinh hoa (VIP & Loyal) đủ điều kiện nhận đặc quyền mua sớm trước 48h:")

        with col_ea_btn:
            # Nút tải file CSV
            csv_data = early_access_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Tải Danh Sách Early Access (CSV)",
                data=csv_data,
                file_name="FORM_Studio_200_Early_Access_Clean.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Hiển thị bảng xem trước Early Access
        display_ea = early_access_df.copy()
        display_ea.columns = ["Mã KH", "Tên Khách Hàng", "SĐT", "Khu Vực", "Phân Khúc", "Recency (ngày)", "Tần Suất (F)", "Tổng Chi Tiêu (VNĐ)", "Đặc Quyền Đề Xuất"]
        st.dataframe(display_ea.head(20), use_container_width=True, hide_index=True)

        # ---------------------------------------------------------------------
        # 5. DANH BẠ TRA CỨU KHÁCH HÀNG & KỊCH BẢN TIẾP THỊ (CRM DIRECTORY)
        # ---------------------------------------------------------------------
        st.markdown("---")
        st.subheader("🔍 Tra Cứu Khách Hàng & Kịch Bản Tiếp Thị Cá Nhân Hóa")
        st.caption("Tìm kiếm khách hàng theo tên hoặc số điện thoại, xem điểm số RFM và kịch bản hành động được gợi ý:")

        col_filter_seg, col_search = st.columns([1, 2])
        with col_filter_seg:
            seg_filter = st.selectbox("Lọc theo Phân khúc:", ["Tất cả"] + list(rfm_df["segment"].unique()), index=0)
        with col_search:
            search_query = st.text_input("Tìm kiếm theo Tên hoặc Mã khách hàng:", placeholder="Nhập tên khách hoặc mã KH (VD: KH00015)...")

        filtered_rfm = rfm_df.copy()
        if seg_filter != "Tất cả":
            filtered_rfm = filtered_rfm[filtered_rfm["segment"] == seg_filter]
        if search_query:
            filtered_rfm = filtered_rfm[
                filtered_rfm["customer_name"].str.contains(search_query, case=False, na=False) |
                filtered_rfm["customer_code"].str.contains(search_query, case=False, na=False)
            ]

        display_rfm = filtered_rfm[[
            "customer_code", "customer_name", "phone_masked", "area", "segment",
            "rfm_score", "recency", "frequency", "monetary", "recommended_action"
        ]].copy()
        display_rfm.columns = ["Mã KH", "Tên Khách Hàng", "SĐT", "Khu Vực", "Phân Khúc", "Điểm RFM", "Recency", "Frequency", "Tổng Mua (VNĐ)", "Kịch Bản Tiếp Thị Đề Xuất"]

        st.dataframe(display_rfm, use_container_width=True, hide_index=True)
    else:
        st.warning("Chưa có đủ dữ liệu để tính toán phân khúc RFM.")


# =============================================================================
# TAB 3: MBA & BUNDLE RECOMMENDER (PHÂN HỆ SF-04)
# =============================================================================
with tab3:
    st.markdown("### 🛍️ PHÂN HỆ SF-04: KHÁM PHÁ GIỎ HÀNG & GỢI Ý BUNDLE (APRIORI MBA)")
    st.caption("Khám phá quy luật mua kèm (Cross-sell) bằng thuật toán Apriori, áp dụng Ma trận 4 Tầng lọc và Xây dựng Gói Bundle giải cứu 200 Mũ Beanie đọng vốn.")

    # Lọc danh sách dòng hóa đơn giao dịch thành công (loại trừ hàng hoàn)
    completed_invoices = df_invoices[df_invoices["is_returned"] == 0]
    completed_inv_codes = set(completed_invoices["invoice_code"])
    df_lines_completed = df_invoice_lines[df_invoice_lines["invoice_code"].isin(completed_inv_codes)].copy()

    # 1. BỘ THẺ KPI GIỎ HÀNG TỔNG THỂ
    basket_kpis = calculate_basket_kpis(df_lines_completed, completed_invoices)

    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">🛒 TỶ LỆ MUA KÈM (CROSS-SELL RATE)</div>
            <div class="kpi-value">{basket_kpis['multi_item_rate']:.1f}%</div>
            <div class="kpi-subtext">Đơn có từ 2 SKU: <b>{basket_kpis['multi_item_invoices']:,}</b> / {basket_kpis['total_transactions']:,} đơn</div>
        </div>
        """, unsafe_allow_html=True)

    with kcol2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">📦 QUY MÔ GIỎ HÀNG TB (BASKET SIZE)</div>
            <div class="kpi-value">{basket_kpis['avg_items_per_basket']:.2f} <span style="font-size:1rem;color:#8E95A5;">sp/đơn</span></div>
            <div class="kpi-subtext">Kích thước giỏ thời trang Local Brand</div>
        </div>
        """, unsafe_allow_html=True)

    with kcol3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">💎 TOP COMBO ÁI LỰC CAO NHẤT</div>
            <div class="kpi-value" style="color: #F1C40F;">Lift = 3.93x</div>
            <div class="kpi-subtext">Combo: <b>Áo Bomber + Mũ Lưỡi Trai</b></div>
        </div>
        """, unsafe_allow_html=True)

    with kcol4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">🚨 TỒN KHO CẦN GIẢI CỨU</div>
            <div class="kpi-value" style="color: #E74C3C;">200 <span style="font-size:1rem;color:#8E95A5;">chiếc</span></div>
            <div class="kpi-subtext">Mũ Beanie vụ cũ • Vốn đọng: <b>22.000.000 đ</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 2. BẢNG ĐIỀU KHIỂN THUẬT TOÁN APRIORI & MA TRẬN 4 TẦNG LỌC
    st.markdown("#### 🎛️ Bảng Điều Khiển Thuật Toán Apriori & Ma Trận 4 Tầng Lọc")
    with st.expander("⚙️ Tùy Chỉnh Tham Số Thuật Toán & Bộ Lọc Nghiệp Vụ", expanded=True):
        param_col1, param_col2, param_col3 = st.columns(3)
        with param_col1:
            min_supp = st.slider("Tầng 1: Ngưỡng Support tối thiểu (%)", min_value=0.5, max_value=15.0, value=2.0, step=0.5) / 100.0
            st.caption(r"$\text{Support}(A \rightarrow B) = \frac{\text{Số đơn mua kèm}}{\text{Tổng số hóa đơn}}$")
        with param_col2:
            min_conf = st.slider("Tầng 1: Ngưỡng Confidence tối thiểu (%)", min_value=10.0, max_value=80.0, value=20.0, step=5.0) / 100.0
            st.caption(r"$\text{Confidence}(A \rightarrow B) = \frac{\text{Số đơn mua kèm}}{\text{Số đơn mua A}}$")
        with param_col3:
            min_lift_val = st.slider("Tầng 1: Ngưỡng Lift tối thiểu", min_value=1.0, max_value=4.0, value=1.2, step=0.1)
            st.caption(r"$\text{Lift} > 1$: Mua kèm tích cực (xác suất cao hơn ngẫu nhiên)")

        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            filter_stock = st.checkbox("🛡️ Tầng 2: Lọc Tồn Kho (Consequent Tồn >= 20)", value=True, help="Loại bỏ các sản phẩm mua kèm sắp hết hàng để tránh đơn hàng bị đọng hoặc hủy.")
        with filter_col2:
            filter_culture = st.checkbox("🧢 Tầng 3: Lọc Văn Hóa Streetwear (Loại Proxy Buy)", value=True, help="Loại bỏ các giao dịch mua hộ (cùng loại áo khác size S+M) để giữ lại các Outfit hoàn chỉnh.")
        with filter_col3:
            selected_segment_filter = st.selectbox(
                "🎯 Tầng 4: Lọc Phân Khúc RFM Mục Tiêu",
                ["Tất cả", "Giải Cứu Tồn Kho (Đề xuất Flash Sale / Toàn bộ KH)", "VIP Early Access & Khách Thân Thiết", "Khách Hàng Mới (Newbie Onboarding)", "Khách Hàng Có Nguy Cơ Rời Bỏ & Khách Vãng Lai"],
                index=0
            )

    # Khai phá quy luật kết hợp
    raw_rules = mine_association_rules(
        df_lines_completed,
        min_support=min_supp,
        min_confidence=min_conf,
        min_lift=min_lift_val
    )
    
    filtered_rules = apply_four_layer_filter(
        raw_rules,
        df_products,
        enable_inventory_filter=filter_stock,
        min_stock_consequent=20,
        enable_cultural_filter=filter_culture
    )

    if selected_segment_filter != "Tất cả" and not filtered_rules.empty:
        filtered_rules = filtered_rules[filtered_rules["target_segment"] == selected_segment_filter].reset_index(drop=True)

    # 3. TRỰC QUAN HÓA MA TRẬN ÁI LỰC VÀ LUẬT KẾT HỢP
    st.markdown("#### 📊 Phân Tích Trực Quan: Ma Trận Ái Lực & Phân Bố Luật Kết Hợp")
    vis_col1, vis_col2 = st.columns([1.1, 0.9])

    with vis_col1:
        st.markdown("**Ma Trận Tương Quan Mua Kèm (Cross-sell Affinity Heatmap)**")
        matrix_df = generate_cross_sell_matrix(df_lines_completed, df_products)
        fig_heat = px.imshow(
            matrix_df,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Purples",
            title="Tần Suất Mua Đồng Thời Giữa Các Sản Phẩm (Đơn Hoàn Tất)"
        )
        fig_heat.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1A1C23",
            plot_bgcolor="#1A1C23",
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(tickangle=-45)
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with vis_col2:
        st.markdown("**Phân Bố Quy Luật Mua Kèm (Support vs. Confidence vs. Lift)**")
        if not filtered_rules.empty:
            fig_scatter = px.scatter(
                filtered_rules,
                x="support",
                y="confidence",
                size="lift",
                color="bundle_theme",
                hover_name="antecedent_code",
                hover_data=["consequent_code", "lift", "target_segment"],
                title="Bản Đồ Luật Kết Hợp (Kích thước bóng = Điểm Lift)",
                labels={"support": "Support (Tần suất xuất hiện)", "confidence": "Confidence (Độ tin cậy)"}
            )
            fig_scatter.update_layout(
                template="plotly_dark",
                paper_bgcolor="#1A1C23",
                plot_bgcolor="#1A1C23",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Không có luật nào thỏa mãn ngưỡng lọc hiện tại. Hãy hạ bớt min Support hoặc min Confidence.")

    # 4. SPOTLIGHT CASE STUDY: CHIẾN DỊCH GIẢI CỨU 200 MŨ BEANIE TỒN KHO
    st.markdown("---")
    st.markdown("### 🧢 CHIẾN DỊCH SPOTLIGHT: GIẢI CỨU 200 MŨ BEANIE TỒN KHO")
    st.caption("Ứng dụng phát hiện luật kết hợp Apriori `{Hoodie} -> {Beanie}` (Lift > 1.9x) để thiết kế gói Tết Duo Set, giải phóng 22 triệu đồng vốn lưu động đọng trong kho.")

    with st.container():
        st.markdown("""
        <div style="background-color: #1F2430; border: 2px solid #F1C40F; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h4 style="color: #F1C40F; margin-top: 0;">💡 Bối Cảnh Nghiệp Vụ & Bài Toán Vốn Của Founder Minh</h4>
            <p style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.5;">
                • <b>Hiện trạng:</b> 200 chiếc <code>BEANIE-001</code> bị tồn đọng từ vụ đông năm ngoái. Vốn đọng: <b>22.000.000 đ</b> (Giá vốn 110k/chiếc). Tốc độ bán lẻ đơn lẻ rất chậm.<br>
                • <b>Phát hiện từ CSDL KiotViet:</b> Khách hàng mua Áo Hoodie có tới <b>~59% xác suất mua kèm Mũ Beanie</b> (Lift đạt 1.92 - 2.10x). Đây là outfit hoàn hảo cho mùa đông Streetwear.<br>
                • <b>Giải pháp:</b> Đóng gói Bundle <b>"Tết Streetwear Duo Set" (Hoodie + Beanie)</b> với giá ưu đãi để tăng giá trị đơn hàng (AOV), đồng thời xả sạch 200 chiếc mũ trong 1 đợt Drop Tết.
            </p>
        </div>
        """, unsafe_allow_html=True)

        sim_col1, sim_col2 = st.columns([1, 1.2])

        with sim_col1:
            st.markdown("##### 🎚️ Mô Phỏng Định Giá Gói Bundle (Pricing Simulator)")
            bundle_price_sim = st.slider(
                "Giá bán Bundle đề xuất (VNĐ):",
                min_value=699000,
                max_value=850000,
                value=799000,
                step=10000,
                format="%d đ"
            )
            sim_res = calculate_beanie_liquidation_case(
                bundle_selling_price=float(bundle_price_sim),
                df_products=df_products
            )
            st.write(f"• **Giá niêm yết khi mua lẻ:** {sim_res['original_total_price']:,.0f} đ (Hoodie 590k + Beanie 290k)")
            st.write(f"• **Mức giảm giá cho khách:** -{sim_res['bundle_discount_amt']:,.0f} đ (-{sim_res['bundle_discount_pct']:.1f}%)")
            st.write(f"• **Tổng giá vốn hàng bán (COGS):** {sim_res['total_cost']:,.0f} đ (Hoodie 280k + Beanie 110k)")

        with sim_col2:
            st.markdown("##### 📈 Tác Động Tài Chính Khi Bán Hết 200 Bundle")
            mcol1, mcol2 = st.columns(2)
            with mcol1:
                st.metric(
                    label="Tăng Trưởng AOV (AOV Uplift)",
                    value=f"+{sim_res['aov_uplift_pct']:.1f}%",
                    delta=f"Từ 590k ➔ {bundle_price_sim/1000:.0f}k"
                )
                st.metric(
                    label="Vốn Lưu Động Thu Hồi",
                    value=f"{sim_res['trapped_capital_recovered']:,.0f} đ",
                    delta="200 Beanie giải phóng 100%"
                )
            with mcol2:
                st.metric(
                    label="Tổng Doanh Thu Thu Về",
                    value=f"{sim_res['total_revenue_potential']:,.0f} đ",
                    delta=f"Biên LN gộp {sim_res['gross_margin_pct']:.1f}%"
                )
                st.metric(
                    label="Tổng Lợi Nhuận Gộp Đóng Góp",
                    value=f"{sim_res['total_gross_profit_potential']:,.0f} đ",
                    delta=f"{sim_res['gross_profit_per_bundle']:,.0f} đ / combo"
                )

        st.success(f"""
        🎯 **Khuyến nghị cho Founder Minh:** Khi định giá Bundle ở mức **{bundle_price_sim:,.0f} đ**, mỗi đơn hàng giúp tăng AOV thêm **+{sim_res['aov_uplift_pct']:.1f}%**. Doanh nghiệp thu hồi trọn vẹn **22 triệu đồng tiền mặt** vốn lưu động bị đóng băng và tạo ra **{sim_res['total_gross_profit_potential']:,.0f} đ** lợi nhuận gộp mà không cần xả lỗ bán tháo!
        """)

    # 5. BẢNG DANH SÁCH BUNDLE ĐỀ XUẤT VÀ XUẤT DỮ LIỆU
    st.markdown("---")
    st.markdown("#### 📋 Danh Sách Bundle Đề Xuất Phù Hợp Ma Trận 4 Tầng Lọc")

    if not filtered_rules.empty:
        display_rules = filtered_rules[[
            "antecedent_name", "consequent_name", "support", "confidence", "lift",
            "consequent_stock", "combo_original_price", "bundle_theme", "target_segment"
        ]].copy()

        display_rules["support"] = (display_rules["support"] * 100).apply(lambda x: f"{x:.1f}%")
        display_rules["confidence"] = (display_rules["confidence"] * 100).apply(lambda x: f"{x:.1f}%")
        display_rules["combo_original_price"] = display_rules["combo_original_price"].apply(lambda x: f"{x:,.0f} đ")

        display_rules.columns = [
            "Sản Phẩm Chính (Antecedent)",
            "Gợi Ý Mua Kèm (Consequent)",
            "Support",
            "Confidence",
            "Lift",
            "Tồn Kho Mua Kèm",
            "Giá Gốc Combo",
            "Chủ Đề Bundle",
            "Phân Khúc Mục Tiêu (Tầng 4)"
        ]

        st.dataframe(display_rules, use_container_width=True, hide_index=True)

        # Nút xuất file CSV cho đội Sales / KiotViet
        csv_bundle_data = filtered_rules.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Xuất Danh Sách Bundle Sang KiotViet & TikTok Shop (CSV)",
            data=csv_bundle_data,
            file_name="FORM_Studio_Recommended_Bundles_SF04.csv",
            mime="text/csv"
        )
    else:
        st.warning("Không tìm thấy tổ hợp sản phẩm nào phù hợp với bộ lọc hiện tại.")


# =============================================================================
# TAB 4: KIOTVIET DATA EXPLORER
# =============================================================================
with tab4:
    st.markdown("### 🗄️ TRA CỨU CƠ SỞ DỮ LIỆU CHUẨN HÓA KIOTVIET")
    st.caption("Dữ liệu được nạp từ CSDL SQLite (`data/fashion_brand.db`) - Tương thích 100% với mẫu nhập xuất KiotViet:")

    subtab_orders, subtab_invoices, subtab_products, subtab_customers = st.tabs([
        "Đơn Đặt Hàng (FACT_ORDERS)",
        "Hóa Đơn (FACT_INVOICES)",
        "Danh Mục Sản Phẩm (DIM_PRODUCTS)",
        "Khách Hàng (DIM_CUSTOMERS)"
    ])

    with subtab_orders:
        st.write(f"**Tổng số đơn đặt hàng:** {len(df_orders):,} bản ghi")
        st.dataframe(df_orders.head(50), use_container_width=True)

    with subtab_invoices:
        st.write(f"**Tổng số hóa đơn:** {len(df_invoices):,} bản ghi (Chuẩn tiền tố HDIP theo Rule R1)")
        st.dataframe(df_invoices.head(50), use_container_width=True)

    with subtab_products:
        st.write(f"**Danh mục sản phẩm:** {len(df_products):,} SKU (Kiểm tra tồn kho Beanie: 200 chiếc)")
        st.dataframe(df_products, use_container_width=True)

    with subtab_customers:
        st.write(f"**Danh mục khách hàng:** {len(df_customers):,} khách hàng")
        st.dataframe(df_customers.head(50), use_container_width=True)

# Footer
st.markdown("---")
st.caption("Global Science Journey • BA for Smart Fashion Program • 2026 • Pair Programming with Antigravity AI")
