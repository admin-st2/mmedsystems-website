/* Local directory filtering only. No tracking, external requests, or submissions. */
(() => {
  'use strict';
  const input=document.getElementById('sector-search');
  if(!input)return;
  const cards=[...document.querySelectorAll('.sector-card[data-sector]')];
  const groups=[...document.querySelectorAll('.sector-group')];
  const status=document.getElementById('sector-search-status');
  const noResults=document.getElementById('sector-no-results');
  const aliases={'outpatient':'clinic practice urgent surgery medical','nursing':'nursing nurse home long-term','behavioral':'behavioral therapy psychiatry recovery','pharmacy':'pharmacy pharmacies'};
  function update(){
    const q=input.value.trim().toLowerCase();
    const terms=(aliases[q]||q).split(/\s+/).filter(Boolean);
    let visible=0;
    cards.forEach(card=>{const text=card.dataset.sector||'';const match=!q||(aliases[q]?terms.some(t=>text.includes(t)):terms.every(t=>text.includes(t)));card.hidden=!match;if(match)visible++;});
    groups.forEach(g=>{g.hidden=![...g.querySelectorAll('.sector-card')].some(c=>!c.hidden);});
    noResults.hidden=visible>0;
    status.textContent=q?`${visible} matching care setting${visible===1?'':'s'}`:`${cards.length} sectors across six groups`;
  }
  input.addEventListener('input',update);
  document.getElementById('clear-sector-search').addEventListener('click',()=>{input.value='';update();input.focus();});
  document.querySelectorAll('.sector-group-jumps a').forEach(a=>a.addEventListener('click',()=>{if(input.value){input.value='';update();}}));
})();
