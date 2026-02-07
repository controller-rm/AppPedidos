import streamlit as st
import pandas as pd
import requests
import re
from io import StringIO, BytesIO
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF  # Adicione esta linha para gerar PDFs (instale com pip install fpdf)

st.set_page_config(page_title="Sistema de Pedidos", layout="wide")
st.title("🛒 Emissão de Pedido - Zionne")


# ==============================
# NOVO PEDIDO (RESET REAL)
# ==============================
if st.button("🆕 Novo Pedido", type="primary", use_container_width=True):

    rc = st.session_state.get("reset_counter", 0) + 1  # guarda próximo número
    st.session_state.clear()  # limpa tudo
    st.session_state.reset_counter = rc  # restaura contador
    st.rerun()


# =====================================================
# ESTADOS
# =====================================================
if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

if "dados_cliente" not in st.session_state:
    st.session_state.dados_cliente = None
# Adicione:
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0
# =====================================================
# FUNÇÃO CONSULTA CNPJ
# =====================================================
def consulta_cnpj(cnpj):
    cnpj = re.sub(r"\D", "", cnpj)
    if len(cnpj) != 14:
        return None, "CNPJ inválido"

    try:
        response = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=10)
        if response.status_code != 200:
            return None, "CNPJ não encontrado"

        d = response.json()
        return {
            "razao": d.get("razao_social", ""),
            "logradouro": d.get("logradouro", ""),
            "numero": d.get("numero", ""),
            "bairro": d.get("bairro", ""),
            "municipio": d.get("municipio", ""),
            "uf": d.get("uf", ""),
            "cep": d.get("cep", "")
        }, None
    except:
        return None, "Erro na consulta do CNPJ"

 # =====================================================
# PRODUTOS - BASE COMPLETA
# =====================================================
dados_produtos = """
0000001	;	 BULE COM INFUSOR - HORTICOOL GREEN 500ML 	;	308,9
0000002	;	 BULE COM INFUSOR - HORTICOOL GREEN 1000M 	;	401,58
0000003	;	 ACUCAREIRO HORTICOOL GREEN 150ML       	;	142,94
0000004	;	 LEITEIRA HORTICOOL GREEN 150ML         	;	118,09
0000005	;	 BULE COM INFUSOR E XICARA HOORTICOL GREE 	;	358,33
0000006	;	 XICARA DE CHA E PIRES APPLE BLOSSOM HORT 	;	149,16
0000007	;	 XICARA DE CHA E PIRES FLOR GEOMETRIA VER 	;	149,16
0000008	;	 CAFE E PIRES HORTICOOL GREEN 100ML     	;	105,65
0000009	;	 PRATO DE PAO LIMA HORTICOOL GREEN 16,5CM 	;	93,21
0000010	;	 PRATO DE PAO PINK HORTICOOL GREEN 16.5CM 	;	93,21
0000011	;	 PRATO DE SOBREMESA FLOR HORTICOOL GREEN  	;	118,09
0000012	;	 PRATO DE SOBREMESA GEOMETRIA GREEN HORTI 	;	118,09
0000013	;	 PRATO DE JANTAR FLOR DE MACA HORTICOOL G 	;	149,16
0000014	;	 PRATO DE JANTAR GEOMETRIA HORTICOOL GREE 	;	149,16
0000015	;	 PRATO FUNDO FLOR DE MACA HORTICOOL GREEN 	;	130,5
0000016	;	 PRATO FUNDO GEOMETRIA HORTICOOL GREEN 22 	;	130,5
0000017	;	 TRAVESSA OBLONGA HORTICOOL GREEN 30CM 29 	;	149,16
0000018	;	 TRAVESSA OBLONGA HORTICOOL GREEN 35CM 34 	;	217,53
0000019	;	 BOWL HORTICOOL GREEN 17CM 700ML        	;	124,28
0000020	;	 BOWL FLOR DE MACA HORTICOOL GREEN 17CM 7 	;	124,28
0000021	;	 SOPEIRA GREEN HORTICOOL 2.4L 2400ML     	;	864,93
0000022	;	 CONJUNTO/2 CANECAS HORTICOOL 300ML 	    ;	155,36
0000023	;	 PRATO DE DOCES 2 CAMADAS HORTICOOL GREEN 	;	236,16
0000024	;	 PRATO DE DOCE 3 CAMADAS HORTICOOL GREEN 	;	403,96
0000025	;	 TRAVESSA OVAL HORTICOOL GREEN 31CM 30.9x 	;	186,46
0000026	;	 TIGELA FLOR DE MACA HORTICOOL GREEN 22CM 	;	279,67
0000027	;	 TIGELA FLOR DE MACA HORTICOOL GREEN 12CM 	;	80,8
0000028	;	 CESTA DE PIQUENIQUE HORTICOOL GREEN 38x2 	;	441,07
0000029	;	 TRILHO DE MESA HORTICOOL                   ;	286,99
0000030	;	 BULE COM INFUSOR - HORTICOOL PINK 500ML  	;	308,9
0000031	;	 BULE COM INFUSOR - HORTICOOL PINK 1000ML 	;	401,58
0000032	;	 ACUCAREIRO HORTICOOL PINK 150ML  	        ;	142,94
0000033	;	 LEITEIRA HORTICOOL PINK 150ML 	            ;	118,09
0000034	;	 BULE COM INFUSOR E XICARA HORTICOOL PINK 	;	358,33
0000035	;	 XICARA DE CHA E PIRES APPLE BLOSSOM HORT 	;	149,16
0000036	;	 XICARA DE CHA E PIRES GEOMETRICA BLOSSOM 	;	149,16
0000037	;	 CAFE E PIRES HORTICOOL PINK 100ML  	    ;	105,65
0000038	;	 PRATO DE PAO LIME HORTICOOL PINK 16,5CM  	;	93,21
0000039	;	 PRATO DE SOBREMESA FLOR BLOSSOM PINK 20, 	;	118,09
0000040	;	 PRATO DE SOBREMESA GEOMETRIA HORTICOOL P 	;	118,09
0000041	;	 PRATO DE JANTAR FLOR DE MACA HORTICOOL P 	;	149,16
0000042	;	 PRATO FUNDO FLOR DE MACA HORTICOOL PINK  	;	129,73
0000043	;	 TRAVESSA OBLONGA HORTICOOL PINK 30CM 29. 	;	148,28
0000044	;	 TRAVESSA OBLONGA HORTICOOL PINK 35CM 34. 	;	216,21
0000045	;	 BOWL HORTICOOL PINK 17CM 700ML  	        ;	123,56
0000046	;	 SOPEIRA HORTICOOL PINK 2.4L 2400ML 	    ;	864,93
0000047	;	 PRATO DE DOCES 2 CAMADAS HORTICOOL PINK  	;	234,77
0000048	;	 TRAVESSA OVAL HORTICOOL PINK 31CM 30.9x1 	;	185,33
0000049	;	 TIGELA FLOR DE MACA HORTICOOL PINK 12CM  	;	80,32
0000050	;	 BOWL FLOR DE MACA HORTICOOL PINK 22CM 21 	;	278,01
0000051	;	 BULE COM INFUSOR - REGENCY DAMASK 500ML  	;	370,67
0000052	;	 BULE COM INFUSOR RENGENCY DAMASKY 1000ML 	;	463,35
0000053	;	 BULE COM INFUSOR E XICARA REGENCY DAMASK 	;	401,58
0000054	;	 PRATOS DE PAO REGENCY DAMASKY 17CM 17.1x 	;	111,2
0000055	;	 PRATO DE PAO REGENCY DAMASKY 17CM 17.1x1 	;	111,2
0000056	;	 PRATO DE PAO REGENCY DAMASKY 17CM 17.1x1 	;	111,2
0000057	;	 PRATO DE PAO REGENCY DAMASKY 17CM 17.1x1 	;	111,2
0000058	;	 PRATO DE SOBREMESA REGENCY DAMASKY 21CM  	;	135,92
0000059	;	 PRATO DE SOBREMESA REGENCY DAMASKY 21CM  	;	135,92
0000060	;	 PRATO DE JANTAR REGENCY DAMASK 26CM 26.3 	;	172,97
0000061	;	 PRATO DE JANTAR REGENCY DAMASK 26CM 26.3 	;	172,97
0000062	;	 PRATO FUNDO REGENCY DAMASKY 21CM 21.7x21 	;	154,45
0000063	;	 PRATO FUNDO REGENCY DAMASKY 21CM 21.7x21 	;	154,45
0000064	;	 XICARA DE CHA E PIRES PINK REGENCY DAMAS 	;	172,97
0000065	;	 XICARA DE CHA E PIRES BLUE REGENCY DAMAS 	;	172,97
0000066	;	 CAFE E PIRES FLOR PINK REGENCY DAMASKY 1 	;	123,56
0000067	;	 CAFE E PIRES BLUE REGENCY DAMASKY 100ML  	;	123,56
0000068	;	 CANECA REGENCY DAMASK FLOR PINK 350ML 	    ;	117,37
0000069	;	 CANECA REGENCY DAMASK FLOR BLUE 350ML 	    ;	117,37
0000070	;	 CANECA REGENCY DAMASK PINK 350ML   	    ;	117,37
0000071	;	 CANECA REGENCY DAMASK BLUE 350ML   	    ;	117,37
0000072	;	 BOWL REGENCY DAMASK PINK 15CM 15x15x7.3C 	;	142,09
0000073	;	 BOWL REGENCY DAMASK BLUE 15CM 15x15x7.3C 	;	142,09
0000074	;	 VASO REGENCY DAMASKY 22,8CM 22.8x22.8x22 	;	1.112,03
0000075	;	 TRAVESSA HEXAGONAL REGENCY DAMASKY AZUL  	;	240,93
0000076	;	 TRAVESSA HEXAGONAL REGENCY DAMASKY PINK  	;	240,93
0000077	;	 TRAVESSA HEXAGONAL REGENCY DAMASKY PINK  	;	148,28
0000078	;	 TRAVESSA HEXAGONAL REGENCY DAMASKY AZUL  	;	148,28
0000079	;	 ACUCAREIRO REGENCY DAMASKY 250ML   	    ;	172,97
0000080	;	 LEITEIRA REGENCY DAMASKY 200ML  	        ;	142,09
0000081	;	 POTE REGENCY DAMASKY PINK 14.7x14.7x16.6 	;	370,67
0000082	;	 POTE REGENCY DAMASKY BLUE 14.7x14.7x16.6 	;	370,67
0000083	;	 CONJUNTO/2 CANECAS (SEM ALCA) REGENCY DA 	;	172,97
0000084	;	 PRATO DE DOCE 3 CAMADAS REGENCY DAMASKY  	;	463,35
0000085	;	 PRATO DE DOCES 2 CAMADAS REGENCY DAMASKY 	;	265,65
0000086	;	 BOWL REGENCY DAMASKY 22CM 22.3x22.3x9.5C 	;	401,58
0000087	;	 BOWL REGENCY DAMASKY 12CM 12x12x5.4CM 22 	;	111,2
0000088	;	 BOWL REGENCY DAMASKY 12CM 12x12x5.4CM 22 	;	111,2
0000089	;	 BOWL REGENCY DAMASKY PINK QUADRADO 12CM  	;	111,2
0000090	;	 BOWL REGENCY DAMASKY BLUE QUADRADO 12CM  	;	111,2
0000091	;	 CONJUNTO AROMA CRISTAL BLUE RIBBON 10x10 	;	370,67
0000092	;	 CONJUNTO AROMA CRISTAL BLUE RIBBON 10x10 	;	370,67
0000093	;	 CONJUNTO DIFUSOR BLUE RIBBON PINK 9.5x9. 	;	370,67
0000094	;	 CONJUNTO DIFUSOR BLUE RIBBON 9.5x9.5x9.8 	;	370,67
0000095	;	 PRATO PAO BLUE RIBBON OVAL CONJUNTO/2 17 	;	154,45
0000096	;	 PRATO SOBREMESA BLUE RIBBON OVAL CONJUNT 	;	222,41
0000097	;	 PRATO DE JANTAR BLUE RIBBON OVAL CONJUNT 	;	284,18
0000098	;	 TRAVESSA OVAL COM ALCA BLUE RIBBON 32CM  	;	296,54
0000099	;	 TRAVESSA OVAL BLUE RIBBON 31CM 30.8x17.5 	;	166,8
0000100	;	 PRATO FUNDO BLUE RIBBON 20CM 20.6x20.6x4 	;	123,56
0000101	;	 BOWL DE FRUTA BLUE RIBBON 450ML  	        ;	142,09
0000102	;	 BULE COM INFUSOR - BLUE RIBBON 1000ML 	    ;	370,67
0000103	;	 ACUCAREIRO BLUE RIBBON 260ML  	            ;	148,28
0000104	;	 LEITEIRA BLUE RIBBON 220ML 	            ;	123,56
0000105	;	 XICARA DE CHA CONJUNTO/2 BLUE RIBBON ROS 	;	259,49
0000106	;	 XICARA DE CHA CONJUNTO/2 BLUE RIBBON QUE 	;	259,49
0000107	;	  BOWL CONJUNTO/4 BLUE RIBBON 270ml 	    ;	259,49
0000108	;	 BOWL BLUE RIBBON 560ML  	                ;	111,2
0000109	;	 TIGELA BLUE RIBBON 22 cm 21.8x21.8x9.5cm 	;	247,13
0000110	;	 CONJUNTO/4 PRATO MINI 11x11x2.7cm  	    ;	166,8
0000111	;	 VASO BLUE RIBBON 22CM 21.8x21.8x9.5cm 	    ;	1.050,26
0000112	;	 PRATO DE JANTAR BARROCO FLORESCENTE BLOO 	;	191,09
0000113	;	 PRATO DE JANTAR BARROCO FLORESCENTE BLOO 	;	191,09
0000114	;	 PRATO DE JANTAR BARROCO FLORESCENTE BLOO 	;	191,09
0000115	;	 PRATO DE PAO BARROCO FLORESCENDO BLOOMIN 	;	139,27
0000116	;	 PRATO DE PAO BARROCO FLORESCENDO BLOOMIN 	;	139,27
0000117	;	 PRATO DE PAO BARROCO FLORESCENDO  BLOOMI 	;	139,27
0000118	;	 PRATO DE PAO BARROCO FLORESCENTE BLOOMIN 	;	108,91
0000119	;	 PRATO DE PAO BARROCO FLORESCENTE BLOOMIN 	;	108,91
0000120	;	 PRATO DE PAO BARROCO FLORESCENTE BLOOMIN 	;	108,91
0000121	;	 PRATO FUNDO BARROCO FLORESCENTE BLOOMING 	;	159,01
0000122	;	 PRATO FUNDO BARROCO FLORESCENTE BLOOMING 	;	159,01
0000123	;	 PRATO FUNDO BARROCO FLORESCENTE BLOOMING 	;	159,01
0000124	;	 TRAVESSA RETANGULAR BLOOMING BAROQUE 35C 	;	233,63
0000125	;	 TIGELA FLORESCENTE BARROCO BLOOMING BARO 	;	394,67
0000126	;	 TIGELA BARROCO FLORESCENTE  BLOOMING BAR 	;	149,29
0000127	;	 TIGELA BARROCO FLORESCENTE BLOOMING BARO 	;	149,29
0000128	;	 TIGELA BARROCO FLORESCENTE BLOOMING BARO 	;	149,29
0000129	;	 BOWL FLORESCENDO BARROCO BLOOMING BAROQU 	;	106,78
0000130	;	 BOWL FLORESCENDO BARROCO BLOOMING BAROQU 	;	106,78
0000131	;	 CANECA GEOMETRICA HORTICOOL GREEN 300ML  	;	98,84
0000132	;	 CANECA HORTICOOL GREEN 300ML  	            ;	98,84
0000133	;	 BULE COM INFUSOR - HORTICOOL BLUE 500ML  	;	308,9
0000134	;	 BULE COM INFUSOR - HORTICOOL BLUE 1000ML 	;	401,58
0000135	;	 ACUCAREIRO HORTICOOL BLUE 150ML  	        ;	142,09
0000136	;	 LEITEIRA HORTICOOL BLUE 150ML 	            ;	117,37
0000137	;	 BULE COM INFUSOR E XICARA HOORTICOL BLUE 	;	358,33
0000138	;	 XICARA DE CHA E PIRES APPLE BLOSSOM HORT 	;	148,28
0000139	;	 XICARA DE CHA E PIRES GEOMETRIA HORTICOO 	;	148,28
0000140	;	 CANECA GEOMETRIA HORTICOOL BLUE 300ML 	    ;	98,84
0000141	;	 CANECA HORTICOOL BLUE 300ML                ;	98,84
0000142	;	 PRATO DE PAO HORTICOOL BLUE 16,5CM 16.7x 	;	92,68
0000143	;	 PRATO DE SOBREMESA FLOR HORTICOOL BLUE 2 	;	117,37
0000144	;	 PRATO HORTICOOL BLUE 20,0CM                ;	117,37
0000145	;	 PRATO DE JANTAR FLOR HORTICOOL BLUE 26CM 	;	148,28
0000146	;	 PRATO DE FUNDO GEOMETRIA HORTICOOL BLUE  	;	129,73
0000147	;	 TRAVESSA OBLONGA HORTICOOL BLUE 30CM 29. 	;	148,28
0000148	;	 TRAVESSA OBLONGA HORTICOOL BLUE 35CM 34. 	;	216,21
0000149	;	 TRAVESSA OVAL HORTICOOL BLUE 31CM 30.9x1 	;	185,33
0000150	;	 CONJUNTO/4 HORTICOOL BLUE PRATO MINI 11x 	;	185,33
0000151	;	 BOWL HORTICOOL BLUE 12CM 220ML  	        ;	80,32
0000152	;	 BOWL COM TAMPA FLORAL HORTICOOL GREEN 12 	;	110,24
0000153	;	 BOWL COM TAMPA FLORAL GEOMETRIA HORTICOO 	;	110,24
0000154	;	 BOWL COM TAMPA FLORAL HORTICOOL GREEN 17 	;	168,76
0000155	;	 CONSOME COM TAMPA FLORAL HORTICOOL GREEN 	;	175,25
0000156	;	 CANECA COM ALCA GEOMETRICA HORTICOOL GRE 	;	98,84
0000157	;	 CANECA COM ALCA FLORAL HORTICOOL GREEN 3 	;	98,84
0000158	;	 TRAVESSA RETANGULAR BLUE TAPESTRY 33CM	    ;	324,82
0000159	;	 XICARA DE CHA WHITE TAPESTRY 250ML 	    ;	292,3
0000160	;	 XICARA DE CHA RED-PEONY TAPESTRY 250ML	    ;	292,3
0000161	;	 XICARA DE CHA BLUE DAHLIA TAPESTRY 360ML 	;	292,3
0000162	;	 CANECA COM ALCA LILAK TAPESTRY 36OML  	    ;	227,29
0000163	;	 CANECA ALCA OFF WHITE PEONY TAPESTRY 360 	;	227,29
0000164	;	 CANECA ALCA LEMON DAHLIA TAPESTRY 360ML  	;	227,29
0000165	;	 BOWL CONJUNTO/2 TAPESTRY 12CM 	            ;	194,77
0000166	;	 BOWL CONJUNTO/2 PEOANY TAPESTRY 12CM  	    ;	227,29
0000167	;	 PRATO CONJUNTO/3 PEOANY TAPESTRY   	    ;	584,95
0000168	;	 PRATO CONJUNTO/3 DAHLIA TAPESTRY   	    ;	422,38
0000169	;	 XICARA DE CAFE E PIRES HORTICOOL BLUE 10 	;	105,01

"""

df_produtos = pd.read_csv(
    pd.io.common.StringIO(dados_produtos),
    sep=";",
    names=["codigo", "descricao", "preco"],
    dtype=str  # 🔥 FORÇA TEXTO
)

# Converter preço BR → float
df_produtos["preco"] = (
    df_produtos["preco"]
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
    .astype(float)
)

# Garantia extra (evita esse erro NUNCA MAIS)
df_produtos["codigo"] = df_produtos["codigo"].astype(str)
df_produtos["descricao"] = df_produtos["descricao"].astype(str)


# =====================================================
# DADOS CLIENTE
# =====================================================
client_card = st.container(border=True)
with client_card:
    st.markdown("### 🏢 Dados do Cliente")

    rc = st.session_state.reset_counter
    col_cnpj, col_btn = st.columns([3, 1])
    with col_cnpj:
        cnpj = st.text_input("CNPJ *", placeholder="00.000.000/0000-00", key=f"cnpj_{rc}")
    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        consultar = st.button("Consultar CNPJ", type="primary", use_container_width=True)

    telefone = st.text_input("📞 WhatsApp *", placeholder="(00) 00000-0000", key=f"tel_{rc}")
    email = st.text_input("✉️ E-mail *", placeholder="email@exemplo.com", key=f"email_{rc}")
    ie = st.text_input("🧾 Inscrição Estadual *", placeholder="000.000.000.000", key=f"ie_{rc}")
    telefone_zionne = st.text_input("📞 Telefone WhatsApp Zionne", placeholder="(00) 00000-0000", key=f"tel_zionne_{rc}")

    # Consulta CNPJ
    if consultar:
        dados, erro = consulta_cnpj(cnpj)
        if erro:
            st.error(erro)
            st.warning("CNPJ não encontrado. Insira os dados manualmente abaixo.")
            st.session_state.dados_cliente = None
        else:
            st.session_state.dados_cliente = dados
            st.success("Cliente localizado!")

# 🔥 NOVO: Campos para entrada manual (sempre visíveis, mas preenchidos se consulta funcionar)
if st.button("Inserir Dados Manualmente", type="secondary", use_container_width=True) or st.session_state.dados_cliente is None:
    st.subheader("📝 Inserir Dados do Cliente Manualmente")
    
    razao_manual = st.text_input("🏢 Razão Social", placeholder="Razão Social", value=st.session_state.dados_cliente.get("razao", "") if st.session_state.dados_cliente else "", key=f"razao_manual_{rc}")
    logradouro_manual = st.text_input("📍 Logradouro", placeholder="Rua, Avenida...", value=st.session_state.dados_cliente.get("logradouro", "") if st.session_state.dados_cliente else "", key=f"logradouro_manual_{rc}")
    numero_manual = st.text_input("🔢 Número", placeholder="Número", value=st.session_state.dados_cliente.get("numero", "") if st.session_state.dados_cliente else "", key=f"numero_manual_{rc}")
    bairro_manual = st.text_input("🏘️ Bairro", placeholder="Bairro", value=st.session_state.dados_cliente.get("bairro", "") if st.session_state.dados_cliente else "", key=f"bairro_manual_{rc}")
    municipio_manual = st.text_input("🏙️ Município", placeholder="Cidade", value=st.session_state.dados_cliente.get("municipio", "") if st.session_state.dados_cliente else "", key=f"municipio_manual_{rc}")
    uf_manual = st.selectbox("UF", ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"], 
                             index=["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"].index(st.session_state.dados_cliente.get("uf", "SP")) if st.session_state.dados_cliente else 24, key=f"uf_manual_{rc}")
    cep_manual = st.text_input("🏷️ CEP", placeholder="00000-000", value=st.session_state.dados_cliente.get("cep", "") if st.session_state.dados_cliente else "", key=f"cep_manual_{rc}")
    
    if st.button("Salvar Dados Manuais", type="primary", use_container_width=True):
        if razao_manual and logradouro_manual and municipio_manual:
            st.session_state.dados_cliente = {
                "razao": razao_manual,
                "logradouro": logradouro_manual,
                "numero": numero_manual,
                "bairro": bairro_manual,
                "municipio": municipio_manual,
                "uf": uf_manual,
                "cep": cep_manual
            }
            st.success("Dados do cliente salvos manualmente!")
        else:
            st.error("Preencha pelo menos Razão Social, Logradouro e Município.")

# Exibe os dados (seja da consulta ou manual)
if st.session_state.dados_cliente:
    d = st.session_state.dados_cliente
    endereco = f'{d["logradouro"]}, {d["numero"]} - {d["bairro"]} | {d["municipio"]}/{d["uf"]} - CEP {d["cep"]}'
    st.text_input("Razão Social", d["razao"], disabled=True)
    st.text_area("Endereço", endereco, disabled=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Source+Sans+3:wght@400;600;700&display=swap');

:root {
    --zionne-green: #1f7a3a;
    --zionne-green-700: #14652f;
    --zionne-green-900: #0d3f1e;
    --zionne-gold: #c9a35d;
    --ink: #1f2937;
    --muted: #6b7280;
    --bg: #f6f4ef;
    --card: #ffffff;
    --line: #e5e7eb;
    --shadow: 0 8px 24px rgba(17, 24, 39, 0.10);
    --shadow-soft: 0 2px 8px rgba(17, 24, 39, 0.08);
    --radius: 14px;
    --btn-primary: #54b97a;
    --btn-primary-hover: #46aa6c;
    --btn-danger: #e07a7a;
    --btn-danger-hover: #d46c6c;
    --btn-whatsapp: #6ac38a;
    --btn-whatsapp-hover: #5ab67d;
}

/* ===== BASE ===== */
html, body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(1200px 600px at 10% -10%, #ffffff 0%, var(--bg) 50%, #f0efe9 100%) !important;
}

[data-testid="stAppViewContainer"] * {
    font-family: "Source Sans 3", sans-serif;
    color: var(--ink);
}

h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: "Source Sans 3", sans-serif !important;
    letter-spacing: 0.1px;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stAppViewContainer"] > .main .block-container {
    padding-top: 2rem;
    padding-bottom: 2.5rem;
}

/* ===== INPUTS ===== */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stSelectbox select {
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    background: #fff !important;
    box-shadow: inset 0 1px 0 rgba(17,24,39,0.02);
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus,
.stSelectbox select:focus {
    border-color: var(--zionne-green) !important;
    box-shadow: 0 0 0 3px rgba(31, 122, 58, 0.18) !important;
}

/* ===== BUTTONS ===== */
div[data-testid="stButton"] {
    width: 100% !important;
}

div[data-testid="stButton"] > button {
    width: 100% !important;
    display: block !important;
    border-radius: 10px !important;
    height: 44px !important;
    font-weight: 700 !important;
    border: none !important;
    box-shadow: var(--shadow-soft) !important;
    transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
}

button[kind="primary"] {
    background: linear-gradient(180deg, #7ad0a0 0%, var(--btn-primary) 100%) !important;
    color: white !important;
}

button[kind="primary"]:hover {
    background: linear-gradient(180deg, #6fc995 0%, var(--btn-primary-hover) 100%) !important;
    transform: translateY(-1px);
    box-shadow: 0 10px 22px rgba(17, 24, 39, 0.16) !important;
}

button[kind="secondary"] {
    background: var(--btn-danger) !important;
    color: white !important;
}

button[kind="secondary"]:hover {
    background: var(--btn-danger-hover) !important;
}

/* ===== CARDS ===== */
.card-produto {
    border: 1px solid var(--line);
    border-left: 6px solid var(--zionne-green);
    padding: 14px 14px 10px 14px;
    border-radius: var(--radius);
    margin-bottom: 12px;
    background: var(--card);
    box-shadow: var(--shadow);
}

/* ===== PRODUTOS GRID ===== */
.card-inner {
    background: #f6f1e7;
    border-radius: 12px;
    padding: 10px;
}

.product-sku {
    display: inline-block;
    font-size: 20px;
    font-weight: 700;
    color: var(--zionne-green-900);
    background: #eaf4ee;
    padding: 4px 8px;
    border-radius: 999px;
    margin-bottom: 6px;
}

.product-desc {
    font-size: 16px;
    color: var(--ink);
    min-height: 40px;
}

.product-price {
    font-size: 20px;
    font-weight: 700;
    color: var(--zionne-green-900);
    margin-top: 8px;
    background: #eaf4ee;
    padding: 6px 8px;
    border-radius: 8px;
    display: inline-block;
}

.product-actions {
    margin-top: 10px;
}

.product-actions .stNumberInput,
.product-actions .stButton {
    margin-top: 6px;
}

.product-card-marker {
    display: none;
}

.product-status {
    margin-top: 8px;
    font-size: 13px;
    color: var(--muted);
}

.product-status b {
    color: var(--ink);
}

/* ===== SEARCH ROW (PRODUTOS) ===== */
.search-row-marker {
    display: none;
}

div[data-testid="stVerticalBlock"]:has(.search-row-marker) .stTextInput input {
    height: 36px !important;
}

div[data-testid="stVerticalBlock"]:has(.search-row-marker) div[data-testid="stButton"] > button {
    height: 36px !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    padding: 6px 10px !important;
}

/* ===== ACTION ROW BUTTONS ===== */
.action-row-marker {
    display: none;
}

div[data-testid="stVerticalBlock"]:has(.action-row-marker) div[data-testid="stDownloadButton"] > button,
div[data-testid="stVerticalBlock"]:has(.action-row-marker) div[data-testid="stLinkButton"] a {
    height: 36px !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    padding: 6px 10px !important;
    box-shadow: none !important;
}

div[data-testid="stVerticalBlock"]:has(.action-row-marker) div[data-testid="stDownloadButton"] > button {
    background: #7b9bff !important;
    color: white !important;
}

div[data-testid="stVerticalBlock"]:has(.action-row-marker) div[data-testid="stDownloadButton"] > button:hover {
    background: #6b8df2 !important;
}

div[data-testid="stVerticalBlock"]:has(.action-row-marker) div[data-testid="stLinkButton"] a {
    background: #65c37f !important;
    color: white !important;
}

div[data-testid="stVerticalBlock"]:has(.action-row-marker) div[data-testid="stLinkButton"] a:hover {
    background: #57b571 !important;
}

/* ===== TABS ===== */
div[data-testid="stTabs"] button {
    border-radius: 12px 12px 0 0 !important;
    font-weight: 700 !important;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--zionne-green-900) !important;
    border-bottom: 3px solid var(--zionne-gold) !important;
}

/* ===== LINKS WHATSAPP ===== */
div[data-testid="stLinkButton"] a {
    display: block !important;
    width: 100% !important;
    text-align: center !important;
    padding: 16px 12px !important;
    border-radius: 12px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 18px rgba(0,0,0,0.18) !important;
    transition: transform 0.12s ease, box-shadow 0.12s ease !important;
    margin-top: 10px !important;
}

a[href*="wa.me"] {
    background: linear-gradient(90deg, var(--btn-whatsapp), #4fbf7a) !important;
    color: white !important;
    border: none !important;
}

div[data-testid="stLinkButton"] a:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 24px rgba(0,0,0,0.22) !important;
    background: linear-gradient(90deg, var(--btn-whatsapp-hover), #45b870) !important;
}

/* ===== SCROLL ÁREAS ===== */
section[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div[data-testid="stMarkdownContainer"] h3:contains("PRODUTOS")) + div {
    height: calc(100vh - 200px);
    overflow-y: auto;
    padding-right: 6px;
}

section[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div[data-testid="stMarkdownContainer"] h3:contains("CARRINHO")) + div {
    height: calc(100vh - 190px);
    overflow-y: auto;
    padding-right: 6px;
}

@media (max-width: 768px) {
    section[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div[data-testid="stMarkdownContainer"] h3:contains("PRODUTOS")) + div {
        height: calc(100vh - 150px) !important;
    }
    section[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div[data-testid="stMarkdownContainer"] h3:contains("CARRINHO")) + div {
        height: calc(100vh - 140px) !important;
    }
    div[data-testid="column"] {
        padding-left: 0px !important;
        padding-right: 0px !important;
    }
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover { background: #888; }

/* ===== TOTAL FIXO ===== */
.total-box {
    background: #ffffff;
    padding: 14px;
    border-radius: 14px;
    box-shadow: 0 -4px 16px rgba(0,0,0,0.08);
    position: sticky;
    bottom: 0;
    z-index: 10;
    border: 1px solid var(--line);
}
</style>
""", unsafe_allow_html=True)

from streamlit_qrcode_scanner import qrcode_scanner

# Estado da câmera
if "camera_on" not in st.session_state:
    st.session_state.camera_on = False

tab1, tab2, tab3 = st.tabs(["📦 PRODUTOS", "🧾 PEDIDOS-CARRINHO", "⚙️ FINALIZAÇÃO"])

# Mapa de produtos já adicionados
carrinho_map = {item["codigo"]: item for item in st.session_state.carrinho}

with tab1:

    st.markdown("### 📦 PRODUTOS")

    busca_key = f"busca_{rc}"
    if "scan_value" in st.session_state:
        st.session_state[busca_key] = st.session_state.pop("scan_value")
    if "clear_search" in st.session_state:
        st.session_state[busca_key] = ""
        st.session_state.pop("clear_search")
    if st.session_state.get("resume_camera"):
        st.session_state.camera_on = True
        st.session_state.resume_camera = False

    # Layout busca + botão QR
    st.markdown('<div class="search-row-marker"></div>', unsafe_allow_html=True)
    colBusca, colQR, top2 = st.columns([6, 1, 1])

    # 🔎 Campo de busca
    with colBusca:
        busca = st.text_input("🔎 Buscar produto", placeholder="Buscar por SKU ou descrição...", key=busca_key)

    # 📷 Botão que liga/desliga câmera
    with colQR:
        if st.button("Scanner", type="primary", use_container_width=True):
            st.session_state.camera_on = not st.session_state.camera_on
        if st.session_state.camera_on:
            if st.button("Fechar Scanner", type="secondary", use_container_width=True):
                st.session_state.camera_on = False

    # 📷 Scanner aparece só se estiver ativo
    if st.session_state.camera_on:
        st.info("Aponte a câmera para o QR Code")

        qr_code = qrcode_scanner()

        if qr_code:
            st.session_state["scan_value"] = qr_code   # preenche o campo no próximo rerun
            st.session_state.resume_camera = True      # reabre a câmera após atualizar a busca
            st.session_state.camera_on = False         # pausa a câmera para atualizar a lista
            st.success(f"Código lido: {qr_code}")
            st.rerun()

    # 🔍 Filtro de produtos
    df_filtrado = df_produtos[
        df_produtos["descricao"].str.contains(busca, case=False, na=False) |
        df_produtos["codigo"].astype(str).str.contains(busca, case=False, na=False)
    ]

    with top2:
        st.markdown(f"<div style='margin-top:8px;font-size:14px'><b>{len(df_filtrado)}</b><br>itens</div>", unsafe_allow_html=True)


    # 👇 CONTAINER NATIVO
    container_produtos = st.container()

    # 👇 MARCADOR CSS
    # container_produtos.markdown('<div class="scroll-fix"></div>', unsafe_allow_html=True)

    with container_produtos:

        carrinho_map = {item["codigo"]: item for item in st.session_state.carrinho}
        produtos = df_filtrado.to_dict("records")

        for i in range(0, len(produtos), 3):
            cols = st.columns(3)

            for j, col in enumerate(cols):
                if i + j >= len(produtos):
                    break

                row = produtos[i + j]
                codigo = row["codigo"]
                preco = row["preco"]
                ja_no_carrinho = codigo in carrinho_map
                badge = "✅ No pedido" if ja_no_carrinho else " "

                with col:
                    card = st.container(border=True)
                    with card:
                        st.markdown('<div class="card-inner">', unsafe_allow_html=True)
                        st.markdown(f'<div class="product-sku">SKU {codigo}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="product-desc">{row["descricao"]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="product-price">R$ {preco:.2f}</div>', unsafe_allow_html=True)

                        st.markdown('<div class="product-actions">', unsafe_allow_html=True)
                        qtd = st.number_input("Qtd", value=1, min_value=1, step=1, key=f"qtd_{codigo}_{rc}")

                        if st.button("Adicionar ➕", key=f"add_{codigo}", type="primary", use_container_width=True):
                            if ja_no_carrinho:
                                idx = next(i for i, item in enumerate(st.session_state.carrinho) if item["codigo"] == codigo)
                                st.session_state.carrinho[idx]["qtd"] += qtd
                                st.session_state.carrinho[idx]["total"] = st.session_state.carrinho[idx]["qtd"] * preco
                            else:
                                st.session_state.carrinho.append({
                                    "codigo": codigo,
                                    "descricao": row["descricao"],
                                    "qtd": qtd,
                                    "preco": preco,
                                    "total": qtd * preco
                                })
                            # Streamlit já faz rerun automaticamente; evitar salto de scroll
                            st.session_state["clear_search"] = True

                        if ja_no_carrinho:
                            qtd_total = carrinho_map[codigo]["qtd"]
                            st.markdown("🟢 **Este produto já está no pedido**")
                            st.markdown(f"✅ **No Pedido: {qtd_total} unidades**")

                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

with tab2:

    st.markdown("### 🧾 CARRINHO")

    if st.session_state.carrinho and st.session_state.dados_cliente:

        df_carrinho = pd.DataFrame(st.session_state.carrinho)
        total_pedido = df_carrinho["total"].sum() if not df_carrinho.empty else 0

        top1, top2 = st.columns([4,1])
        with top1:
            st.caption("Itens adicionados")
        with top2:
            st.markdown(
                f"<div style='text-align:right;margin-top:6px'>"
                f"<b>{len(st.session_state.carrinho)}</b><br>itens"
                f"<div style='font-size:16px;color:#6b7280;margin-top:4px'>"
                f"Total: R$ {total_pedido:,.2f}"
                f"</div></div>",
                unsafe_allow_html=True
            )

        container_carrinho = st.container()
        # container_carrinho.markdown('<div class="scroll-carrinho"></div>', unsafe_allow_html=True)

        with container_carrinho:

            def atualizar_item(idx, key_qtd, preco):
                nova_qtd = st.session_state.get(key_qtd, 1)
                st.session_state.carrinho[idx]["qtd"] = nova_qtd
                st.session_state.carrinho[idx]["total"] = nova_qtd * preco

            def remover_item(idx):
                del st.session_state.carrinho[idx]

            for i, item in enumerate(st.session_state.carrinho):

                card = st.container(border=True)
                with card:
                    st.markdown('<div class="card-inner">', unsafe_allow_html=True)
                    st.markdown(f'<div class="product-sku">SKU {item["codigo"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="product-desc">{item["descricao"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="product-price">R$ {item["preco"]:.2f}</div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="product-status">Total do item: <b>R$ {item["total"]:.2f}</b></div>',
                        unsafe_allow_html=True
                    )

                    st.markdown('<div class="product-actions">', unsafe_allow_html=True)
                    key_qtd = f"edit_qtd_{i}_{st.session_state.reset_counter}"
                    st.number_input(
                        "Qtd",
                        value=item["qtd"],
                        min_value=1,
                        step=1,
                        key=key_qtd
                    )

                    st.button(
                        "Atualizar 🔄",
                        key=f"update_{i}",
                        type="primary",
                        use_container_width=True,
                        on_click=atualizar_item,
                        args=(i, key_qtd, item["preco"])
                    )

                    st.button(
                        "Remover 🗑️",
                        key=f"remove_{i}",
                        type="secondary",
                        use_container_width=True,
                        on_click=remover_item,
                        args=(i,)
                    )

                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="product-status">✅ No Pedido: <b>{item["qtd"]} unidades</b></div>',
                        unsafe_allow_html=True
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

        # TOTAL FIXO FORA DO SCROLL

        st.markdown(
            f"<div class='total-box'><h3>💰 TOTAL: R$ {total_pedido:,.2f}</h3>",
            unsafe_allow_html=True
        )


    else:
        st.info("Nenhum produto adicionado ao pedido ainda.")



with tab3:
    st.header("⚙️ FINALIZAÇÃO")

    if not st.session_state.carrinho or not st.session_state.dados_cliente:
        st.info("É necessário cliente e produtos para finalizar.")
        st.stop()

    # 🔥 CRIA AQUI (resolve o erro)
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    total_pedido = df_carrinho["total"].sum()
    condicao_pagamento = st.session_state.get("cond_pag", "")
    tipo_Frete = st.session_state.get("frete", "")
    observacoes = st.session_state.get("obs_pedido", "")

    # =========================
    # CAMPOS DA FINALIZAÇÃO
    # =========================
    condicao_pagamento = st.selectbox(
        "Condição de Pagamento",
        ["À Vista - PIX", "30% Adto + 30 dias", "30% Adto + 30/60", "30% Adto + 30/60/90", "Outro"],
        key="cond_pag"
    )

    tipo_Frete = st.selectbox(
        "Tipo Frete",
        ["FOB - Por conta do cliente", "CIF", "FOB + CIF"],
        key="frete"
    )
    observacoes = st.text_area(
        "Observações do Pedido",
        key="obs_pedido"
    )

    # CSV com colunas Código;descrição,qtde,preco e nome CNPJ-data
    agora = datetime.now()
    timestamp = agora.strftime("%d-%m-%Y_%H-%M-%S")

    nome_csv = f"PEDIDO_ZIONNE_{cnpj}_{timestamp}.csv"
    csv_buffer = StringIO()

    # Cabeçalho do pedido
    csv_buffer.write(f"CLIENTE;{st.session_state.dados_cliente['razao']}\n")
    csv_buffer.write(f"CNPJ;{cnpj}\n")
    csv_buffer.write(f"COND_PAG;{condicao_pagamento}\n")
    csv_buffer.write(f"TIPO_FRETE;{tipo_Frete}\n")
    csv_buffer.write(f"TOTAL_PEDIDO;{total_pedido:.2f}\n")
    csv_buffer.write("\nITENS\n")

    df_carrinho[["codigo", "descricao", "qtd", "preco", "total"]].to_csv(
        csv_buffer, sep=";", index=False
    )

    csv_content = csv_buffer.getvalue()

    # Função para gerar PDF
    # Função para gerar PDF
    from fpdf import FPDF
    from datetime import datetime

    # ================= CLASSE PDF PERSONALIZADA =================
    class PedidoPDF(FPDF):

        def footer(self):
            self.set_y(-20)  # posição do rodapé
            self.set_font("Arial", "", 8)

            self.cell(0, 4, "Instagram: @zionne.oficial", 0, 1, "C")
            self.cell(0, 4, "Telefone / WhatsApp: (41) 3043-0595", 0, 1, "C")
            self.cell(0, 4, "Site: zionne.com.br | E-mail: comercial@zionne.com", 0, 1, "C")
            self.cell(0, 4, "R. Gen. Mário Tourinho, 2465 - Curitiba - PR", 0, 0, "C")


    # ================= FUNÇÃO GERAR PDF =================
    def gerar_pdf(dados_cliente, carrinho, total, cond_pag, frete, obs, cnpj, telefone, email, ie):

        pdf = PedidoPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=25)

        # ================= CABEÇALHO =================
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 8, "PEDIDO DE VENDA - FEIRA ABUP SHOW HOME - 2-5 FEVEREIRO/2026", 0, 1, "C")

        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 5, f"Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, "R")

        pdf.ln(3)

        # ================= DADOS DO CLIENTE =================
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "DADOS DO CLIENTE", 0, 1)

        pdf.set_font("Arial", "", 9)

        endereco = f"{dados_cliente['logradouro']}, {dados_cliente['numero']} - {dados_cliente['bairro']} - {dados_cliente['municipio']}/{dados_cliente['uf']} - CEP {dados_cliente['cep']}"

        pdf.cell(0, 5, f"Cliente: {dados_cliente['razao']}", 0, 1)
        pdf.cell(0, 5, f"CNPJ: {cnpj}    IE: {ie}", 0, 1)
        pdf.cell(0, 5, f"Telefone: {telefone}    Email: {email}", 0, 1)
        pdf.multi_cell(0, 5, f"Endereço: {endereco}")

        pdf.ln(2)

        # ================= INFORMAÇÕES COMERCIAIS =================
        pdf.cell(0, 5, "Natureza da Operação: Venda de Produtos", 0, 1)
        pdf.cell(0, 5, "Representante: Vendedor Interno", 0, 1)

        pdf.ln(3)

        # ================= TABELA PRODUTOS =================
        pdf.set_font("Arial", "B", 9)
        pdf.cell(10, 6, "Item", 1, 0, "C")
        pdf.cell(20, 6, "Código", 1, 0, "C")
        pdf.cell(90, 6, "Descrição", 1, 0, "C")
        pdf.cell(15, 6, "Qtde", 1, 0, "C")
        pdf.cell(20, 6, "Vlr Unit", 1, 0, "C")
        pdf.cell(10, 6, "Desc.", 1, 0, "C")
        pdf.cell(25, 6, "Vlr Total", 1, 1, "C")

        pdf.set_font("Arial", "", 9)

        subtotal = 0
        for i, item in enumerate(carrinho, start=1):
            pdf.cell(10, 6, str(i), 1, 0, "C")
            pdf.cell(20, 6, item['codigo'], 1)
            pdf.cell(90, 6, item['descricao'], 1)
            pdf.cell(15, 6, f"{item['qtd']}", 1, 0, "C")
            pdf.cell(20, 6, f"{item['preco']:.2f}", 1, 0, "R")
            pdf.cell(10, 6, "0,00", 1, 0, "R")
            pdf.cell(25, 6, f"{item['total']:.2f}", 1, 1, "R")
            subtotal += item['total']

        pdf.ln(3)

        # ================= TOTAIS =================
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "TOTAIS", 0, 1)

        pdf.set_font("Arial", "", 9)

        pdf.cell(140, 6, "")
        pdf.cell(25, 6, "Subtotal:", 1)
        pdf.cell(25, 6, f"{subtotal:.2f}", 1, 1, "R")

        pdf.cell(140, 6, "")
        pdf.cell(25, 6, "Frete:", 1)
        pdf.cell(25, 6, "0,00", 1, 1, "R")

        pdf.cell(140, 6, "")
        pdf.cell(25, 6, "Outras Desp.:", 1)
        pdf.cell(25, 6, "0,00", 1, 1, "R")

        pdf.cell(140, 6, "")
        pdf.set_font("Arial", "B", 10)
        pdf.cell(25, 6, "TOTAL:", 1)
        pdf.cell(25, 6, f"{total:.2f}", 1, 1, "R")

        pdf.ln(4)

        # ================= PAGAMENTO / OBS =================
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 5, f"Condição de Pagamento: {cond_pag}")
        pdf.ln(2)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "INFORMAÇÕES DE ENTREGA", 0, 1)

        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 5, f"Tipo de Frete: {frete}")

        pdf.multi_cell(0, 5, f"Observações: {obs}")

        return pdf.output(dest='S').encode('latin1')


    # Gerar PDF
    pdf_bytes = gerar_pdf(st.session_state.dados_cliente, st.session_state.carrinho, total_pedido, condicao_pagamento, tipo_Frete, observacoes, cnpj, telefone, email, ie)
    agora = datetime.now()
    timestamp = agora.strftime("%d-%m-%Y_%H-%M-%S")

    nome_pdf = f"PEDIDO_ZIONNE_{cnpj}_{timestamp}.pdf"

    # Ações em linha (CSV / PDF / WhatsApp Cliente)
    telefone_limpo = re.sub(r'\D', '', telefone)
    d = st.session_state.dados_cliente
    mensagem_cliente_full = f"""🧾 *PEDIDO ZIONNE – FEIRA ABUP*

━━━━━━━━━━━━━━━━━━
👤 *DADOS DO CLIENTE*
Razão Social: {d["razao"]}
CNPJ: {cnpj}
IE: {ie}
Telefone: {telefone}
E-mail: {email}

📍 Endereço:
{d["logradouro"]}, {d["numero"]} - {d["bairro"]}
{d["municipio"]}/{d["uf"]} - CEP {d["cep"]}

━━━━━━━━━━━━━━━━━━
🚚 *FRETE:* {tipo_Frete}
💳 *PAGAMENTO:* {condicao_pagamento}

📝 *OBSERVAÇÕES*
{observacoes if observacoes else "—"}

━━━━━━━━━━━━━━━━━━
📦 *ITENS DO PEDIDO*
"""

    for item in st.session_state.carrinho:
        mensagem_cliente_full += (
            f"\n🔹 *{item['descricao']}*\n"
            f"Cód: {item['codigo']}\n"
            f"{item['qtd']} x R$ {item['preco']:.2f} = *R$ {item['total']:.2f}*\n"
        )

    mensagem_cliente_full += f"""
━━━━━━━━━━━━━━━━━━
💰 *TOTAL DO PEDIDO: R$ {total_pedido:.2f}*
━━━━━━━━━━━━━━━━━━

Obrigado por comprar com a *Zionne* 🤍
"""
    action_row = st.container()
    with action_row:
        st.markdown('<div class="action-row-marker"></div>', unsafe_allow_html=True)
        c_csv, c_pdf = st.columns(2)
        with c_csv:
            st.download_button("Gerar CSV", csv_content, nome_csv, mime="text/csv", use_container_width=True)
        with c_pdf:
            st.download_button("Gerar PDF", pdf_bytes, nome_pdf, mime="application/pdf", use_container_width=True)

# =====================================================
# WHATSAPP
# =====================================================

d = st.session_state.dados_cliente

telefone_limpo = re.sub(r'\D', '', telefone)
telefone_zionne_limpo = re.sub(r'\D', '', telefone_zionne)

# ================= MENSAGEM CLIENTE =================
mensagem_cliente = f"""🧾 *PEDIDO ZIONNE – FEIRA ABUP*

━━━━━━━━━━━━━━━━━━
👤 *DADOS DO CLIENTE*
Razão Social: {d["razao"]}
CNPJ: {cnpj}
IE: {ie}
Telefone: {telefone}
E-mail: {email}

📍 Endereço:
{d["logradouro"]}, {d["numero"]} - {d["bairro"]}
{d["municipio"]}/{d["uf"]} - CEP {d["cep"]}

━━━━━━━━━━━━━━━━━━
🚚 *FRETE:* {tipo_Frete}
💳 *PAGAMENTO:* {condicao_pagamento}


📝 *OBSERVAÇÕES*
{observacoes if observacoes else "—"}

━━━━━━━━━━━━━━━━━━
📦 *ITENS DO PEDIDO*
"""

for item in st.session_state.carrinho:
    mensagem_cliente += (
        f"\n🔹 *{item['descricao']}*\n"
        f"Cód: {item['codigo']}\n"
        f"{item['qtd']} x R$ {item['preco']:.2f} = *R$ {item['total']:.2f}*\n"
    )

mensagem_cliente += f"""
━━━━━━━━━━━━━━━━━━
💰 *TOTAL DO PEDIDO: R$ {total_pedido:.2f}*
━━━━━━━━━━━━━━━━━━

Obrigado por comprar com a *Zionne* 🤍
"""

# ================= MENSAGEM INTERNA ZIONNE =================
mensagem_zionne = f"""📥 *NOVO PEDIDO – FEIRA ABUP*

━━━━━━━━━━━━━━━━━━
👤 CLIENTE: {d["razao"]}
CNPJ: {cnpj}
IE: {ie}
TEL: {telefone}
EMAIL: {email}

📍 ENDEREÇO:
{d["logradouro"]}, {d["numero"]} - {d["bairro"]}
{d["municipio"]}/{d["uf"]} - CEP {d["cep"]}

🚚 *FRETE:* {tipo_Frete}
💳 *PAGAMENTO:* {condicao_pagamento}

📝 OBS: {observacoes if observacoes else "—"}

━━━━━━━━━━━━━━━━━━
📦 PRODUTOS
"""

for item in st.session_state.carrinho:
    mensagem_zionne += (
        f"\n• {item['codigo']} | {item['descricao']}"
        f"\n  Qtde: {item['qtd']}  |  Unit: R$ {item['preco']:.2f}  |  Total: R$ {item['total']:.2f}\n"
    )

mensagem_zionne += f"""
━━━━━━━━━━━━━━━━━━
💰 TOTAL PEDIDO: R$ {total_pedido:.2f}
━━━━━━━━━━━━━━━━━━

📎 CSV:
{csv_content}
"""

# ================= LINKS WHATSAPP =================
if telefone_limpo:
    link_cliente = f"https://wa.me/55{telefone_limpo}?text={quote(mensagem_cliente)}"
    st.link_button("📲 Enviar Pedido para Cliente no WhatsApp", link_cliente)
else:
    st.warning("Informe o telefone do cliente para envio via WhatsApp.")

if telefone_zionne_limpo:
    link_zionne = f"https://wa.me/55{telefone_zionne_limpo}?text={quote(mensagem_zionne)}"
    st.link_button("📲 Enviar Pedido para Zionne no WhatsApp", link_zionne)
else:
    st.warning("Informe o Telefone WhatsApp Zionne para enviar.")

st.info("Para enviar o PDF como anexo, baixe o arquivo e anexe manualmente no WhatsApp. O CSV é enviado como texto na mensagem para Zionne.")


