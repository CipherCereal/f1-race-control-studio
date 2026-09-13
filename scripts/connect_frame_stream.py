from pathlib import Path
p=Path(__file__).resolve().parents[1]/'src/Studio.tsx';s=p.read_text(encoding='utf-8')
s="import {useFrameResults} from './useFrameResults';\n"+s
s=s.replace(",[result,setResult]=useState<any>({})",'')
a=s.index(' useEffect(()=>{let active=true;if(job)api(');b=s.index('\n',a);s=s[:a]+s[b:]
needle=" const refresh=()=>"
s=s.replace(needle," const result=useFrameResults(video,job?.id,asset?.fps||25,asset?.frames||1,time,job?.status);\n"+needle)
p.write_text(s,encoding='utf-8')
