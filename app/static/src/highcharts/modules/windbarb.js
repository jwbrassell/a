!/**
 * Highcharts JS v12.0.2 (2024-12-04)
 * @module highcharts/modules/windbarb
 * @requires highcharts
 *
 * Wind barb series module
 *
 * (c) 2010-2024 Torstein Honsi
 *
 * License: www.highcharts.com/license
 */function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e(t._Highcharts,t._Highcharts.dataGrouping.approximations,t._Highcharts.Series.types.column,t._Highcharts.Series,t._Highcharts.SeriesRegistry):"function"==typeof define&&define.amd?define("highcharts/modules/windbarb",["highcharts/highcharts"],function(t){return e(t,t.dataGrouping,["approximations"],t.Series,["types"],["column"],t.Series,t.SeriesRegistry)}):"object"==typeof exports?exports["highcharts/modules/windbarb"]=e(t._Highcharts,t._Highcharts.dataGrouping.approximations,t._Highcharts.Series.types.column,t._Highcharts.Series,t._Highcharts.SeriesRegistry):t.Highcharts=e(t.Highcharts,t.Highcharts.dataGrouping.approximations,t.Highcharts.Series.types.column,t.Highcharts.Series,t.Highcharts.SeriesRegistry)}("undefined"==typeof window?this:window,(t,e,r,o,i)=>(()=>{"use strict";var s,a={448:t=>{t.exports=r},820:t=>{t.exports=o},512:t=>{t.exports=i},956:t=>{t.exports=e},944:e=>{e.exports=t}},n={};function l(t){var e=n[t];if(void 0!==e)return e.exports;var r=n[t]={exports:{}};return a[t](r,r.exports,l),r.exports}l.n=t=>{var e=t&&t.__esModule?()=>t.default:()=>t;return l.d(e,{a:e}),e},l.d=(t,e)=>{for(var r in e)l.o(e,r)&&!l.o(t,r)&&Object.defineProperty(t,r,{enumerable:!0,get:e[r]})},l.o=(t,e)=>Object.prototype.hasOwnProperty.call(t,e);var p={};l.d(p,{default:()=>W});var h=l(944),c=/*#__PURE__*/l.n(h),u=l(956),d=/*#__PURE__*/l.n(u),f=l(448),g=/*#__PURE__*/l.n(f),x=l(820),y=/*#__PURE__*/l.n(x);let{composed:b}=c(),{prototype:m}=g(),{prototype:v}=y(),{defined:S,pushUnique:w,stableSort:L}=c();!function(t){function e(t){return v.getPlotBox.call(this.options.onSeries&&this.chart.get(this.options.onSeries)||this,t)}function r(){m.translate.apply(this);let t=this,e=t.options,r=t.chart,o=t.points,i=e.onSeries,s=i&&r.get(i),a=s&&s.options.step,n=s&&s.points,l=r.inverted,p=t.xAxis,h=t.yAxis,c=o.length-1,u,d,f=e.onKey||"y",g=n&&n.length,x=0,y,b,v,w,H;if(s&&s.visible&&g){for(x=(s.pointXOffset||0)+(s.barW||0)/2,w=s.currentDataGrouping,b=n[g-1].x+(w?w.totalRange:0),L(o,(t,e)=>t.x-e.x),f="plot"+f[0].toUpperCase()+f.substr(1);g--&&o[c];)if(y=n[g],(u=o[c]).y=y.y,y.x<=u.x&&void 0!==y[f]){if(u.x<=b&&(u.plotY=y[f],y.x<u.x&&!a&&(v=n[g+1])&&void 0!==v[f])){if(S(u.plotX)&&s.is("spline")){let t=[y.plotX||0,y.plotY||0],e=[v.plotX||0,v.plotY||0],r=y.controlPoints?.high||t,o=v.controlPoints?.low||e,i=(i,s)=>Math.pow(1-i,3)*t[s]+3*(1-i)*(1-i)*i*r[s]+3*(1-i)*i*i*o[s]+i*i*i*e[s],s=0,a=1,n;for(let t=0;t<100;t++){let t=(s+a)/2,e=i(t,0);if(null===e)break;if(.25>Math.abs(e-u.plotX)){n=t;break}e<u.plotX?s=t:a=t}S(n)&&(u.plotY=i(n,1),u.y=h.toValue(u.plotY,!0))}else H=(u.x-y.x)/(v.x-y.x),u.plotY+=H*(v[f]-y[f]),u.y+=H*(v.y-y.y)}if(c--,g++,c<0)break}}o.forEach((e,r)=>{let i;e.plotX+=x,(void 0===e.plotY||l)&&(e.plotX>=0&&e.plotX<=p.len?l?(e.plotY=p.translate(e.x,0,1,0,1),e.plotX=S(e.y)?h.translate(e.y,0,0,0,1):0):e.plotY=(p.opposite?0:t.yAxis.len)+p.offset:e.shapeArgs={}),(d=o[r-1])&&d.plotX===e.plotX&&(void 0===d.stackIndex&&(d.stackIndex=0),i=d.stackIndex+1),e.stackIndex=i}),this.onSeries=s}t.compose=function(t){if(w(b,"OnSeries")){let o=t.prototype;o.getPlotBox=e,o.translate=r}return t},t.getPlotBox=e,t.translate=r}(s||(s={}));let H=s;var X=l(512),k=/*#__PURE__*/l.n(X);let{isNumber:G}=c();class M extends g().prototype.pointClass{isValid(){return G(this.value)&&this.value>=0}}let{animObject:O}=c(),{column:P}=k().seriesTypes,{extend:A,merge:Y,pick:_}=c();class I extends P{init(t,e){super.init(t,e)}pointAttribs(t,e){let r=this.options,o=t.color||this.color,i=this.options.lineWidth;return e&&(o=r.states[e].color||o,i=(r.states[e].lineWidth||i)+(r.states[e].lineWidthPlus||0)),{stroke:o,"stroke-width":i}}windArrow(t){let e=t.beaufortLevel,r=this.options.vectorLength/20,o=1.943844*t.value,i,s=-10;if(t.isNull)return[];if(0===e)return this.chart.renderer.symbols.circle(-10*r,-10*r,20*r,20*r);let a=[["M",0,7*r],["L",-1.5*r,7*r],["L",0,10*r],["L",1.5*r,7*r],["L",0,7*r],["L",0,-10*r]];if((i=(o-o%50)/50)>0)for(;i--;)a.push(-10===s?["L",0,s*r]:["M",0,s*r],["L",5*r,s*r+2],["L",0,s*r+4]),o-=50,s+=7;if((i=(o-o%10)/10)>0)for(;i--;)a.push(-10===s?["L",0,s*r]:["M",0,s*r],["L",7*r,s*r]),o-=10,s+=3;if((i=(o-o%5)/5)>0)for(;i--;)a.push(-10===s?["L",0,s*r]:["M",0,s*r],["L",4*r,s*r]),o-=5,s+=3;return a}drawPoints(){let t=this.chart,e=this.yAxis,r=t.inverted,o=this.options.vectorLength/2;for(let i of this.points){let s=i.plotX,a=i.plotY;!1===this.options.clip||t.isInsidePlot(s,0)?(i.graphic||(i.graphic=this.chart.renderer.path().add(this.markerGroup).addClass("highcharts-point highcharts-color-"+_(i.colorIndex,i.series.colorIndex))),i.graphic.attr({d:this.windArrow(i),translateX:s+this.options.xOffset,translateY:a+this.options.yOffset,rotation:i.direction}),this.chart.styledMode||i.graphic.attr(this.pointAttribs(i))):i.graphic&&(i.graphic=i.graphic.destroy()),i.tooltipPos=[s+this.options.xOffset+(r&&!this.onSeries?o:0),a+this.options.yOffset-(r?0:o+e.pos-t.plotTop)]}}animate(t){t?this.markerGroup.attr({opacity:.01}):this.markerGroup.animate({opacity:1},O(this.options.animation))}markerAttribs(){return{}}getExtremes(){return{}}shouldShowTooltip(t,e,r={}){return r.ignoreX=this.chart.inverted,r.ignoreY=!r.ignoreX,super.shouldShowTooltip(t,e,r)}}I.defaultOptions=Y(P.defaultOptions,{dataGrouping:{enabled:!0,approximation:"windbarb",groupPixelWidth:30},lineWidth:2,onSeries:null,states:{hover:{lineWidthPlus:0}},tooltip:{pointFormat:'<span style="color:{point.color}">●</span> {series.name}: <b>{point.value}</b> ({point.beaufort})<br/>'},vectorLength:20,colorKey:"value",yOffset:-20,xOffset:0}),H.compose(I),A(I.prototype,{beaufortFloor:[0,.3,1.6,3.4,5.5,8,10.8,13.9,17.2,20.8,24.5,28.5,32.7],beaufortName:["Calm","Light air","Light breeze","Gentle breeze","Moderate breeze","Fresh breeze","Strong breeze","Near gale","Gale","Strong gale","Storm","Violent storm","Hurricane"],invertible:!1,parallelArrays:["x","value","direction"],pointArrayMap:["value","direction"],pointClass:M,trackerGroups:["markerGroup"],translate:function(){let t=this.beaufortFloor,e=this.beaufortName;for(let r of(H.translate.call(this),this.points)){let o=0;for(;o<t.length&&!(t[o]>r.value);o++);r.beaufortLevel=o-1,r.beaufort=e[o-1]}}}),k().registerSeriesType("windbarb",I),d().windbarb||(d().windbarb=(t,e)=>{let r=0,o=0;for(let i=0,s=t.length;i<s;i++)r+=t[i]*Math.cos(e[i]*c().deg2rad),o+=t[i]*Math.sin(e[i]*c().deg2rad);return[t.reduce((t,e)=>t+e,0)/t.length,Math.atan2(o,r)/c().deg2rad]});let W=c();return p.default})());