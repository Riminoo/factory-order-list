import streamlit as st
import pandas as pd
import io
import time

# ================= 页面配置 =================
st.set_page_config(page_title="工厂智能报货清单（演示版）", layout="wide")
st.title("🏭 工厂智能报货清单生成器 (演示模式)")
st.markdown("⚠️ **当前为免Key演示模式**：AI 功能仅模拟演示，不消耗额度。")

# ================= 模拟数据函数 =================
def get_fake_ai_result():
    """模拟AI返回的数据"""
    return [
        {"产品名称": "高强度螺栓", "规格": "M12*50", "数量": 500, "单位": "套", "备注": "发黑处理"},
        {"产品名称": "平垫圈", "规格": "M12", "数量": 1000, "单位": "个", "备注": "镀锌"},
        {"产品名称": "六角螺母", "规格": "M12", "数量": 500, "单位": "个", "备注": ""},
        {"产品名称": "轴承", "规格": "6204-2RS", "数量": 20, "单位": "个", "备注": "哈尔滨轴承"},
        {"产品名称": "密封圈", "规格": "ID:50 OD:70", "数量": 10, "单位": "条", "备注": "氟胶"}
    ]

# ================= 页面布局 =================
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. 上传图片")
    uploaded_file = st.file_uploader("随便传一张图测试...", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption='已上传图片', use_column_width=True)

with col2:
    st.subheader("2. 识别结果")
    
    if uploaded_file is not None:
        if st.button("🚀 开始模拟识别", type="primary"):
            with st.spinner('正在模拟 AI 分析图片内容...'):
                # 假装思考 2 秒钟
                time.sleep(2)
                
                # 获取模拟数据
                data_list = get_fake_ai_result()
                
                # 存入 Session 状态
                st.session_state['df_result'] = pd.DataFrame(data_list)
                st.success("识别成功！(这是模拟数据)")

    # 显示可编辑表格
    if 'df_result' in st.session_state:
        st.info("👇 你可以在下面的表格里直接修改数据：")
        
        # 可编辑表格
        edited_df = st.data_editor(
            st.session_state['df_result'],
            num_rows="dynamic",
            use_container_width=True
        )

        st.subheader("3. 导出文件")
        
        # 生成 Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, index=False, sheet_name='报货清单')
        
        st.download_button(
            label="📥 下载 Excel 报货单",
            data=output.getvalue(),
            file_name="测试报货单.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
