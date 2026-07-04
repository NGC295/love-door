import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
from datetime import datetime

# ============================================================
# 1. Supabase 配置（和情侣网站共用同一个数据库）
# ============================================================
SUPABASE_URL = 'https://ucxtoekdjqlkkfrkpbol.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVjeHRvZWtkanFsa2tmcmtwYm9sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMwOTEwNDcsImV4cCI6MjA5ODY2NzA0N30.bGAUFN92YZLfmDUbd9t_DsmxymA8KZgr1Z67ezWLBJY'

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ============================================================
# 2. 页面配置
# ============================================================
st.set_page_config(page_title="📊 成绩看板", page_icon="📊", layout="wide")
st.title("📊 成绩统计看板")
st.markdown("---")

# ============================================================
# 3. 侧边栏：录入成绩
# ============================================================
with st.sidebar:
    st.header("📝 录入新成绩")
    subject = st.text_input("科目名称", placeholder="如：数学")
    score = st.number_input("分数", min_value=0, max_value=100, step=1)
    exam_date = st.date_input("考试日期", value=datetime.today())
    
    if st.button("✅ 录入成绩", use_container_width=True):
        if not subject:
            st.error("请输入科目名称")
        else:
            try:
                data = {
                    "subject": subject,
                    "score": int(score),
                    "exam_date": exam_date.strftime("%Y-%m-%d")
                }
                supabase.table("scores").insert(data).execute()
                st.success("✅ 成绩录入成功！")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 录入失败：{e}")

# ============================================================
# 4. 主区域：数据展示
# ============================================================
try:
    response = supabase.table("scores").select("*").order("exam_date", desc=False).execute()
    data = response.data
except Exception as e:
    st.error(f"读取数据失败：{e}")
    data = []

if not data:
    st.info("📝 还没有成绩数据，请在左侧录入第一条！")
    st.stop()

df = pd.DataFrame(data)
df["exam_date"] = pd.to_datetime(df["exam_date"])

# ============================================================
# 5. 统计概览卡片
# ============================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📚 科目数", df["subject"].nunique())
with col2:
    st.metric("📝 考试次数", len(df))
with col3:
    st.metric("📈 平均分", f"{df['score'].mean():.1f}")
with col4:
    st.metric("🏆 最高分", df["score"].max())

st.markdown("---")

# ============================================================
# 6. 折线统计图
# ============================================================
st.subheader("📈 成绩趋势图")

fig = px.line(
    df,
    x="exam_date",
    y="score",
    color="subject",
    markers=True,
    title="各科目成绩变化趋势",
    labels={"exam_date": "考试日期", "score": "分数", "subject": "科目"},
    color_discrete_sequence=px.colors.qualitative.Set2
)

fig.update_layout(
    xaxis_title="考试日期",
    yaxis_title="分数",
    yaxis_range=[0, 100],
    legend_title="科目",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 7. 成绩明细 + 删除功能
# ============================================================
st.markdown("---")
st.subheader("📋 成绩明细")

subjects = ["全部"] + sorted(df["subject"].unique().tolist())
selected_subject = st.selectbox("按科目筛选", subjects)

if selected_subject != "全部":
    filtered_df = df[df["subject"] == selected_subject]
else:
    filtered_df = df

st.dataframe(
    filtered_df[["subject", "score", "exam_date"]].sort_values("exam_date", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "subject": "科目",
        "score": st.column_config.NumberColumn("分数", min_value=0, max_value=100),
        "exam_date": "考试日期",
    }
)

st.markdown("---")
st.subheader("🗑️ 删除成绩")

delete_options = [f"{row['subject']} - {row['score']}分 ({row['exam_date']})" for row in filtered_df.to_dict('records')]
if delete_options:
    selected_delete = st.selectbox("选择要删除的成绩", delete_options)
    if st.button("🗑️ 删除选中的成绩", type="secondary", use_container_width=True):
        selected_row = filtered_df.iloc[delete_options.index(selected_delete)]
        try:
            supabase.table("scores").delete().eq("id", selected_row["id"]).execute()
            st.success("✅ 删除成功！")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 删除失败：{e}")
else:
    st.info("暂无成绩可删除")
