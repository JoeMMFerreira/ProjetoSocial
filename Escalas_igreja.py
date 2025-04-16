import random
from collections import defaultdict
import streamlit as st
from datetime import datetime, timedelta

# Configuração inicial
st.set_page_config(page_title="Escala de Serviço Igreja", layout="wide")
st.title("📅 Sistema de Escala de Serviço - Padrão Dom/Terça")

# Dados dos membros
homens_estacionamento = ["Renan", "Rafael", "Beri", "Wesley", "Diego", "Jhon", "Thiago"]
homens_altar = ["Wanderlei", "Renan", "Beri", "Diego", "Jhon", "Thiago", "Júlio", "Wesley", "Rafael"]
mulheres_recepcao = ["Monique", "Risalva", "Ednéia", "Cláudia", "Elaine", "Nicole", "Sara", "Mari", "Meire"]
mulheres_altar = ["Priscila", "Marlene", "Fafá", "Amanda", "Rejane"]

# Dicionário de casais (chave: marido; valor: esposa)
casais = {
    "Renan": "Monique",
    "Beri": "Cláudia",    # Certifique-se de que o nome esteja presente em mulheres_recepcao
    "Júlio": "Elaine",
    "Thiago": "Meire",
    "Wanderlei": "Priscila",
    "Jhon": "Nicole",
}

# Juntando todos para histórico
pessoas_altar = homens_altar + mulheres_altar
pessoas_estacionamento = homens_estacionamento
pessoas_recepcao = mulheres_recepcao

# Histórico de serviços e dicionário de indisponibilidade
historico = defaultdict(list)
escala_gerada = []
indisponibilidade = defaultdict(list)  # Exemplo: {"Renan": ["13/04", "20/04"], "Monique": ["13/04"]}

##############################################
# Cadastro de Indisponibilidade (Sidebar)    #
##############################################
st.sidebar.header("Cadastro de Indisponibilidade")
with st.sidebar.form(key="form_indisponibilidade"):
    nome_indisp = st.text_input("Nome do Membro:")
    data_indisp = st.text_input("Data de indisponibilidade (DD/MM):", help="Informe a data no formato DD/MM")
    submit_indisp = st.form_submit_button("Adicionar Indisponibilidade")
    
    if submit_indisp:
        if nome_indisp and data_indisp:
            if data_indisp not in indisponibilidade[nome_indisp]:
                indisponibilidade[nome_indisp].append(data_indisp)
            st.success(f"Indisponibilidade cadastrada para {nome_indisp} no dia {data_indisp}.")
        else:
            st.error("Preencha os campos corretamente.")

##############################################
# Função para Verificar Disponibilidade      #
##############################################
def esta_disponivel(nome, data_str):
    """
    Retorna True se o membro estiver disponível na data (formato DD/MM).
    Se a data constar na lista de indisponibilidade do membro, retorna False.
    Se não houver cadastro para esse membro, assume disponível.
    """
    if nome in indisponibilidade and indisponibilidade[nome]:
        return data_str not in indisponibilidade[nome]
    return True

##############################################
# Função para Atribuição dos Serviços        #
##############################################
def atribuir_servicos(dia_escala, data_str):
    # Seleciona candidatos disponíveis, filtrando pela indisponibilidade:
    available_altar = [p for p in pessoas_altar if esta_disponivel(p, data_str)]
    available_estac = [p for p in homens_estacionamento if esta_disponivel(p, data_str)]
    available_recep = [p for p in mulheres_recepcao if esta_disponivel(p, data_str)]
    
    # Seleção independente para cada função:
    if available_altar:
        dia_escala["Altar"] = random.sample(available_altar, 1)
    else:
        dia_escala["Altar"] = []
        
    if len(available_estac) >= 2:
        dia_escala["Estacionamento"] = random.sample(available_estac, 2)
    else:
        dia_escala["Estacionamento"] = available_estac.copy()
        
    if len(available_recep) >= 2:
        dia_escala["Recepção"] = random.sample(available_recep, 2)
    else:
        dia_escala["Recepção"] = available_recep.copy()
        
    # Atualiza o histórico dos selecionados
    for pessoa in dia_escala["Altar"] + dia_escala["Estacionamento"] + dia_escala["Recepção"]:
        historico[pessoa].append(data_str)

##############################################
# Função para Gerar a Escala                 #
##############################################
def gerar_escala(data_inicio, num_semanas):
    escala = {}
    try:
        data = datetime.strptime(data_inicio, "%d/%m/%Y")
    except ValueError:
        st.error("Formato de data inválido. Use DD/MM/AAAA")
        return {}
    
    # Garantir que começamos num domingo
    while data.strftime("%A") != "Sunday":
        data += timedelta(days=1)
    
    for semana in range(num_semanas):
        # DOMINGO
        data_dom = data
        data_str_dom = data_dom.strftime("%d/%m")
        
        escala_dom = {
            "Dia": f"{data_str_dom}: DOMINGO",
            "Altar": [],
            "Estacionamento": [],
            "Recepção": []
        }
        atribuir_servicos(escala_dom, data_str_dom)
        escala[data_str_dom] = escala_dom
        
        # TERÇA-FEIRA (2 dias depois)
        data_ter = data_dom + timedelta(days=2)
        data_str_ter = data_ter.strftime("%d/%m")
        
        # A escala de terça herda Estacionamento e Recepção do domingo e
        # escolhe um altar diferente dentre os disponíveis (para variar a atuação no altar)
        escala_ter = {
            "Dia": f"{data_str_ter}: TERÇA-FEIRA",
            "Altar": [],
            "Estacionamento": escala_dom["Estacionamento"].copy(),
            "Recepção": escala_dom["Recepção"].copy()
        }
        
        available_alt_ter = [p for p in pessoas_altar if (p not in escala_dom["Altar"] and esta_disponivel(p, data_str_ter))]
        if available_alt_ter:
            escala_ter["Altar"] = random.sample(available_alt_ter, 1)
            historico[escala_ter["Altar"][0]].append(data_str_ter)
        
        escala[data_str_ter] = escala_ter
        
        # Avançar para o próximo domingo (5 dias depois da terça)
        data = data_ter + timedelta(days=5)
    
    return escala

##############################################
# Interface para Geração da Escala           #
##############################################
st.sidebar.header("Configurações para Escala")
data_inicio = st.sidebar.text_input("Data de início (DD/MM/AAAA):", "13/04/2025")
num_semanas = st.sidebar.number_input("Número de semanas:", 1, 52, 4)

if st.sidebar.button("Gerar Escala"):
    # Resetar histórico para nova geração
    historico.clear()
    escala = gerar_escala(data_inicio, num_semanas)
    
    if escala:
        st.success("Escala gerada com sucesso!")
        texto_escala = ""
        datas_ordenadas = sorted(escala.keys(), key=lambda x: datetime.strptime(x, "%d/%m"))
        
        for data in datas_ordenadas:
            servicos = escala[data]
            texto_escala += f"{servicos['Dia']}\n- Altar: {', '.join(servicos['Altar'])}\n"
            texto_escala += f"- Estacionamento: {', '.join(servicos['Estacionamento'])}\n"
            texto_escala += f"- Recepção: {', '.join(servicos['Recepção'])}\n\n"
            
            # Verifica se algum casal foi formado:
            # Para cada entrada no dicionário de casais, se o marido está presente (em altar ou estacionamento)
            # e a esposa na recepção, marcamos como 'Casal + Mulher'
            casal_presente = any(
                (h in servicos["Altar"] or h in servicos["Estacionamento"]) and (casais[h] in servicos["Recepção"])
                for h in casais
            )
            
            tipo = "Casal + Mulher" if casal_presente else "Sem casal completo"
            
            st.subheader(servicos["Dia"])
            st.write(f"- Altar: {', '.join(servicos['Altar'])}")
            st.write(f"- Estacionamento: {', '.join(servicos['Estacionamento'])}")
            st.write(f"- Recepção: {', '.join(servicos['Recepção'])}")
            st.write(f"**Tipo:** {tipo}")
            st.write("---")
        
        st.download_button(
            "Baixar Escala Completa",
            texto_escala,
            file_name=f"escala_igreja_{data_inicio.replace('/', '-')}.txt"
        )

st.markdown("""
### Regras Implementadas:
1. **Seleção Independente:** Cada função (Altar, Estacionamento e Recepção) é preenchida com uma seleção aleatória dos disponíveis, sem preferência explícita para casais.
2. **Formação de Casal (Acidental):** Se na escala o marido (presente no Altar ou Estacionamento) e sua esposa (na Recepção) forem sorteados, o sistema reconhece isso e indica o tipo "Casal + Mulher".
3. **Sem Casal Completo:** Caso não haja um casal formado na escala, o tipo exibido será "Sem casal completo".
4. **Indisponibilidade:** Datas cadastradas são desconsideradas para a escala.
5. **Padrão Dom/Terça:** As escalas para domingo e terça compartilham as funções de Estacionamento e Recepção, variando apenas o Altar na terça.
""")
