import asyncio

import streamlit as st
from transformers import AutoTokenizer
import base64
import pandas as pd
import io
from fastapi import FastAPI
import stripe
from util import carregar_arquivos
import os
import glob
from forms.contact import cadastrar_cliente, agendar_reuniao

import replicate
from langchain.llms import Replicate

from key_config import API_KEY_STRIPE, URL_BASE
from decouple import config


app = FastAPI()



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


    if "image" not in st.session_state:
        st.session_state.image = None
    
    def ler_arquivos_txt(pasta):
        """
        Lê todos os arquivos .txt na pasta especificada e retorna uma lista com o conteúdo de cada arquivo.

        Args:
            pasta (str): O caminho da pasta onde os arquivos .txt estão localizados.

        Returns:
            list: Uma lista contendo o conteúdo de cada arquivo .txt.
        """
        conteudos = []  # Lista para armazenar o conteúdo dos arquivos

        # Cria o caminho para buscar arquivos .txt na pasta especificada
        caminho_arquivos = os.path.join(pasta, '*.txt')

        # Usa glob para encontrar todos os arquivos .txt na pasta
        arquivos_txt = glob.glob(caminho_arquivos)

        # Lê o conteúdo de cada arquivo .txt encontrado
        for arquivo in arquivos_txt:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()  # Lê o conteúdo do arquivo
                conteudos.append(conteudo)  # Adiciona o conteúdo à lista

        return conteudos  # Retorna a lista de conteúdos

    # Exemplo de uso da função
    pasta_conhecimento = './conhecimento'  # Caminho da pasta onde os arquivos .txt estão localizados
    conteudos_txt = ler_arquivos_txt(pasta_conhecimento)

    is_in_registration = False
    is_in_scheduling = False


    # Função para verificar se a pergunta está relacionada a cadastro
    def is_health_question(prompt):
        keywords = ["cadastrar", "inscrição", "quero me cadastrar", "gostaria de me registrar",
                    "desejo me cadastrar", "quero fazer o cadastro", "quero me registrar", "quero me increver",
                    "desejo me registrar", "desejo me inscrever","eu quero me cadastrar", "eu desejo me cadastrar",
                    "eu desejo me registrar", "eu desejo me inscrever", "eu quero me registrar", "eu desejo me registrar",
                    "eu quero me inscrever"]
        return any(keyword.lower() in prompt.lower() for keyword in keywords)

    #Função que analisa desejo de agendar uma reunião
    def is_schedule_meeting_question(prompt):
        keywords = [
            "agendar reunião", "quero agendar uma reunião", "gostaria de agendar uma reunião",
            "desejo agendar uma reunião", "quero marcar uma reunião", "gostaria de marcar uma reunião",
            "desejo marcar uma reunião", "posso agendar uma reunião", "posso marcar uma reunião",
            "Eu gostaria de agendar uma reuniao", "eu quero agendar", "eu quero agendar uma reunião,",
            "quero reunião"
        ]
        return any(keyword.lower() in prompt.lower() for keyword in keywords)

    system_prompt = f'''
    Você é uma atendente virtual chamada "KIRA", que atuará como atendente virtual da plataforma FAM, facilitando a 
    interação entre fabricantes de moda e lojistas no Brasil. 

    **Cadastro e Agendamento:**
       - Se o usuário estiver com o status de cadastro {is_in_registration} ou agendamento {is_in_scheduling}, 
       informe que não enviará mais informações até que finalize o cadastro. Use uma resposta padrão que diga: 
       "Aguardo a finalização do seu cadastro para continuar."

    **Opção de Cadastro e Agendamento:**
       - Se o usuário enviar {is_health_question} ou {is_schedule_meeting_question}, responda que está aguardando o preenchimento completo do formulário. 
       - Mantenha a mesma resposta enquanto ele não finalizar o cadastro.
       - Se o status do cadastro estiver {is_in_scheduling} ou {is_in_registration} mantenha a mesma resposta enquanto
       ele não finalizar o cadastro.
    
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
        st.session_state.messages = [{
            "role": "assistant", "content": '🌟 Bem-vindo ao Alan Coach! Estou aqui para te guiar na jornada de autodescoberta e transformação, rumo à sua melhor versão. Vamos juntos! 💪✨'}]

    # Dicionário de ícones
    icons = {
        "assistant": "./src/img/perfil-kira2.png",  # Ícone padrão do assistente
        "user": "./src/img/perfil-usuario.png"            # Ícone padrão do usuário
    }
    
    # Caminho para a imagem padrão
    default_avatar_path = "./src/img/usuario.jpg"
    
    # Exibição das mensagens
    for message in st.session_state.messages:
        if message["role"] == "user":
            # Verifica se a imagem do usuário existe
            avatar_image = st.session_state.image if "image" in st.session_state and st.session_state.image else default_avatar_path
        else:
            avatar_image = icons["assistant"]  # Ícone padrão do assistente
    
        with st.chat_message(message["role"], avatar=avatar_image):
            st.write(message["content"])

    def clear_chat_history():
        st.session_state.messages = [{"role": "assistant", "content": 'Olá! Sou a KIRA, sua assistente virtual de moda aqui na FAM. Vou te ajudar a conectar com os melhores fabricantes e tornar sua experiência de compra ainda mais incrível.'}]

    st.sidebar.button('LIMPAR CONVERSA', on_click=clear_chat_history)
   
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

        if is_health_question(prompt_str):
            cadastrar_cliente()


        if is_schedule_meeting_question(prompt_str):
            agendar_reuniao()

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

    
    def get_avatar_image():
        """Retorna a imagem do usuário ou a imagem padrão se não houver imagem cadastrada."""
        if st.session_state.image is not None:
            return st.session_state.image  # Retorna a imagem cadastrada
        else:
            return default_avatar_path  # Retorna a imagem padrão
    
    # User-provided prompt
    if prompt := st.chat_input(disabled=not replicate_api):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Chama a função para obter a imagem correta
        avatar_image = get_avatar_image()
        
        with st.chat_message("user", avatar=avatar_image):
            st.write(prompt)
    
    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant", avatar="./src/img/perfil-kira2.png"):
            response = generate_arctic_response()
            full_response = st.write_stream(response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)



