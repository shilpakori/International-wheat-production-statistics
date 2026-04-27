import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

# ========================= LOGIN SETUP =========================
USERNAME = "admin"
PASSWORD = "1234"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ========================= DATA LOADER =========================
@st.cache_data
def load_wheat_data(custom_path: str = None):
    """
    Loads the wheat dataset safely, detects CSV/Excel.
    Cleans columns and converts year columns to numeric.
    """
    candidates = []
    if custom_path:
        candidates.append(custom_path)
    candidates.extend([
        r"C:\Users\HP\Desktop\Myapp\International wheat production statistics.csv.xls",
        r"C:\Users\HP\Desktop\Myapp\International_wheat_production_statistics.csv",
        "International wheat production statistics.csv.xls",
        "International_wheat_production_statistics.csv"
    ])

    last_exc = None
    for p in candidates:
        try:
            if str(p).lower().endswith(".csv") or ".csv" in str(p).lower():
                df = pd.read_csv(p)
            else:
                df = pd.read_excel(p, engine="openpyxl")

            # Clean column names
            df.columns = df.columns.astype(str).str.replace(r"\[.*\]", "", regex=True).str.strip()
            df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]
            if "Country" not in df.columns:
                df = df.rename(columns={df.columns[0]: "Country"})

            # Convert all year columns to numeric
            for col in df.columns:
                if col.isdigit():
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            return df

        except Exception as e:
            last_exc = e
            continue

    raise FileNotFoundError(f"Could not load dataset. Tried paths: {candidates}. Last error: {last_exc}")

# ========================= LOGIN PAGE =========================
if not st.session_state.logged_in:
    st.title("🌾 International Wheat Production Dashboard")
    st.subheader("Please login to continue")

    username = st.text_input("👤 Username")
    password = st.text_input("🔒 Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.logged_in = True
            st.success("✅ Login successful! Redirecting...")
            st.rerun()
        else:
            st.error("❌ Invalid username or password.")

# ========================= MAIN DASHBOARD =========================
else:
    st.sidebar.title("📊 Navigation")
    option = st.sidebar.selectbox(
        "Choose an Option:",
        (
            "🏠 Home",
            "Display Data",
            "Plot Bar Graph (All Countries)",
            "Top 5 Countries (Year-wise)",
            "Overall Production",
            "Pie Chart - Top 5 Countries",
            "ℹ️ About Us"
        )
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # Custom dataset path input
    st.sidebar.markdown("---")
    st.sidebar.caption("Optional: Enter custom dataset path (leave blank to use default)")
    data_path_input = st.sidebar.text_input("📂 Custom Dataset Path", "")

    # Load dataset
    try:
        df = load_wheat_data(custom_path=data_path_input.strip() or None)
    except Exception as e:
        st.error(f"❌ Unable to load dataset.\n\n*Error:* {e}")
        st.stop()

    available_years = [c for c in df.columns if c.isdigit()]

    # ========================= HOME PAGE =========================
    if option == "🏠 Home":
        st.title("🌾 International Wheat Production Dashboard")
        st.subheader("Welcome to the Global Wheat Statistics Portal")
        st.image(
            "wheat-field-wheat-cereals-grain-39015.JPEG",
            caption="Golden Wheat Fields Around the World",
            use_container_width=True
        )
       
    # ========================= DISPLAY DATA =========================
    elif option == "Display Data":
        st.header("📄 Complete Wheat Production Data (All Years)")
        st.dataframe(df.style.background_gradient(cmap="YlGn"))

    # ========================= BAR GRAPH =========================
    elif option == "Plot Bar Graph (All Countries)":
        if available_years:
            selected_year = st.selectbox("Select Year:", available_years, index=len(available_years)-1)
            st.header(f"📊 Wheat Production by Country ({selected_year})")
            fig, ax = plt.subplots(figsize=(12, 6))
            sorted_df = df.sort_values(by=selected_year, ascending=False)
            ax.bar(sorted_df["Country"], sorted_df[selected_year], color="#72A0C1", edgecolor="black")
            ax.set_title(f"Wheat Production by Country - {selected_year}", fontsize=14, fontweight='bold')
            ax.set_xlabel("Country", fontsize=12)
            ax.set_ylabel("Production (Million Tonnes)", fontsize=12)
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)
        else:
            st.warning("No valid year columns found in dataset.")

    # ========================= TOP 5 COUNTRIES =========================
    elif option == "Top 5 Countries (Year-wise)":
        st.header("🏆 Top 5 Countries by Wheat Production (Year-wise)")
        for year in available_years:
            st.subheader(f"Top 5 Producers in {year}")
            top5 = df.nlargest(5, year)[["Country", year]]
            st.table(top5.style.highlight_max(axis=0, color='lightgreen'))

    # ========================= OVERALL PRODUCTION =========================
    elif option == "Overall Production":
        st.header("🌍 Overall Wheat Production (Sum Across Years)")
        df["Total_Production"] = df[available_years].sum(axis=1)
        top10_total = df.sort_values(by="Total_Production", ascending=False).head(10)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(top10_total["Country"], top10_total["Total_Production"], color="#F4A261", edgecolor="black")
        ax.set_title("Top 10 Countries by Overall Wheat Production (2014–2020)", fontsize=14, fontweight='bold')
        ax.set_xlabel("Country", fontsize=12)
        ax.set_ylabel("Total Production (Million Tonnes)", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)

      
    # ========================= PIE CHART =========================
    elif option == "Pie Chart - Top 5 Countries":
        if available_years:
            selected_year = st.selectbox("Select Year for Pie Chart:", available_years, index=len(available_years)-1)
            st.header(f"🥧 Top 5 Countries by Wheat Production ({selected_year})")
            top5 = df.nlargest(5, selected_year)[["Country", selected_year]]
            fig, ax = plt.subplots(figsize=(6, 6))
            colors = ["#FFD700", "#90EE90", "#87CEFA", "#FFA07A", "#FFB6C1"]
            ax.pie(top5[selected_year], labels=top5["Country"], autopct="%1.1f%%",
                   startangle=90, shadow=True, colors=colors)
            ax.set_title(f"Top 5 Wheat Producers ({selected_year})", fontsize=14, fontweight='bold')
            st.pyplot(fig)

    # ========================= ABOUT US =========================
    elif option == "ℹ️ About Us":
        st.header("👩‍💻 About Us")
      
        st.markdown("""
        📊 Project: International Wheat Production Dashboard
          
        Developed by:
       
       
       
        
        Zeel Code Labs is a leading IT solutions and software development company based in Belagavi, Karnataka, dedicated to delivering innovative, reliable, and high-quality technology solutions. With years of experience in the IT industry, the company specializes in web application development, data analytics, automation, and custom software solutions tailored to meet the unique needs of clients across different sectors.

         At Zeel Code Labs, technology and creativity work hand in hand to design solutions that drive business success. The company’s strength lies in understanding client challenges, developing efficient strategies, and providing sustainable digital solutions that enhance productivity and user experience.

         Guided by a philosophy of integrity, teamwork, and continuous improvement, Zeel Code Labs fosters a collaborative environment that encourages innovation and learning. Every project is approached with a focus on quality, transparency, and customer satisfaction, ensuring long-term value for clients.

         Our Mission :

         To deliver high-quality IT services and consultancy that exceed client expectations through innovation, efficiency, and a customer-centric approach.

         Our Vision :

         To be recognized as a global leader in innovative IT solutions, blending advanced technologies, structured methodologies, and a smart-work culture that empowers both clients and employees.
        """)
