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
if st.button("🆕 Novo Pedido"):
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
0000001	;	BULE COM INFUSOR - HORTICOOL GREEN 500ML	;	308,9
0000002	;	BULE COM INFUSOR - HORTICOOL GREEN 1000M	;	401,58
0000030	;	BULE COM INFUSOR - HORTICOOL PINK 500ML 	;	308,9
0000031	;	BULE COM INFUSOR - HORTICOOL PINK 1000ML	;	401,58
0000051	;	BULE COM INFUSOR - REGENCY DAMASK 500ML 	;	370,67
0000052	;	BULE COM INFUSOR RENGENCY DAMASKY 1000ML	;	463,35
0000102	;	BULE COM INFUSOR - BLUE RIBBON 1000ML   	;	370,67
0000134	;	BULE COM INFUSOR - HORTICOOL BLUE 1000ML	;	401,58
0000133	;	BULE COM INFUSOR - HORTICOOL BLUE 500ML 	;	308,9
0000032	;	ACUCAREIRO HORTICOOL PINK 150ML         	;	142,94
0000079	;	ACUCAREIRO REGENCY DAMASKY 250ML        	;	172,97
0000103	;	ACUCAREIRO BLUE RIBBON 260ML            	;	148,28
0000135	;	ACUCAREIRO HORTICOOL BLUE 150ML         	;	142,09
0000003	;	ACUCAREIRO HORTICOOL GREEN 150ML        	;	142,94
0000004	;	LEITEIRA HORTICOOL GREEN 150ML          	;	118,09
0000033	;	LEITEIRA HORTICOOL PINK 150ML           	;	118,09
0000080	;	LEITEIRA REGENCY DAMASKY 200ML          	;	142,09
0000104	;	LEITEIRA BLUE RIBBON 220ML              	;	123,56
0000136	;	LEITEIRA HORTICOOL BLUE 150ML           	;	117,37
0000005	;	BULE COM INFUSOR E XICARA HOORTICOL GREE	;	358,33
0000034	;	BULE COM INFUSOR E XICARA HORTICOOL PINK	;	358,33
0000053	;	BULE COM INFUSOR E XICARA REGENCY DAMASK	;	401,58
0000137	;	BULE COM INFUSOR E XICARA HOORTICOL BLUE	;	358,33
0000006	;	XICARA DE CHA E PIRES APPLE BLOSSOM HORT	;	149,16
0000007	;	XICARA DE CHA E PIRES FLOR GEOMETRIA VER	;	149,16
0000008	;	CAFE E PIRES HORTICOOL GREEN 100ML      	;	105,65
0000035	;	XICARA DE CHA E PIRES APPLE BLOSSOM HORT	;	149,16
0000036	;	XICARA DE CHA E PIRES GEOMETRICA BLOSSOM	;	149,16
0000037	;	CAFE E PIRES HORTICOOL PINK 100ML       	;	105,65
0000064	;	XICARA DE CHA E PIRES PINK REGENCY DAMAS	;	172,97
0000065	;	XICARA DE CHA E PIRES BLUE REGENCY DAMAS	;	172,97
0000066	;	CAFE E PIRES FLOR PINK REGENCY DAMASKY 1	;	123,56
0000067	;	CAFE E PIRES BLUE REGENCY DAMASKY 100ML 	;	123,56
0000105	;	XICARA DE CHA CONJUNTO/2 BLUE RIBBON ROS	;	259,49
0000106	;	XICARA DE CHA CONJUNTO/2 BLUE RIBBON QUE	;	259,49
0000138	;	XICARA DE CHA E PIRES APPLE BLOSSOM HORT	;	148,28
0000139	;	XICARA DE CHA E PIRES GEOMETRIA HORTICOO	;	148,28
0000169	;	XICARA DE CAFE E PIRES HORTICOOL BLUE 10	;	105,01
0000159	;	XICARA DE CHA WHITE TAPESTRY 250ML      	;	292,3
0000160	;	XICARA DE CHA RED-PEONY TAPESTRY 250ML  	;	292,3
0000161	;	XICARA DE CHA BLUE DAHLIA TAPESTRY 360ML	;	292,3
0000131	;	CANECA GEOMETRICA HORTICOOL GREEN 300ML 	;	98,84
0000132	;	CANECA HORTICOOL GREEN 300ML            	;	98,84
0000156	;	CANECA COM ALCA GEOMETRICA HORTICOOL GRE	;	98,84
0000157	;	CANECA COM ALCA FLORAL HORTICOOL GREEN 3	;	98,84
0000068	;	CANECA REGENCY DAMASK FLOR PINK 350ML   	;	117,37
0000069	;	CANECA REGENCY DAMASK FLOR BLUE 350ML   	;	117,37
0000070	;	CANECA REGENCY DAMASK PINK 350ML        	;	117,37
0000071	;	CANECA REGENCY DAMASK BLUE 350ML        	;	117,37
0000083	;	CONJUNTO/2 CANECAS (SEM ALCA) REGENCY DA	;	172,97
0000141	;	CANECA HORTICOOL BLUE 300ML             	;	98,84
0000140	;	CANECA GEOMETRIA HORTICOOL BLUE 300ML   	;	98,84
0000162	;	CANECA COM ALCA LILAK TAPESTRY 36OML    	;	227,29
0000163	;	CANECA ALCA OFF WHITE PEONY TAPESTRY 360	;	227,29
0000164	;	CANECA ALCA LEMON DAHLIA TAPESTRY 360ML 	;	227,29
0000081	;	POTE REGENCY DAMASKY PINK 14.7x14.7x16.6	;	370,67
0000082	;	POTE REGENCY DAMASKY BLUE 14.7x14.7x16.6	;	370,67
0000009	;	PRATO DE PAO LIMA HORTICOOL GREEN 16,5CM	;	93,21
0000010	;	PRATO DE PAO PINK HORTICOOL GREEN 16.5CM	;	93,21
0000038	;	PRATO DE PAO LIME HORTICOOL PINK 16,5CM 	;	93,21
0000054	;	PRATOS DE PAO REGENCY DAMASKY 17CM 17.1x	;	111,2
0000055	;	PRATO DE PAO REGENCY DAMASKY 17CM 17.1x1	;	111,2
0000056	;	PRATO DE PAO REGENCY DAMASKY 17CM 17.1x1	;	111,2
0000057	;	PRATO DE PAO REGENCY DAMASKY 17CM 17.1x1	;	111,2
0000095	;	PRATO PAO BLUE RIBBON OVAL CONJUNTO/2 17	;	154,45
0000110	;	CONJUNTO/4 PRATO MINI 11x11x2.7cm       	;	166,8
0000142	;	PRATO DE PAO HORTICOOL BLUE 16,5CM 16.7x	;	92,68
0000115	;	PRATO DE PAO BARROCO FLORESCENDO BLOOMIN	;	139,27
0000116	;	PRATO DE PAO BARROCO FLORESCENDO BLOOMIN	;	139,27
0000117	;	PRATO DE PAO BARROCO FLORESCENDO  BLOOMI	;	139,27
0000118	;	PRATO DE PAO BARROCO FLORESCENTE BLOOMIN	;	108,91
0000119	;	PRATO DE PAO BARROCO FLORESCENTE BLOOMIN	;	108,91
0000120	;	PRATO DE PAO BARROCO FLORESCENTE BLOOMIN	;	108,91
0000011	;	PRATO DE SOBREMESA FLOR HORTICOOL GREEN 	;	118,09
0000012	;	PRATO DE SOBREMESA GEOMETRIA GREEN HORTI	;	118,09
0000039	;	PRATO DE SOBREMESA FLOR BLOSSOM PINK 20,	;	118,09
0000040	;	PRATO DE SOBREMESA GEOMETRIA HORTICOOL P	;	118,09
0000058	;	PRATO DE SOBREMESA REGENCY DAMASKY 21CM 	;	135,92
0000059	;	PRATO DE SOBREMESA REGENCY DAMASKY 21CM 	;	135,92
0000096	;	PRATO SOBREMESA BLUE RIBBON OVAL CONJUNT	;	222,41
0000143	;	PRATO DE SOBREMESA FLOR HORTICOOL BLUE 2	;	117,37
0000013	;	PRATO DE JANTAR FLOR DE MACA HORTICOOL G	;	149,16
0000014	;	PRATO DE JANTAR GEOMETRIA HORTICOOL GREE	;	149,16
0000041	;	PRATO DE JANTAR FLOR DE MACA HORTICOOL P	;	149,16
0000060	;	PRATO DE JANTAR REGENCY DAMASK 26CM 26.3	;	172,97
0000061	;	PRATO DE JANTAR REGENCY DAMASK 26CM 26.3	;	172,97
0000063	;	PRATO FUNDO REGENCY DAMASKY 21CM 21.7x21	;	154,45
0000097	;	PRATO DE JANTAR BLUE RIBBON OVAL CONJUNT	;	284,18
0000112	;	PRATO DE JANTAR BARROCO FLORESCENTE BLOO	;	191,09
0000113	;	PRATO DE JANTAR BARROCO FLORESCENTE BLOO	;	191,09
0000114	;	PRATO DE JANTAR BARROCO FLORESCENTE BLOO	;	191,09
0000145	;	PRATO DE JANTAR FLOR HORTICOOL BLUE 26CM	;	148,28
0000146	;	PRATO DE FUNDO GEOMETRIA HORTICOOL BLUE 	;	129,73
0000015	;	PRATO FUNDO FLOR DE MACA HORTICOOL GREEN	;	130,5
0000016	;	PRATO FUNDO GEOMETRIA HORTICOOL GREEN 22	;	130,5
0000042	;	PRATO FUNDO FLOR DE MACA HORTICOOL PINK 	;	129,73
0000062	;	PRATO FUNDO REGENCY DAMASKY 21CM 21.7x21	;	154,45
0000100	;	PRATO FUNDO BLUE RIBBON 20CM 20.6x20.6x4	;	123,56
0000121	;	PRATO FUNDO BARROCO FLORESCENTE BLOOMING	;	159,01
0000122	;	PRATO FUNDO BARROCO FLORESCENTE BLOOMING	;	159,01
0000123	;	PRATO FUNDO BARROCO FLORESCENTE BLOOMING	;	159,01
0000144	;	PRATO HORTICOOL BLUE 20,0CM             	;	117,37
0000150	;	CONJUNTO/4 HORTICOOL BLUE PRATO MINI 11x	;	185,33
0000167	;	PRATO CONJUNTO/3 PEOANY TAPESTRY        	;	584,95
0000168	;	PRATO CONJUNTO/3 DAHLIA TAPESTRY        	;	422,38
0000017	;	TRAVESSA OBLONGA HORTICOOL GREEN 30CM 29	;	149,16
0000018	;	TRAVESSA OBLONGA HORTICOOL GREEN 35CM 34	;	217,53
0000025	;	TRAVESSA OVAL HORTICOOL GREEN 31CM 30.9x	;	186,46
0000043	;	TRAVESSA OBLONGA HORTICOOL PINK 30CM 29.	;	148,28
0000044	;	TRAVESSA OBLONGA HORTICOOL PINK 35CM 34.	;	216,21
0000048	;	TRAVESSA OVAL HORTICOOL PINK 31CM 30.9x1	;	185,33
0000075	;	TRAVESSA HEXAGONAL REGENCY DAMASKY AZUL 	;	240,93
0000076	;	TRAVESSA HEXAGONAL REGENCY DAMASKY PINK 	;	240,93
0000077	;	TRAVESSA HEXAGONAL REGENCY DAMASKY PINK 	;	148,28
0000078	;	TRAVESSA HEXAGONAL REGENCY DAMASKY AZUL 	;	148,28
0000098	;	TRAVESSA OVAL COM ALCA BLUE RIBBON 32CM 	;	296,54
0000099	;	TRAVESSA OVAL BLUE RIBBON 31CM 30.8x17.5	;	166,8
0000124	;	TRAVESSA RETANGULAR BLOOMING BAROQUE 35C	;	233,63
0000147	;	TRAVESSA OBLONGA HORTICOOL BLUE 30CM 29.	;	148,28
0000148	;	TRAVESSA OBLONGA HORTICOOL BLUE 35CM 34.	;	216,21
0000149	;	TRAVESSA OVAL HORTICOOL BLUE 31CM 30.9x1	;	185,33
0000158	;	TRAVESSA RETANGULAR BLUE TAPESTRY 33CM  	;	324,82
0000023	;	PRATO DE DOCES 2 CAMADAS HORTICOOL GREEN	;	236,16
0000024	;	 PRATO DE DOCE 3 CAMADAS HORTICOOL GREEN	;	403,96
0000047	;	PRATO DE DOCES 2 CAMADAS HORTICOOL PINK 	;	234,77
0000084	;	PRATO DE DOCE 3 CAMADAS REGENCY DAMASKY 	;	463,35
0000085	;	PRATO DE DOCES 2 CAMADAS REGENCY DAMASKY	;	265,65
0000021	;	SOPEIRA GREEN HORTICOOL 2.4L 2400ML     	;	864,93
0000155	;	CONSOME COM TAMPA FLORAL HORTICOOL GREEN	;	175,25
0000019	;	BOWL HORTICOOL GREEN 17CM 700ML         	;	124,28
0000020	;	BOWL FLOR DE MACA HORTICOOL GREEN 17CM 7	;	124,28
0000152	;	BOWL COM TAMPA FLORAL HORTICOOL GREEN 12	;	110,24
0000153	;	BOWL COM TAMPA FLORAL GEOMETRIA HORTICOO	;	110,24
0000154	;	BOWL COM TAMPA FLORAL HORTICOOL GREEN 17	;	168,76
0000046	;	SOPEIRA HORTICOOL PINK 2.4L 2400ML      	;	864,93
0000049	;	TIGELA FLOR DE MACA HORTICOOL PINK 12CM 	;	80,32
0000050	;	BOWL FLOR DE MACA HORTICOOL PINK 22CM 21	;	278,01
0000072	;	BOWL REGENCY DAMASK PINK 15CM 15x15x7.3C	;	142,09
0000086	;	BOWL REGENCY DAMASKY 22CM 22.3x22.3x9.5C	;	401,58
0000087	;	BOWL REGENCY DAMASKY 12CM 12x12x5.4CM 22	;	111,2
0000088	;	BOWL REGENCY DAMASKY 12CM 12x12x5.4CM 22	;	111,2
0000089	;	BOWL REGENCY DAMASKY PINK QUADRADO 12CM 	;	111,2
0000090	;	BOWL REGENCY DAMASKY BLUE QUADRADO 12CM 	;	111,2
0000101	;	BOWL DE FRUTA BLUE RIBBON 450ML         	;	142,09
0000107	;	 BOWL CONJUNTO/4 BLUE RIBBON 270ml      	;	259,49
0000109	;	TIGELA BLUE RIBBON 22 cm 21.8x21.8x9.5cm	;	247,13
0000129	;	BOWL FLORESCENDO BARROCO BLOOMING BAROQU	;	106,78
0000130	;	BOWL FLORESCENDO BARROCO BLOOMING BAROQU	;	106,78
0000151	;	BOWL HORTICOOL BLUE 12CM 220ML          	;	80,32
0000165	;	BOWL CONJUNTO/2 TAPESTRY 12CM           	;	194,77
0000166	;	BOWL CONJUNTO/2 PEOANY TAPESTRY 12CM    	;	227,29
0000022	;	CONJUNTO/2 CANECAS HORTICOOL 300ML      	;	155,36
0000026	;	TIGELA FLOR DE MACA HORTICOOL GREEN 22CM	;	279,67
0000027	;	TIGELA FLOR DE MACA HORTICOOL GREEN 12CM	;	80,8
0000045	;	BOWL HORTICOOL PINK 17CM 700ML          	;	123,56
0000073	;	BOWL REGENCY DAMASK BLUE 15CM 15x15x7.3C	;	142,09
0000108	;	BOWL BLUE RIBBON 560ML                  	;	111,2
0000125	;	TIGELA FLORESCENTE BARROCO BLOOMING BARO	;	394,67
0000126	;	TIGELA BARROCO FLORESCENTE  BLOOMING BAR	;	149,29
0000127	;	TIGELA BARROCO FLORESCENTE BLOOMING BARO	;	149,29
0000128	;	TIGELA BARROCO FLORESCENTE BLOOMING BARO	;	149,29
0000028	;	CESTA DE PIQUENIQUE HORTICOOL GREEN 38x2	;	441,07
0000029	;	TRILHO DE MESA HORTICOOL                	;	286,99
0000074	;	VASO REGENCY DAMASKY 22,8CM 22.8x22.8x22	;	1.112,03
0000111	;	VASO BLUE RIBBON 22CM 21.8x21.8x9.5cm   	;	1.050,26
0000091	;	CONJUNTO AROMA CRISTAL BLUE RIBBON 10x10	;	370,67
0000092	;	CONJUNTO AROMA CRISTAL BLUE RIBBON 10x10	;	370,67
0000093	;	CONJUNTO DIFUSOR BLUE RIBBON PINK 9.5x9.	;	370,67
0000094	;	CONJUNTO DIFUSOR BLUE RIBBON 9.5x9.5x9.8	;	370,67

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
st.header("🏢 Dados do Cliente")

col1, col2, col3, col4 = st.columns(4)
rc = st.session_state.reset_counter

cnpj = col1.text_input("CNPJ", key=f"cnpj_{rc}")
telefone = col2.text_input("Telefone WhatsApp", key=f"tel_{rc}")
email = col3.text_input("E-mail", key=f"email_{rc}")
ie = col4.text_input("Inscrição Estadual", key=f"ie_{rc}")

telefone_zionne = st.text_input("Telefone WhatsApp Zionne", key=f"tel_zionne_{rc}")


if st.button("Consultar CNPJ"):
    dados, erro = consulta_cnpj(cnpj)
    if erro:
        st.error(erro)
    else:
        st.session_state.dados_cliente = dados
        st.success("Cliente localizado!")

if st.session_state.dados_cliente:
    d = st.session_state.dados_cliente
    endereco = f'{d["logradouro"]}, {d["numero"]} - {d["bairro"]} | {d["municipio"]}/{d["uf"]} - CEP {d["cep"]}'
    st.text_input("Razão Social", d["razao"], disabled=True)
    st.text_area("Endereço", endereco, disabled=True)

st.markdown("""
<style>
.card-produto {
    border: 1px solid #e6e6e6;
    border-left: 6px solid #4CAF50;
    padding: 12px 12px 6px 12px;
    border-radius: 8px;
    margin-bottom: 10px;
    background-color: #ffffff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)


# Adicione ou expanda o st.markdown existente:
st.markdown("""
<style>
.stTextInput input {
    border: 2px solid #4CAF50 !important;  /* Borda verde para destacar */
    border-radius: 5px !important;
}
.stButton button {
    background-color: #4CAF50 !important;  /* Verde para o botão */
    color: white !important;
    border: none !important;
    border-radius: 5px !important;
}
</style>
""", unsafe_allow_html=True)

# Adicione:
st.markdown("""
<style>
.stButton button {
    background-color: #4CAF50 !important;  /* Verde */
    color: white !important;
    border: none !important;
    border-radius: 5px !important;
}
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📦 PRODUTOS", "🧾 PEDIDOS-CARRINHO", "⚙️ FINALIZAÇÃO"])

# Mapa de produtos já adicionados
carrinho_map = {item["codigo"]: item for item in st.session_state.carrinho}

with tab1:
    # =====================================================
    # PRODUTOS
    # =====================================================
    st.header("📦 PRODUTOS")
    busca = st.text_input("Pesquisar por código ou descrição", key=f"busca_{rc}")

    df_filtrado = df_produtos[
        df_produtos["descricao"].str.contains(busca, case=False, na=False) |
        df_produtos["codigo"].str.contains(busca, case=False, na=False)
    ]

    # 🔥 MAPA DO CARRINHO
    carrinho_map = {item["codigo"]: item for item in st.session_state.carrinho}

    for _, row in df_filtrado.iterrows():

        codigo = row["codigo"]
        preco = row["preco"]

        # 🔎 Verifica se já está no carrinho
        ja_no_carrinho = codigo in carrinho_map

        # 🎨 Cor da lateral do card
        border_color = "#4CAF50" if ja_no_carrinho else "#e6e6e6"

        # 🟩 ABRE O CARD (APENAS UMA VEZ)
        st.markdown(f"""
        <div style="
            border:1px solid #e6e6e6;
            border-left:6px solid {border_color};
            padding:12px;
            border-radius:8px;
            margin-bottom:10px;
            background:white;">
        """, unsafe_allow_html=True)

        # 📦 COLUNAS
        c1, c2, c3, c4, c5 = st.columns([1,3,2,2,2])

        c1.write(codigo)
        c2.write(row["descricao"])
        c3.write(f'R$ {preco:.2f}')

        qtd = c4.number_input("Qtd", value=1, min_value=1, step=1, key=f"qtd_{codigo}_{rc}")

        # 🔘 BOTÃO ADICIONAR
        if c5.button("Adicionar ➕", key=f"add_{codigo}"):
            if ja_no_carrinho:
                idx = next(i for i, item in enumerate(st.session_state.carrinho) if item["codigo"] == codigo)
                st.session_state.carrinho[idx]["qtd"] += qtd
                st.session_state.carrinho[idx]["total"] = st.session_state.carrinho[idx]["qtd"] * preco
                st.success("Quantidade somada ao produto!")
            else:
                st.session_state.carrinho.append({
                    "codigo": codigo,
                    "descricao": row["descricao"],
                    "qtd": qtd,
                    "preco": preco,
                    "total": qtd * preco
                })
                st.success("Produto adicionado ao pedido!")

            st.rerun()

        # 🟢 MOSTRA QUANTIDADE SE JÁ ESTIVER NO PEDIDO
        if ja_no_carrinho:
            qtd_total = carrinho_map[codigo]["qtd"]
            c5.markdown(f"✅ **No Pedido: {qtd_total}**")

        # ❌ FECHA O CARD
        st.markdown("</div>", unsafe_allow_html=True)


with tab2:
    # =====================================================
    # PEDIDO
    # =====================================================
    st.header("🧾 PEDIDOS-CARRINHO")

    if st.session_state.carrinho and st.session_state.dados_cliente:
        df_carrinho = pd.DataFrame(st.session_state.carrinho)
        total_pedido = df_carrinho["total"].sum()

        st.subheader("Itens no Pedido")
        for i, item in enumerate(st.session_state.carrinho):
            st.markdown('<div class="card-produto">', unsafe_allow_html=True)
            col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 2, 2, 2, 2])
            col1.write(item["codigo"])
            col2.write(item["descricao"])
            col3.write(f'R$ {item["preco"]:.2f}')
            
            # Alterar quantidade
            nova_qtd = col4.number_input("Qtd", value=item["qtd"], min_value=1, step=1, key=f"edit_qtd_{i}_{st.session_state.reset_counter}")
            if col5.button("Atualizar Qtd", key=f"update_{i}"):
                st.session_state.carrinho[i]["qtd"] = nova_qtd
                st.session_state.carrinho[i]["total"] = nova_qtd * item["preco"]
                st.success("Quantidade atualizada!")
                st.rerun()
            
            # Remover produto
            if col6.button("Remover", key=f"remove_{i}"):
                del st.session_state.carrinho[i]
                st.success("Produto removido!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        # Após a lista interativa, adicione:
        df_carrinho = pd.DataFrame(st.session_state.carrinho)
        total_pedido = df_carrinho["total"].sum() if not df_carrinho.empty else 0     

        st.subheader(f"💰 TOTAL: R$ {total_pedido:,.2f}")

with tab3:
    st.header("⚙️ FINALIZAÇÃO")

    if not st.session_state.carrinho or not st.session_state.dados_cliente:
        st.info("É necessário cliente e produtos para finalizar.")
        st.stop()

    # 🔥 CRIA AQUI (resolve o erro)
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    total_pedido = df_carrinho["total"].sum()
    condicao_pagamento = st.session_state.get("cond_pag", "")
    observacoes = st.session_state.get("obs_pedido", "")

    # =========================
    # CAMPOS DA FINALIZAÇÃO
    # =========================
    condicao_pagamento = st.selectbox(
        "Condição de Pagamento",
        ["À Vista - PIX", "30% Adto + 30 dias", "30% Adto + 30/60", "30% Adto + 30/60/90", "Outro"],
        key="cond_pag"
    )

    observacoes = st.text_area(
        "Observações do Pedido",
        key="obs_pedido"
    )


    # CSV com colunas Código;descrição,qtde,preco e nome CNPJ-data
    data_atual = datetime.now().strftime("%Y%m%d")
    nome_csv = f"{cnpj}-{data_atual}.csv"
    csv_buffer = StringIO()
    df_carrinho[["codigo", "descricao", "qtd", "preco"]].to_csv(csv_buffer, sep=";", index=False)
    csv_content = csv_buffer.getvalue()
    st.download_button("📥 Baixar CSV", csv_content, nome_csv, mime="text/csv")

    # Função para gerar PDF
    def gerar_pdf(dados_cliente, carrinho, total, cond_pag, obs, cnpj, telefone, email, ie):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Cabeçalho
        pdf.cell(200, 10, txt="PEDIDO ZIONNE - FEIRA ABUP", ln=True, align='C')
        pdf.ln(10)
        
        # Dados do Cliente
        pdf.cell(200, 10, txt=f"Cliente: {dados_cliente['razao']}", ln=True)
        pdf.cell(200, 10, txt=f"CNPJ: {cnpj}", ln=True)
        pdf.cell(200, 10, txt=f"Telefone: {telefone}", ln=True)
        pdf.cell(200, 10, txt=f"E-mail: {email}", ln=True)
        pdf.cell(200, 10, txt=f"Inscrição Estadual: {ie}", ln=True)
        endereco = f"{dados_cliente['logradouro']}, {dados_cliente['numero']} - {dados_cliente['bairro']} | {dados_cliente['municipio']}/{dados_cliente['uf']} - CEP {dados_cliente['cep']}"
        pdf.multi_cell(200, 10, txt=f"Endereço: {endereco}")
        pdf.ln(5)
        
        # Condição de Pagamento e Observações
        pdf.cell(200, 10, txt=f"Condição de Pagamento: {cond_pag}", ln=True)
        pdf.multi_cell(200, 10, txt=f"Observações: {obs}")
        pdf.ln(5)
        
        # Produtos
        pdf.cell(200, 10, txt="Produtos:", ln=True)
        for item in carrinho:
            pdf.cell(200, 10, txt=f"{item['codigo']} - {item['descricao']} - Qtde: {item['qtd']} - Preço: R$ {item['preco']:.2f} - Total: R$ {item['total']:.2f}", ln=True)
        pdf.ln(5)
        
        # Total
        pdf.cell(200, 10, txt=f"TOTAL: R$ {total:.2f}", ln=True)
        
        return pdf.output(dest='S').encode('latin1')

    # Gerar PDF
    pdf_bytes = gerar_pdf(st.session_state.dados_cliente, st.session_state.carrinho, total_pedido, condicao_pagamento, observacoes, cnpj, telefone, email, ie)
    nome_pdf = f"pedido_{cnpj}-{data_atual}.pdf"
    st.download_button("📄 Baixar PDF", pdf_bytes, nome_pdf, mime="application/pdf")

    # =====================================================
    # WHATSAPP
    # =====================================================
    d = st.session_state.dados_cliente
    telefone_limpo = re.sub(r'\D', '', telefone)
    telefone_zionne_limpo = re.sub(r'\D', '', telefone_zionne)

    # Mensagem para o cliente (formatada)
    mensagem_cliente = f"""*PEDIDO ZIONNE - FEIRA ABUP*

Cliente: {d["razao"]}
CNPJ: {cnpj}
Telefone: {telefone}
E-mail: {email}
Inscrição Estadual: {ie}

Endereço: {d["logradouro"]}, {d["numero"]} - {d["bairro"]} | {d["municipio"]}/{d["uf"]} - CEP {d["cep"]}

Condição de Pagamento: {condicao_pagamento}
Observações: {observacoes}

#--Codigo -----Descrição ------------------------------ Qtde ----Valor ---#
"""

    for item in st.session_state.carrinho:
        mensagem_cliente += f'{item["codigo"]:>6}   {item["descricao"][:35]:<35}   {item["qtd"]}x   R$ {item["preco"]:.2f}\n'

    mensagem_cliente += f"\nTOTAL: R$ {total_pedido:.2f}"

    # Mensagem para Zionne (inclui o conteúdo do CSV)
    mensagem_zionne = f"""*PEDIDO ZIONNE - FEIRA ABUP*

Cliente: {d["razao"]}
CNPJ: {cnpj}
Telefone: {telefone}
E-mail: {email}
Inscrição Estadual: {ie}

Endereço: {d["logradouro"]}, {d["numero"]} - {d["bairro"]} | {d["municipio"]}/{d["uf"]} - CEP {d["cep"]}

Condição de Pagamento: {condicao_pagamento}
Observações: {observacoes}

Produtos:
"""
    for item in st.session_state.carrinho:
        mensagem_zionne += f'{item["codigo"]} - {item["descricao"]} - Qtde: {item["qtd"]} - Preço: R$ {item["preco"]:.2f}\n'

    mensagem_zionne += f"\nTOTAL: R$ {total_pedido:.2f}\n\nCSV:\n{csv_content}"

    # Link para o cliente
    link_cliente = f"https://wa.me/55{telefone_limpo}?text={quote(mensagem_cliente)}"
    st.link_button("📲 Enviar Pedido para Cliente no WhatsApp", link_cliente)

    # Link para Zionne
    if telefone_zionne_limpo:
        link_zionne = f"https://wa.me/55{telefone_zionne_limpo}?text={quote(mensagem_zionne)}"
        st.link_button("📲 Enviar Pedido para Zionne no WhatsApp", link_zionne)
    else:
        st.warning("Informe o Telefone WhatsApp Zionne para enviar.")

    st.info("Para enviar o PDF como anexo, baixe o arquivo e anexe manualmente no WhatsApp. O CSV é enviado como texto na mensagem para Zionne.")



