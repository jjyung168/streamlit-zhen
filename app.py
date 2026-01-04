import streamlit as st
import subprocess
import os
import requests
import zipfile
import io
import time
import psutil  # 引入新库

# --- 页面 UI ---
st.set_page_config(page_title="哪吒探针", page_icon="⚡")
st.title("⚡ 哪吒 Agent V1 (Python Native)")

# --- 1. 读取 Secrets ---
NEZHA_SERVER = st.secrets.get("NEZHA_SERVER", "")
NEZHA_KEY = st.secrets.get("NEZHA_KEY", "")
NEZHA_UUID = st.secrets.get("NEZHA_UUID", "")
NEZHA_TLS = st.secrets.get("NEZHA_TLS", "false")

# --- 2. 核心功能 ---
def install_agent():
    if not os.path.exists("nezha-agent"):
        st.info("⬇️ 正在下载哪吒 Agent...")
        try:
            url = "https://github.com/nezhahq/agent/releases/download/v1.14.3/nezha-agent_linux_amd64.zip"
            r = requests.get(url, timeout=30)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                z.extractall(".")
            subprocess.run(["chmod", "+x", "nezha-agent"])
            st.success("✅ 下载完成")
        except Exception as e:
            st.error(f"❌ 下载失败: {e}")
            return False
    return True

def generate_config():
    st.info("📝 生成配置文件...")
    tls_val = "true" if str(NEZHA_TLS).lower() in ["true", "1", "yes", "on"] else "false"
    
    config_content = f"""
server: "{NEZHA_SERVER}"
client_secret: "{NEZHA_KEY}"
uuid: "{NEZHA_UUID}"
tls: {tls_val}
debug: false
disable_auto_update: true
disable_command_execute: true
report_delay: 2
"""
    try:
        with open("config.yml", "w") as f:
            f.write(config_content)
        st.success(f"✅ Config生成完毕")
        return True
    except Exception as e:
        st.error(f"❌ Config生成失败: {e}")
        return False

def check_process_running():
    """
    使用 psutil 检查进程，不再依赖系统 ps 命令
    """
    try:
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                # 检查进程名是否包含 nezha-agent
                if 'nezha-agent' in proc.info['name']:
                    return True
                # 或者检查命令行参数
                if proc.info['cmdline'] and './nezha-agent' in proc.info['cmdline']:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception:
        pass
    return False

def run_agent():
    # 使用新函数检查进程
    if check_process_running():
        st.success("🟢 探针运行中...")
        return

    st.warning("🟡 正在启动...")
    
    cmd = ["./nezha-agent", "-c", "config.yml"]

    try:
        with open("agent.log", "w") as log_file:
            subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)
        
        time.sleep(2)
        
        # 再次检查
        if check_process_running():
            st.success("🚀 启动成功！已连接面板。")
        else:
            st.error("❌ 启动失败，日志如下：")
            if os.path.exists("agent.log"):
                with open("agent.log", "r") as f:
                    st.code(f.read())
    except Exception as e:
        st.error(f"执行异常: {e}")

# --- 入口 ---
if not NEZHA_SERVER or not NEZHA_KEY:
    st.error("⚠️ 请先在 Secrets 配置 NEZHA_SERVER 和 NEZHA_KEY")
else:
    if install_agent():
        if generate_config():
            run_agent()

if st.button("刷新状态"):
    st.rerun()
