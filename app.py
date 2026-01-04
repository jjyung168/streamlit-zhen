import streamlit as st
import subprocess
import os
import requests
import zipfile
import io
import time

# --- 页面 UI ---
st.set_page_config(page_title="哪吒 V1 探针 (修正版)", page_icon="🛡️")
st.title("🛡️ 哪吒 V1 Agent (Fixed)")

# --- 1. 配置读取 (从 Secrets 获取) ---
# 面板地址 (例如: grpc.example.com:443)
NEZHA_SERVER = st.secrets.get("NEZHA_SERVER", "")

# 探针密钥 (通信认证用，对应面板里的 Secret) - 修正点：这才是 -p 参数
NEZHA_PASSWORD = st.secrets.get("NEZHA_PASSWORD", "")

# 探针 UUID (身份标识，对应面板里的 Server ID) - 修正点：这是 --uuid 参数
NEZHA_UUID = st.secrets.get("NEZHA_UUID", "")

# 是否开启 TLS (通常填 true)
NEZHA_TLS = st.secrets.get("NEZHA_TLS", "true")

# --- 2. 核心逻辑 ---
def get_agent_status():
    try:
        # 简单检查进程是否存在
        res = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
        if "nezha-agent" in res.stdout:
            return True
    except:
        return False
    return False

def install_agent():
    agent_bin = "nezha-agent"
    if not os.path.exists(agent_bin):
        st.info("⬇️ 正在下载哪吒 Agent...")
        try:
            # 下载最新版 Linux amd64
            url = "https://github.com/nezhahq/agent/releases/latest/download/nezha-agent_linux_amd64.zip"
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

def run_agent():
    if get_agent_status():
        st.success("🟢 探针运行中 (Running)")
        return

    st.warning("🟡 正在启动探针...")
    
    # --- 修正后的启动命令构建 ---
    # 基础命令: ./nezha-agent -s <server> -p <password>
    cmd = ["./nezha-agent", "-s", NEZHA_SERVER, "-p", NEZHA_PASSWORD]
    
    # 如果指定了 UUID，强行绑定 (固定身份，防止重启变新机)
    if NEZHA_UUID:
        cmd.extend(["--uuid", NEZHA_UUID])
    
    # TLS 处理
    if NEZHA_TLS.lower() in ["true", "1", "yes", "on"]:
        cmd.append("--tls")
    
    # 禁用自动更新 (Streamlit 环境没权限更新自身)
    cmd.append("--disable-auto-update")

    try:
        # 后台静默运行
        with open("agent.log", "w") as log_file:
            subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
        
        time.sleep(2)
        
        if get_agent_status():
            st.success(f"🚀 启动成功！")
            st.write(f"📡 Server: `{NEZHA_SERVER}`")
            # 隐藏显示一部分 UUID 以防截图泄露
            if NEZHA_UUID:
                st.write(f"🆔 UUID: `{NEZHA_UUID[:4]}...{NEZHA_UUID[-4:]}`")
        else:
            st.error("❌ 启动失败")
            # 读取日志帮助排错
            if os.path.exists("agent.log"):
                with open("agent.log", "r") as f:
                    st.code(f.read())
    except Exception as e:
        st.error(f"启动异常: {e}")

# --- 3. 执行入口 ---
if not NEZHA_SERVER or not NEZHA_PASSWORD:
    st.error("⚠️ 缺少配置！请在 Secrets 中配置 `NEZHA_SERVER` 和 `NEZHA_PASSWORD`")
else:
    if install_agent():
        run_agent()

# --- 4. 调试与保活 ---
st.divider()
st.caption("ℹ️ 这是修正版：分离了密钥(-p)和UUID(--uuid)。请使用监控工具保持此页面活跃。")
