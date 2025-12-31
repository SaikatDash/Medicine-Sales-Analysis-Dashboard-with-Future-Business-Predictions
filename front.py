import streamlit as st
import mysql.connector
from mysql.connector import Error
import base64

st.set_page_config(
    page_title="Business Analytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

@st.cache_resource
def init_connection():
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="sys449420",
            database="company"
        )
        return mydb
    except Error as e:
        st.error(f"Error connecting to MySQL Database: {e}")
        return None

def authenticate_user(user_or_email, password):
    try:
        mydb = init_connection()
        if mydb is None:
            return False, ""
        cursor = mydb.cursor()
        query = """SELECT username, email FROM users 
                   WHERE (email = %s OR username = %s) AND password = %s"""
        cursor.execute(query, (user_or_email, user_or_email, password))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return True, result[1] if result[1] else result[0]
        else:
            return False, ""
    except Error as e:
        st.error(f"Database authentication error: {e}")
        return False, ""

def check_email_exists(email):
    try:
        mydb = init_connection()
        if mydb is None:
            return True
        cursor = mydb.cursor()
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        exists = cursor.fetchone()
        cursor.close()
        return bool(exists)
    except Error:
        return True

def check_username_exists(username):
    try:
        mydb = init_connection()
        if mydb is None:
            return True
        cursor = mydb.cursor()
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        exists = cursor.fetchone()
        cursor.close()
        return bool(exists)
    except Error:
        return True

def add_user(data):
    try:
        mydb = init_connection()
        if mydb is None:
            return False
        cursor = mydb.cursor()
        insert_query = """
        INSERT INTO users (name, company_name, age, adhaar_card_number, phone_number, username, email, password)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            data['name'], data['company_name'], data['age'], data['adhaar_card_number'],
            data['phone_number'], data['username'], data['email'], data['password']
        ))
        mydb.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Sign up error: {e}")
        return False

def create_users_table():
    try:
        mydb = init_connection()
        if mydb is None:
            return False
        cursor = mydb.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            company_name VARCHAR(100),
            age INT,
            adhaar_card_number VARCHAR(20),
            phone_number VARCHAR(20),
            username VARCHAR(50) UNIQUE,
            password VARCHAR(255),
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        cursor.close()
        return True
    except Error as e:
        st.error(f"Error creating users table: {e}")
        return False

def get_base64_image():
    svg = """
    <svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
            </linearGradient>
        </defs>
        <rect width="800" height="400" fill="url(#grad1)" rx="20" ry="20"/>
        <circle cx="150" cy="150" r="50" fill="rgba(255,255,255,0.2)"/>
        <circle cx="650" cy="100" r="30" fill="rgba(255,255,255,0.3)"/>
        <circle cx="700" cy="300" r="40" fill="rgba(255,255,255,0.2)"/>
        <rect x="50" y="50" width="100" height="20" fill="rgba(255,255,255,0.3)" rx="10"/>
        <rect x="600" y="350" width="150" height="25" fill="rgba(255,255,255,0.3)" rx="12"/>
        <polygon points="400,50 450,150 350,150" fill="rgba(255,255,255,0.2)"/>
    </svg>
    """
    b64 = base64.b64encode(svg.encode()).decode()
    return b64

def load_css():
    bg_img = get_base64_image()
    st.markdown(f"""
    <style>
    .main-header {{ 
        font-size: 3.5rem; font-weight: 700; color: #1f77b4; text-align: center; margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }}
    .sub-header {{ font-size: 1.5rem; color: #666; text-align: center; margin-bottom: 2rem;}}
    .feature-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        padding: 1.5rem; border-radius: 15px; color: white; margin: 1rem 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        position: relative; overflow: hidden;}}
    .feature-card::before {{
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 100%;
        height: 100%;
        background: url("data:image/svg+xml;base64,{bg_img}") no-repeat;
        background-size: 200px 100px;
        opacity: 0.1;
    }}
    .signin-container {{ background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem; border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); margin: 2rem 0;}}
    .hero-section {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem; border-radius: 20px; color: white; margin: 2rem 0; text-align: center;
        background-image: url("data:image/svg+xml;base64,{bg_img}"); background-size: cover; background-blend-mode: soft-light;}}
    .stat-card {{ background: white; padding: 1.5rem; border-radius: 10px; text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 1rem 0; border: 2px solid transparent; transition: all 0.3s ease;}}
    .stat-card:hover {{ border-color: #667eea; transform: translateY(-5px);}}
    .logo-section {{ text-align: center; margin: 2rem 0;}}
    .dashboard-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;}}
    </style>
    """, unsafe_allow_html=True)

def create_front_page():
    load_css()
    create_users_table()

    # Show the logo/banner center aligned at medium size (width=350 px)
    st.markdown(
        f"""
        <div style='text-align: center;'>
            <img src='data:image/png;base64,{base64.b64encode(open("business.png", "rb").read()).decode()}' width='350'/>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<h1 class="main-header">Business Analytics Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transform Your Data into Actionable Business Insights</p>', unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-section">
        <h2>🚀 Powerful Analytics at Your Fingertips</h2>
        <p style="font-size: 1.2rem; margin: 1.5rem 0;">
            Upload multiple CSV files, get instant insights, build ML models, and predict future trends - all in one platform!
        </p>
        <div style="font-size: 3rem; margin: 1rem 0; opacity: 0.8;">
            📈 📊 🤖 📋
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">📈</div>
            <h3>Smart Analytics</h3>
            <p>• Automatic data analysis<br>
            • Statistical insights<br>
            • Business recommendations<br>
            • Interactive visualizations</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">🤖</div>
            <h3>Machine Learning</h3>
            <p>• Predictive modeling<br>
            • Future forecasting<br>
            • Product analysis<br>
            • Sales optimization</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2 = st.tabs(["🔑 Sign In", "🆕 Sign Up"])
    with tab1:
        col_img, col_form = st.columns([1, 2])
        with col_img:
            st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 5rem; color: #667eea; margin-bottom: 1rem;">🔐</div>
                <h3 style="color: #333;">Welcome Back!</h3>
                <p style="color: #666;">Sign in to access your analytics dashboard</p>
            </div>
            """, unsafe_allow_html=True)
        with col_form:
            st.markdown("""
            <div class="signin-container">
                <h2 style="text-align: center; color: #333; margin-bottom: 1.5rem;">Sign In</h2>
            </div>""", unsafe_allow_html=True)
            with st.form("signin_form"):
                user_or_email = st.text_input("👤 Username or 📧 Email ID", placeholder="Enter username or email")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                submit_button = st.form_submit_button("🚀 Sign In")
                if submit_button:
                    valid, session_id = authenticate_user(user_or_email, password)
                    if valid:
                        st.session_state.logged_in = True
                        st.session_state.username = session_id
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")

    with tab2:
        col_img, col_form = st.columns([1, 2])
        with col_img:
            st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 5rem; color: #667eea; margin-bottom: 1rem;">🚀</div>
                <h3 style="color: #333;">Join Us Today!</h3>
                <p style="color: #666;">Create your account and start analyzing data instantly</p>
            </div>
            """, unsafe_allow_html=True)
        with col_form:
            st.markdown("""
            <div class="signin-container">
                <h2 style="text-align: center; color: #333; margin-bottom: 1.5rem;">Sign Up</h2>
            </div>""", unsafe_allow_html=True)
            with st.form("signup_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    name = st.text_input("👤 Full Name", placeholder="Enter your name")
                    company = st.text_input("🏢 Company Name", placeholder="Enter your company name")
                    age = st.number_input("🎂 Age", min_value=16, max_value=100, value=25)
                    adhaar = st.text_input("🪪 Adhaar Card Number", placeholder="Enter your Aadhar number")
                with col_b:
                    phone = st.text_input("📱 Phone Number", placeholder="Enter your phone number")
                    username = st.text_input("🧑 Username", placeholder="Create a username")
                    sign_email = st.text_input("📧 Email ID", placeholder="Enter your Email ID", key="signup_email")
                    sign_pass = st.text_input("🔒 Password", type="password", placeholder="Enter your password", key="signup_pwd")
                submit_signup = st.form_submit_button("🆕 Create Account", use_container_width=True)
                if submit_signup:
                    if not name or not company or not adhaar or not phone or not username or not sign_email or not sign_pass:
                        st.warning("Please enter all fields.")
                    elif check_email_exists(sign_email):
                        st.error("❌ That email is already registered.")
                    elif check_username_exists(username):
                        st.error("❌ That username is already taken.")
                    else:
                        data = {
                            'name': name, 'company_name': company, 'age': int(age),
                            'adhaar_card_number': adhaar, 'phone_number': phone,
                            'username': username, 'email': sign_email, 'password': sign_pass
                        }
                        if add_user(data):
                            st.success("🎉 Account created! Please Sign In.")
                        else:
                            st.error("Sign up failed. Please try again.")

    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #333; margin: 2rem 0;'>📊 Platform Statistics</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    stats = [
        ("👥", "10,000+", "Active Users"),
        ("📁", "1M+", "Files Analyzed"),
        ("🎯", "95%", "Accuracy Rate"),
        ("⚡", "2.5s", "Avg Analysis Time")
    ]
    for i, (icon, number, label) in enumerate(stats):
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size: 2rem;">{icon}</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #1f77b4; margin: 0.5rem 0;">{number}</div>
                <div style="color: #666;">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <div style="font-size: 1.5rem; margin-bottom: 1rem;">🌟 ⚡ 🔒</div>
        <p>Built with Streamlit & MySQL | © 2025 Business Analytics Pro | All Rights Reserved</p>
        <p>🔒 Secure • 🚀 Fast • 📊 Powerful</p>
    </div>
    """, unsafe_allow_html=True)

def create_main_app():
    st.markdown("""
    <div class="dashboard-header">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center;">
                <div style="font-size: 2.5rem; margin-right: 1rem;">📊</div>
                <div>
                    <h1 style="margin: 0; font-size: 2rem;">Business Analytics Dashboard</h1>
                    <p style="margin: 0; opacity: 0.8;">Welcome back, {st.session_state.username}! 👋</p>
                </div>
            </div>
            <div style="font-size: 3rem; opacity: 0.6;">🚀</div>
        </div>
    </div>
    """.format(st.session_state.username), unsafe_allow_html=True)

    col1, col2, col3 = st.columns([6, 1, 1])
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    st.markdown("""
    <div style="background: #f8f9fa; padding: 2rem; border-radius: 15px; text-align: center; margin: 2rem 0;">
        <div style="font-size: 4rem; color: #667eea; margin-bottom: 1rem;">📈</div>
        <h2>Your Analytics Workspace</h2>
        <p style="color: #666; font-size: 1.1rem;">Upload CSV files, build ML models, and generate insights here!</p>
        <div style="margin-top: 2rem; font-size: 1.5rem;">
            📊 📋 🤖 📈 💡
        </div>
    </div>
    """, unsafe_allow_html=True)
    
def main():
    if not st.session_state.logged_in:
        create_front_page()
    else:
        create_main_app()

if __name__ == "__main__":
    main()
