import test from 'node:test';import assert from 'node:assert/strict';
import {nearestSample,targetTime} from '../src/telemetrySync.mjs';
const data={session:{session_key:1},lap:{date_start:'2024-01-01T00:00:00Z',lap_duration:90}};
const alignment={asset_id:'a',session_key:1,video_lap_start:5};
test('video time maps to lap UTC',()=>assert.equal(targetTime(data,'a',15,alignment),Date.parse(data.lap.date_start)+10000));
test('other footage and outside lap have no synchronized sample',()=>{assert.equal(targetTime(data,'b',15,alignment),null);assert.equal(targetTime(data,'a',1,alignment),null);assert.equal(targetTime(data,'a',100,alignment),null)});
test('large telemetry gaps are not filled',()=>assert.equal(nearestSample([{date:data.lap.date_start}],Date.parse(data.lap.date_start)+2000),null));
