# PJeCalc Web

Sistema web de cálculos trabalhistas inspirado no PJe-Calc Cidadão do TRT.

## Stack

- **Backend:** Python 3.11+ / FastAPI
- **Frontend:** React + Vite
- **Cálculos:** módulo `backend/app/calc` (verbas rescisórias, tabelas fiscais)

## Estrutura

```
backend/
  app/
    main.py            # API FastAPI
    schemas.py         # modelos Pydantic (entrada/saída)
    calc/
      rescisao.py      # saldo salário, aviso, 13º, férias, FGTS+40%
      horas_extras.py  # cálculo de HE com adicional
      tabelas.py       # INSS e IRRF por competência
      indices.py       # atualização monetária (stub)
  requirements.txt
frontend/
  index.html
  package.json
  src/
    main.jsx
    App.jsx
```

## Rodar (dev)

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Roadmap

- **Fase 1 (atual):** verbas rescisórias básicas + tabelas INSS/IRRF 2025
- **Fase 2:** reflexos, adicionais (insalubridade/periculosidade/noturno), multas 467/477, honorários, atualização monetária + juros (TR/IPCA-E/SELIC)
- **Fase 3:** entrada por sentença (texto livre) → extração automática das verbas deferidas
