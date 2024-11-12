import streamlit as st
import os
from transformers import AutoTokenizer
import base64
from forms.contact import cadastro_pedido
import asyncio

import replicate
from langchain.llms import Replicate

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config


st.set_page_config(page_title='ORACULO MODAS', page_icon="👗", layout="wide")


# --- Verifica se o token da API está nos segredos ---
if 'REPLICATE_API_TOKEN':
    replicate_api = config('REPLICATE_API_TOKEN')
else:
    # Se a chave não está nos segredos, define um valor padrão ou continua sem o token
    replicate_api = None

# Essa parte será executada se você precisar do token em algum lugar do seu código
if replicate_api is None:
    # Se você quiser fazer algo específico quando não há token, você pode gerenciar isso aqui
    # Por exemplo, configurar uma lógica padrão ou deixar o aplicativo continuar sem mostrar nenhuma mensagem:
    st.warning('Um token de API é necessário para determinados recursos.', icon='⚠️')

# Inicializar o modelo da Replicate
llm = Replicate(
    model="meta/meta-llama-3-70b-instruct",
    api_token=replicate_api
)



async def showPedido():

    system_prompt = f'''
    Você é uma atendente virtual chamada "KIRA", que atuará como atendente virtual da plataforma FAM, facilitando a interação entre fabricantes de moda e lojistas no Brasil. 
    
    1. **Definição Clara**: Você deve ser uma assistente que não apenas responde perguntas, mas também oferece conselhos sobre como maximizar as vendas, sugere estratégias de marketing e conecta os fabricantes aos lojistas de forma eficaz. Isso ajudará a IA a entender melhor as expectativas dos usuários.
    
    2. **Estrutura da Resposta**: Ao interagir com os usuários, KIRA deve organizar suas respostas em partes lógicas. Por exemplo:
    - **Saudação**: "Olá! Sou a KIRA, sua assistente virtual."
    - **Identificação de Necessidades**: "Como posso ajudar você hoje? Está buscando conectar-se a um lojista ou precisa de dicas para aumentar suas vendas?"
    - **Solução**: Após a identificação, KIRA pode fornecer informações específicas ou direcionar o usuário para as funcionalidades da plataforma.
    
    3. **Tom de Comunicação**: O tom de seu deve ser amigável e acessível. Em conversas mais formais, ela pode usar uma linguagem técnica e objetiva, mas em interações cotidianas, ela deve adotar um tom mais descontraído e motivacional. Por exemplo: "Vamos juntos fazer seu negócio brilhar no mercado!".
    
    4. **Personalização e Precisão**:Você deve ser capaz de personalizar suas respostas com base nas informações fornecidas pelos usuários. Por exemplo, se o fabricante mencionar que está lançando uma nova linha de produtos, FAMOSA pode oferecer dicas específicas sobre como promovê-los para os lojistas, aumentando assim a relevância da interação.
    5. Se o cliente quiser fazer uma assinatura para ter acessoa plataforma envie este link: https://buy.stripe.com/test_fZeg2L7MBcCE9heeUY
    6. Se o cliente desejar conversar com uma consultora envie este link de WhatsApp da Consultora Mari: https://wa.me/+553199302907
    '''

    # Set assistant icon to Snowflake logo
    icons = {"assistant": "./src/img/perfil-kira1.png", "user": "./src/img/perfil-usuario.png"}

    # Replicate Credentials
    with st.sidebar:
        st.markdown(
            """
            <h1 style='text-align: center;'>KIRA - Assistente Virtual FAM</h1>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
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
        img_path = "./src/img/perfil-kira.jpeg"
        img_base64 = img_to_base64(img_path)
        st.sidebar.markdown(
            f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
            unsafe_allow_html=True,
        )
        st.sidebar.markdown("---")
        st.info("Agora que você está aqui, vamos aprender como interagir comigo, KIRA, sua assistente virtual de moda!"
    
                "Perguntando à KIRA"
                
                "Para perguntar algo, basta digitar sua pergunta no campo de texto abaixo." "Você pode perguntar sobre:"
                
                "Produtos e marcas disponíveis na plataforma"
                "Tendências e estilos de moda"
                "Dicas de compra e estilo"
                "Informações sobre os fornecedores e lojas parceiras"
                
                "Exemplos de Perguntas"
                
                "Quais são as últimas tendências de moda para o verão?"
                "Onde posso encontrar um vestido de noite para uma ocasião especial?"
                "Quais são as melhores marcas de calçados para homens?"
                
                "Interagindo com a KIRA"
                
                "Além de perguntar, você também pode interagir comigo de outras maneiras:"
                
                "Clique nos botões de opção para escolher entre diferentes respostas"
                "Use os ícones de emoção para expressar sua opinião ou humor"
                "Compartilhe suas preferências e interesses para que eu possa oferecer recomendações personalizadas"
                
                "Dicas e Lembranças"
                
                "Certifique-se de digitar sua pergunta de forma clara e concisa"
                "Se você não encontrar a resposta que procura, não hesite em perguntar novamente"
                "Lembre-se de que estou aqui para ajudá-lo, então não hesite em me perguntar qualquer coisa!"
                
                "Se você desejar finalizar uma compra aguarde para que eu mande o link de pagamento da compra."
                "Aqui está o link para efetuar seu pagamento: https://buy.stripe.com/test_fZeg2L7MBcCE9heeUY"
                "Se voce quiser conversar com uma de nossas consultoras entre em contato com a Mari clicando no link: https://wa.me/+553199302907 ")


        st.sidebar.markdown("---")


    # Store LLM-generated responses
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": 'Olá! Sou a KIRA, sua assistente virtual de moda aqui na FAM. Vou te ajudar a conectar com os melhores fabricantes e tornar sua experiência de compra ainda mais incrível.'}]

    # Display or clear chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=icons[message["role"]]):
            st.write(message["content"])

    def clear_chat_history():
        st.session_state.messages = [{"role": "assistant", "content": 'Olá! Sou a KIRA, sua assistente virtual de moda aqui na FAM. Vou te ajudar a conectar com os melhores fabricantes e tornar sua experiência de compra ainda mais incrível.'}]

    st.sidebar.button('LIMPAR CONVERSA', on_click=clear_chat_history)
    st.sidebar.caption(
        'Built by [Snowflake](https://snowflake.com/) to demonstrate [Snowflake Arctic](https://www.snowflake.com/blog/arctic-open-and-efficient-foundation-language-models-snowflake). App hosted on [Streamlit Community Cloud](https://streamlit.io/cloud). Model hosted by [Replicate](https://replicate.com/snowflake/snowflake-arctic-instruct).')
    st.sidebar.caption(
        'Build your own app powered by Arctic and [enter to win](https://arctic-streamlit-hackathon.devpost.com/) $10k in prizes.')

    st.sidebar.markdown("Desenvolvido por [WILLIAM EUSTÁQUIO](https://www.instagram.com/flashdigital.tech/)")

    @st.cache_resource(show_spinner=False)
    def get_tokenizer():
        """Get a tokenizer to make sure we're not sending too much text
        text to the Model. Eventually we will replace this with ArcticTokenizer
        """
        return AutoTokenizer.from_pretrained("huggyllama/llama-7b")

    def get_num_tokens(prompt):
        """Get the number of tokens in a given prompt"""
        tokenizer = get_tokenizer()
        tokens = tokenizer.tokenize(prompt)
        return len(tokens)

    # Function for generating Snowflake Arctic response

    def generate_arctic_response():
        prompt = []
        for dict_message in st.session_state.messages:

            if dict_message["role"] == "user":
                prompt.append("<|im_start|>user\n" + dict_message["content"] + "<|im_end|>")
            else:
                prompt.append("<|im_start|>assistant\n" + dict_message["content"] + "<|im_end|>")

        prompt.append("<|im_start|>assistant")
        prompt.append("")
        prompt_str = "\n".join(prompt)

        if get_num_tokens(prompt_str) >= 3500:  # padrão3072
            if cadastro_pedido in system_prompt:
                @st.dialog("DADOS PARA PEDIDO")
                def show_contact_form():
                    cadastro_pedido()

        for event in replicate.stream(
                "meta/meta-llama-3-70b-instruct",
                input={
                    "top_k": 0,
                    "top_p": 1,
                    "prompt": prompt_str,
                    "temperature": 0.1,
                    "system_prompt": system_prompt,
                    "length_penalty": 1,
                    "max_new_tokens": 3500,

                },
        ):
            yield str(event)

    # User-provided prompt
    if prompt := st.chat_input(disabled=not replicate_api):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="./src/img/perfil-usuario.png"):
            st.write(prompt)

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant", avatar="./src/img/perfil-kira1.png"):
            response = generate_arctic_response()
            full_response = st.write_stream(response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)



