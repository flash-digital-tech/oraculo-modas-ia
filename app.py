import asyncio

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator import Authenticate
import base64
from streamlit_option_menu import option_menu
import time


from pgs.home import showHome
from pgs.cliente_criar import showCliente
from pgs.dashboard import showDashboard
from pgs.financeiro import showFinanceiro
from pgs.pedido import showPedido
from pgs.link_pagamento import showLinks
from pgs.subcontas_criar import showParceiro
from pgs.webhooks import shoWebhooks


# --- LOAD CONFIGURATION ---
with open("config.yaml") as file:
    config = yaml.safe_load(file)

# --- AUTHENTICATION SETUP ---
credentials = {
    'usernames': {user['username']: {
        'name': user['name'],
        'password': user['password'],
        'email': user['email'],
    } for user in config['credentials']['users']}
}

authenticator = Authenticate(
    credentials=credentials,
    cookie_name=config['cookie']['name'],
    key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days']
)

# --- PAGE SETUP ---
authenticator.login(key='login_form')


class MultiPage:
    def __init__(self):  # Corrigido de __int__ para __init__
        self.pages = []

    def add_page(self, title, func):
        self.pages.append({
            "title": title,
            "function": func
        })

    def run(self):
        with st.sidebar:
           pag = option_menu(
                menu_title="MENU",
                options=['Início', 'Fazer Pedido', 'Criar Cliente', 'Dashboard', 'Financeiro', 'Link de Pagamento',
                         'Parceiro', 'Webhook'],
                icons=['house-fill', 'cart-fill', 'person-fill', 'cash-stack', 'link', 'people-fill', 'code-slash', 'grid'],
                menu_icon='list',
                default_index=0,  # Ajustado para o índice correto
                styles={
                    "container": {"padding": "5!important","background-color":'black'},
        "icon": {"color": "white", "font-size": "15px"},
        "nav-link": {"color":"white","font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "blue"},
        "nav-link-selected": {"background-color": "#02ab21"},}
            )

        for page in self.pages:
            if page["title"] == pag:
                page["function"]()  # Chame a função da página selecionada

                if pag == "Início":
                    asyncio.run(showHome())

                elif pag == "Fazer Pedido":
                    asyncio.run(showPedido())

                elif pag == "Criar Cliente":
                     asyncio.run(showCliente())

                elif pag == "Dashboard":
                    asyncio.run(showDashboard())

                elif pag == "Financeiro":
                    asyncio.run(showFinanceiro())

                elif pag == "Link de Pagamento":
                    asyncio.run(showLinks())

                elif pag == "Parceiro":
                    asyncio.run(showParceiro())

                elif pag == "Webhook":
                    asyncio.run(shoWebhooks())

if 'authentication_status' in st.session_state and st.session_state['authentication_status']:
    user_email = next(user['email'] for user in config['credentials']['users'] if user['username'] == st.session_state['username'])
    authenticator.logout('SAIR', 'sidebar')
    if user_email:
        with st.spinner('Saindo...'):
            time.sleep(0.2)  # Simula uma operação demorada

    st.sidebar.markdown(
    f"<h1 style='color: #FFFFFF; font-size: 24px;'>🎉 Seja bem-vindo(a), <span style='font-weight: bold;'>{st.session_state['name']}</span>!!! 🎉</h1>",unsafe_allow_html=True
    )

    st.sidebar.markdown(
        """
        <h1 style='text-align: center;'>ORÁCULO MODAS</h1>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #330000,
                0 0 10px #660000,
                0 0 15px #990000,
                0 0 20px #CC0000,
                0 0 25px #FF0000,
                0 0 30px #FF3333,
                0 0 35px #FF6666;
            position: relative;
            z-index: -1;
            border-radius: 30px;  /* Rounded corners */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Function to convert image to base64
    def img_to_base64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    # Load and display sidebar image with glowing effect
    img_path = "./src/img/kira.png"
    img_base64 = img_to_base64(img_path)
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    if 'username' in st.session_state:
        user_role = next((user['role'] for user in config['credentials']['users'] if user['username'] == st.session_state['username']), None)
        if user_role:
            with st.spinner('Acessando...'):
                time.sleep(0.1)  # Simula uma operação demorada

        if user_role is None:
            with st.spinner('Saindo...'):
                time.sleep(2)  # Simula uma operação demorada

    else:
        st.error("Usuário não está autenticado.")
        st.stop()

    # Defina as permissões de acesso
    permissoes = {
        "admin": [
            "pgs/home.py",
            "pgs/pedido.py",
            "pgs/cliente_criar.py",
            "pgs/financeiro.py",
            "pgs/link_pagamento.py",
            "pgs/subcontas_criar.py",
            "pgs/webhooks.py",
            "pgs/dashboard.py"
        ],
        "parceiro": [
            "pgs/home.py",
            "pgs/pedido.py",
            "pgs/cliente_criar.py",
        ],
        "cliente": [
            "pgs/home.py",
            "pgs/pedido.py",
        ],
    }

    if user_role in permissoes:
        multi_page = MultiPage()

        # Crie um menu de páginas com base nas permissões do usuário
        menu_options = []
        for pagina in permissoes[user_role]:
            if pagina == "pgs/home.py":
                menu_options.append({"title": "Início", "function": showHome})
            elif pagina == "pgs/pedido.py":
                menu_options.append({"title": "Fazer Pedido", "function": showPedido})
            elif pagina == "pgs/cliente_criar.py":
                menu_options.append({"title": "Criar Cliente", "function": showCliente})
            elif pagina == "pgs/dashboard.py":
                menu_options.append({"title": "Dashboard", "function": showDashboard})
            elif pagina == "pgs/financeiro.py":
                menu_options.append({"title": "Financeiro", "function": showFinanceiro})
            elif pagina == "pgs/link_pagamento.py":
                menu_options.append({"title": "Link de Pagamento", "function": showLinks})
            elif pagina == "pgs/subcontas_criar.py":
                menu_options.append({"title": "Parceiro", "function": showParceiro})
            elif pagina == "pgs/webhooks.py":
                menu_options.append({"title": "Webhook", "function": shoWebhooks})

        # Adicione o menu ao MultiPage
        for option in menu_options:
            multi_page.add_page(option["title"], option["function"])

        multi_page.run()  # Executa a aplicação com as páginas permitidas
    else:
        st.error("Você não tem permissão para acessar esta aplicação.")
