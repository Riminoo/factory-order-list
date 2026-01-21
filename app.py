import streamlit as st
import base64
import pandas as pd
import json
from openai import OpenAI
import io

# ================= 配置区域 =================
api_key = st.secrets.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=api_key)

# ================= 核心函数 =================
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def analyze_image_with_gpt4o(base64_image):
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
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
            max_tokens=4096,
            temperature=0.1,
            response_format={ "type": "json_object" }
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

# ================= 页面布局 =================
st.set_page_config(page_title="工厂智能报货清单生成器", layout="wide")
st.title("🏭 工厂智能报货清单生成器")

if not api_key:
    st.error("⚠️ 未检测到 API Key，请在 Streamlit Secrets 中配置 OPENAI_API_KEY")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. 上传图片")
    uploaded_file = st.file_uploader("选择图片...", type=['jpg', 'jpeg', 'png'])
    if uploaded_file:
        st.image(uploaded_file, caption='已上传图片', use_column_width=True)

with col2:
    st.subheader("2. 识别结果")
    if uploaded_file and st.button("开始识别", type="primary"):
        if not api_key:
            st.warning("请先配置 API Key 才能运行")
        else:
            with st.spinner('AI 正在识别...'):
                base64_image = encode_image(uploaded_file)
                json_result = analyze_image_with_gpt4o(base64_image)
                try:
                    data_obj = json.loads(json_result)
                    if isinstance(data_obj, dict):
                        # 兼容不同返回格式
                        data_list = data_obj.get("items") or data_obj.get("data") or list(data_obj.values())[0]
                    else:
                        data_list = data_obj
                    st.session_state['df_result'] = pd.DataFrame(data_list)
                    st.success("识别成功！")
                except:
                    st.error("识别结果解析失败，请重试")

    if 'df_result' in st.session_state:
        edited_df = st.data_editor(st.session_state['df_result'], num_rows="dynamic", use_container_width=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, index=False, sheet_name='报货清单')
        st.download_button("📥 下载 Excel", data=output.getvalue(), file_name="order_list.xlsx")
