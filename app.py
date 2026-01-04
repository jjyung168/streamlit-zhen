import streamlit as st
import subprocess
import os
import requests
import zipfile
import io
import time
import uuid

# --- 页面 UI ---
st.set_page_config(page_title="哪吒 V1 (Config模式)", page_icon="⚙️")
st.title("⚙️ 哪吒 V1 Agent (v1.14.3+)")

# --- 1. 读取配置 ---
# 必填
NEZHA_SERVER = st.secrets.get("NEZHA_SERVER", "")  # 面板地址:端口
NEZHA_KEY = st.secrets.get("NEZHA_KEY", "")        # 对应面板里的密钥/Client Secret

# 选填
NEZHA_UUID = st.secrets.get("NEZHA_UUID", "")      # 固定 UUID，防止重启变新机
NEZHA_TLS = st.secrets.get("NEZHA_TLS", "true")    # 是否开启 TLS

# --- 2. 核心功能 ---

def install_agent():
    agent_bin = "nezha-agent"
    if not os.path.exists(agent_bin):
        st.info("⬇️ 正在下载哪吒 Agent v1.14.3...")
        try:
            # 下载官方 Release
            url = "https://github.com/nezhahq/agent/releases/download/v1.14.3/nezha-agent_linux_amd64.zip"
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    z.extractall(".")
                subprocess.run(["chmod", "+x", agent_bin])
                st.success("✅ 下载完成")
            else:
                st.error(f"❌ 下载失败: {r.status_code}")
                return False
        except Exception as e:
            st.error(f"❌ 下载错误: {e}")
            return False
    return True

def generate_config():
    """
    根据 Secrets 生成 config.yml 文件
    因为 V1 版本必须通过配置文件启动
    """
    st.info("📝 正在生成配置文件...")
    
    # 处理 TLS 布尔值
    tls_bool = "true" if NEZHA_TLS.lower() in ["true", "1", "yes"] else "false"
    
    # 如果用户没提供 UUID，为了防止每次重启变 ID，我们可以生成一个存下来（但在 Streamlit 存不住）
    # 所以建议用户务必在 Secrets 提供 UUID
    final_uuid = NEZHA_UUID
    if not final_uuid:
        st.warning("⚠️ 你没有配置 NEZHA_UUID，每次重启面板上都会出现一个新的离线机器！")
    
    # 构造 YAML 内容
    # V1 版本的标准配置结构
    config_content = f"""
server: "{NEZHA_SERVER}"
client_secret: "{NEZHA_KEY}"
uuid: "{final_uuid}"
tls: {tls_bool}
debug: false
disable_auto_update: true
disable_command_execute: true
report_delay: 2
"""
    
    try:
        with open("config.yml", "w") as f:
            f.write(config_content)
        st.success("✅ 配置文件生成成功")
        return True
    except Exception as e:
        st.error(f"❌ 配置文件生成失败: {e}")
        return False

def run_agent():
    # 检查是否已经在运行
    try:
        res = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
        if "nezha-agent" in res.stdout:
            st.success("🟢 探针运行中 (Running)")
            return
    except:
        pass

    st.warning("🟡 正在启动探针...")
    
    # 使用 -c config.yml 启动
    cmd = ["./nezha-agent", "-c", "config.yml"]

    try:
        with open("agent.log", "w") as log_file:
            subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
        
        time.sleep(2)
        
        # 再次检查进程
        res = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
        if "nezha-agent" in res.stdout:
            st.success(f"🚀 启动成功！")
            st.caption(f"Server: {NEZHA_SERVER}")
        else:
            st.error("❌ 启动失败，请检查 agent.log")
            if os.path.exists("agent.log"):
                with open("agent.log", "r") as f:
                    st.code(f.read())
                    
    except Exception as e:
        st.error(f"启动异常: {e}")

# --- 3. 执行入口 ---
if not NEZHA_SERVER or not NEZHA_KEY:
    st.error("请先在 Secrets 配置 `NEZHA_SERVER` 和 `NEZHA_KEY`")
else:
    if install_agent():
        if generate_config():
            run_agent()

# --- 4. 调试 ---
with st.expander("查看生成的 config.yml (敏感信息)"):
    if os.path.exists("config.yml"):
        with open("config.yml", "r") as f:
            st.code(f.read())
