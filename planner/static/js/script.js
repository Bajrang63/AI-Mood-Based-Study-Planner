(() => {
  const root=document.documentElement, toggle=document.getElementById('themeToggle');
  function updateTheme(){const dark=root.dataset.theme==='dark';document.getElementById('themeIcon').textContent=dark?'☀':'☾';document.getElementById('themeLabel').textContent=dark?'Light mode':'Dark mode';toggle.setAttribute('aria-label',dark?'Switch to light mode':'Switch to dark mode');}
  toggle?.addEventListener('click',()=>{root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';try{localStorage.setItem('study-theme',root.dataset.theme)}catch(e){}updateTheme()});if(toggle)updateTheme();
  const menu=document.querySelector('.menu-toggle'),sidebar=document.getElementById('sidebar');
  const closeMenu=()=>{sidebar?.classList.remove('open');menu?.setAttribute('aria-expanded','false')};
  menu?.addEventListener('click',()=>{const open=sidebar.classList.toggle('open');menu.setAttribute('aria-expanded',String(open))});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu()});document.addEventListener('click',e=>{if(sidebar?.classList.contains('open')&&!sidebar.contains(e.target)&&!menu.contains(e.target))closeMenu()});
  const focus=document.getElementById('id_focus');focus?.addEventListener('input',()=>document.getElementById('focusValue').textContent=focus.value+' / 10');
  document.getElementById('printPlan')?.addEventListener('click',()=>window.print());
  // Wall-clock deadlines avoid interval drift when the browser throttles a background tab.
  const display=document.getElementById('timerDisplay');if(!display)return;
  let duration=25*60,remaining=duration,deadline=null,interval=null;
  const control=document.getElementById('timerToggle'),status=document.getElementById('timerStatus');
  function paint(){const seconds=Math.max(0,Math.ceil(remaining));display.textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0');}
  function pause(){if(deadline!==null)remaining=Math.max(0,(deadline-Date.now())/1000);deadline=null;clearInterval(interval);control.textContent='Resume';paint()}
  function tick(){if(deadline===null)return;remaining=Math.max(0,(deadline-Date.now())/1000);paint();if(remaining===0){clearInterval(interval);deadline=null;control.textContent='Start again';status.textContent='Session finished. Take a breath, then mark your block complete.'}}
  function start(){if(remaining<=0)remaining=duration;deadline=Date.now()+remaining*1000;control.textContent='Pause';status.textContent='One thing at a time. You’ve got this.';interval=setInterval(tick,250);tick()}
  control.addEventListener('click',()=>deadline===null?start():pause());
  document.getElementById('timerReset').addEventListener('click',()=>{pause();remaining=duration;control.textContent='Start';status.textContent='Ready when you are.';paint()});
  document.querySelectorAll('.start-timer').forEach(btn=>btn.addEventListener('click',()=>{pause();duration=Number(btn.dataset.minutes)*60;remaining=duration;document.getElementById('timerTitle').textContent=btn.dataset.title;start();display.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'})}));
  document.addEventListener('visibilitychange',()=>{if(deadline!==null)tick()});
})();
