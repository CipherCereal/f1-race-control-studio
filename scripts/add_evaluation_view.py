from pathlib import Path
p=Path(__file__).resolve().parents[1]/'src/Studio.tsx'
s=p.read_text(encoding='utf-8')
if "import EvaluationSummary" not in s:s="import EvaluationSummary from './EvaluationSummary';\n"+s
s=s.replace('<pre>{JSON.stringify(state.evaluation,null,2)}</pre>','<EvaluationSummary evaluation={state.evaluation}/><details><summary>Inspect full evaluation evidence</summary><pre>{JSON.stringify(state.evaluation,null,2)}</pre></details>')
p.write_text(s,encoding='utf-8')
