import pandas as pd

# ==========================================
# 🧠 ロジック担当 (計算・判定) - V41修正版
# ==========================================

def load_data(file_path):
    """CSVファイルを読み込んで前処理する"""
    try:
        df = pd.read_csv(file_path)
        numeric_cols = ['株価', '時価総額', 'PER', 'PBR', 'ROE', '配当利回り', '現金', '借金', '売上成長率']
        for col in numeric_cols:
            if col in df.columns and df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '').str.replace('%', '').str.replace('倍', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        return None

def calculate_score_from_row(row, strategy, budget_option, use_small_cap, use_debt_filter):
    try:
        price = float(row.get('株価', 0))
        if price <= 0: return None # 株価0円は除外

        code = str(row.get('コード', ''))
        name = str(row.get('銘柄名', ''))
        market_cap = float(row.get('時価総額', 0))
        cash = float(row.get('現金', 0))
        debt = float(row.get('借金', 0))
        per = float(row.get('PER', 999))
        pbr = float(row.get('PBR', 1.0))
        roe = float(row.get('ROE', 0))
        div_percent = float(row.get('配当利回り', 0))
        rev_growth = float(row.get('売上成長率', 0))
        industry = str(row.get('業種', '-'))

        # フィルター
        budget = price * 100
        if budget_option == "5万円以下" and budget > 50000: return None
        if budget_option == "10万円以下" and budget > 100000: return None
        if budget_option == "20万円以下" and budget > 200000: return None
        if use_small_cap and market_cap > 1000 * 100000000: return None 
        
        net_cash = cash - debt
        if use_debt_filter and net_cash < 0: return None
        cash_ratio = net_cash / market_cap if market_cap > 0 else 0

        # スコア計算
        score = 0; comment = ""; reasons = []

        if "学生" in strategy:
            # 配当スコア
            if div_percent > 4.5: score += 40; reasons.append("★超高配当")
            elif div_percent > 3.0: score += 20; reasons.append("★高配当")
            else: score -= 10
            
            # ★ここを修正しました！(大きい順に判定)
            if cash_ratio > 1.0: score += 50; reasons.append("★超金持ち") # ネットネット
            elif cash_ratio > 0.5: score += 30; reasons.append("★金持ち")
            elif cash_ratio > 0.1: score += 10
            
            if pbr < 1.0: score += 20; reasons.append("★割安")
            if budget < 50000: score += 10; reasons.append("★激安")
            
            if score >= 80: comment = "🎓 S級"; stock_type = "🛡️ 鉄壁要塞"
            elif score >= 60: comment = "🏫 A級"; stock_type = "💰 配当マシン"
            else: comment = "ー"; stock_type = "バランス"

        elif "割安成長" in strategy:
            if rev_growth > 0.20: score += 30; reasons.append("★爆速成長")
            elif rev_growth > 0.05: score += 10
            if 0 < per < 15: score += 30; reasons.append("★PER割安")
            if roe > 10: score += 20; reasons.append("★高効率")
            if cash_ratio > 0.3: score += 10
            
            if score >= 80: comment = "🔥 S級"; stock_type = "🚀 急成長"
            elif score >= 60: comment = "💎 A級"; stock_type = "💎 隠れ優良"
            else: comment = "ー"; stock_type = "バランス"
        
        else: 
             if div_percent > 4.0: score += 50; reasons.append("★神配当")
             elif div_percent > 3.0: score += 20
             if cash_ratio > 0.5: score += 30; reasons.append("★鉄壁財務")
             if pbr < 1.0: score += 20
             if score >= 80: comment = "💴 S級"; stock_type = "💰 配当王"
             elif score >= 60: comment = "💵 A級"; stock_type = "堅実"
             else: comment = "ー"; stock_type = "バランス"

        stats = {
            "守り": min(10, int(cash_ratio * 10)) if cash_ratio > 0 else 0,
            "割安": min(10, int((1.5 - pbr) * 10)) if pbr < 1.5 else 1,
            "攻め": min(10, int(rev_growth * 50)) if rev_growth > 0 else 0,
            "稼ぐ": min(10, int(roe)) if roe > 0 else 0,
            "還元": min(10, int(div_percent * 2))
        }

        return {
            "コード": code, "銘柄名": name, "業種": industry,
            "リンク": f"https://finance.yahoo.co.jp/quote/{code}",
            "スコア": score, "判定": comment, "タイプ": stock_type,
            "予算": budget, "利回り": div_percent, "PBR": pbr, "ROE": roe, "PER": per,
            "現金比率": cash_ratio, "売上成長": rev_growth,
            "stats": stats, "score_reasons": " ".join([f"`{r}`" for r in reasons])
        }

    except Exception:
        return None