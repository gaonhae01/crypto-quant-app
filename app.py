import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# --- 1. 페이지 설정 (Fancy한 디자인) ---
st.set_page_config(page_title="Alpha Stochastic", layout="wide", page_icon="📈")

st.markdown("""
<style>
    .big-font { font-size:30px !important; font-weight: bold; }
    .metric-box { border: 1px solid #333; padding: 20px; border-radius: 10px; background-color: #0e1117; }
</style>
""", unsafe_allow_html=True)

# --- 2. 사이드바: 파라미터 컨트롤 (Optimal Control) ---
st.sidebar.title("⚙️ Model Parameters")
st.sidebar.markdown("금융수학 모델(SDE) 파라미터를 설정하세요.")

mu = st.sidebar.slider("Drift (μ, 연간 기대수익률)", -0.5, 1.0, 0.15)
sigma = st.sidebar.slider("Volatility (σ, 변동성)", 0.1, 1.5, 0.65)
days = st.sidebar.slider("Simulation Horizon (Days)", 7, 90, 30)
simulations = st.sidebar.slider("Number of Paths", 10, 1000, 100)

# --- 3. 실시간 데이터 로딩 ---
def get_bitcoin_data():
    btc = yf.Ticker("BTC-USD")
    data = btc.history(period="1y")
    current_price = data['Close'].iloc[-1]
    return current_price, data

st.title("Alpha-Stochastic: Crypto Quant Advisor")
st.markdown("Powered by **Geometric Brownian Motion (SDE)** & **Optimal Control Theory**")

try:
    current_price, hist_data = get_bitcoin_data()
    
    # 상단 지표 표시
    col1, col2, col3 = st.columns(3)
    col1.metric("Real-time BTC Price", f"${current_price:,.2f}", 
                f"{hist_data['Close'].pct_change().iloc[-1]*100:.2f}%")
    col2.metric("Model Drift (μ)", f"{mu:.2f}")
    col3.metric("Model Volatility (σ)", f"{sigma:.2f}")

    # --- 4. SDE 시뮬레이션 엔진 (GBM) ---
    st.subheader("📊 Monte Carlo Simulation (SDE)")
    
    # 수식 표시 (LaTeX)
    st.latex(r"dS_t = \mu S_t dt + \sigma S_t dW_t")
    
    dt = 1/365
    S0 = current_price
    price_paths = []

    for _ in range(simulations):
        prices = [S0]
        for _ in range(days):
            # 브라운 운동 dW
            shock = np.random.normal(0, 1)
            # 이산화된 SDE 해
            price = prices[-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shock)
            prices.append(price)
        price_paths.append(prices)

    # 시각화
    fig = go.Figure()
    for path in price_paths[:50]: # 너무 많으면 느리므로 50개만 그림
        fig.add_trace(go.Scatter(y=path, mode='lines', line=dict(width=1), opacity=0.3, showlegend=False))
    
    # 평균 경로
    mean_path = np.mean(price_paths, axis=0)
    fig.add_trace(go.Scatter(y=mean_path, mode='lines', name='Expected Path', line=dict(color='red', width=3)))
    
    fig.update_layout(title=f"Forward Price Projection ({days} Days)", xaxis_title="Days", yaxis_title="Price ($)", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # --- 5. 퀀트 어드바이저 (결과 분석) ---
    final_prices = [p[-1] for p in price_paths]
    exp_return = (np.mean(final_prices) - S0) / S0
    var_95 = np.percentile(final_prices, 5) # VaR 95%
    
    st.divider()
    st.subheader("🧠 Quant Strategic Advice")

    # 간단한 켈리 기준 계산 (f* = mu / sigma^2) - 단순화된 버전
    kelly_fraction = max(0, mu / (sigma**2)) if mu > 0 else 0
    recommendation = "HOLD / NEUTRAL"
    color = "yellow"
    
    if kelly_fraction > 0.5:
        recommendation = "STRONG BUY"
        color = "green"
    elif kelly_fraction > 0.1:
        recommendation = "BUY"
        color = "lightgreen"
    elif exp_return < -0.05:
        recommendation = "SELL / HEDGE"
        color = "red"

    st.info(f"""
    **Optimal Control Analysis:**
    기하학적 브라운 운동 모델링 결과, 30일 후 예상 수익률은 **{exp_return*100:.2f}%** 입니다.
    하방 리스크(VaR 95%)는 현재가 대비 **{(var_95-S0)/S0*100:.2f}%** 수준입니다.
    """)

    st.markdown(f"### Recommended Action: :{color}[{recommendation}]")
    st.markdown(f"**Theoretical Allocation (Kelly Criterion):** 포트폴리오의 **{kelly_fraction*100:.1f}%** 비중 권장")
    
    st.warning("⚠️ Disclaimer: 이 모델은 금융수학적 시뮬레이션 도구일 뿐, 실제 투자 권유가 아닙니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
