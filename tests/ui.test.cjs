// DOM contract checks for the shipped theme/menu/timer script; no external packages.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function element(){return {textContent:'',dataset:{},attrs:{},events:{},classList:{open:false,toggle(){return this.open=!this.open},remove(){this.open=false},contains(){return this.open}},addEventListener(name,fn){this.events[name]=fn},setAttribute(name,value){this.attrs[name]=value},contains(){return false},scrollIntoView(){},click(){this.events.click?.({target:this})}}}
const ids=Object.fromEntries(['themeToggle','themeIcon','themeLabel','sidebar','id_focus','focusValue','printPlan','timerDisplay','timerToggle','timerReset','timerStatus','timerTitle'].map(id=>[id,element()]));
const menu=element(),block=element();block.dataset={minutes:'25',title:'SQL joins'};
const root={dataset:{theme:'light'}},storage=new Map(),events={},intervals=new Map();let now=1000,id=0;
const document={documentElement:root,getElementById:key=>ids[key]||null,querySelector:key=>key==='.menu-toggle'?menu:null,querySelectorAll:key=>key==='.start-timer'?[block]:[],addEventListener:(name,fn)=>events[name]=fn};
const context={document,localStorage:{setItem:(k,v)=>storage.set(k,v)},matchMedia:()=>({matches:true}),window:{print(){}},Date:{now:()=>now},setInterval:fn=>{intervals.set(++id,fn);return id},clearInterval:key=>intervals.delete(key)};
vm.runInNewContext(fs.readFileSync('planner/static/js/script.js','utf8'),context);
ids.themeToggle.click();assert.equal(root.dataset.theme,'dark');assert.equal(storage.get('study-theme'),'dark');assert.equal(ids.themeToggle.attrs['aria-label'],'Switch to light mode');
ids.themeToggle.click();assert.equal(root.dataset.theme,'light');
menu.click();assert.equal(menu.attrs['aria-expanded'],'true');events.keydown({key:'Escape'});assert.equal(menu.attrs['aria-expanded'],'false');
ids.id_focus.value='8';ids.id_focus.events.input();assert.equal(ids.focusValue.textContent,'8 / 10');
block.click();assert.equal(ids.timerDisplay.textContent,'25:00');assert.equal(ids.timerTitle.textContent,'SQL joins');
now+=61000;for(const tick of intervals.values())tick();assert.equal(ids.timerDisplay.textContent,'23:59');
ids.timerToggle.click();now+=90000;assert.equal(ids.timerDisplay.textContent,'23:59');
ids.timerToggle.click();now+=239*1000;events.visibilitychange();assert.equal(ids.timerDisplay.textContent,'20:00');
now+=1201*1000;events.visibilitychange();assert.equal(ids.timerDisplay.textContent,'00:00');assert.match(ids.timerStatus.textContent,/finished/);
ids.timerReset.click();assert.equal(ids.timerDisplay.textContent,'25:00');assert.equal(intervals.size,0);
console.log('PASS: theme persistence, menu accessibility, focus output, timer selection, pause/resume, background elapsed time, finish and reset.');
