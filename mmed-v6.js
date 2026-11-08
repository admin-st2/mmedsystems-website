
(function(){
 'use strict';
 var nav=document.getElementById('main-nav'),toggle=document.getElementById('menu-toggle'),header=document.querySelector('.site-header');
 var menuPanel=document.getElementById('site-menu-panel');
 var toggleText=toggle&&toggle.querySelector('span');
 function closeMenu(returnFocus){
  if(!menuPanel||!toggle)return;
  var wasOpen=!menuPanel.hidden;
  menuPanel.hidden=true;
  document.body.classList.remove('menu-open');
  toggle.setAttribute('aria-expanded','false');
  toggle.setAttribute('aria-label','Open navigation menu');
  if(toggleText)toggleText.textContent='Menu';
  if(returnFocus&&wasOpen)toggle.focus({preventScroll:true});
 }
 function openMenu(){
  if(!menuPanel||!toggle)return;
  menuPanel.hidden=false;
  document.body.classList.add('menu-open');
  toggle.setAttribute('aria-expanded','true');
  toggle.setAttribute('aria-label','Close navigation menu');
  if(toggleText)toggleText.textContent='Close';
  // Focus the first visible menu destination, not a link hidden at
  // this viewport (desktop menu intentionally avoids duplicate top links).
  var first=[].slice.call(menuPanel.querySelectorAll('a[href]')).find(function(link){
   return link.getClientRects().length>0 && getComputedStyle(link).visibility!=='hidden';
  });
  if(first)first.focus({preventScroll:true});
 }
 if(toggle&&menuPanel){
  toggle.addEventListener('click',function(){
   if(menuPanel.hidden)openMenu();else closeMenu(true);
  });
  menuPanel.querySelectorAll('a[href]').forEach(function(link){
   link.addEventListener('click',function(){closeMenu(false)});
  });
  document.addEventListener('keydown',function(e){
   if(e.key==='Escape'&&!menuPanel.hidden){e.preventDefault();closeMenu(true)}
  });
  document.addEventListener('click',function(e){
   if(!menuPanel.hidden&&!menuPanel.contains(e.target)&&!toggle.contains(e.target))closeMenu(false);
  });
  // The hamburger is a disclosure panel, not a modal: keyboard users can
  // continue tabbing through the page without focus being trapped behind it.
  document.addEventListener('focusin',function(e){
   if(!menuPanel.hidden&&!menuPanel.contains(e.target)&&!toggle.contains(e.target))closeMenu(false);
  });
  window.addEventListener('pageshow',function(){closeMenu(false)});
  // A layout switch can hide the focused primary link. Close the disclosure
  // and return focus to its toggle rather than leave focus on hidden content.
  var compactNavigation=window.matchMedia('(max-width:1120px)');
  compactNavigation.addEventListener('change',function(){closeMenu(true)});
 }
 // Keep the current page identifiable even in the large hamburger menu.
 // Do not reorder navigation, change URLs, or mark anchor-only links as pages.
 var here=window.location.pathname.replace(/\/+$/,'/')||'/';
 document.querySelectorAll('#main-nav a, #site-menu-panel nav a').forEach(function(link){
  var parsed;
  try{parsed=new URL(link.href,window.location.href)}catch(_){return}
  var path=parsed.pathname.replace(/\/+$/,'/')||'/';
  if(parsed.origin===window.location.origin&&!parsed.hash&&path===here){
   link.setAttribute('aria-current','page');
  }else if(link.getAttribute('aria-current')==='page'){
   link.removeAttribute('aria-current');
  }
 });
 /* Category headings open real pages; hovering or focusing changes the preview panel. */
 var solutionLinks=[].slice.call(document.querySelectorAll('.adaptation-tab[data-adapt]'));
 function previewCategory(link){solutionLinks.forEach(function(item){var active=item===link;item.classList.toggle('is-active',active);var panel=document.getElementById('panel-'+item.getAttribute('data-adapt'));if(panel)panel.hidden=!active})}
 solutionLinks.forEach(function(link){link.addEventListener('mouseenter',function(){previewCategory(link)});link.addEventListener('focus',function(){previewCategory(link)})});
 var sections=[{id:'platform',href:'#platform'},{id:'solutions',href:'#solutions'}];
 var needsUpdate=false;
 function updateScroll(){needsUpdate=false;var top=window.scrollY||document.documentElement.scrollTop||0;
  if(header)header.classList.toggle('is-scrolled',top>8);
  var active='';sections.forEach(function(s){var section=document.getElementById(s.id);if(section&&section.getBoundingClientRect().top<=window.innerHeight*.33)active=s.href});
  document.querySelectorAll('.nav-links a[href="#platform"],.nav-links a[href="#solutions"]').forEach(function(a){if(a.getAttribute('href')===active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current')});
 }
 function scrollHandler(){if(!needsUpdate){needsUpdate=true;window.requestAnimationFrame(updateScroll)}}
 window.addEventListener('scroll',scrollHandler,{passive:true});window.addEventListener('resize',scrollHandler);updateScroll();
 if('IntersectionObserver' in window){
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(!reduce){var observer=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(entry.isIntersecting){entry.target.classList.remove('reveal-pending');entry.target.classList.add('reveal-visible');observer.unobserve(entry.target)}})},{rootMargin:'0px 0px -35px 0px',threshold:.04});
   [].slice.call(document.querySelectorAll('[data-reveal]')).forEach(function(el){if(el.getBoundingClientRect().top>window.innerHeight*.85){el.classList.add('reveal-pending');observer.observe(el)}else el.classList.add('reveal-visible')});
   document.documentElement.classList.add('motion-ready');
  }
 }
})();
