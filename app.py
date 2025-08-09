import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="IslamiChat 🤖", layout="wide")
st.title("IslamiChat – Tanya Jawab")
st.caption("Powered by ArtiBot / Botsonic")

# Pilih widget mana yang mau ditampilkan
mode = st.radio("Pilih widget:", ["ArtiBot", "BotSonic"], horizontal=True)

container_css = """
<div style="display:flex;justify-content:center;width:100%;">
  <div style="width:90%;max-width:1200px;">
    {WIDGET}
  </div>
</div>
"""

if mode == "ArtiBot":
    widget = """
    <script type="text/javascript">
    !function(t,e){t.artibotApi={l:[],t:[],on:function(){this.l.push(arguments)},trigger:function(){this.t.push(arguments)}};
    var a=!1,i=e.createElement("script");i.async=!0,i.type="text/javascript",i.src="https://app.artibot.ai/loader.js",
    e.getElementsByTagName("head").item(0).appendChild(i),
    i.onreadystatechange=i.onload=function(){if(!(a||this.readyState&&"loaded"!=this.readyState&&"complete"!=this.readyState)){
      new window.ArtiBot({i:"5ace9d64-708e-48cb-86df-b8c605d17c1e"});a=!0}}}(window,document);
    </script>
    """
else:
    widget = """
    <iframe style="height:100vh;width:100vw" frameBorder="0" 
src="https://widget.botsonic.com/CDN/index.html?service-base-url=https%3A%2F%2Fapi-bot.writesonic.com&token=78d9eaba-80fc-4293-b290-fe72e1899607&base-origin=https%3A%2F%2Fbot.writesonic.com&instance-name=Botsonic&standalone=true&page-url=https%3A%2F%2Fislamichat.streamlit.app/%2Fbots%2Fa148b878-259e-4591-858a-8869b9b23604%2Fconnect">
</iframe>
    """

html(container_css.replace("{WIDGET}", widget), height=750)
