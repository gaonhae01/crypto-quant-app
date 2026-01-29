import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import io

# --- 1. 페이지 설정 (위트와 장난기 가득) ---
st.set_page_config(page_title="비트코인가격예상", layout="wide", page_icon="🤑")

# 커스텀 CSS로 스타일 꾸미기
st.markdown("""
<style>
    .main-title {
        font-size: 3em !important;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        text-shadow: 2px 2px 4px #000000;
    }
    .sub-text {
        font-size: 1.2em;
        text-align: center;
        color: #FFFFFF;
        margin-bottom: 30px;
    }
    .highlight {
        color: #FFD700;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 사이드바: 파라미터 컨트롤 (초보자 친화적) ---
st.sidebar.title("🎛️ 설정 컨트롤러")
st.sidebar.markdown("본인의 <span class='highlight'>야수의 심장</span> 크기를 선택하세요.", unsafe_allow_html=True)

# 투자 성향 선택으로 변경
risk_appetite = st.sidebar.radio(
    "당신의 투자 스타일은?",
    ("안전 제일", "적당히 즐기자", "드가자~", "인생역전 풀매수"),
    index=1
)

# 선택에 따른 내부 파라미터 매핑 (mu: 기대수익률, sigma: 변동성)
if risk_appetite == "안전 제일":
    mu = 0.05
    sigma = 0.4
elif risk_appetite == "적당히 즐기자":
    mu = 0.15
    sigma = 0.65
elif risk_appetite == "드가자~":
    mu = 0.3
    sigma = 0.9
else: # 뇌동매매 풀매수
    mu = 0.5
    sigma = 1.2

days = st.sidebar.slider("시뮬레이션 기간 (일)", 7, 90, 30)
simulations = st.sidebar.slider("시뮬레이션 횟수 (경로 수)", 10, 500, 100)

# --- 3. 실시간 데이터 로딩 ---
@st.cache_data(ttl=60*5) # 5분 캐싱으로 로딩 속도 개선
def get_bitcoin_data():
    btc = yf.Ticker("BTC-USD")
    data = btc.history(period="1y")
    current_price = data['Close'].iloc[-1]
    return current_price, data

# 제목과 문구 출력
st.markdown('<p class="main-title">🤑 비트코인어디까지갈까? 🤑</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">코스피 5000시대에 주식도 못해서 배아픈데 <span class="highlight">코인이라도~</span> 🚀</p>', unsafe_allow_html=True)

try:
    current_price, hist_data = get_bitcoin_data()
    
    # 상단 지표 표시
    col1, col2 = st.columns(2)
    col1.metric("현재 비트코인 가격", f"${current_price:,.2f}", 
                f"{hist_data['Close'].pct_change().iloc[-1]*100:.2f}%")
    col2.info(f"선택한 모드: **{risk_appetite}**\n\n(내부 설정: 기대수익률 {mu*100:.0f}%, 변동성 {sigma*100:.0f}%)")

    # --- 4. 몬테카를로 시뮬레이션 엔진 ---
    st.subheader("🎲 미래 가격 뽑기")
    st.markdown("멀티버스 속 코인가격")
    
    dt = 1/365
    S0 = current_price
    price_paths = []

    for _ in range(simulations):
        prices = [S0]
        for _ in range(days):
            shock = np.random.normal(0, 1)
            price = prices[-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shock)
            prices.append(price)
        price_paths.append(prices)

    # 시각화
    fig = go.Figure()
    for path in price_paths[:50]:
        fig.add_trace(go.Scatter(y=path, mode='lines', line=dict(width=1), opacity=0.3, showlegend=False))
    
    mean_path = np.mean(price_paths, axis=0)
    fig.add_trace(go.Scatter(y=mean_path, mode='lines', name='평균 예상 경로', line=dict(color='red', width=3)))
    
    fig.update_layout(
        title=f"향후 {days}일간 가격 예측 시나리오",
        xaxis_title="경과 일수 (Day)",
        yaxis_title="가격 (USD)",
        template="plotly_dark",
        hovermode="x"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- 5. 결과 분석 및 엑셀 다운로드 ---
    st.divider()
    st.subheader("📊 결과 분석 & 엑셀로 가져가기")

    final_prices = [p[-1] for p in price_paths]
    exp_return_pct = (np.mean(final_prices) - S0) / S0 * 100
    var_95 = np.percentile(final_prices, 5)
    loss_95_pct = (var_95 - S0) / S0 * 100

    col_res1, col_res2 = st.columns(2)
    col_res1.metric(f"{days}일 후 예상 평균 수익률", f"{exp_return_pct:+.2f}%")
    col_res2.metric("최악의 경우 손실률 (하위 5%)", f"{loss_95_pct:.2f}%", delta_color="inverse")

    # 엑셀 다운로드 기능 추가
    st.markdown("#### 💾 시뮬레이션 결과 엑셀로 받기")
    st.markdown("이 데이터를 가지고 엑셀에서 더 분석해보세요!")

    # 결과 데이터를 DataFrame으로 변환
    df_paths = pd.DataFrame(np.array(price_paths).T, columns=[f'시나리오_{i+1}' for i in range(simulations)])
    df_paths.index.name = 'Day'

    # 엑셀 파일 저장을 위한 버퍼 생성
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_paths.to_excel(writer, sheet_name='시뮬레이션_경로')
        # 요약 시트 추가
        summary_data = {
            '항목': ['현재가', '시뮬레이션 기간(일)', '기대수익률(연간)', '변동성(연간)', '예상 평균 수익률', 'VaR 95% 손실률'],
            '값': [current_price, days, mu, sigma, exp_return_pct/100, loss_95_pct/100]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='요약', index=False)
    
    # 다운로드 버튼
    st.download_button(
        label="📥 엑셀 파일 다운로드 (xlsx)",
        data=buffer.getvalue(),
        file_name=f"bitcoin_simulation_{days}days.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.warning("⚠️ **경고:** 이 앱은 순수재미용으로 만들어졌습니다. 이 결과를 보고 실제로 투자했다가 발생하는 손실에 대해 제작자는 **절대 책임지지 않습니다.** 서원규를 찾아가시오")

except Exception as e:
    st.error(f"어익후, 데이터를 가져오다가 넘어졌네요: {e}")
