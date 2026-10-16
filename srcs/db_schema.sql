-- ====================================================================
-- CƠ SỞ DỮ LIỆU TƯƠNG THÍCH KIOTVIET CHO FORM STUDIO SMART DASHBOARD
-- Căn cứ theo tài liệu 01_DATA_STRUCTURE_ANALYSIS.md & GSJ_Huong dan thuc hanh.md
-- Phiên bản: v2.0 (Bổ sung đầy đủ FACT_ORDERS và FACT_ORDERS_LINES)
-- ====================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS FACT_INVOICE_LINES;
DROP TABLE IF EXISTS FACT_INVOICES;
DROP TABLE IF EXISTS FACT_ORDERS_LINES;
DROP TABLE IF EXISTS FACT_ORDERS;
DROP TABLE IF EXISTS DIM_PRODUCTS;
DROP TABLE IF EXISTS DIM_EMPLOYEES;
DROP TABLE IF EXISTS DIM_CUSTOMERS;

-- 1. BẢNG DANH MỤC KHÁCH HÀNG (DIM_CUSTOMERS)
CREATE TABLE DIM_CUSTOMERS (
    customer_code TEXT PRIMARY KEY,
    customer_type TEXT DEFAULT 'Cá nhân',
    customer_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    area TEXT,
    ward TEXT,
    company TEXT,
    tax_code TEXT,
    debt REAL DEFAULT 0,
    total_sales REAL DEFAULT 0,
    last_transaction_date TEXT,
    is_active INTEGER DEFAULT 1
);

-- 2. BẢNG DANH MỤC NHÂN VIÊN (DIM_EMPLOYEES)
CREATE TABLE DIM_EMPLOYEES (
    employee_code TEXT PRIMARY KEY,
    employee_name TEXT NOT NULL UNIQUE,
    phone TEXT,
    department TEXT DEFAULT 'Bán hàng',
    title TEXT DEFAULT 'Nhân viên bán hàng',
    login TEXT,
    branch_working TEXT DEFAULT 'Chi nhánh Hà Nội'
);

-- 3. BẢNG DANH MỤC SẢN PHẨM / HÀNG HÓA (DIM_PRODUCTS)
CREATE TABLE DIM_PRODUCTS (
    product_code TEXT PRIMARY KEY,
    barcode TEXT,
    product_name TEXT NOT NULL,
    product_type TEXT DEFAULT 'Hàng hóa',
    category_path TEXT NOT NULL,
    brand TEXT DEFAULT 'FORM Studio',
    sale_price REAL NOT NULL,
    cost_price REAL NOT NULL,
    stock_on_hand INTEGER NOT NULL DEFAULT 500,
    uom TEXT DEFAULT 'Cái',
    is_active INTEGER DEFAULT 1,
    is_direct_sale INTEGER DEFAULT 1
);

-- 4. BẢNG ĐƠN ĐẶT HÀNG (FACT_ORDERS)
-- Đại diện cho giai đoạn khách hàng đặt hàng / pre-order / giỏ hàng
-- Mã đơn có tiền tố DH (DH00001, DH00002,...) theo chuẩn KiotViet
CREATE TABLE FACT_ORDERS (
    order_code TEXT PRIMARY KEY,
    order_time TEXT NOT NULL,
    customer_code TEXT,
    seller TEXT,
    sales_channel TEXT NOT NULL,
    amount_due REAL NOT NULL,
    amount_paid REAL DEFAULT 0,
    status TEXT DEFAULT 'Đã hoàn thành',
    invoice_code TEXT,
    note TEXT,
    FOREIGN KEY (customer_code) REFERENCES DIM_CUSTOMERS (customer_code) ON DELETE SET NULL,
    FOREIGN KEY (seller) REFERENCES DIM_EMPLOYEES (employee_name) ON DELETE SET NULL
);

-- 5. BẢNG CHI TIẾT ĐƠN ĐẶT HÀNG (FACT_ORDERS_LINES)
CREATE TABLE FACT_ORDERS_LINES (
    order_line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT NOT NULL,
    product_code TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    discount_percent REAL DEFAULT 0,
    discount_amount REAL DEFAULT 0,
    line_total REAL NOT NULL,
    FOREIGN KEY (order_code) REFERENCES FACT_ORDERS (order_code) ON DELETE CASCADE,
    FOREIGN KEY (product_code) REFERENCES DIM_PRODUCTS (product_code) ON DELETE RESTRICT
);

-- 6. BẢNG GIAO DỊCH HÓA ĐƠN (FACT_INVOICES)
-- Đại diện cho giao dịch thanh toán thành công (ghi nhận doanh thu / hoàn trả)
-- Rule R1: invoice_code có prefix HDIP (HDIP00001, HDIP00002,...)
CREATE TABLE FACT_INVOICES (
    invoice_code TEXT PRIMARY KEY,
    invoice_time TEXT NOT NULL,
    seller TEXT,
    sales_channel TEXT NOT NULL,
    customer_code TEXT,
    order_code TEXT,
    pricebook TEXT DEFAULT 'Bảng giá chung',
    invoice_discount_amount REAL DEFAULT 0,
    invoice_discount_percent REAL DEFAULT 0,
    total_amount REAL NOT NULL,
    pay_cash REAL DEFAULT 0,
    pay_card REAL DEFAULT 0,
    pay_transfer REAL DEFAULT 0,
    note TEXT,
    order_status TEXT DEFAULT 'COMPLETED',
    is_returned INTEGER DEFAULT 0,
    FOREIGN KEY (customer_code) REFERENCES DIM_CUSTOMERS (customer_code) ON DELETE SET NULL,
    FOREIGN KEY (seller) REFERENCES DIM_EMPLOYEES (employee_name) ON DELETE SET NULL,
    FOREIGN KEY (order_code) REFERENCES FACT_ORDERS (order_code) ON DELETE SET NULL
);

-- 7. BẢNG CHI TIẾT HÓA ĐƠN (FACT_INVOICE_LINES)
CREATE TABLE FACT_INVOICE_LINES (
    invoice_line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_code TEXT NOT NULL,
    product_code TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    line_discount_percent REAL DEFAULT 0,
    line_discount_amount REAL DEFAULT 0,
    line_total REAL NOT NULL,
    FOREIGN KEY (invoice_code) REFERENCES FACT_INVOICES (invoice_code) ON DELETE CASCADE,
    FOREIGN KEY (product_code) REFERENCES DIM_PRODUCTS (product_code) ON DELETE RESTRICT
);

-- CHỈ MỤC TỐI ƯU HÓA TRUY VẤN CHO DASHBOARD
CREATE INDEX idx_orders_customer ON FACT_ORDERS (customer_code);
CREATE INDEX idx_orders_time ON FACT_ORDERS (order_time);
CREATE INDEX idx_orders_status ON FACT_ORDERS (status);
CREATE INDEX idx_orders_lines_order ON FACT_ORDERS_LINES (order_code);
CREATE INDEX idx_orders_lines_prod ON FACT_ORDERS_LINES (product_code);

CREATE INDEX idx_invoices_customer ON FACT_INVOICES (customer_code);
CREATE INDEX idx_invoices_time ON FACT_INVOICES (invoice_time);
CREATE INDEX idx_invoices_channel ON FACT_INVOICES (sales_channel);
CREATE INDEX idx_invoices_status ON FACT_INVOICES (order_status, is_returned);
CREATE INDEX idx_lines_invoice ON FACT_INVOICE_LINES (invoice_code);
CREATE INDEX idx_lines_product ON FACT_INVOICE_LINES (product_code);
