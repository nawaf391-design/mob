import os
import streamlit as st
import yfinance as yf
import ta
from crewai import Agent, Task, Crew, Process
from langchain.tools import tool

# ضبط إعدادات الصفحة لتكون متجاوبة مع الجوال
st.set_page_config(
    page_title="مستشار تاسي الذكي",
    page_icon="🔍",
    layout="centered"
)

# تعيين اتجاه الصفحة إلى العربية (RTL) وتنسيق الخطوط
st.markdown("""
    <style>
    .reportview-container { text-align: right; direction: RTL; }
    .stTextInput>div>div>input { text-align: right; direction: RTL; }
    div[data-testid="stMarkdownContainer"] > p { text-align: right; direction: RTL; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. أداة الفحص والتصفية الفنية
# ==========================================
@tool("Multi-Stock TASI Technical Screener")
def scan_tasi_stocks(tickers_list: str) -> str:
    """
    تقوم هذه الأداة بفحص قائمة من أسهم السوق السعودي (مفصولة بفاصلة مثل: '1120.SR, 2010.SR')
    وتحسب المؤشرات الفنية اللحظية لكل سهم لتسهيل التصفية والمقارنة.
    """
    tickers = [t.strip() for t in tickers_list.split(',')]
    summary_results = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="5d", interval="15m")
            if df.empty:
                continue

            # حساب المؤشرات
            df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
            macd = ta.trend.MACD(close=df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['EMA_20'] = ta.trend.EMAIndicator(close=df['Close'], window=20).ema_indicator()
            df['EMA_50'] = ta.trend.EMAIndicator(close=df['Close'], window=50).ema_indicator()

            latest = df.iloc[-1]
            recent_data = df.tail(20)
            support = recent_data['Low'].min()
            resistance = recent_data['High'].max()

            is_bullish_trend = latest['EMA_20'] > latest['EMA_50']
            macd_cross = latest['MACD'] > latest['MACD_Signal']

            summary_results.append({
                "ticker": ticker,
                "price": round(latest['Close'], 2),
                "rsi": round(latest['RSI'], 2),
                "macd_positive": macd_cross,
                "bullish_trend": is_bullish_trend,
                "support": round(support, 2),
                "resistance": round(resistance, 2)
            })
        except Exception:
            continue

    if not summary_results:
        return "لم يتم العثور على بيانات صالحة للأسهم الممررة."

    output = "نتائج فحص الأسهم اللحظي:\n"
    for res in summary_results:
        output += f"- سهم {res['ticker']}: السعر {res['price']} ريال | RSI: {res['rsi']} | اتجاه صاعد: {res['bullish_trend']} | تقاطع MACD إيجابي: {res['macd_positive']} | دعم: {res['support']} | مقاومة: {res['resistance']}\n"
    return output

# ==========================================
# 2. بناء واجهة الويب (Streamlit UI)
# ==========================================
st.title("🔍 نظام فحص واقتناص فرص الأسهم السعودية (TASI)")
st.caption("مستشار تاسي الذكي اللحظي المدعوم بالذكاء الاصطناعي")

# قسّم الإعدادات
st.subheader("⚙️ إعدادات الاتصال والمدخلات")
api_key = st.text_input("OpenAI API Key:", type="password", help="أدخل مفتاح الـ API الخاص بـ OpenAI لتشغيل وكيل الذكاء الاصطناعي")

stocks_list = st.text_input(
    "قائمة الأسهم المراد فحصها (مفصولة بفاصلة متبوعة بـ .SR):",
    value="1120.SR, 2010.SR, 2222.SR, 1150.SR, 2082.SR"
)

# زر التشغيل
if st.button("🚀 بدء الفحص والتحليل اللحظي", use_container_width=True):
    if not api_key:
        st.warning("⚠️ الرجاء إدخال مفتاح OpenAI API Key الخاص بك أولاً.")
    elif not stocks_list:
        st.warning("⚠️ الرجاء كتابة رمز سهم واحد على الأقل لفحصه.")
    else:
        # تعيين مفتاح التشفير
        os.environ["OPENAI_API_KEY"] = api_key

        with st.spinner("جاري سحب البيانات اللحظية وتشغيل وكيل الذكاء الاصطناعي للفحص والمقارنة... يرجى الانتظار."):
            # إنشاء الوكيل
            stock_screener_agent = Agent(
                role='محلل ومصفي صفقات تاسي اللحظية',
                goal='مقارنة عدة أسهم في السوق السعودي واختيار أفضل سهم واحد يمتلك أعلى فرصة مضاربية ومخاطرة منخفضة.',
                backstory="""أنت مضارب محترف في السوق السعودي، مهمتك ليست التوصية بكل الأسهم،
                بل اختيار "السهم الماسي" الفائز بفرصة دخول آمنة وسريعة بناءً على مؤشرات RSI و MACD والمحاذاة مع المتوسطات المتحركة.""",
                tools=[scan_tasi_stocks],
                verbose=True
            )

            # إنشاء المهمة
            multi_scan_task = Task(
                description=f"""
                افحص قائمة الأسهم التالية: [{stocks_list}] باستخدام أداة 'Multi-Stock TASI Technical Screener'.
                
                خطوات العمل المطلوب منك تنفيذها:
                1. قارن المؤشرات الفنية بين جميع الأسهم المفحوصة.
                2. استبعد الأسهم التي يكون فيها مؤشر RSI ألمح إلى تشبع شرائي (> 70) أو ذات اتجاه هابط.
                3. اختر السهم الأفضل فقط من حيث قوة الزخم الإيجابي واقترابه من مستوى دعم قوي.
                4. صغ خطة تداول لحظية كاملة لهذا السهم المختار حصراً.
                """,
                expected_output="""تقرير صفقات يركز على سهم واحد متصدر:
                - اسم/رمز السهم المختار للأفضلية
                - أسباب استبعاد الأسهم الأخرى باختصار
                - سعر الدخول المقترح للسهم الفائز
                - الهدف اللحظي (Take Profit)
                - حد وقف الخسارة (Stop Loss)
                """,
                agent=stock_screener_agent
            )

            # تشغيل النظام
            crew = Crew(
                agents=[stock_screener_agent],
                tasks=[multi_scan_task],
                process=Process.sequential
            )

            try:
                result = crew.kickoff()
                
                # عرض النتيجة في صندوق مخصص ومتناسق
                st.success("✅ تم الانتهاء من التحليل بنجاح!")
                st.subheader("📋 التوصية والتقرير الفني الفائز")
                st.text_area(label="", value=str(result), height=400)
                
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء التشغيل:\n{str(e)}")
