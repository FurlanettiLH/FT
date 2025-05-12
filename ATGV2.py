# O programa a seguir tem o intuito de autiomatizar a tarefa de criar diagramas unifilares 
# Autor: Luiz Furlanetti 
# Versão: 1.0.7# parte unifilar totalmente pronta, faz todo o desenho a partir de um csv por leitura do pandas
# melhorias necessarias carimbo e multifilar, sugestão 
# Para execução basta ter python instalado na maquina e executar o arquivo .bat com nome similar ao .py contido aqui 
# Se julgar necessario posso tambem colocar na internet ai funciona a aprtir de um URL pela nuvem do streamlit cloud 
import streamlit as st
import pandas as pd
import ezdxf
import tempfile

st.set_page_config(page_title="DIAGRAMA UNIFILAR", layout="wide", page_icon="⚡")
st.title("📐 Gerador de Diagrama Unifilar")

# === SIDEBAR ===
st.sidebar.title("Configurações do Projeto")
template_file = st.sidebar.file_uploader("📁 Envie o arquivo BASE.B.dxf", type=["dxf"])
nome_arquivo = st.sidebar.text_input("📄 Nome do arquivo", value="TIPO-OBRA-DEPARTAMENTO-NUMERO-VERSÃO")
nome_painel = st.sidebar.text_input("📄 Nome do painel", value="QDF-01")
nome_barramento = st.sidebar.text_input("📄 Informação do barramento", value="2Ø -220 - 60Hz  - In = 50A")
planilha = st.sidebar.file_uploader("📄 Planilha de Cargas (.xlsx)", type=["xlsx"], key="excel_sidebar")
st.sidebar.image(r'U:\Profissionais\LUIZ FURLANETTI\PROG\32443B9A-0511-49A5-BBA6-4B5C0A836BA8.PNG', 
                 caption=None, 
                 width=None, 
                 use_column_width=None, 
                 clamp=False, 
                 channels="RGB", 
                 output_format="auto",
                 use_container_width=False)
if planilha:
    df_temp = pd.read_excel(planilha)
    col_tag_temp = df_temp.columns[0]
    tags_temp = (
        df_temp[col_tag_temp]
        .dropna()
        .loc[~df_temp[col_tag_temp].astype(str).str.upper().isin([col_tag_temp.upper()])]
        .tolist()
    )
    num_cargas = len(tags_temp)
    st.sidebar.success(f"✅ {num_cargas} cargas detectadas na planilha.")
else:
    num_cargas = st.sidebar.number_input("🔢 Número de Cargas", min_value=1, value=3)

gerar_dxf = st.sidebar.button("Gerar e Baixar DXF")

# === TABS ===
tab1, tab2, tab3 = st.tabs(["ENTRADA", "CARGAS", "MULTIFILAR"])

# === TAB 1: ENTRADA ===
with tab1:
    st.subheader("🔲 ALIMENTAÇÃO DO PAINEL")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Condutores de entrada")
        origem = st.text_input("🔌 ORIGEM", value="Painel Principal")
        # Parâmetros do barramento e circuito
        # 'nome_barramento' vem do sidebar
        tag_barr = st.text_input("🏷️ TAG-DO-CIRCUITO", value="CIR-01")
        f_info = st.text_input("🔌 F_INFO", value="3x35mm²")
        t_info = st.text_input("🔌 T_INFO", value="3x35mm²")
        n_info = st.text_input("🔌 N_INFO", value="3x35mm²")
    with col2:
        st.subheader("Disjuntor principal")
        tipo_entr = st.text_input("🎚️ TIPO", value="C")
        corrente_entr = st.text_input("⚡ CORRENTE DE ABERTURA DO DISJUNTOR", value="10kA")
        fases_entr = st.text_input("⚡ FASES", value="3F+N")
        ik_entr = st.text_input("⚡ IK", value="25kA")
    atributos_entrada = {
        "ORIGEM": origem,
        "INFORMACAO_BARRAMENTO": nome_barramento,
        "TAG-DO-CIRCUITO": tag_barr,
        "F_INFO": f_info,
        "T_INFO": t_info,
        "N_INFO": n_info,
        "TIPO": tipo_entr,
        "CORRENTE_DE_RUPTURA": corrente_entr,
        "FASES": fases_entr,
        "IK": ik_entr,
    }
    OBS = {
        "ORIGEM_M": "ORIGEM",
        "RF_INFO": "F_INFO",
        "SF_INFO": "F_INFO",
        "TF_INFO": "F_INFO",
        "NE_INFO": "N_INFO",
        "PE_INFO": "T_INFO",
        "CORRENTE_DE_ABERTURA": "CORRENTE_DE_RUPTURA"
    }

# === TAB 2: CARGAS ===
dados_cargas = []
with tab2:
    st.subheader("🔧 Dados das Cargas (planilha + manual)")

    if planilha:
        df_raw = pd.read_excel(planilha, header=0)

        col_tag = df_raw.columns[0]
        tags = (
            df_raw[col_tag]
            .dropna()
            .loc[~df_raw[col_tag].astype(str).str.upper().isin([col_tag.upper()])]
            .tolist()
        )

        col_dest = next(c for c in df_raw.columns if "DESCRIÇÃO" in c.upper())
        destinos = df_raw[col_dest].dropna().tolist()

        col_idisj = next(c for c in df_raw.columns if "IDISJ" in c.upper())
        correntes = (
            df_raw[col_idisj]
            .dropna()
            .astype(str)
            .apply(lambda x: x if x.upper().endswith("A") else x + "A")
            .tolist()
        )

        df_base = pd.DataFrame({
            "TAG_DO_CIRCUITO": tags[:num_cargas],
            "DESTINO": destinos[:num_cargas],
            "CORRENTE_DE_RUPTURA": correntes[:num_cargas],
            "FASES": [""] * num_cargas,
            "IK": [""] * num_cargas,
            "CONDUTOR_INFO": [""] * num_cargas,
        })

        df_editado = st.data_editor(df_base, use_container_width=True, num_rows="fixed")
        dados_cargas = df_editado.to_dict("records")
    else:
        for i in range(num_cargas):
            with st.expander(f"Carga {i+1}"):
                tipo = st.text_input("🎚️ TIPO", key=f"tipo_{i}")
                corrente = st.text_input("⚡ CORRENTE_DE_RUPTURA", key=f"corrente_{i}")
                fases = st.text_input("⚡ FASES", key=f"fases_{i}")
                ik = st.text_input("⚡ IK", key=f"ik_{i}")
                condutor = st.text_input("🔌 CONDUTOR_INFO", key=f"condutor_{i}")
                tag = st.text_input("🏷️ TAG_DO_CIRCUITO", key=f"tag_{i}")
                destino = st.text_input("📍 DESTINO", key=f"destino_{i}")
                dados_cargas.append({
                    "TIPO": tipo,
                    "CORRENTE_DE_RUPTURA": corrente,
                    "FASES": fases,
                    "IK": ik,
                    "CONDUTOR_INFO": condutor,
                    "TAG_DO_CIRCUITO": tag,
                    "DESTINO": destino
                })

# === TAB 3: MULTIFILAR ===
with tab3:
    st.subheader("📑 Diagrama Multifilar")
    st.text("Seção em desenvolvimento ---- cria apenas o bloco central")
    tem_multifilar = st.checkbox("✔️ Incluir bloco C_MULT no projeto")

# === GERAÇÃO DE DXF FINAL ===
if gerar_dxf:
    if not template_file:
        st.error("❌ Envie o XREF.dxf com os blocos.")
    else:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
                tmp.write(template_file.read())
                caminho_template = tmp.name

            doc = ezdxf.readfile(caminho_template)
            msp = doc.modelspace()

            # --- Setup de Linhas e Camadas ---
            if "PHANTOM2" not in doc.linetypes:
                doc.linetypes.load("PHANTOM2", dxfversion="R2010")
            if "BASICA 6" not in doc.layers:
                doc.layers.add("BASICA 6", linetype="PHANTOM2")

            # --- Cálculo de Espaçamento e Dimensões ---
            ESPACO = 21.6363
            margem_inicio = 10.0
            margem_final = 10.8671
            comprimento_total = (num_cargas - 1) * ESPACO + margem_inicio + margem_final

            # Barramento principal
            linha = msp.add_line((0, 0), (comprimento_total, 0), dxfattribs={
                "layer": "BASICA 6", "linetype": "CONTINUOUS", "lineweight": -1
            })
            linha.dxf.ltscale = 50.0

            # Retângulo perímetro original
            margem_x = 12.0; margem_y_topo = 43.0; margem_y_base = 70.0
            # Contorno externo reforçado
            extra_x = margem_x + 2.0
            extra_y_topo = margem_y_topo + 5.0
            extra_y_base = margem_y_base + 5.0
            contorno = msp.add_lwpolyline([
                (-extra_x, -extra_y_base),
                (comprimento_total + extra_x, -extra_y_base),
                (comprimento_total + extra_x, extra_y_topo),
                (-extra_x, extra_y_topo),
                (-extra_x, -extra_y_base)
            ], close=True, dxfattribs={
                "layer": "BASICA 6",
                "linetype": "PHANTOM2",
                "lineweight": -1
            })
            contorno.dxf.ltscale = 50.0

            # Textos identificadores
            texto1 = msp.add_text(f"{nome_barramento}", dxfattribs={"layer": "TEXTO 2", "linetype": "CONTINUOUS", "lineweight": -1, "color": 256})
            texto1.dxf.insert = (0, 0.8); texto1.dxf.height = 2
            texto2 = msp.add_text(f"{nome_painel}", dxfattribs={"layer": "TEXTO 2", "linetype": "CONTINUOUS", "lineweight": -1, "color": 256})
            texto2.dxf.insert = (-margem_x, margem_y_topo + 0.8); texto2.dxf.height = 2

            # Inserção de blocos
            entrada_x = comprimento_total / 2
            if "ENTRADA" in doc.blocks:
                ent_ref = msp.add_blockref("ENTRADA", insert=(entrada_x, 0))
                ent_ref.add_auto_attribs(atributos_entrada)

            for i, dados in enumerate(dados_cargas):
                x = margem_inicio + i * ESPACO
                carga_ref = msp.add_blockref("CARGA", insert=(x, 0))
                carga_ref.add_auto_attribs(dados)

            if tem_multifilar and "C_MULT" in doc.blocks:
                mult_x = comprimento_total + 60; mult_y = 56.6471
                mult_ref = msp.add_blockref("C_MULT", insert=(mult_x, mult_y))
                atributos_mult = {ch: atributos_entrada.get(v, v) for ch, v in OBS.items()}
                mult_ref.add_auto_attribs(atributos_mult)
                largura = 187; altura = (num_cargas/2)*23.04 + 55
                x0 = mult_x - 42; y0 = mult_y - altura
                rect = msp.add_lwpolyline([
                    (x0, mult_y-10), (x0+largura, mult_y-10),
                    (x0+largura, y0), (x0, y0), (x0, mult_y-10)
                ], close=True, dxfattribs={"layer":"BASICA 6","linetype":"PHANTOM2","lineweight":-1})
                rect.dxf.ltscale = 50.0

            # Salvar e download
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as out:
                doc.saveas(out.name)
                dxf_bytes = open(out.name, "rb").read()
            st.success("✅ DXF gerado com sucesso!")
            st.download_button("📥 Baixar DXF", data=dxf_bytes, file_name=f"{nome_arquivo}.dxf", mime="application/dxf")
        except Exception as e:
            st.error(f"❌ Erro ao gerar DXF: {e}")