!/**
 * Highcharts JS v12.0.2 (2024-12-04)
 * @module highcharts/modules/overlapping-datalabels
 * @requires highcharts
 *
 * (c) 2009-2024 Torstein Honsi
 *
 * License: www.highcharts.com/license
 */function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e(t._Highcharts):"function"==typeof define&&define.amd?define("highcharts/modules/overlapping-datalabels",["highcharts/highcharts"],function(t){return e(t)}):"object"==typeof exports?exports["highcharts/modules/overlapping-datalabels"]=e(t._Highcharts):t.Highcharts=e(t.Highcharts)}("undefined"==typeof window?this:window,t=>(()=>{"use strict";var e,a={944:e=>{e.exports=t}},l={};function o(t){var e=l[t];if(void 0!==e)return e.exports;var i=l[t]={exports:{}};return a[t](i,i.exports,o),i.exports}o.n=t=>{var e=t&&t.__esModule?()=>t.default:()=>t;return o.d(e,{a:e}),e},o.d=(t,e)=>{for(var a in e)o.o(e,a)&&!o.o(t,a)&&Object.defineProperty(t,a,{enumerable:!0,get:e[a]})},o.o=(t,e)=>Object.prototype.hasOwnProperty.call(t,e);var i={};o.d(i,{default:()=>b});var n=o(944),r=/*#__PURE__*/o.n(n);!function(t){t.getCenterOfPoints=function(t){let e=t.reduce((t,e)=>(t.x+=e.x,t.y+=e.y,t),{x:0,y:0});return{x:e.x/t.length,y:e.y/t.length}},t.getDistanceBetweenPoints=function(t,e){return Math.sqrt(Math.pow(e.x-t.x,2)+Math.pow(e.y-t.y,2))},t.getAngleBetweenPoints=function(t,e){return Math.atan2(e.x-t.x,e.y-t.y)},t.pointInPolygon=function({x:t,y:e},a){let l=a.length,o,i,n=!1;for(o=0,i=l-1;o<l;i=o++){let[l,r]=a[o],[s,p]=a[i];r>e!=p>e&&t<(s-l)*(e-r)/(p-r)+l&&(n=!n)}return n}}(e||(e={}));let{pointInPolygon:s}=e,{addEvent:p,fireEvent:h,objectEach:c,pick:d}=r();function f(t){let e=t.length,a=(t,e)=>!(e.x>=t.x+t.width||e.x+e.width<=t.x||e.y>=t.y+t.height||e.y+e.height<=t.y),l=(t,e)=>{for(let a of t)if(s({x:a[0],y:a[1]},e))return!0;return!1},o,i,n,r,p,c=!1;for(let a=0;a<e;a++)(o=t[a])&&(o.oldOpacity=o.opacity,o.newOpacity=1,o.absoluteBox=function(t){if(t&&(!t.alignAttr||t.placed)){let e=t.box?0:t.padding||0,a=t.alignAttr||{x:t.attr("x"),y:t.attr("y")},l=t.getBBox();return t.width=l.width,t.height=l.height,{x:a.x+(t.parentGroup?.translateX||0)+e,y:a.y+(t.parentGroup?.translateY||0)+e,width:(t.width||0)-2*e,height:(t.height||0)-2*e,polygon:l?.polygon}}}(o));t.sort((t,e)=>(e.labelrank||0)-(t.labelrank||0));for(let o=0;o<e;++o){r=(i=t[o])&&i.absoluteBox;let s=r?.polygon;for(let h=o+1;h<e;++h){p=(n=t[h])&&n.absoluteBox;let e=!1;if(r&&p&&i!==n&&0!==i.newOpacity&&0!==n.newOpacity&&"hidden"!==i.visibility&&"hidden"!==n.visibility){let t=p.polygon;if(s&&t&&s!==t?l(s,t)&&(e=!0):a(r,p)&&(e=!0),e){let t=i.labelrank<n.labelrank?i:n,e=t.text;t.newOpacity=0,e?.element.querySelector("textPath")&&e.hide()}}}}for(let e of t)u(e,this)&&(c=!0);c&&h(this,"afterHideAllOverlappingLabels")}function u(t,e){let a,l,o=!1;return t&&(l=t.newOpacity,t.oldOpacity!==l&&(t.hasClass("highcharts-data-label")?(t[l?"removeClass":"addClass"]("highcharts-data-label-hidden"),a=function(){e.styledMode||t.css({pointerEvents:l?"auto":"none"})},o=!0,t[t.isOld?"animate":"attr"]({opacity:l},void 0,a),h(e,"afterHideOverlappingLabel")):t.attr({opacity:l})),t.isOld=!0),o}function y(){let t=this,e=[];for(let a of t.labelCollectors||[])e=e.concat(a());for(let a of t.yAxis||[])a.stacking&&a.options.stackLabels&&!a.options.stackLabels.allowOverlap&&c(a.stacking.stacks,t=>{c(t,t=>{t.label&&e.push(t.label)})});for(let a of t.series||[])if(a.visible&&a.hasDataLabels?.()){let l=a=>{for(let l of a)l.visible&&(l.dataLabels||[]).forEach(a=>{let o=a.options||{};a.labelrank=d(o.labelrank,l.labelrank,l.shapeArgs?.height),o.allowOverlap??Number(o.distance)>0?(a.oldOpacity=a.opacity,a.newOpacity=1,u(a,t)):e.push(a)})};l(a.nodes||[]),l(a.points)}this.hideOverlappingLabels(e)}let g=r();g.OverlappingDataLabels=g.OverlappingDataLabels||{compose:function(t){let e=t.prototype;e.hideOverlappingLabels||(e.hideOverlappingLabels=f,p(t,"render",y))}},g.OverlappingDataLabels.compose(g.Chart);let b=r();return i.default})());