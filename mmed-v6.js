
(function(){
 'use strict';
 var nav=document.getElementById('main-nav'),toggle=document.getElementById('menu-toggle'),header=document.querySelector('.site-header'),progress=document.querySelector('.scroll-indicator');
 var menuPanel=document.getElementById('site-menu-panel');
 function closeMenu(returnFocus){if(!menuPanel||!toggle)return;var wasOpen=!menuPanel.hidden;menuPanel.hidden=true;document.body.classList.remove('menu-open');toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label','Open navigation menu');if(returnFocus&&wasOpen)toggle.focus()}
 if(toggle&&menuPanel){
   toggle.addEventListener('click',function(){var open=menuPanel.hidden;if(open){menuPanel.hidden=false;document.body.classList.add('menu-open');toggle.setAttribute('aria-expanded','true');toggle.setAttribute('aria-label','Close navigation menu');var first=menuPanel.querySelector('a');if(first)first.focus({preventScroll:true})}else closeMenu(true)});
   menuPanel.querySelectorAll('a').forEach(function(link){link.addEventListener('click',function(){closeMenu(false)})});
   document.addEventListener('keydown',function(e){if(e.key==='Escape')closeMenu(true)});
   document.addEventListener('click',function(e){if(!menuPanel.hidden&&!menuPanel.contains(e.target)&&!toggle.contains(e.target))closeMenu(false)});
 }
 /* Category headings open real pages; hovering or focusing changes the preview panel. */
 var solutionLinks=[].slice.call(document.querySelectorAll('.adaptation-tab[data-adapt]'));
 function previewCategory(link){solutionLinks.forEach(function(item){var active=item===link;item.classList.toggle('is-active',active);var panel=document.getElementById('panel-'+item.getAttribute('data-adapt'));if(panel)panel.hidden=!active})}
 solutionLinks.forEach(function(link){link.addEventListener('mouseenter',function(){previewCategory(link)});link.addEventListener('focus',function(){previewCategory(link)})});
 var sections=[{id:'platform',href:'#platform'},{id:'solutions',href:'#solutions'}];
 var needsUpdate=false;
 function updateScroll(){needsUpdate=false;var top=window.scrollY||document.documentElement.scrollTop||0;var max=document.documentElement.scrollHeight-window.innerHeight;
  if(header)header.classList.toggle('is-scrolled',top>8);
  if(progress)progress.style.transform='scaleX('+Math.max(0,Math.min(1,max>0?top/max:0))+')';
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
