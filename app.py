import streamlit as st
import pandas as pd
import plotly.express as px
import pymysql
from pymysql.cursors import DictCursor

# =========================================================
# 1. CẤU HÌNH TRANG STREAMLIT
# =========================================================

st.set_page_config(
    page_title="Quản Lý & Theo Dõi Tình Trạng Phòng",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. THÔNG TIN KẾT NỐI DATABASE MYSQL AIVEN
# =========================================================

DB_USER = "avnadmin"
DB_PASSWORD = "AVNS_DFTmGqDGhpod7tVs9_v"
DB_HOST = "mysql-1905d98b-su27062005-0289.b.aivencloud.com"
DB_PORT = 24833
DB_NAME = "defaultdb"


# =========================================================
# 3. KẾT NỐI MYSQL VỚI CHẾ ĐỘ AUTO-RECONNECT
# =========================================================

@st.cache_resource
def init_connection():
    """Tạo kết nối MySQL ban đầu."""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=DictCursor,
        connect_timeout=15,
        read_timeout=15,
        write_timeout=15,
        autocommit=False
    )

def get_connection():
    """Lấy kết nối và tự động kết nối lại nếu bị timeout."""
    conn = init_connection()
    try:
        conn.ping(reconnect=True)
    except Exception:
        st.cache_resource.clear()
        conn = init_connection()
    return conn


# =========================================================
# 4. TẠO BẢNG ROOMS TRÊN DATABASE
# =========================================================

def create_rooms_table():
    conn = get_connection()
    sql = """
    CREATE TABLE IF NOT EXISTS rooms (
        id INT AUTO_INCREMENT PRIMARY KEY,
        room_number VARCHAR(20) NOT NULL UNIQUE,
        floor INT NOT NULL,
        room_type VARCHAR(100) NOT NULL,
        status VARCHAR(50) NOT NULL,
        price DECIMAL(15,2) DEFAULT 0,
        note TEXT,
        image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# =========================================================
# 5. DỮ LIỆU MẪU BAN ĐẦU
# =========================================================

SAMPLE_ROOMS = [
    {
        "room_number": "101",
        "floor": 1,
        "room_type": "Standard",
        "status": "Trống",
        "price": 500000,
        "note": "Sạch sẽ, sẵn sàng",
        "image_url": "https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=800"
    },
    {
        "room_number": "102",
        "floor": 1,
        "room_type": "Standard",
        "status": "Đang ở",
        "price": 500000,
        "note": "Khách checkout 12h",
        "image_url": "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800"
    },
    {
        "room_number": "103",
        "floor": 1,
        "room_type": "Deluxe",
        "status": "Đang dọn dẹp",
        "price": 800000,
        "note": "Đang thay ga giường",
        "image_url": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800"
    },
    {
        "room_number": "104",
        "floor": 1,
        "room_type": "Deluxe",
        "status": "Bảo trì",
        "price": 800000,
        "note": "Hỏng điều hòa",
        "image_url": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?w=800"
    },
    {
        "room_number": "201",
        "floor": 2,
        "room_type": "Standard",
        "status": "Trống",
        "price": 550000,
        "note": "",
        "image_url": "https://images.unsplash.com/photo-1591088398332-8a7791972843?w=800"
    },
    {
        "room_number": "202",
        "floor": 2,
        "room_type": "VIP Suite",
        "status": "Đang ở",
        "price": 1500000,
        "note": "Khách VIP",
        "image_url": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=800"
    },
    {
        "room_number": "203",
        "floor": 2,
        "room_type": "VIP Suite",
        "status": "Trống",
        "price": 1500000,
        "note": "",
        "image_url": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=800"
    },
    {
        "room_number": "204",
        "floor": 2,
        "room_type": "Deluxe",
        "status": "Đang dọn dẹp",
        "price": 850000,
        "note": "",
        "image_url": "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=800"
    }
]


def insert_sample_rooms():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM rooms")
            result = cursor.fetchone()

            # Chỉ thêm dữ liệu mẫu nếu bảng đang trống
            if result["total"] == 0:
                sql = """
                INSERT INTO rooms (room_number, floor, room_type, status, price, note, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                for room in SAMPLE_ROOMS:
                    cursor.execute(
                        sql,
                        (
                            room["room_number"],
                            room["floor"],
                            room["room_type"],
                            room["status"],
                            room["price"],
                            room["note"],
                            room["image_url"]
                        )
                    )
                conn.commit()
    except Exception:
        conn.rollback()
        raise


# =========================================================
# 6. TRUY VẤN & THAO TÁC DỮ LIỆU
# =========================================================

def get_rooms():
    conn = get_connection()
    sql = """
    SELECT
        id,
        room_number AS `Phòng`,
        floor AS `Tầng`,
        room_type AS `Loại phòng`,
        status AS `Trạng thái`,
        price AS `Giá (VNĐ)`,
        note AS `Ghi chú`,
        image_url AS `Hình ảnh`
    FROM rooms
    ORDER BY floor, room_number
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        data = cursor.fetchall()
    return pd.DataFrame(data)


def add_room(room_number, floor, room_type, status, price, note, image_url):
    conn = get_connection()
    sql = """
    INSERT INTO rooms (room_number, floor, room_type, status, price, note, image_url)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    str(room_number),
                    int(floor),
                    str(room_type),
                    str(status),
                    float(price),
                    str(note),
                    str(image_url)
                )
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def delete_room(room_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM rooms WHERE id = %s", (int(room_id),))
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# =========================================================
# 7. CẤU HÌNH GIAO DIỆN & MÀU SẮC
# =========================================================

STATUS_COLORS = {
    "Trống": "#2e7d32",
    "Đang ở": "#c62828",
    "Đang dọn dẹp": "#f57c00",
    "Bảo trì": "#616161"
}

STATUS_CLASS = {
    "Trống": "status-trong",
    "Đang ở": "status-dang-o",
    "Đang dọn dẹp": "status-dang-dondep",
    "Bảo trì": "status-bao-tri"
}

st.markdown(
    """
    <style>
    .room-card {
        padding: 12px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        font-family: sans-serif;
    }
    .room-number {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 2px;
    }
    .room-type {
        font-size: 13px;
        opacity: 0.9;
        margin-bottom: 6px;
    }
    .room-status {
        font-size: 13px;
        font-weight: 600;
        background-color: rgba(255,255,255,0.25);
        padding: 4px 8px;
        border-radius: 6px;
        display: inline-block;
    }
    .status-trong { background-color: #2e7d32; }
    .status-dang-o { background-color: #c62828; }
    .status-dang-dondep { background-color: #f57c00; }
    .status-bao-tri { background-color: #616161; }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 8. KHỞI TẠO VÀ TẢI DỮ LIỆU BAN ĐẦU
# =========================================================

try:
    create_rooms_table()
    insert_sample_rooms()
    rooms_df = get_rooms()
except Exception as e:
    st.error("❌ Không thể kết nối tới MySQL Aiven.")
    st.code(str(e))
    st.info("Vui lòng kiểm tra lại cấu hình kết nối mạng hoặc DB Aiven.")
    st.stop()


# =========================================================
# 9. THANH BÊN (SIDEBAR)
# =========================================================

st.sidebar.title("🏨 Điều Khiển Hệ Thống")
st.sidebar.success("🟢 MySQL Aiven đã kết nối")

st.sidebar.subheader("🔍 Bộ lọc sơ đồ")
floor_options = sorted(rooms_df["Tầng"].dropna().unique().tolist()) if not rooms_df.empty else []

selected_floor = st.sidebar.multiselect(
    "Chọn Tầng",
    options=floor_options,
    default=floor_options
)

selected_status = st.sidebar.multiselect(
    "Trạng thái phòng",
    options=list(STATUS_COLORS.keys()),
    default=list(STATUS_COLORS.keys())
)

st.sidebar.divider()

# Form cập nhật trạng thái nhanh
st.sidebar.subheader("⚡ Cập nhật nhanh")
room_numbers = rooms_df["Phòng"].astype(str).tolist() if not rooms_df.empty else []

if room_numbers:
    with st.sidebar.form("update_room_form"):
        room_to_update = st.selectbox("Chọn Phòng", options=room_numbers)
        new_status = st.selectbox("Trạng thái mới", options=list(STATUS_COLORS.keys()))
        new_note = st.text_input("Ghi chú bổ sung", value="")
        new_img = st.text_input("Link ảnh phòng", value="")
        submit_update = st.form_submit_button("💾 Cập Nhật", use_container_width=True)

        if submit_update:
            try:
                conn = get_connection()
                with conn.cursor() as cursor:
                    updates = ["status = %s"]
                    params = [new_status]

                    if new_note:
                        updates.append("note = %s")
                        params.append(new_note)
                    if new_img:
                        updates.append("image_url = %s")
                        params.append(new_img)

                    params.append(room_to_update)
                    sql_update = f"UPDATE rooms SET {', '.join(updates)} WHERE room_number = %s"
                    cursor.execute(sql_update, tuple(params))
                conn.commit()
                st.sidebar.success(f"Đã cập nhật phòng {room_to_update}!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Lỗi cập nhật: {e}")


# =========================================================
# 10. BỘ LỌC DỮ LIỆU LÊN TRANG CHÍNH
# =========================================================

st.title("🏨 Hệ Thống Theo Dõi Tình Trạng Phòng")
st.caption("Dữ liệu được lưu trữ và đồng bộ trực tiếp trên MySQL Aiven Cloud")

filtered_df = rooms_df.copy()

if selected_floor:
    filtered_df = filtered_df[filtered_df["Tầng"].isin(selected_floor)]
else:
    filtered_df = filtered_df.iloc[0:0]

if selected_status:
    filtered_df = filtered_df[filtered_df["Trạng thái"].isin(selected_status)]
else:
    filtered_df = filtered_df.iloc[0:0]


# =========================================================
# 11. THỐNG KÊ TỔNG QUAN (METRICS)
# =========================================================

st.subheader("📊 Thống Kê Tổng Quan")
total_rooms = len(rooms_df)
count_trong = len(rooms_df[rooms_df["Trạng thái"] == "Trống"])
count_dango = len(rooms_df[rooms_df["Trạng thái"] == "Đang ở"])
count_dondep = len(rooms_df[rooms_df["Trạng thái"] == "Đang dọn dẹp"])
count_baotri = len(rooms_df[rooms_df["Trạng thái"] == "Bảo trì"])

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
col_m1.metric("Tổng số phòng", total_rooms)
col_m2.metric("Phòng Trống", count_trong, f"{count_trong / total_rooms * 100:.0f}%" if total_rooms > 0 else "0%")
col_m3.metric("Đang Ở", count_dango, f"{count_dango / total_rooms * 100:.0f}%" if total_rooms > 0 else "0%")
col_m4.metric("Đang Dọn Dẹp", count_dondep)
col_m5.metric("Bảo Trì", count_baotri)

st.divider()


# =========================================================
# 12. TAB CHỨC NĂNG
# =========================================================

tab_sodo, tab_danhsach, tab_bieudo = st.tabs([
    "🗺️ Sơ Đồ Phòng",
    "📋 Danh Sách Chi Tiết",
    "📈 Biểu Đồ Báo Cáo"
])

# ---------------------------------------------------------
# TAB 1: SƠ ĐỒ PHÒNG TRỰC QUAN
# ---------------------------------------------------------
with tab_sodo:
    st.subheader("🗺️ Sơ Đồ Trực Quan Theo Tầng")
    if filtered_df.empty:
        st.warning("Không có phòng nào phù hợp với bộ lọc hiện tại.")
    else:
        floors = sorted(filtered_df["Tầng"].unique())
        for floor in floors:
            st.markdown(f"#### 🏢 Tầng {floor}")
            floor_rooms = filtered_df[filtered_df["Tầng"] == floor]
            cols = st.columns(4)

            for idx, (_, room) in enumerate(floor_rooms.iterrows()):
                col_idx = idx % 4
                status_cls = STATUS_CLASS.get(room["Trạng thái"], "status-bao-tri")

                with cols[col_idx]:
                    image_url = room["Hình ảnh"]
                    if pd.notna(image_url) and str(image_url).strip():
                        try:
                            st.image(str(image_url), use_container_width=True)
                        except Exception:
                            st.caption("⚠️ URL ảnh lỗi")

                    note = room["Ghi chú"]
                    note_html = f"<br><i>📝 {note}</i>" if pd.notna(note) and str(note).strip() else ""

                    st.markdown(
                        f"""
                        <div class="room-card {status_cls}">
                            <div class="room-number">Phòng {room['Phòng']}</div>
                            <div class="room-type">{room['Loại phòng']}</div>
                            <div class="room-status">{room['Trạng thái']}</div>
                            <div style="font-size:12px; margin-top:6px;">
                                {float(room['Giá (VNĐ)']):,.0f} VNĐ
                                {note_html}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# ---------------------------------------------------------
# TAB 2: QUẢN LÝ DANH SÁCH & CHỈNH SỬA
# ---------------------------------------------------------
with tab_danhsach:
    st.subheader("📋 Quản Lý & Chỉnh Sửa Danh Sách")
    st.caption("Chỉnh sửa trực tiếp dữ liệu trên bảng bên dưới và nhấn кнопку 'Lưu Thay Đổi' để cập nhật MySQL.")

    display_df = rooms_df[["id", "Phòng", "Tầng", "Loại phòng", "Trạng thái", "Giá (VNĐ)", "Ghi chú", "Hình ảnh"]].copy()

    edited_df = st.data_editor(
        display_df,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "Phòng": st.column_config.TextColumn("Phòng", required=True),
            "Tầng": st.column_config.NumberColumn("Tầng", min_value=1, step=1),
            "Loại phòng": st.column_config.TextColumn("Loại phòng"),
            "Trạng thái": st.column_config.SelectboxColumn("Trạng thái", options=list(STATUS_COLORS.keys()), required=True),
            "Giá (VNĐ)": st.column_config.NumberColumn("Giá (VNĐ)", format="%d VNĐ", min_value=0, step=50000),
            "Ghi chú": st.column_config.TextColumn("Ghi chú"),
            "Hình ảnh": st.column_config.ImageColumn("Hình ảnh phòng", help="URL ảnh phòng", width="medium")
        },
        hide_index=True,
        use_container_width=True
    )

    if st.button("💾 Lưu Thay Đổi Vào MySQL", type="primary", use_container_width=True):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                for _, row in edited_df.iterrows():
                    cursor.execute(
                        """
                        UPDATE rooms
                        SET room_number = %s, floor = %s, room_type = %s, status = %s, price = %s, note = %s, image_url = %s
                        WHERE id = %s
                        """,
                        (
                            str(row["Phòng"]),
                            int(row["Tầng"]),
                            str(row["Loại phòng"]),
                            str(row["Trạng thái"]),
                            float(row["Giá (VNĐ)"]),
                            str(row["Ghi chú"]) if pd.notna(row["Ghi chú"]) else "",
                            str(row["Hình ảnh"]) if pd.notna(row["Hình ảnh"]) else "",
                            int(row["id"])
                        )
                    )
            conn.commit()
            st.success("✅ Đã lưu toàn bộ thay đổi vào CSDL thành công!")
            st.rerun()
        except Exception as e:
            conn.rollback()
            st.error(f"Lỗi khi lưu dữ liệu: {e}")

    st.divider()

    # Form thêm phòng mới
    st.subheader("➕ Thêm Phòng Mới")
    with st.form("add_room_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            add_room_number = st.text_input("Số phòng", placeholder="Ví dụ: 301")
            add_floor = st.number_input("Tầng", min_value=1, value=3, step=1)
        with col2:
            add_type = st.selectbox("Loại phòng", ["Standard", "Deluxe", "VIP Suite"])
            add_status = st.selectbox("Trạng thái", list(STATUS_COLORS.keys()))
        with col3:
            add_price = st.number_input("Giá phòng (VNĐ)", min_value=0, value=500000, step=50000)
            add_image = st.text_input("URL hình ảnh")

        add_note = st.text_input("Ghi chú")
        add_submit = st.form_submit_button("➕ Thêm Phòng", use_container_width=True)

        if add_submit:
            if not add_room_number.strip():
                st.error("Vui lòng nhập số phòng!")
            else:
                try:
                    add_room(add_room_number, add_floor, add_type, add_status, add_price, add_note, add_image)
                    st.success(f"Đã thêm phòng {add_room_number} thành công!")
                    st.rerun()
                except pymysql.err.IntegrityError:
                    st.error(f"Phòng {add_room_number} đã tồn tại trong cơ sở dữ liệu.")
                except Exception as e:
                    st.error(f"Lỗi khi thêm phòng: {e}")

    st.divider()

    # Xóa phòng
    st.subheader("🗑️ Xóa Phòng")
    if not rooms_df.empty:
        delete_options = {f"Phòng {row['Phòng']} - {row['Loại phòng']}": row["id"] for _, row in rooms_df.iterrows()}
        selected_delete = st.selectbox("Chọn phòng muốn xóa", options=list(delete_options.keys()))

        if st.button("🗑️ Xóa Phòng Ngay", type="secondary"):
            room_id = delete_options[selected_delete]
            try:
                delete_room(room_id)
                st.success(f"Đã xóa thành công {selected_delete}.")
                st.rerun()
            except Exception as e:
                st.error(f"Không thể xóa phòng: {e}")

# ---------------------------------------------------------
# TAB 3: BIỂU ĐỒ BÁO CÁO PHÂN TÍCH
# ---------------------------------------------------------
with tab_bieudo:
    st.subheader("📈 Phân Tích & Báo Cáo Thống Kê")
    col_chart1, col_chart2 = st.columns(2)

    # Biểu đồ tròn
    with col_chart1:
        status_counts = rooms_df["Trạng thái"].value_counts().reset_index()
        status_counts.columns = ["Trạng thái", "Số lượng"]

        fig_pie = px.pie(
            status_counts,
            values="Số lượng",
            names="Trạng thái",
            title="Tỷ lệ Trạng thái Phòng Hiện Tại",
            color="Trạng thái",
            color_discrete_map=STATUS_COLORS,
            hole=0.4
        )
        fig_pie.update_layout(legend_title_text="Trạng thái")
        st.plotly_chart(fig_pie, use_container_width=True)

    # Biểu đồ cột phân bố theo tầng
    with col_chart2:
        floor_status = rooms_df.groupby(["Tầng", "Trạng thái"]).size().reset_index(name="Số lượng")

        fig_bar = px.bar(
            floor_status,
            x="Tầng",
            y="Số lượng",
            color="Trạng thái",
            title="Phân Bố Trạng Thái Phòng Theo Tầng",
            color_discrete_map=STATUS_COLORS,
            barmode="group"
        )
        fig_bar.update_layout(xaxis_title="Tầng", yaxis_title="Số lượng phòng")
        st.plotly_chart(fig_bar, use_container_width=True)
