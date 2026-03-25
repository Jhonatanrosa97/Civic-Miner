import os
import pandas as pd
from datetime import datetime

def salvar_resultado(cidade, fornecedor, dados):
    if not dados:
        print(f"Nenhum contrato encontrado para {cidade}")
        return

    os.makedirs("data", exist_ok=True)

    df = pd.DataFrame({"contratos": dados})
    arquivo = f"data/contratos_{cidade}_{fornecedor}_{datetime.now().date()}.csv"
    df.to_csv(arquivo, index=False, encoding="utf-8")
    print(f"Salvo em: {arquivo}")
