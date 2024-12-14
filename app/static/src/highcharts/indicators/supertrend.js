!/**
 * Highstock JS v12.0.2 (2024-12-04)
 * @module highcharts/indicators/supertrend
 * @requires highcharts
 * @requires highcharts/modules/stock
 *
 * Indicator series type for Highcharts Stock
 *
 * (c) 2010-2024 Wojciech Chmiel
 *
 * License: www.highcharts.com/license
 */function(e,o){"object"==typeof exports&&"object"==typeof module?module.exports=o(e._Highcharts,e._Highcharts.SeriesRegistry):"function"==typeof define&&define.amd?define("highcharts/indicators/supertrend",["highcharts/highcharts"],function(e){return o(e,e.SeriesRegistry)}):"object"==typeof exports?exports["highcharts/indicators/supertrend"]=o(e._Highcharts,e._Highcharts.SeriesRegistry):e.Highcharts=o(e.Highcharts,e.Highcharts.SeriesRegistry)}("undefined"==typeof window?this:window,(e,o)=>(()=>{"use strict";var t={512:e=>{e.exports=o},944:o=>{o.exports=e}},r={};function i(e){var o=r[e];if(void 0!==o)return o.exports;var l=r[e]={exports:{}};return t[e](l,l.exports,i),l.exports}i.n=e=>{var o=e&&e.__esModule?()=>e.default:()=>e;return i.d(o,{a:o}),o},i.d=(e,o)=>{for(var t in o)i.o(o,t)&&!i.o(e,t)&&Object.defineProperty(e,t,{enumerable:!0,get:o[t]})},i.o=(e,o)=>Object.prototype.hasOwnProperty.call(e,o);var l={};i.d(l,{default:()=>S});var s=i(944),n=/*#__PURE__*/i.n(s),p=i(512),a=/*#__PURE__*/i.n(p);let{atr:h,sma:d}=a().seriesTypes,{addEvent:c,correctFloat:u,isArray:g,isNumber:x,extend:y,merge:f,objectEach:m}=n();function C(e,o){return{index:o,close:e.getColumn("close")[o],x:e.getColumn("x")[o]}}class T extends d{init(){let e=this;super.init.apply(e,arguments);let o=c(this.chart.constructor,"afterLinkSeries",()=>{if(e.options){let o=e.options,t=e.linkedParent.options;o.cropThreshold=t.cropThreshold-(o.params.period-1)}o()},{order:1})}drawGraph(){let e=this,o=e.options,t=e.linkedParent,r=t.getColumn("x"),i=t?t.points:[],l=e.points,s=e.graph,n=i.length-l.length,p=n>0?n:0,a={options:{gapSize:o.gapSize}},h={top:[],bottom:[],intersect:[]},c={top:{styles:{lineWidth:o.lineWidth,lineColor:o.fallingTrendColor||o.color,dashStyle:o.dashStyle}},bottom:{styles:{lineWidth:o.lineWidth,lineColor:o.risingTrendColor||o.color,dashStyle:o.dashStyle}},intersect:o.changeTrendLine},u,g,y,T,S,b,v,w,H,D=l.length;for(;D--;)u=l[D],g=l[D-1],y=i[D-1+p],T=i[D-2+p],S=i[D+p],b=i[D+p+1],v=u.options.color,w={x:u.x,plotX:u.plotX,plotY:u.plotY,isNull:!1},!T&&y&&x(r[y.index-1])&&(T=C(t,y.index-1)),!b&&S&&x(r[S.index+1])&&(b=C(t,S.index+1)),!y&&T&&x(r[T.index+1])?y=C(t,T.index+1):!y&&S&&x(r[S.index-1])&&(y=C(t,S.index-1)),u&&y&&S&&T&&u.x!==y.x&&(u.x===S.x?(T=y,y=S):u.x===T.x?(y=T,T={close:t.getColumn("close")[y.index-1],x:r[y.index-1]}):b&&u.x===b.x&&(y=b,T=S)),g&&T&&y?(H={x:g.x,plotX:g.plotX,plotY:g.plotY,isNull:!1},u.y>=y.close&&g.y>=T.close?(u.color=v||o.fallingTrendColor||o.color,h.top.push(w)):u.y<y.close&&g.y<T.close?(u.color=v||o.risingTrendColor||o.color,h.bottom.push(w)):(h.intersect.push(w),h.intersect.push(H),h.intersect.push(f(H,{isNull:!0})),u.y>=y.close&&g.y<T.close?(u.color=v||o.fallingTrendColor||o.color,g.color=v||o.risingTrendColor||o.color,h.top.push(w),h.top.push(f(H,{isNull:!0}))):u.y<y.close&&g.y>=T.close&&(u.color=v||o.risingTrendColor||o.color,g.color=v||o.fallingTrendColor||o.color,h.bottom.push(w),h.bottom.push(f(H,{isNull:!0}))))):y&&(u.y>=y.close?(u.color=v||o.fallingTrendColor||o.color,h.top.push(w)):(u.color=v||o.risingTrendColor||o.color,h.bottom.push(w)));m(h,function(o,t){e.points=o,e.options=f(c[t].styles,a),e.graph=e["graph"+t+"Line"],d.prototype.drawGraph.call(e),e["graph"+t+"Line"]=e.graph}),e.points=l,e.options=o,e.graph=s}getValues(e,o){let t=o.period,r=o.multiplier,i=e.xData,l=e.yData,s=[],n=[],p=[],a=0===t?0:t-1,d=[],c=[],x=[],y,f,m,C,T,S,b,v,w;if(!(i.length<=t)&&g(l[0])&&4===l[0].length&&!(t<0)){for(w=0,x=h.prototype.getValues.call(this,e,{period:t}).yData;w<x.length;w++)v=l[a+w],b=l[a+w-1]||[],C=d[w-1],T=c[w-1],S=p[w-1],0===w&&(C=T=S=0),y=u((v[1]+v[2])/2+r*x[w]),f=u((v[1]+v[2])/2-r*x[w]),y<C||b[3]>C?d[w]=y:d[w]=C,f>T||b[3]<T?c[w]=f:c[w]=T,S===C&&v[3]<d[w]||S===T&&v[3]<c[w]?m=d[w]:(S===C&&v[3]>d[w]||S===T&&v[3]>c[w])&&(m=c[w]),s.push([i[a+w],m]),n.push(i[a+w]),p.push(m);return{values:s,xData:n,yData:p}}}}T.defaultOptions=f(d.defaultOptions,{params:{index:void 0,multiplier:3,period:10},risingTrendColor:"#06b535",fallingTrendColor:"#f21313",changeTrendLine:{styles:{lineWidth:1,lineColor:"#333333",dashStyle:"LongDash"}}}),y(T.prototype,{nameBase:"Supertrend",nameComponents:["multiplier","period"]}),a().registerSeriesType("supertrend",T);let S=n();return l.default})());