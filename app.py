import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import logic  # ロジックファイル(logic.py)を読み込む

st.set_page_config(layout="wide", page_title="清原式 小型株ハンターPro V42 (スコア青天井版)")

# ==========================================
# UIパーツ: 詳細カード表示
# ==========================================
def render_detail_card(row):
    st.markdown(f"### {row['判定']} {row['銘柄名']} ({row['コード']})")
    col_main, col_radar, col_chart = st.columns([1.2, 1, 1.4])
    
    with col_main:
        st.caption(f"🏢 {row['業種']} | {row['タイプ']}")
        m1, m2, m3 = st.columns(3)
        m1.metric("スコア", f"{row['スコア']}", row['判定'])
        m2.metric("利回り", f"{row['利回り']:.2f}%")
        m3.metric("予算", f"¥{row['予算']:,.0f}")
        
        st.write(f"**PBR:** {row['PBR']:.2f}倍 | **PER:** {row['PER']:.1f}倍 | **ROE:** {row['ROE']:.1f}%")
        st.write(f"**現金比率:** {row['現金比率']:.2f}")
        st.info(f"📝 理由: {row['score_reasons']}")
        st.markdown(f"[Yahooファイナンス]({row['リンク']})")

    with col_radar:
        stats = row['stats']
        fig = go.Figure(data=go.Scatterpolar(r=list(stats.values()), theta=list(stats.keys()), fill='toself'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False, height=220, margin=dict(t=20, b=20, l=40, r=40))
        st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

    with col_chart:
        if st.button(f"📈 最新チャート", key=f"btn_{row['コード']}"):
            with st.spinner("取得中..."):
                try:
                    ticker = yf.Ticker(row['コード'])
                    hist = ticker.history(period="6mo")
                    if not hist.empty:
                        fig_chart = go.Figure()
                        fig_chart.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='株価'))
                        fig_chart.update_layout(height=250, showlegend=False, title="直近6ヶ月", margin=dict(l=0,r=0,t=30,b=0))
                        st.plotly_chart(fig_chart, use_container_width=True)
                except: st.error("取得エラー")
        else: st.markdown("👆 ボタンで表示")

# ==========================================
# メイン画面実行
# ==========================================
st.title('⚡ 清原式 小型株ハンターPro V42 (スコア青天井版)')

with st.sidebar:
    st.header("📂 データ読み込み")
    uploaded_file = st.file_uploader("stock_list.csv をアップロード", type="csv")
    
    st.header("🔍 分析フィルター")
    strategy = st.radio("戦略", ("🎓 学生・少額高配当", "🚀 割安成長株", "💰 MBO/解散価値"))
    st.markdown("---")
    budget_option = st.selectbox("上限予算", ("指定なし", "5万円以下", "10万円以下", "20万円以下"))
    use_small_cap = st.checkbox("小型株のみ", value=False)
    use_debt_filter = st.checkbox("借金超過を除外", value=True)

if uploaded_file is not None:
    # logic.pyを使ってデータを読み込む
    df_raw = logic.load_data(uploaded_file)
    
    if df_raw is not None:
        results = []
        # 全件計算
        for index, row in df_raw.iterrows():
            res = logic.calculate_score_from_row(row, strategy, budget_option, use_small_cap, use_debt_filter)
            if res: results.append(res)
        
        df_res = pd.DataFrame(results)
        
        if not df_res.empty:
            # スコアが高い順に並び替え
            df_res = df_res.sort_values('スコア', ascending=False).reset_index(drop=True)
            st.success(f"📊 {len(df_res)}件 ヒット (全{len(df_raw)}件中)")
            
            # ▼ ここが修正ポイント！ max_value=200 にして青天井に対応
            st.dataframe(df_res, column_config={
                "リンク": st.column_config.LinkColumn("詳細"),
                "スコア": st.column_config.ProgressColumn(
                    "Score", 
                    format="%d", 
                    min_value=0, 
                    max_value=200  # ★ここを200に増やしました！
                ),
                "予算": st.column_config.NumberColumn("予算", format="¥%d"),
                "利回り": st.column_config.NumberColumn("利回り", format="%.2f%%"),
                "PBR": st.column_config.NumberColumn("PBR", format="%.2f倍"),
                "ROE": st.column_config.NumberColumn("ROE", format="%.1f%%"),
                "stats": None, "score_reasons": None, "タイプ": None
            }, hide_index=True)
            
            st.divider()
            st.header("🏆 詳細分析")
            top_n = st.slider("表示件数", 1, 20, 3)
            for i, row in df_res.head(top_n).iterrows():
                render_detail_card(row)
                st.markdown("---")
        else:
            st.warning("条件に合う銘柄がありません。")
    else:
        st.error("CSVファイルの読み込みに失敗しました。")
else:
    st.info("👈 サイドバーから `stock_list.csv` をアップロードしてください。")