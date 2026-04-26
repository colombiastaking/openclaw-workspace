(function(d){var h=[];d.loadImages=function(a,e){"string"==typeof a&&(a=[a]);for(var f=a.length,g=0,b=0;b<f;b++){var c=document.createElement("img");c.onload=function(){g++;g==f&&d.isFunction(e)&&e()};c.src=a[b];h.push(c)}}})(window.jQuery);
var wl;

var lwi=-1;function thresholdPassed(){var w=$(window).width();var p=false;var cw=0;if(w>=480){cw++;}if(w>=768){cw++;}if(w>=960){cw++;}if(w>=1200){cw++;}if(lwi!=cw){p=true;}lwi=cw;return p;}
!function(){if("Promise"in window&&void 0!==window.performance){var e,t,r=document,n=function(){return r.createElement("link")},o=new Set,a=n(),i=a.relList&&a.relList.supports&&a.relList.supports("prefetch"),s=location.href.replace(/#[^#]+$/,"");o.add(s);var c=function(e){var t=location,r="http:",n="https:";if(e&&e.href&&e.origin==t.origin&&[r,n].includes(e.protocol)&&(e.protocol!=r||t.protocol!=n)){var o=e.pathname;if(!(e.hash&&o+e.search==t.pathname+t.search||"?preload=no"==e.search.substr(-11)||".html"!=o.substr(-5)&&".html"!=o.substr(-5)&&"/"!=o.substr(-1)))return!0}},u=function(e){var t=e.replace(/#[^#]+$/,"");if(!o.has(t)){if(i){var a=n();a.rel="prefetch",a.href=t,r.head.appendChild(a)}else{var s=new XMLHttpRequest;s.open("GET",t,s.withCredentials=!0),s.send()}o.add(t)}},p=function(e){return e.target.closest("a")},f=function(t){var r=t.relatedTarget;r&&p(t)==r.closest("a")||e&&(clearTimeout(e),e=void 0)},d={capture:!0,passive:!0};r.addEventListener("touchstart",function(e){t=performance.now();var r=p(e);c(r)&&u(r.href)},d),r.addEventListener("mouseover",function(r){if(!(performance.now()-t<1200)){var n=p(r);c(n)&&(n.addEventListener("mouseout",f,{passive:!0}),e=setTimeout(function(){u(n.href),e=void 0},80))}},d)}}();

$(function(){
r=function(){if(thresholdPassed()){dpi=window.devicePixelRatio;if($(window).width()>=1200){var e=document.querySelector('.un1');e.setAttribute('src',(dpi>1)?'images/transparent-logo-326-2.png':'images/transparent-logo-163-2.png');
var e=document.querySelector('.un2');e.setAttribute('src',(dpi>1)?'images/flag_of_france.svg-78.png':'images/flag_of_france.svg-39.png');
var e=document.querySelector('.un3');e.setAttribute('src',(dpi>1)?'images/1200px-flag_of_the_united_kingdom.svg-84.jpg':'images/1200px-flag_of_the_united_kingdom.svg-42.jpg');
var e=document.querySelector('.un4');e.setAttribute('src',(dpi>1)?'images/colombias-gold-220-1.png':'images/colombias-gold-110-1.png');
var e=document.querySelector('.un6');e.setAttribute('src',(dpi>1)?'images/colombias-bronze-174-1.png':'images/colombias-bronze-87-1.png');
var e=document.querySelector('.un10');e.setAttribute('src',(dpi>1)?'images/grayscale-transparent-2078.png':'images/grayscale-transparent-1039.png');}else if($(window).width()>=960){var e=document.querySelector('.un1');e.setAttribute('src',(dpi>1)?'images/transparent-logo-260.png':'images/transparent-logo-130.png');
var e=document.querySelector('.un2');e.setAttribute('src',(dpi>1)?'images/flag_of_france.svg-64.png':'images/flag_of_france.svg-32.png');
var e=document.querySelector('.un3');e.setAttribute('src',(dpi>1)?'images/1200px-flag_of_the_united_kingdom.svg-68.jpg':'images/1200px-flag_of_the_united_kingdom.svg-34.jpg');
var e=document.querySelector('.un4');e.setAttribute('src',(dpi>1)?'images/colombias-gold-176.png':'images/colombias-gold-88.png');
var e=document.querySelector('.un6');e.setAttribute('src',(dpi>1)?'images/colombias-bronze-140.png':'images/colombias-bronze-70.png');
var e=document.querySelector('.un10');e.setAttribute('src',(dpi>1)?'images/grayscale-transparent-1662.png':'images/grayscale-transparent-831.png');}else if($(window).width()>=768){var e=document.querySelector('.un1');e.setAttribute('src',(dpi>1)?'images/transparent-logo-208-1.png':'images/transparent-logo-104.png');
var e=document.querySelector('.un2');e.setAttribute('src',(dpi>1)?'images/flag_of_france.svg-52.png':'images/flag_of_france.svg-26.png');
var e=document.querySelector('.un3');e.setAttribute('src',(dpi>1)?'images/1200px-flag_of_the_united_kingdom.svg-52-1.jpg':'images/1200px-flag_of_the_united_kingdom.svg-26-1.jpg');
var e=document.querySelector('.un4');e.setAttribute('src',(dpi>1)?'images/colombias-gold-140.png':'images/colombias-gold-70.png');
var e=document.querySelector('.un6');e.setAttribute('src',(dpi>1)?'images/colombias-bronze-112.png':'images/colombias-bronze-56.png');
var e=document.querySelector('.un10');e.setAttribute('src',(dpi>1)?'images/grayscale-transparent-1330.png':'images/grayscale-transparent-665.png');}else if($(window).width()>=480){var e=document.querySelector('.un1');e.setAttribute('src',(dpi>1)?'images/transparent-logo-198.png':'images/transparent-logo-99.png');
var e=document.querySelector('.un2');e.setAttribute('src',(dpi>1)?'images/flag_of_france.svg-72.png':'images/flag_of_france.svg-36.png');
var e=document.querySelector('.un3');e.setAttribute('src',(dpi>1)?'images/1200px-flag_of_the_united_kingdom.svg-80-1.jpg':'images/1200px-flag_of_the_united_kingdom.svg-40-1.jpg');
var e=document.querySelector('.un4');e.setAttribute('src',(dpi>1)?'images/colombias-gold-216-1.png':'images/colombias-gold-108-1.png');
var e=document.querySelector('.un6');e.setAttribute('src',(dpi>1)?'images/colombias-bronze-116-1.png':'images/colombias-bronze-58-1.png');
var e=document.querySelector('.un10');e.setAttribute('src',(dpi>1)?'images/grayscale-transparent-950.png':'images/grayscale-transparent-475.png');}else{var e=document.querySelector('.un1');e.setAttribute('src',(dpi>1)?'images/transparent-logo-132.png':'images/transparent-logo-66.png');
var e=document.querySelector('.un2');e.setAttribute('src',(dpi>1)?'images/flag_of_france.svg-48.png':'images/flag_of_france.svg-24.png');
var e=document.querySelector('.un3');e.setAttribute('src',(dpi>1)?'images/1200px-flag_of_the_united_kingdom.svg-52.jpg':'images/1200px-flag_of_the_united_kingdom.svg-26.jpg');
var e=document.querySelector('.un4');e.setAttribute('src',(dpi>1)?'images/colombias-gold-144.png':'images/colombias-gold-72.png');
var e=document.querySelector('.un6');e.setAttribute('src',(dpi>1)?'images/colombias-bronze-78-1.png':'images/colombias-bronze-39-1.png');
var e=document.querySelector('.un10');e.setAttribute('src',(dpi>1)?'images/grayscale-transparent-634.png':'images/grayscale-transparent-317.png');}}};
if(!window.HTMLPictureElement){$(window).resize(r);r();}
!function(){var e=document.querySelectorAll('a[href^="#"]');[].forEach.call(e,function(e){e.addEventListener("click",function(t){var o=0;if(e.hash.length>1){var l=parseFloat(getComputedStyle(document.body).getPropertyValue("zoom"));l||(l=1);var n=document.querySelectorAll('[name="'+e.hash.slice(1)+'"]')[0];o=(n.getBoundingClientRect().top+pageYOffset)*l}if("scrollBehavior"in document.documentElement.style)scroll({top:o,left:0,behavior:"smooth"});else if("requestAnimationFrame"in window){var r=pageYOffset,a=null;requestAnimationFrame(function e(t){a||(a=t);var l=t-a;scrollTo(0,r<o?(o-r)*l/400+r:r-(r-o)*l/400),l<400?requestAnimationFrame(e):scrollTo(0,o)})}else scrollTo(0,o);t.preventDefault()},!1)})}();
initMenu($('#m1')[0]);
initMenu($('#m2')[0]);
$('.s5').Stickyfill();
wl=new woolite();
wl.init();
wl.addAnimation($('.un5'), "4.00s", "0.80s", 1, 100);
wl.addAnimation($('.un7'), "2.00s", "2.00s", 1, 100);
wl.addAnimation($('.un8'), "2.50s", "0.00s", 1, 100);
wl.addAnimation($('.un9'), "2.50s", "0.00s", 1, 100);
wl.addAnimation($('.un11'), "2.50s", "0.00s", 1, 100);
wl.addAnimation($('.un12'), "2.50s", "0.00s", 1, 100);
wl.start();
if(location.hash){var e=location.hash.replace("#",""),o=function(){var t=document.querySelectorAll('[name="'+e+'"]')[0];t&&t.scrollIntoView(),"complete"!=document.readyState&&setTimeout(o,100)};o()}

});