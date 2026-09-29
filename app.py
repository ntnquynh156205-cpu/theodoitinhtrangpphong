import streamlit as st
import pandas as pd
import plotly.express as px
import pymysql
from pymysql.cursors import DictCursor


# =========================================================
# 1. CẤU HÌNH TRANG
# =========================================================

st.set_page_config(
    page_title="Quản Lý & Theo Dõi Tình Trạng Phòng",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. THÔNG TIN DATABASE AIVEN MYSQL
# =========================================================

DB_USER = "avnadmin"
DB_PASSWORD = "AVNS_DFTmGqDGhpod7tVs9_v"
DB_HOST = "mysql-1905d98b-su27062005-0289.b.aivencloud.com"
DB_PORT = 24833
DB_NAME = "defaultdb"


# =========================================================
# 3. KẾT NỐI MYSQL
# =========================================================

@st.cache_resource
def get_connection():
    """
    Tạo kết nối MySQL tới Aiven.
    Connection được cache để tránh tạo kết nối mới
    sau mỗi lần Streamlit rerun.
    """

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


def test_database_connection():
    """
    Kiểm tra kết nối database.
    """

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 AS test")
            result = cursor.fetchone()

        return result is not None

    except Exception:
        return False


# =========================================================
# 4. TẠO BẢNG ROOMS
# =========================================================

def create_rooms_table():
    """
    Tạo bảng rooms nếu chưa tồn tại.
    """

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
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
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
# 5. DỮ LIỆU MẪU
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
    """
    Nếu bảng rooms chưa có dữ liệu thì thêm dữ liệu mẫu.
    """

    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("SELECT COUNT(*) AS total FROM rooms")
            result = cursor.fetchone()

            total = result["total"]

            if total == 0:

                sql = """
                INSERT INTO rooms
                (
                    room_number,
                    floor,
                    room_type,
                    status,
                    price,
                    note,
                    image_url
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
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
# 6. LẤY DỮ LIỆU PHÒNG
# =========================================================

def get_rooms():
    """
    Lấy toàn bộ dữ liệu phòng từ MySQL.
    """

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

    df = pd.DataFrame(data)

    return df


# =========================================================
# 7. CẬP NHẬT PHÒNG
# =========================================================

def update_room(
    room_id,
    room_number,
    floor,
    room_type,
    status,
    price,
    note,
    image_url
):
    """
    Cập nhật một phòng trong database.
    """

    conn = get_connection()

    sql = """
    UPDATE rooms
    SET
        room_number = %s,
        floor = %s,
        room_type = %s,
        status = %s,
        price = %s,
        note = %s,
        image_url = %s
    WHERE id = %s
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
                    str(image_url),
                    int(room_id)
                )
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise


# =========================================================
# 8. XÓA PHÒNG
# =========================================================

def delete_room(room_id):
    """
    Xóa phòng khỏi database.
    """

    conn = get_connection()

    try:

        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM rooms WHERE id = %s",
                (int(room_id),)
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise


# =========================================================
# 9. THÊM PHÒNG
# =========================================================

def add_room(
    room_number,
    floor,
    room_type,
    status,
    price,
    note,
    image_url
):
    """
    Thêm phòng mới vào database.
    """

    conn = get_connection()

    sql = """
    INSERT INTO rooms
    (
        room_number,
        floor,
        room_type,
        status,
        price,
        note,
        image_url
    )
    VALUES
    (
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s
    )
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


# =========================================================
# 10. CẬP NHẬT TRẠNG THÁI NHANH
# =========================================================

def update_room_status(room_number, new_status):
    """
    Cập nhật trạng thái phòng.
    """

    conn = get_connection()

    sql = """
    UPDATE rooms
    SET status = %s
    WHERE room_number = %s
    """

    try:

        with conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    new_status,
                    str(room_number)
                )
            )

        conn.commit()

        return cursor.rowcount

    except Exception:
        conn.rollback()
        raise


# =========================================================
# 11. CẤU HÌNH MÀU
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


# =========================================================
# 12. CSS
# =========================================================

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

    .status-trong {
        background-color: #2e7d32;
    }

    .status-dang-o {
        background-color: #c62828;
    }

    .status-dang-dondep {
        background-color: #f57c00;
    }

    .status-bao-tri {
        background-color: #616161;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 13. KHỞI TẠO DATABASE
# =========================================================

try:

    create_rooms_table()
    insert_sample_rooms()

except Exception as e:

    st.error("❌ Không thể kết nối tới MySQL Aiven.")
    st.code(str(e))

    st.info(
        "Hãy kiểm tra DB_HOST, DB_PORT, DB_USER, DB_PASSWORD "
        "và trạng thái MySQL trên Aiven."
    )

    st.stop()


# =========================================================
# 14. LOAD DỮ LIỆU
# =========================================================

try:

    rooms_df = get_rooms()

except Exception as e:

    st.error("Không thể lấy dữ liệu từ bảng rooms.")
    st.code(str(e))

    st.stop()


# =========================================================
# 15. SIDEBAR
# =========================================================

st.sidebar.title("🏨 Điều Khiển Hệ Thống")

st.sidebar.success("🟢 MySQL Aiven đã kết nối")


# ---------------------------------------------------------
# Bộ lọc
# ---------------------------------------------------------

st.sidebar.subheader("🔍 Bộ lọc sơ đồ")

if not rooms_df.empty:

    floor_options = sorted(
        rooms_df["Tầng"].dropna().unique().tolist()
    )

else:

    floor_options = []


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


# =========================================================
# 16. CẬP NHẬT NHANH
# =========================================================

st.sidebar.subheader("⚡ Cập nhật nhanh")

room_numbers = (
    rooms_df["Phòng"].astype(str).tolist()
    if not rooms_df.empty
    else []
)


if room_numbers:

    with st.sidebar.form("update_room_form"):

        room_to_update = st.selectbox(
            "Chọn Phòng",
            options=room_numbers
        )

        new_status = st.selectbox(
            "Trạng thái mới",
            options=list(STATUS_COLORS.keys())
        )

        new_note = st.text_input(
            "Ghi chú bổ sung",
            value=""
        )

        new_img = st.text_input(
            "Link ảnh phòng",
            value=""
        )

        submit_update = st.form_submit_button(
            "💾 Cập Nhật",
            use_container_width=True
        )

        if submit_update:

            try:

                conn = get_connection()

                with conn.cursor() as cursor:

                    if new_note and new_img:

                        cursor.execute(
                            """
                            UPDATE rooms
                            SET
                                status = %s,
                                note = %s,
                                image_url = %s
                            WHERE room_number = %s
                            """,
                            (
                                new_status,
                                new_note,
                                new_img,
                                room_to_update
                            )
                        )

                    elif new_note:

                        cursor.execute(
                            """
                            UPDATE rooms
                            SET
                                status = %s,
                                note = %s
                            WHERE room_number = %s
                            """,
                            (
                                new_status,
                                new_note,
                                room_to_update
                            )
                        )

                    elif new_img:

                        cursor.execute(
                            """
                            UPDATE rooms
                            SET
                                status = %s,
                                image_url = %s
                            WHERE room_number = %s
                            """,
                            (
                                new_status,
                                new_img,
                                room_to_update
                            )
                        )

                    else:

                        cursor.execute(
                            """
                            UPDATE rooms
                            SET status = %s
                            WHERE room_number = %s
                            """,
                            (
                                new_status,
                                room_to_update
                            )
                        )

                conn.commit()

                st.sidebar.success(
                    f"Đã cập nhật phòng {room_to_update}!"
                )

                st.rerun()

            except Exception as e:

                st.sidebar.error(
                    f"Lỗi cập nhật: {e}"
                )


# =========================================================
# 17. TIÊU ĐỀ
# =========================================================

st.title("🏨 Hệ Thống Theo Dõi Tình Trạng Phòng")

st.caption(
    "Dữ liệu được lưu trữ trực tiếp trên MySQL Aiven"
)


# =========================================================
# 18. LỌC DỮ LIỆU
# =========================================================

filtered_df = rooms_df.copy()

if selected_floor:

    filtered_df = filtered_df[
        filtered_df["Tầng"].isin(selected_floor)
    ]

else:

    filtered_df = filtered_df.iloc[0:0]


if selected_status:

    filtered_df = filtered_df[
        filtered_df["Trạng thái"].isin(selected_status)
    ]

else:

    filtered_df = filtered_df.iloc[0:0]


# =========================================================
# 19. THỐNG KÊ
# =========================================================

st.subheader("📊 Thống Kê Tổng Quan")


total_rooms = len(rooms_df)

count_trong = len(
    rooms_df[
        rooms_df["Trạng thái"] == "Trống"
    ]
)

count_dango = len(
    rooms_df[
        rooms_df["Trạng thái"] == "Đang ở"
    ]
)

count_dondep = len(
    rooms_df[
        rooms_df["Trạng thái"] == "Đang dọn dẹp"
    ]
)

count_baotri = len(
    rooms_df[
        rooms_df["Trạng thái"] == "Bảo trì"
    ]
)


col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)


col_m1.metric(
    "Tổng số phòng",
    total_rooms
)


col_m2.metric(
    "Phòng Trống",
    count_trong,
    f"{count_trong / total_rooms * 100:.0f}%"
    if total_rooms > 0 else "0%"
)


col_m3.metric(
    "Đang Ở",
    count_dango,
    f"{count_dango / total_rooms * 100:.0f}%"
    if total_rooms > 0 else "0%"
)


col_m4.metric(
    "Đang Dọn Dẹp",
    count_dondep
)


col_m5.metric(
    "Bảo Trì",
    count_baotri
)


st.divider()


# =========================================================
# 20. TABS
# =========================================================

tab_sodo, tab_danhsach, tab_bieudo = st.tabs(
    [
        "🗺️ Sơ Đồ Phòng",
        "📋 Danh Sách Chi Tiết",
        "📈 Biểu Đồ Báo Cáo"
    ]
)


# =========================================================
# 21. TAB SƠ ĐỒ PHÒNG
# =========================================================

with tab_sodo:

    st.subheader(
        "🗺️ Sơ Đồ Trực Quan Theo Tầng"
    )

    if filtered_df.empty:

        st.warning(
            "Không có phòng nào phù hợp với bộ lọc."
        )

    else:

        floors = sorted(
            filtered_df["Tầng"].unique()
        )

        for floor in floors:

            st.markdown(
                f"#### 🏢 Tầng {floor}"
            )

            floor_rooms = filtered_df[
                filtered_df["Tầng"] == floor
            ]

            cols = st.columns(4)

            for idx, (_, room) in enumerate(
                floor_rooms.iterrows()
            ):

                col_idx = idx % 4

                status_cls = STATUS_CLASS.get(
                    room["Trạng thái"],
                    "status-bao-tri"
                )

                with cols[col_idx]:

                    image_url = room["Hình ảnh"]

                    if (
                        pd.notna(image_url)
                        and str(image_url).strip()
                    ):

                        try:

                            st.image(
                                str(image_url),
                                use_container_width=True
                            )

                        except Exception:

                            st.warning(
                                "Không thể tải ảnh phòng."
                            )

                    note = room["Ghi chú"]

                    note_html = ""

                    if pd.notna(note) and str(note).strip():

                        note_html = (
                            f"<br><i>📝 {note}</i>"
                        )

                    st.markdown(
                        f"""
                        <div class="room-card {status_cls}">

                            <div class="room-number">
                                Phòng {room['Phòng']}
                            </div>

                            <div class="room-type">
                                {room['Loại phòng']}
                            </div>

                            <div class="room-status">
                                {room['Trạng thái']}
                            </div>

                            <div style="font-size:12px; margin-top:6px;">
                                {float(room['Giá (VNĐ)']):,.0f} VNĐ
                                {note_html}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )


# =========================================================
# 22. TAB DANH SÁCH
# =========================================================

with tab_danhsach:

    st.subheader(
        "📋 Quản Lý Danh Sách Phòng"
    )

    st.caption(
        "Bạn có thể chỉnh sửa dữ liệu trực tiếp "
        "trên bảng rồi nhấn Lưu để cập nhật MySQL."
    )


    display_df = rooms_df[
        [
            "id",
            "Phòng",
            "Tầng",
            "Loại phòng",
            "Trạng thái",
            "Giá (VNĐ)",
            "Ghi chú",
            "Hình ảnh"
        ]
    ].copy()


    edited_df = st.data_editor(

        display_df,

        column_config={

            "id": st.column_config.NumberColumn(
                "ID",
                disabled=True
            ),

            "Phòng": st.column_config.TextColumn(
                "Phòng",
                required=True
            ),

            "Tầng": st.column_config.NumberColumn(
                "Tầng",
                min_value=1,
                step=1
            ),

            "Loại phòng": st.column_config.TextColumn(
                "Loại phòng"
            ),

            "Trạng thái": st.column_config.SelectboxColumn(
                "Trạng thái",
                options=list(
                    STATUS_COLORS.keys()
                ),
                required=True
            ),

            "Giá (VNĐ)": st.column_config.NumberColumn(
                "Giá (VNĐ)",
                format="%d VNĐ",
                min_value=0,
                step=50000
            ),

            "Ghi chú": st.column_config.TextColumn(
                "Ghi chú"
            ),

            "Hình ảnh": st.column_config.ImageColumn(
                "Hình ảnh phòng",
                help="URL ảnh phòng",
                width="medium"
            )
        },

        hide_index=True,

        use_container_width=True
    )


    if st.button(
        "💾 Lưu Thay Đổi Vào MySQL",
        type="primary",
        use_container_width=True
    ):

        try:

            conn = get_connection()

            with conn.cursor() as cursor:

                for _, row in edited_df.iterrows():

                    cursor.execute(
                        """
                        UPDATE rooms
                        SET
                            room_number = %s,
                            floor = %s,
                            room_type = %s,
                            status = %s,
                            price = %s,
                            note = %s,
                            image_url = %s
                        WHERE id = %s
                        """,
                        (
                            str(row["Phòng"]),
                            int(row["Tầng"]),
                            str(row["Loại phòng"]),
                            str(row["Trạng thái"]),
                            float(row["Giá (VNĐ)"]),
                            str(row["Ghi chú"])
                            if pd.notna(row["Ghi chú"])
                            else "",
                            str(row["Hình ảnh"])
                            if pd.notna(row["Hình ảnh"])
                            else "",
                            int(row["id"])
                        )
                    )

            conn.commit()

            st.success(
                "✅ Đã lưu toàn bộ thay đổi vào MySQL Aiven."
            )

            st.rerun()

        except Exception as e:

            conn.rollback()

            st.error(
                f"Không thể lưu dữ liệu: {e}"
            )


    st.divider()


    # =====================================================
    # THÊM PHÒNG
    # =====================================================

    st.subheader("➕ Thêm Phòng Mới")

    with st.form("add_room_form"):

        col1, col2, col3 = st.columns(3)

        with col1:

            add_room_number = st.text_input(
                "Số phòng",
                placeholder="Ví dụ: 301"
            )

            add_floor = st.number_input(
                "Tầng",
                min_value=1,
                value=3,
                step=1
            )

        with col2:

            add_type = st.selectbox(
                "Loại phòng",
                [
                    "Standard",
                    "Deluxe",
                    "VIP Suite"
                ]
            )

            add_status = st.selectbox(
                "Trạng thái",
                list(STATUS_COLORS.keys())
            )

        with col3:

            add_price = st.number_input(
                "Giá phòng",
                min_value=0,
                value=500000,
                step=50000
            )

            add_image = st.text_input(
                "URL hình ảnh"
            )

        add_note = st.text_input(
            "Ghi chú"
        )


        add_submit = st.form_submit_button(
            "➕ Thêm Phòng",
            use_container_width=True
        )


        if add_submit:

            if not add_room_number.strip():

                st.error(
                    "Vui lòng nhập số phòng."
                )

            else:

                try:

                    add_room(
                        add_room_number,
                        add_floor,
                        add_type,
                        add_status,
                        add_price,
                        add_note,
                        add_image
                    )

                    st.success(
                        f"Đã thêm phòng {add_room_number}."
                    )

                    st.rerun()

                except pymysql.err.IntegrityError:

                    st.error(
                        f"Phòng {add_room_number} đã tồn tại."
                    )

                except Exception as e:

                    st.error(
                        f"Lỗi khi thêm phòng: {e}"
                    )


    # =====================================================
    # XÓA PHÒNG
    # =====================================================

    st.divider()

    st.subheader("🗑️ Xóa Phòng")

    if not rooms_df.empty:

        delete_options = {
            f"Phòng {row['Phòng']} - {row['Loại phòng']}":
            row["id"]
            for _, row in rooms_df.iterrows()
        }

        selected_delete = st.selectbox(
            "Chọn phòng muốn xóa",
            options=list(delete_options.keys())
        )


        if st.button(
            "🗑️ Xóa Phòng",
            type="secondary"
        ):

            room_id = delete_options[
                selected_delete
            ]

            try:

                delete_room(room_id)

                st.success(
                    f"Đã xóa {selected_delete}."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Không thể xóa phòng: {e}"
                )


# =========================================================
# 23. TAB BIỂU ĐỒ
# =========================================================

with tab_bieudo:

    st.subheader(
        "📈 Phân Tích Tình Trạng Phòng"
    )


    col_chart1, col_chart2 = st.columns(2)


    # -----------------------------------------------------
    # BIỂU ĐỒ TRÒN
    # -----------------------------------------------------

    with col_chart1:

        status_counts = (
            rooms_df["Trạng thái"]
            .value_counts()
            .reset_index()
        )

        status_counts.columns = [
            "Trạng thái",
            "Số lượng"
        ]


        fig_pie = px.pie(

            status_counts,

            values="Số lượng",

            names="Trạng thái",

            title="Tỷ lệ Trạng thái Phòng",

            color="Trạng thái",

            color_discrete_map=STATUS_COLORS,

            hole=0.4
        )


        fig_pie.update_layout(
            legend_title_text="Trạng thái"
        )


        st.plotly_chart(
            fig_pie,
            use_container_width=True
        )


    # -----------------------------------------------------
    # BIỂU ĐỒ CỘT
    # -----------------------------------------------------

    with col_chart2:

        floor_status = (
            rooms_df
            .groupby(
                [
                    "Tầng",
                    "Trạng thái"
                ]
            )
            .size()
            .reset_index(
                name="Số lượng"
            )
        )


        fig_bar = px.bar(

            floor_status,

            x="Tầng",

            y="Số lượng",

            color="Trạng thái",

            title="Phân bố Trạng thái Theo Tầng",

            barmode="stack",

            color_discrete_map=STATUS_COLORS
        )


        st.plotly_chart(
            fig_bar,
            use_container_width=True
        )


    # -----------------------------------------------------
    # BẢNG THỐNG KÊ
    # -----------------------------------------------------

    st.subheader(
        "📊 Bảng thống kê"
    )

    summary_df = (
        rooms_df
        .groupby(
            ["Tầng", "Trạng thái"]
        )
        .size()
        .reset_index(
            name="Số lượng phòng"
        )
    )

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 24. AI CHATBOT
# =========================================================

st.divider()

st.subheader(
    "💬 Trợ Lý AI Khách Sạn"
)

st.caption(
    "Trợ lý có thể tra cứu trực tiếp dữ liệu phòng trong MySQL."
)


# =========================================================
# 25. HÀM CHATBOT TRUY VẤN DATABASE
# =========================================================

def chatbot_response(prompt):

    prompt_lower = prompt.lower().strip()

    conn = get_connection()


    # -----------------------------------------------------
    # TỔNG SỐ PHÒNG
    # -----------------------------------------------------

    if (
        "bao nhiêu phòng" in prompt_lower
        or "tổng số phòng" in prompt_lower
        or "tổng phòng" in prompt_lower
        or "có bao nhiêu" in prompt_lower
    ):

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM rooms
                """
            )

            result = cursor.fetchone()

        total = result["total"]

        return (
            f"🏨 Hiện tại hệ thống đang quản lý "
            f"**{total} phòng**."
        )


    # -----------------------------------------------------
    # PHÒNG TRỐNG
    # -----------------------------------------------------

    elif (
        "phòng trống" in prompt_lower
        or "phòng nào trống" in prompt_lower
        or "phòng còn trống" in prompt_lower
        or prompt_lower == "trống"
    ):

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT room_number
                FROM rooms
                WHERE status = 'Trống'
                ORDER BY room_number
                """
            )

            result = cursor.fetchall()

        rooms = [
            str(row["room_number"])
            for row in result
        ]

        if rooms:

            return (
                "🟢 Các phòng đang **Trống**: "
                + ", ".join(rooms)
            )

        return (
            "🔴 Hiện tại không có phòng trống."
        )


    # -----------------------------------------------------
    # PHÒNG ĐANG Ở
    # -----------------------------------------------------

    elif (
        "đang ở" in prompt_lower
        or "phòng đang ở" in prompt_lower
        or "khách đang ở" in prompt_lower
    ):

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT room_number
                FROM rooms
                WHERE status = 'Đang ở'
                ORDER BY room_number
                """
            )

            result = cursor.fetchall()

        rooms = [
            str(row["room_number"])
            for row in result
        ]

        if rooms:

            return (
                "🔴 Các phòng **Đang ở**: "
                + ", ".join(rooms)
            )

        return (
            "Hiện không có phòng nào đang ở."
        )


    # -----------------------------------------------------
    # ĐANG DỌN DẸP
    # -----------------------------------------------------

    elif (
        "dọn dẹp" in prompt_lower
        or "đang dọn" in prompt_lower
        or "phòng dọn" in prompt_lower
    ):

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT room_number
                FROM rooms
                WHERE status = 'Đang dọn dẹp'
                ORDER BY room_number
                """
            )

            result = cursor.fetchall()

        rooms = [
            str(row["room_number"])
            for row in result
        ]

        if rooms:

            return (
                "🟠 Các phòng đang **Dọn dẹp**: "
                + ", ".join(rooms)
            )

        return (
            "Hiện không có phòng nào đang dọn dẹp."
        )


    # -----------------------------------------------------
    # BẢO TRÌ
    # -----------------------------------------------------

    elif (
        "bảo trì" in prompt_lower
        or "phòng hỏng" in prompt_lower
        or "phòng sửa" in prompt_lower
    ):

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT room_number, note
                FROM rooms
                WHERE status = 'Bảo trì'
                ORDER BY room_number
                """
            )

            result = cursor.fetchall()

        if not result:

            return (
                "🟢 Hiện không có phòng nào bảo trì."
            )

        response = (
            "⚙️ Các phòng đang **Bảo trì**:\n\n"
        )

        for row in result:

            note = row["note"] or "Không có ghi chú"

            response += (
                f"- Phòng **{row['room_number']}**: "
                f"{note}\n"
            )

        return response


    # -----------------------------------------------------
    # THỐNG KÊ TRẠNG THÁI
    # -----------------------------------------------------

    elif (
        "thống kê" in prompt_lower
        or "tình trạng phòng" in prompt_lower
        or "tình trạng hiện tại" in prompt_lower
    ):

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    status,
                    COUNT(*) AS total
                FROM rooms
                GROUP BY status
                ORDER BY status
                """
            )

            result = cursor.fetchall()

        response = (
            "📊 **Tình trạng phòng hiện tại:**\n\n"
        )

        for row in result:

            response += (
                f"- {row['status']}: "
                f"**{row['total']} phòng**\n"
            )

        return response


    # -----------------------------------------------------
    # TRA CỨU PHÒNG CỤ THỂ
    # -----------------------------------------------------

    import re

    room_match = re.search(
        r"\b(10[1-9]|1[1-9]\d|20[1-9]|2[1-9]\d|3\d\d)\b",
        prompt_lower
    )


    if room_match:

        room_number = room_match.group(1)

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    room_number,
                    floor,
                    room_type,
                    status,
                    price,
                    note
                FROM rooms
                WHERE room_number = %s
                """,
                (room_number,)
            )

            result = cursor.fetchone()


        if not result:

            return (
                f"Không tìm thấy phòng **{room_number}** "
                "trong cơ sở dữ liệu."
            )


        note = result["note"] or "Không có ghi chú"


        return (
            f"🏨 **Thông tin phòng {result['room_number']}**\n\n"
            f"- Tầng: **{result['floor']}**\n"
            f"- Loại phòng: **{result['room_type']}**\n"
            f"- Trạng thái: **{result['status']}**\n"
            f"- Giá: **{float(result['price']):,.0f} VNĐ**\n"
            f"- Ghi chú: **{note}**"
        )


    # -----------------------------------------------------
    # TRỢ GIÚP
    # -----------------------------------------------------

    elif (
        "giúp" in prompt_lower
        or "có thể làm gì" in prompt_lower
        or "hỗ trợ" in prompt_lower
    ):

        return """
Tôi có thể hỗ trợ bạn tra cứu:

- 🏨 Tổng số phòng
- 🟢 Phòng đang trống
- 🔴 Phòng đang có khách
- 🟠 Phòng đang dọn dẹp
- ⚙️ Phòng đang bảo trì
- 📊 Thống kê tình trạng phòng
- 🔎 Thông tin một phòng cụ thể

Ví dụ:

**"Có bao nhiêu phòng?"**

**"Phòng nào đang trống?"**

**"Phòng 102 đang ở trạng thái nào?"**

**"Có phòng nào đang bảo trì không?"**
"""


    else:

        return """
Tôi chưa hiểu câu hỏi.

Bạn có thể hỏi:

- "Có bao nhiêu phòng?"
- "Phòng nào đang trống?"
- "Phòng nào đang ở?"
- "Phòng nào đang dọn dẹp?"
- "Phòng nào đang bảo trì?"
- "Thông tin phòng 101?"
- "Thống kê tình trạng phòng"
"""


# =========================================================
# 26. SESSION CHAT
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content":
                "Xin chào! 👋 Tôi có thể giúp bạn "
                "tra cứu thông tin phòng trực tiếp "
                "từ cơ sở dữ liệu MySQL."
        }
    ]


# =========================================================
# 27. HIỂN THỊ LỊCH SỬ CHAT
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# 28. CHAT INPUT
# =========================================================

if prompt := st.chat_input(
    "Hỏi về tình trạng phòng..."
):

    # -----------------------------------------------------
    # USER MESSAGE
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )


    with st.chat_message("user"):

        st.markdown(prompt)


    # -----------------------------------------------------
    # ASSISTANT MESSAGE
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        try:

            response = chatbot_response(
                prompt
            )

        except Exception as e:

            response = (
                "❌ Có lỗi khi truy vấn database.\n\n"
                f"Chi tiết: `{e}`"
            )


        st.markdown(response)


    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )
```
