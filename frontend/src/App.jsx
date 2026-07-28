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
