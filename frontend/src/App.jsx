import React, { useState } from 'react'

const brl = (v) => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export default function App() {
  const [form, setForm] = useState({
    admissao: '2020-01-15',
    demissao: '2025-06-20',
    salario: '3000.00',
    motivo: 'sem_justa_causa',
    aviso_cumprido: false,
    ferias_vencidas: false,
    dependentes: 0,
    saldo_fgts_depositado: '0',
  })
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)

  const upd = (k) => (e) => setForm({ ...form, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    const r = await fetch('/calc/rescisao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    setRes(await r.json())
    setLoading(false)
  }

  return (
    <div style={{ fontFamily: 'system-ui', maxWidth: 900, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>PJeCalc Web</h1>
      <p style={{ color: '#666' }}>Cálculo de verbas rescisórias — MVP</p>

      <form onSubmit={submit} style={{ display: 'grid', gap: '.75rem', gridTemplateColumns: '1fr 1fr' }}>
        <label>Admissão<input type="date" value={form.admissao} onChange={upd('admissao')} /></label>
        <label>Demissão<input type="date" value={form.demissao} onChange={upd('demissao')} /></label>
        <label>Salário (R$)<input type="number" step="0.01" value={form.salario} onChange={upd('salario')} /></label>
        <label>Motivo
          <select value={form.motivo} onChange={upd('motivo')}>
            <option value="sem_justa_causa">Dispensa sem justa causa</option>
            <option value="pedido_demissao">Pedido de demissão</option>
            <option value="justa_causa">Justa causa</option>
            <option value="acordo_484a">Acordo (art. 484-A)</option>
          </select>
        </label>
        <label>Dependentes<input type="number" min="0" value={form.dependentes} onChange={upd('dependentes')} /></label>
        <label>Saldo FGTS já depositado (R$)<input type="number" step="0.01" value={form.saldo_fgts_depositado} onChange={upd('saldo_fgts_depositado')} /></label>
        <label><input type="checkbox" checked={form.aviso_cumprido} onChange={upd('aviso_cumprido')} /> Aviso prévio cumprido (trabalhado)</label>
        <label><input type="checkbox" checked={form.ferias_vencidas} onChange={upd('ferias_vencidas')} /> Tem férias vencidas</label>
        <button type="submit" disabled={loading} style={{ gridColumn: '1 / -1', padding: '.75rem' }}>
          {loading ? 'Calculando…' : 'Calcular'}
        </button>
      </form>

      <SentencaUpload />

      {res && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Memória de cálculo</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr><th align="left">Verba</th><th align="left">Detalhe</th><th align="right">Valor</th></tr></thead>
            <tbody>
              {res.verbas.map((v, i) => (
                <tr key={i}><td>{v.nome}</td><td style={{ color: '#666' }}>{v.detalhe}</td><td align="right">{brl(v.valor)}</td></tr>
              ))}
              <tr><td colSpan="2">FGTS rescisório (8%)</td><td align="right">{brl(res.fgts_rescisorio)}</td></tr>
              <tr><td colSpan="2">Multa FGTS</td><td align="right">{brl(res.multa_fgts)}</td></tr>
              <tr><td colSpan="2">(-) INSS</td><td align="right">-{brl(res.inss)}</td></tr>
              <tr><td colSpan="2">(-) IRRF</td><td align="right">-{brl(res.irrf)}</td></tr>
              <tr style={{ fontWeight: 'bold', borderTop: '2px solid #333' }}>
                <td colSpan="2">LÍQUIDO</td><td align="right">{brl(res.liquido)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function SentencaUpload() {
  const [texto, setTexto] = useState('')
  const [arquivo, setArquivo] = useState(null)
  const [msg, setMsg] = useState('')
  const [lista, setLista] = useState([])

  const refresh = async () => setLista(await (await fetch('/sentencas')).json())
  React.useEffect(() => { refresh() }, [])

  const enviarArquivo = async (e) => {
    e.preventDefault()
    if (!arquivo) return
    const fd = new FormData(); fd.append('arquivo', arquivo)
    const r = await fetch('/sentencas/upload', { method: 'POST', body: fd })
    const j = await r.json()
    setMsg(`Sentença #${j.id} salva (${j.tamanho_texto} caracteres extraídos)`)
    setArquivo(null); refresh()
  }
  const enviarTexto = async () => {
    if (!texto.trim()) return
    const fd = new FormData(); fd.append('texto', texto)
    const r = await fetch('/sentencas/texto', { method: 'POST', body: fd })
    const j = await r.json()
    setMsg(`Sentença #${j.id} salva`)
    setTexto(''); refresh()
  }

  return (
    <div style={{ marginTop: '2rem', padding: '1rem', border: '1px solid #ddd', borderRadius: 6 }}>
      <h2>Sentença</h2>
      <form onSubmit={enviarArquivo} style={{ marginBottom: '1rem' }}>
        <label>Upload de PDF/DOCX/TXT: </label>
        <input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setArquivo(e.target.files[0])} />
        <button type="submit" disabled={!arquivo}>Enviar arquivo</button>
      </form>
      <div>
        <label>...ou cole o texto:</label>
        <textarea value={texto} onChange={(e) => setTexto(e.target.value)} rows={6} style={{ width: '100%' }} />
        <button onClick={enviarTexto} disabled={!texto.trim()}>Salvar texto</button>
      </div>
      {msg && <p style={{ color: 'green' }}>{msg}</p>}
      {lista.length > 0 && (
        <>
          <h3>Sentenças salvas</h3>
          <ul>{lista.map(s => <li key={s.id}>#{s.id} — {s.criado_em} — {s.nome_original || 'texto colado'}</li>)}</ul>
        </>
      )}
    </div>
  )
}
