import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium

# ============================================
# CONFIG
# ============================================
st.set_page_config(
    page_title="E-Commerce Dashboard",
    page_icon="🛒",
    layout="wide"
)

# ============================================
# LOAD DATA
# ============================================
@st.cache_data
def load_data():
    main_df              = pd.read_csv('main_data.csv')
    rfm_df               = pd.read_csv('rfm_data.csv')
    top_category_order   = pd.read_csv('top_category_order.csv')
    top_category_revenue = pd.read_csv('top_category_revenue.csv')
    monthly_order        = pd.read_csv('monthly_order.csv')
    delivery_summary     = pd.read_csv('delivery_summary.csv')
    top_city             = pd.read_csv('top_city.csv')
    top_payment          = pd.read_csv('top_payment.csv')
    location_df          = pd.read_csv('geolocation_dataset.csv')
    main_df['order_purchase_timestamp'] = pd.to_datetime(main_df['order_purchase_timestamp'])
    return (main_df, rfm_df, top_category_order, top_category_revenue,
            monthly_order, delivery_summary, top_city, top_payment, location_df)

(main_df, rfm_df, top_category_order, top_category_revenue,
 monthly_order, delivery_summary, top_city, top_payment, location_df) = load_data()

# ============================================
# SIDEBAR
# ============================================
st.sidebar.image("https://img.icons8.com/color/96/shopping-cart.png", width=80)
st.sidebar.title("🛒 E-Commerce Dashboard")
st.sidebar.markdown("---")

page = st.sidebar.radio("📌 Navigasi", [
    "🏠 Overview",
    "📦 Analisis Produk",
    "📈 Tren Order & Pengiriman",
    "🏙️ Analisis Pelanggan",
    "💳 Metode Pembayaran",
    "🗺️ Geospatial Analysis",
    "👥 Customer Segmentation"
])

# Filter tanggal
st.sidebar.markdown("---")
st.sidebar.subheader("🗓️ Filter Tanggal")
min_date = main_df['order_purchase_timestamp'].min().date()
max_date = main_df['order_purchase_timestamp'].max().date()
start_date = st.sidebar.date_input("Dari", min_date)
end_date   = st.sidebar.date_input("Sampai", max_date)

# Filter data berdasarkan tanggal
filtered_df = main_df[
    (main_df['order_purchase_timestamp'].dt.date >= start_date) &
    (main_df['order_purchase_timestamp'].dt.date <= end_date)
]

st.sidebar.markdown("---")
st.sidebar.caption("Dibuat dengan ❤️ menggunakan Streamlit")

# ============================================
# PAGE 1: OVERVIEW
# ============================================
if page == "🏠 Overview":
    st.title("🏠 Overview")
    st.markdown("Ringkasan keseluruhan performa e-commerce.")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Order", f"{filtered_df['order_id'].nunique():,}")
    with col2:
        st.metric("Total Customer", f"{filtered_df['customer_unique_id'].nunique():,}")
    with col3:
        st.metric("Total Revenue", f"R${filtered_df['price'].sum():,.0f}")
    with col4:
        st.metric("Rata-rata Order Value", f"R${filtered_df['price'].mean():,.0f}")

    st.markdown("---")

    # Tren order bulanan di overview
    st.subheader("📈 Tren Order Bulanan")
    filtered_df['year_month'] = filtered_df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    monthly = filtered_df.groupby('year_month')['order_id'].count().reset_index()
    monthly.columns = ['year_month', 'total_order']

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(monthly['year_month'], monthly['total_order'],
            marker='o', color='steelblue', linewidth=2)
    ax.fill_between(monthly['year_month'], monthly['total_order'], alpha=0.3)
    ax.set_xlabel('Bulan')
    ax.set_ylabel('Total Order')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

# ============================================
# PAGE 2: ANALISIS PRODUK
# ============================================
elif page == "📦 Analisis Produk":
    st.title("📦 Analisis Kategori Produk")
    st.markdown("Kategori produk apa yang paling banyak di-order dan menghasilkan revenue tertinggi?")
    st.markdown("---")

    # Filter top N
    top_n = st.slider("Tampilkan Top N Kategori", min_value=5, max_value=20, value=10)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔢 Terbanyak di-Order")
        data = top_category_order.head(top_n)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=data, x='total_order', y='category', palette='Blues_r', ax=ax)
        ax.set_title(f'Top {top_n} Kategori by Order', fontweight='bold')
        ax.set_xlabel('Total Order')
        ax.set_ylabel('')
        for i, v in enumerate(data['total_order']):
            ax.text(v, i, f' {v:,}', va='center', fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.subheader("💰 Revenue Tertinggi")
        data = top_category_revenue.head(top_n)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=data, x='total_revenue', y='category', palette='Greens_r', ax=ax)
        ax.set_title(f'Top {top_n} Kategori by Revenue', fontweight='bold')
        ax.set_xlabel('Total Revenue (R$)')
        ax.set_ylabel('')
        for i, v in enumerate(data['total_revenue']):
            ax.text(v, i, f' R${v:,.0f}', va='center', fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)

    # Tabel interaktif
    st.markdown("---")
    st.subheader("📊 Tabel Detail Kategori")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(top_category_order, use_container_width=True)
    with col2:
        st.dataframe(top_category_revenue, use_container_width=True)

# ============================================
# PAGE 3: TREN ORDER & PENGIRIMAN
# ============================================
elif page == "📈 Tren Order & Pengiriman":
    st.title("📈 Tren Order & Ketepatan Pengiriman")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tren Order per Bulan")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(monthly_order['year_month'], monthly_order['total_order'],
                marker='o', color='steelblue', linewidth=2)
        ax.fill_between(monthly_order['year_month'],
                        monthly_order['total_order'], alpha=0.3)
        ax.set_xlabel('Bulan')
        ax.set_ylabel('Total Order')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.subheader("Status Ketepatan Pengiriman")
        colors = sns.color_palette('Greens_r', len(delivery_summary))
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.pie(delivery_summary['total'], labels=delivery_summary['status'],
               autopct='%1.1f%%', colors=colors, startangle=90,
               wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        plt.tight_layout()
        st.pyplot(fig)

    # Tabel
    st.markdown("---")
    st.subheader("📊 Detail Status Pengiriman")
    st.dataframe(delivery_summary, use_container_width=True)

# ============================================
# PAGE 4: ANALISIS PELANGGAN
# ============================================
elif page == "🏙️ Analisis Pelanggan":
    st.title("🏙️ Analisis Pelanggan per Kota")
    st.markdown("---")

    top_n_city = st.slider("Tampilkan Top N Kota", min_value=5, max_value=20, value=10)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top_city.head(top_n_city), x='total_customer', y='city',
                palette='Oranges_r', ax=ax)
    ax.set_title(f'Top {top_n_city} Kota dengan Pelanggan Terbanyak', fontweight='bold')
    ax.set_xlabel('Total Pelanggan')
    ax.set_ylabel('Kota')
    for i, v in enumerate(top_city.head(top_n_city)['total_customer']):
        ax.text(v, i, f' {v:,}', va='center', fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 Tabel Detail Kota")
    st.dataframe(top_city, use_container_width=True)

# ============================================
# PAGE 5: METODE PEMBAYARAN
# ============================================
elif page == "💳 Metode Pembayaran":
    st.title("💳 Analisis Metode Pembayaran")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots(figsize=(8, 8))
        colors = sns.color_palette('Set2', len(top_payment))
        ax.pie(top_payment['total'], labels=top_payment['payment_type'],
               autopct='%1.1f%%', colors=colors, startangle=90,
               wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        ax.set_title('Distribusi Metode Pembayaran', fontweight='bold')
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(data=top_payment, x='payment_type', y='total',
                    palette='Set2', ax=ax)
        ax.set_title('Jumlah Transaksi per Metode Pembayaran', fontweight='bold')
        ax.set_xlabel('Metode Pembayaran')
        ax.set_ylabel('Total Transaksi')
        for i, v in enumerate(top_payment['total']):
            ax.text(i, v, f' {v:,}', ha='center', fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)

    st.markdown("---")
    st.dataframe(top_payment, use_container_width=True)

# ============================================
# PAGE 6: GEOSPATIAL ANALYSIS
# ============================================
elif page == "🗺️ Geospatial Analysis":
    st.title("🗺️ Geospatial Analysis")
    st.markdown("Distribusi pelanggan berdasarkan lokasi geografis.")
    st.markdown("---")

    # Sample data agar tidak berat
    sample_location = location_df.sample(n=3000, random_state=42)

    # Buat peta folium
    m = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)

    for _, row in sample_location.iterrows():
        folium.CircleMarker(
            location=[row['geolocation_lat'], row['geolocation_lng']],
            radius=2,
            color='steelblue',
            fill=True,
            fill_opacity=0.5
        ).add_to(m)

    st_folium(m, width=1200, height=500)

    st.markdown("---")
    st.subheader("📊 Distribusi per State")
    state_count = location_df['geolocation_state'].value_counts().reset_index()
    state_count.columns = ['state', 'total']

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.barplot(data=state_count, x='state', y='total', palette='Blues_r', ax=ax)
    ax.set_title('Distribusi Pelanggan per State', fontweight='bold')
    ax.set_xlabel('State')
    ax.set_ylabel('Total')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

# ============================================
# PAGE 7: CUSTOMER SEGMENTATION
# ============================================
elif page == "👥 Customer Segmentation":
    st.title("👥 Customer Segmentation - RFM Analysis")
    st.markdown("---")

    # Metric per segment
    segment_count = rfm_df['Segment'].value_counts().reset_index()
    segment_count.columns = ['Segment', 'Total']

    col1, col2, col3, col4 = st.columns(4)
    segments = ['Champion', 'Loyal Customer', 'At Risk', 'Hibernating']
    icons    = ['👑', '😊', '⚠️', '😴']
    colors_metric = ['#2ecc71', '#3498db', '#e67e22', '#e74c3c']

    for i, (col, seg, icon) in enumerate(zip([col1,col2,col3,col4], segments, icons)):
        val = segment_count[segment_count['Segment']==seg]['Total'].values
        val = val[0] if len(val) > 0 else 0
        with col:
            st.metric(f"{icon} {seg}", f"{val:,}")

    st.markdown("---")

    # Filter segment
    selected_segment = st.multiselect(
        "Filter Segment",
        options=rfm_df['Segment'].unique(),
        default=rfm_df['Segment'].unique()
    )
    filtered_rfm = rfm_df[rfm_df['Segment'].isin(selected_segment)]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Jumlah Customer per Segment")
        fig, ax = plt.subplots(figsize=(8, 5))
        data = filtered_rfm['Segment'].value_counts().reset_index()
        data.columns = ['Segment', 'Total']
        sns.barplot(data=data, x='Segment', y='Total', palette='Set2', ax=ax)
        ax.set_xlabel('Segment')
        ax.set_ylabel('Jumlah Customer')
        plt.xticks(rotation=15)
        for i, v in enumerate(data['Total']):
            ax.text(i, v, f' {v:,}', ha='center', fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.subheader("Recency vs Monetary")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.scatterplot(data=filtered_rfm, x='Recency', y='Monetary',
                        hue='Segment', palette='Set2', s=50, alpha=0.7, ax=ax)
        ax.set_xlabel('Recency (Hari)')
        ax.set_ylabel('Monetary (R$)')
        plt.tight_layout()
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 RFM Summary per Segment")
    rfm_summary = filtered_rfm.groupby('Segment')[['Recency','Frequency','Monetary']] \
                               .mean().round(2).reset_index()
    st.dataframe(rfm_summary, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Data RFM Detail")
    st.dataframe(filtered_rfm[['customer_unique_id','Recency','Frequency',
                                'Monetary','Segment']].reset_index(drop=True),
                 use_container_width=True)