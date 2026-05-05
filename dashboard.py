"""
Streamlit Dashboard for Cross-Channel Reply Operator
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Cross-Channel Reply Operator",
    page_icon="📧",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #000;
    }
    @media (prefers-color-scheme: dark) {
        .main-header { color: #fff; }
    }
    .subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .message-container {
        margin: 1.5rem 0;
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
    }
    @media (prefers-color-scheme: dark) {
        .message-container { background-color: #2b2b2b; }
    }
    .incoming-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2196f3;
        margin-bottom: 0.5rem;
    }
    .outgoing-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #4caf50;
        margin-bottom: 0.5rem;
    }
    .message-text {
        background-color: white;
        padding: 1rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
        color: #000;
        border: 1px solid #dee2e6;
        white-space: pre-wrap;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    @media (prefers-color-scheme: dark) {
        .message-text {
            background-color: #1e1e1e;
            color: #fff;
            border: 1px solid #444;
        }
    }
    .context-info {
        background-color: #fff3cd;
        padding: 0.75rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
        color: #000;
        border: 1px solid #ffc107;
    }
    @media (prefers-color-scheme: dark) {
        .context-info {
            background-color: #3d3d00;
            color: #ffc107;
            border: 1px solid #ffc107;
        }
    }
    .risk-low { color: #28a745; font-weight: bold; }
    .risk-medium { color: #fd7e14; font-weight: bold; }
    .risk-high { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">Cross-Channel Reply Operator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Real-time AI communication with cross-platform intelligence</div>', unsafe_allow_html=True)

# Check server status
def check_server_status():
    try:
        import requests
        response = requests.get("http://localhost:8000/status", timeout=2)
        return response.json() if response.status_code == 200 else None
    except:
        return None

status = check_server_status()

# Status
if status:
    st.success(f"✓ Server Active - Processed {status.get('messages_processed', 0)} messages")
else:
    st.error("✗ Server Offline - Start with: `python unified_server.py`")

st.markdown("---")

# Controls
col1, col2, col3 = st.columns([2, 2, 6])

with col1:
    if st.button("🗑️ Clear Logs", use_container_width=True):
        log_file = Path("logs/run_logs.json")
        if log_file.exists():
            with open(log_file, 'w') as f:
                json.dump([], f)
            st.success("Logs cleared!")
            st.rerun()

with col2:
    num_messages = st.selectbox("Show:", [5, 10, 20, 50], index=0, label_visibility="collapsed")

st.markdown("---")

# Main content
st.subheader("Recent Messages")

log_file = Path("logs/run_logs.json")

if not log_file.exists():
    st.info("📭 Waiting for messages... Send an email or SMS to trigger processing.")
else:
    try:
        with open(log_file, 'r') as f:
            logs = json.load(f)
        
        if not logs:
            st.info("📭 No messages yet. Send an email or SMS to get started.")
        else:
            # Group by session
            sessions = []
            current_session = []
            
            for event in logs:
                current_session.append(event)
                if event['step'] == 'END':
                    sessions.append(current_session)
                    current_session = []
            
            # Display sessions
            for idx, session in enumerate(reversed(sessions[-num_messages:])):
                # Extract events
                normalized = next((e for e in session if e['step'] == 'NORMALIZED'), None)
                identity = next((e for e in session if e['step'] == 'IDENTITY_RESOLVED'), None)
                context = next((e for e in session if e['step'] == 'CONTEXT_AGGREGATED'), None)
                risk = next((e for e in session if e['step'] == 'RISK_ASSESSED'), None)
                reply = next((e for e in session if e['step'] == 'REPLY_GENERATED'), None)
                end = next((e for e in session if e['step'] == 'END'), None)
                
                if not (normalized and end):
                    continue
                
                # Extract data
                person = normalized['data'].get('person', 'Unknown')
                source = normalized['data'].get('source', 'unknown').upper()
                preview = normalized['data'].get('preview', '').strip()
                
                timestamp = datetime.fromisoformat(end['timestamp']).strftime('%I:%M:%S %p')
                
                risk_level = risk['data'].get('risk_level', 'UNKNOWN') if risk else 'UNKNOWN'
                risk_class = f"risk-{risk_level.lower()}"
                
                action = end['message'].split(' - ')[-1].replace('_', ' ').title() if ' - ' in end['message'] else 'Processed'
                
                sources = identity['data'].get('sources', [source.lower()]) if identity else [source.lower()]
                sources_str = ', '.join(sources)
                
                total_msgs = context['data'].get('total_messages', 1) if context else 1
                
                reply_text = reply['message'].split('Draft ready: ')[-1] if reply else 'No reply'
                
                # Expandable section for each message
                with st.expander(f"**{source}** from **{person}** at {timestamp}", expanded=(idx == 0)):
                    # Incoming message
                    st.markdown(f'<div class="incoming-header">📨 INCOMING {source}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="message-text">{preview if preview else "No content"}</div>', unsafe_allow_html=True)
                    
                    # Context info
                    st.markdown(f"""
                    <div class="context-info">
                        <strong>Context:</strong> Found {total_msgs} message(s) from: {sources_str}<br>
                        <strong>Risk Level:</strong> <span class="{risk_class}">{risk_level}</span><br>
                        <strong>Action:</strong> {action}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Reply
                    st.markdown(f'<div class="outgoing-header">✉️ REPLY {action.upper()}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="message-text">{reply_text}</div>', unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading logs: {e}")

# Footer
st.markdown("---")
col_footer1, col_footer2 = st.columns([3, 1])

with col_footer1:
    st.caption("Dashboard updates automatically")

with col_footer2:
    if st.button("🔄 Refresh"):
        st.rerun()

# Auto-refresh using st.rerun with timer
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

current_time = datetime.now()
if (current_time - st.session_state.last_refresh).total_seconds() > 3:
    st.session_state.last_refresh = current_time
    st.rerun()