import streamlit as st
import base64
import pandas as pd
import json
from openai import OpenAI
import io

# ================= 配置区域 =================
# 建议将 API Key 放在 Streamlit secrets 中，或者在这里临时填入
# 如果你有自己的 key，请替换下面的 "your-api-key"
# 实际生产中不要直接写在代码里
api_key = st.secrets.get("OPENAI_API_KEY", "在此处填入你的sk-xxxxxx")

client = OpenAI(api_key=api_key)

# ================= 核心函数 =================

def encode_image(image_file):
    """将上传的图片转换为Base64格式"""
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def analyze_image_with_gpt4o(base64_image):
    """调用GPT-4o进行视觉识别和数据结构化"""
    
    # 这里的Prompt是关键，教AI如何提取数据
    prompt_text = """
    你是一个工厂订单处理专家。请分析这张图片（可能是手写清单、白板照片或打印件）。
    请提取所有的：产品名称、规格/型号、数量、单位、颜色/备注。
    
    请严格按照以下JSON格式返回数据，不要包含Markdown标记或其他文字：
    [
        {"产品名称": "示例螺丝", "规格": "M4x10", "数量": 1000, "单位": "个", "备注": "不锈钢"},
        ...
    ]
    如果某个字段无法识别，请留空字符串。如果是无关内容请忽略。
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # 使用具备视觉能力的模型
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=4096,
            temperature=0.1, # 低温度保证数据准确性
            response_format={ "type": "json_object" } # 强制返回JSON模式
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

# ================= 页面布局 =================

st.set_page_config(page_title="工厂智能报货清单生成器", layout="wide")

st.title("🏭 工厂智能报货清单生成器")
st.markdown("上传手写单据、白板照片或聊天截图，AI 自动生成 Excel 报货单。")

# 侧边栏：设置与帮助
with st.sidebar:
    st.header("使用说明")
    st.markdown("""
    1. 点击右侧上传图片 (jpg/png)。
    2. 等待 AI 识别。
    3. 在表格中直接修改错误数据。
    4. 点击下载 Excel 文件。
    """)
    if api_key == "在此处填入你的sk-xxxxxx":
        st.warning("⚠️ 请先在代码中配置 OpenAI API Key")

# 主界面布局
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. 上传图片")
    uploaded_file = st.file_uploader("选择图片...", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption='已上传图片', use_column_width=True)

with col2:
    st.subheader("2. 识别结果")
    
    if uploaded_file is not None:
        if st.button("开始识别生成清单", type="primary"):
            with st.spinner('AI 正在看图识别中，请稍候...'):
                try:
                    # 1. 编码图片
                    base64_image = encode_image(uploaded_file)
                    
                    # 2. 调用 AI
                    json_result = analyze_image_with_gpt4o(base64_image)
                    
                    # 3. 解析 JSON 数据
                    # 有时候模型返回的不仅是列表，可能是 { "data": [...] }，这里做个简单兼容
                    data_obj = json.loads(json_result)
                    if isinstance(data_obj, dict):
                        # 尝试寻找列表键值
                        if "items" in data_obj:
                            data_list = data_obj["items"]
                        elif "data" in data_obj:
                            data_list = data_obj["data"]
                        else:
                            # 假设只有一个键是列表
                            keys = list(data_obj.keys())
                            data_list = data_obj[keys[0]]
                    else:
                        data_list = data_obj

                    # 4. 转换为 DataFrame
                    df = pd.DataFrame(data_list)
                    
                    # 将 DataFrame 存入 Session State 以便后续编辑和下载
                    st.session_state['df_result'] = df
                    st.success("识别成功！")
                    
                except Exception as e:
                    st.error(f"发生错误: {e}")
                    st.info("提示：请检查 API Key 是否正确，或网络是否通畅。")

    # 显示可编辑表格
    if 'df_result' in st.session_state:
        st.markdown("💡 **提示**：直接点击表格内容进行修改，修改后会自动保存。")
        
        # Data Editor 允许用户在网页上直接修改数据
        edited_df = st.data_editor(
            st.session_state['df_result'],
            num_rows="dynamic", # 允许添加/删除行
            use_container_width=True
        )

        st.subheader("3. 导出文件")
        
        # 生成 Excel 下载流
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, index=False, sheet_name='报货清单')
        
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 下载 Excel 报货单",
            data=processed_data,
            file_name="factory_order_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )