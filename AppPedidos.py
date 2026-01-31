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
# =====================================================
# PRODUTOS
# =====================================================
st.header("📦 Produtos")
busca = st.text_input("Pesquisar por código ou descrição", key=f"busca_{rc}")


df_filtrado = df_produtos[
    df_produtos["descricao"].str.contains(busca, case=False, na=False) |
    df_produtos["codigo"].str.contains(busca, case=False, na=False)
]

for _, row in df_filtrado.iterrows():
    c1, c2, c3, c4 = st.columns([1,3,2,2])
    c1.write(row["codigo"])
    c2.write(row["descricao"])
    c3.write(f'R$ {row["preco"]:.2f}')
    qtd = c4.number_input(
    "Qtd",
    value=1,
    min_value=1,
    step=1,
    key=f"qtd_{row['codigo']}_{rc}"
)


    if c4.button("Adicionar", key=f"add_{row['codigo']}"):
        st.session_state.carrinho.append({
            "codigo": row["codigo"],
            "descricao": row["descricao"],
            "qtd": qtd,
            "preco": row["preco"],
            "total": qtd * row["preco"]
        })
        st.success(f'{row["descricao"]} adicionado!')

# =====================================================
# PEDIDO
# =====================================================
st.header("🧾 Pedido")

if st.session_state.carrinho and st.session_state.dados_cliente:
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    total_pedido = df_carrinho["total"].sum()

    st.subheader("Itens no Pedido")
    for i, item in enumerate(st.session_state.carrinho):
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

    # Após a lista interativa, adicione:
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    total_pedido = df_carrinho["total"].sum() if not df_carrinho.empty else 0     

    st.subheader(f"💰 TOTAL: R$ {total_pedido:,.2f}")

    # Campos adicionais
    condicao_pagamento = st.text_input("Condição de Pagamento", key=f"cond_{rc}")
    observacoes = st.text_area("Observações", key=f"obs_{rc}")


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

elif not st.session_state.dados_cliente:
    st.info("Consulte um CNPJ para iniciar o pedido.")
else:
    st.info("Adicione produtos ao pedido.")