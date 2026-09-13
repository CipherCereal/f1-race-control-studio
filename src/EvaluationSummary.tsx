type Props={evaluation:any};
const pct=(value:any)=>typeof value==='number'?`${(value*100).toFixed(1)}%`:'Unavailable';
export default function EvaluationSummary({evaluation}:Props){
 const comparison=evaluation['baseline-comparison'];
 const wheel=evaluation['wheel-evaluation'];
 const steering=evaluation['steering-evaluation'];
 return <><div className="panel-title">Measured results <span className="pill">DIAGNOSTIC VALIDATION</span></div>
 <div className="table-scroll"><table><thead><tr><th>Detector</th><th>Precision</th><th>Recall</th><th>Evaluation scope</th></tr></thead><tbody>{Object.entries(comparison?.results||{}).map(([name,m]:[string,any])=><tr key={name}><td>{name==='yolo11n.pt'?'Pretrained baseline':'Trained F1 detector'}</td><td>{pct(m.precision)}</td><td>{pct(m.recall)}</td><td>{m.images} images · confidence {m.confidence_threshold} · IoU {m.iou_threshold}</td></tr>)}</tbody></table></div>
 <p className="explain">One broadcast, split chronologically. These measurements do not establish performance on new circuits, camera types or speeds.</p>
 <div className="table-scroll"><table><thead><tr><th>Component</th><th>Result</th><th>What this establishes</th></tr></thead><tbody>
 <tr><td>Wheel masks</td><td>{pct(wheel?.metrics?.['metrics/recall(M)'])} recall</td><td>{wheel?.validation_images||0} road-car validation images. No F1 accuracy established.</td></tr>
 <tr><td>Steering wheel</td><td>{steering?.validation_mae_degrees?.toFixed(2)||'—'}° MAE</td><td>Steering-wheel rotation, not tire angle. Independent testing pending.</td></tr>
 <tr><td>Track limits</td><td>Not evaluated</td><td>Reviewed boundaries and four-wheel contact truth are missing.</td></tr>
 </tbody></table></div></>;
}
