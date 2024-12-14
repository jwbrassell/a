!/**
 * Highcharts JS v12.0.2 (2024-12-04)
 * @module highcharts/modules/bullet
 * @requires highcharts
 *
 * Bullet graph series type for Highcharts
 *
 * (c) 2010-2024 Kacper Madej
 *
 * License: www.highcharts.com/license
 */function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e(t._Highcharts,t._Highcharts.Series.types.column,t._Highcharts.SeriesRegistry):"function"==typeof define&&define.amd?define("highcharts/modules/bullet",["highcharts/highcharts"],function(t){return e(t,t.Series,["types"],["column"],t.SeriesRegistry)}):"object"==typeof exports?exports["highcharts/modules/bullet"]=e(t._Highcharts,t._Highcharts.Series.types.column,t._Highcharts.SeriesRegistry):t.Highcharts=e(t.Highcharts,t.Highcharts.Series.types.column,t.Highcharts.SeriesRegistry)}("undefined"==typeof window?this:window,(t,e,r)=>(()=>{"use strict";var s={448:t=>{t.exports=e},512:t=>{t.exports=r},944:e=>{e.exports=t}},i={};function o(t){var e=i[t];if(void 0!==e)return e.exports;var r=i[t]={exports:{}};return s[t](r,r.exports,o),r.exports}o.n=t=>{var e=t&&t.__esModule?()=>t.default:()=>t;return o.d(e,{a:e}),e},o.d=(t,e)=>{for(var r in e)o.o(e,r)&&!o.o(t,r)&&Object.defineProperty(t,r,{enumerable:!0,get:e[r]})},o.o=(t,e)=>Object.prototype.hasOwnProperty.call(t,e);var a={};o.d(a,{default:()=>w});var h=o(944),l=/*#__PURE__*/o.n(h),n=o(448),p=/*#__PURE__*/o.n(n);class d extends p().prototype.pointClass{destroy(){this.targetGraphic&&(this.targetGraphic=this.targetGraphic.destroy()),super.destroy.apply(this,arguments)}}var c=o(512),g=/*#__PURE__*/o.n(c);let{extend:u,isNumber:y,merge:x,pick:f,relativeLength:b}=l();class m extends p(){drawPoints(){let t=this.chart,e=this.options,r=e.animationLimit||250;for(let s of(super.drawPoints.apply(this,arguments),this.points)){let i=s.options,o=s.target,a=s.y,h,l=s.targetGraphic,n,p,d,c;if(y(o)&&null!==o){p=(d=x(e.targetOptions,i.targetOptions)).height;let g=s.shapeArgs;s.dlBox&&g&&!y(g.width)&&(g=s.dlBox),n=b(d.width,g.width),c=this.yAxis.translate(o,!1,!0,!1,!0)-d.height/2-.5,h=this.crispCol.apply({chart:t,borderWidth:d.borderWidth,options:{crisp:e.crisp}},[g.x+g.width/2-n/2,c,n,p]),l?(l[t.pointCount<r?"animate":"attr"](h),y(a)&&null!==a?l.element.point=s:l.element.point=void 0):s.targetGraphic=l=t.renderer.rect().attr(h).add(this.group),t.styledMode||l.attr({fill:f(d.color,i.color,this.zones.length&&(s.getZone.call({series:this,x:s.x,y:o,options:{}}).color||this.color)||void 0,s.color,this.color),stroke:f(d.borderColor,s.borderColor,this.options.borderColor),"stroke-width":d.borderWidth,r:d.borderRadius}),y(a)&&null!==a&&(l.element.point=s),l.addClass(s.getClassName()+" highcharts-bullet-target",!0)}else l&&(s.targetGraphic=l.destroy())}}getExtremes(t){let e=super.getExtremes.call(this,t),r=this.targetData;if(r&&r.length){let t=super.getExtremes.call(this,r);y(t.dataMin)&&(e.dataMin=Math.min(f(e.dataMin,1/0),t.dataMin)),y(t.dataMax)&&(e.dataMax=Math.max(f(e.dataMax,-1/0),t.dataMax))}return e}}m.defaultOptions=x(p().defaultOptions,{targetOptions:{width:"140%",height:3,borderWidth:0,borderRadius:0},tooltip:{pointFormat:'<span style="color:{series.color}">●</span> {series.name}: <b>{point.y}</b>. Target: <b>{point.target}</b><br/>'}}),u(m.prototype,{parallelArrays:["x","y","target"],pointArrayMap:["y","target"]}),m.prototype.pointClass=d,g().registerSeriesType("bullet",m);let w=l();return a.default})());