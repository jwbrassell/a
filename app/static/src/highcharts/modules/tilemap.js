!/**
 * Highmaps JS v12.0.2 (2024-12-04)
 * @module highcharts/modules/tilemap
 * @requires highcharts
 * @requires highcharts/modules/map
 *
 * Tilemap module
 *
 * (c) 2010-2024 Highsoft AS
 *
 * License: www.highcharts.com/license
 */function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e(t._Highcharts,t._Highcharts.SeriesRegistry,t._Highcharts.Color):"function"==typeof define&&define.amd?define("highcharts/modules/tilemap",["highcharts/highcharts"],function(t){return e(t,t.SeriesRegistry,t.Color)}):"object"==typeof exports?exports["highcharts/modules/tilemap"]=e(t._Highcharts,t._Highcharts.SeriesRegistry,t._Highcharts.Color):t.Highcharts=e(t.Highcharts,t.Highcharts.SeriesRegistry,t.Highcharts.Color)}("undefined"==typeof window?this:window,(t,e,i)=>(()=>{"use strict";var s,o={620:t=>{t.exports=i},512:t=>{t.exports=e},944:e=>{e.exports=t}},a={};function r(t){var e=a[t];if(void 0!==e)return e.exports;var i=a[t]={exports:{}};return o[t](i,i.exports,r),i.exports}r.n=t=>{var e=t&&t.__esModule?()=>t.default:()=>t;return r.d(e,{a:e}),e},r.d=(t,e)=>{for(var i in e)r.o(e,i)&&!r.o(t,i)&&Object.defineProperty(t,i,{enumerable:!0,get:e[i]})},r.o=(t,e)=>Object.prototype.hasOwnProperty.call(t,e);var n={};r.d(n,{default:()=>U});var l=r(944),h=/*#__PURE__*/r.n(l),p=r(512),d=/*#__PURE__*/r.n(p),c=r(620);let{parse:u}=/*#__PURE__*/r.n(c)(),{addEvent:g,extend:x,merge:f,pick:y,splat:m}=h();!function(t){let e;function i(){let{userOptions:t}=this;this.colorAxis=[],t.colorAxis&&(t.colorAxis=m(t.colorAxis),t.colorAxis.map(t=>new e(this,t)))}function s(t){let e=this.chart.colorAxis||[],i=e=>{let i=t.allItems.indexOf(e);-1!==i&&(this.destroyItem(t.allItems[i]),t.allItems.splice(i,1))},s=[],o,a;for(e.forEach(function(t){(o=t.options)&&o.showInLegend&&(o.dataClasses&&o.visible?s=s.concat(t.getDataClassLegendSymbols()):o.visible&&s.push(t),t.series.forEach(function(t){(!t.options.showInLegend||o.dataClasses)&&("point"===t.options.legendType?t.points.forEach(function(t){i(t)}):i(t))}))}),a=s.length;a--;)t.allItems.unshift(s[a])}function o(t){t.visible&&t.item.legendColor&&t.item.legendItem.symbol.attr({fill:t.item.legendColor})}function a(t){this.chart.colorAxis?.forEach(e=>{e.update({},t.redraw)})}function r(){(this.chart.colorAxis&&this.chart.colorAxis.length||this.colorAttribs)&&this.translateColors()}function n(){let t=this.axisTypes;t?-1===t.indexOf("colorAxis")&&t.push("colorAxis"):this.axisTypes=["colorAxis"]}function l(t){let e=this,i=t?"show":"hide";e.visible=e.options.visible=!!t,["graphic","dataLabel"].forEach(function(t){e[t]&&e[t][i]()}),this.series.buildKDTree()}function h(){let t=this,e=this.getPointsCollection(),i=this.options.nullColor,s=this.colorAxis,o=this.colorKey;e.forEach(e=>{let a=e.getNestedProperty(o),r=e.options.color||(e.isNull||null===e.value?i:s&&void 0!==a?s.toColor(a,e):e.color||t.color);r&&e.color!==r&&(e.color=r,"point"===t.options.legendType&&e.legendItem&&e.legendItem.label&&t.chart.legend.colorizeItem(e,e.visible))})}function p(){this.elem.attr("fill",u(this.start).tweenTo(u(this.end),this.pos),void 0,!0)}function d(){this.elem.attr("stroke",u(this.start).tweenTo(u(this.end),this.pos),void 0,!0)}t.compose=function(t,c,u,m,b){let A=c.prototype,P=u.prototype,M=b.prototype;A.collectionsWithUpdate.includes("colorAxis")||(e=t,A.collectionsWithUpdate.push("colorAxis"),A.collectionsWithInit.colorAxis=[A.addColorAxis],g(c,"afterCreateAxes",i),function(t){let i=t.prototype.createAxis;t.prototype.createAxis=function(t,s){if("colorAxis"!==t)return i.apply(this,arguments);let o=new e(this,f(s.axis,{index:this[t].length,isX:!1}));return this.isDirtyLegend=!0,this.axes.forEach(t=>{t.series=[]}),this.series.forEach(t=>{t.bindAxes(),t.isDirtyData=!0}),y(s.redraw,!0)&&this.redraw(s.animation),o}}(c),P.fillSetter=p,P.strokeSetter=d,g(m,"afterGetAllItems",s),g(m,"afterColorizeItem",o),g(m,"afterUpdate",a),x(M,{optionalAxis:"colorAxis",translateColors:h}),x(M.pointClass.prototype,{setVisible:l}),g(b,"afterTranslate",r,{order:1}),g(b,"bindAxes",n))},t.pointSetVisible=l}(s||(s={}));let b=s,{series:{prototype:{pointClass:A}},seriesTypes:{heatmap:{prototype:{pointClass:P}}}}=d(),{extend:M}=h();class L extends P{haloPath(){return this.series.tileShape.haloPath.apply(this,arguments)}}M(L.prototype,{setState:A.prototype.setState,setVisible:b.pointSetVisible});let{noop:v}=h(),{heatmap:S,scatter:C}=d().seriesTypes,{clamp:w,pick:T}=h();function D(t,e,i){let s=t.options;return{xPad:-((s.colsize||1)/e),yPad:-((s.rowsize||1)/i)}}let I={hexagon:{alignDataLabel:C.prototype.alignDataLabel,getSeriesPadding:function(t){return D(t,3,2)},haloPath:function(t){if(!t)return[];let e=this.tileEdges;return[["M",e.x2-t,e.y1+t],["L",e.x3+t,e.y1+t],["L",e.x4+1.5*t,e.y2],["L",e.x3+t,e.y3-t],["L",e.x2-t,e.y3-t],["L",e.x1-1.5*t,e.y2],["Z"]]},translate:function(){let t;let e=this.options,i=this.xAxis,s=this.yAxis,o=e.pointPadding||0,a=(e.colsize||1)/3,r=(e.rowsize||1)/2;for(let e of(this.generatePoints(),this.points)){let n=w(Math.floor(i.len-i.translate(e.x-2*a,0,1,0,1)),-i.len,2*i.len),l=w(Math.floor(i.len-i.translate(e.x-a,0,1,0,1)),-i.len,2*i.len),h=w(Math.floor(i.len-i.translate(e.x+a,0,1,0,1)),-i.len,2*i.len),p=w(Math.floor(i.len-i.translate(e.x+2*a,0,1,0,1)),-i.len,2*i.len),d=w(Math.floor(s.translate(e.y-r,0,1,0,1)),-s.len,2*s.len),c=w(Math.floor(s.translate(e.y,0,1,0,1)),-s.len,2*s.len),u=w(Math.floor(s.translate(e.y+r,0,1,0,1)),-s.len,2*s.len),g=e.pointPadding??o,x=g*Math.abs(l-n)/Math.abs(u-c),f=i.reversed?-x:x,y=i.reversed?-g:g,m=s.reversed?-g:g;e.x%2&&(t=t||Math.round(Math.abs(u-d)/2)*(s.reversed?-1:1),d+=t,c+=t,u+=t),e.plotX=e.clientX=(l+h)/2,e.plotY=c,n+=f+y,l+=y,h-=y,p-=f+y,d-=m,u+=m,e.tileEdges={x1:n,x2:l,x3:h,x4:p,y1:d,y2:c,y3:u},e.shapeType="path",e.shapeArgs={d:[["M",l,d],["L",h,d],["L",p,c],["L",h,u],["L",l,u],["L",n,c],["Z"]]}}this.translateColors()}},diamond:{alignDataLabel:C.prototype.alignDataLabel,getSeriesPadding:function(t){return D(t,2,2)},haloPath:function(t){if(!t)return[];let e=this.tileEdges;return[["M",e.x2,e.y1+t],["L",e.x3+t,e.y2],["L",e.x2,e.y3-t],["L",e.x1-t,e.y2],["Z"]]},translate:function(){let t;let e=this.options,i=this.xAxis,s=this.yAxis,o=e.pointPadding||0,a=e.colsize||1,r=(e.rowsize||1)/2;for(let e of(this.generatePoints(),this.points)){let n=w(Math.round(i.len-i.translate(e.x-a,0,1,0,0)),-i.len,2*i.len),l=w(Math.round(i.len-i.translate(e.x+a,0,1,0,0)),-i.len,2*i.len),h=w(Math.round(s.translate(e.y-r,0,1,0,0)),-s.len,2*s.len),p=w(Math.round(s.translate(e.y,0,1,0,0)),-s.len,2*s.len),d=w(Math.round(s.translate(e.y+r,0,1,0,0)),-s.len,2*s.len),c=w(Math.round(i.len-i.translate(e.x,0,1,0,0)),-i.len,2*i.len),u=T(e.pointPadding,o),g=u*Math.abs(c-n)/Math.abs(d-p),x=i.reversed?-g:g,f=s.reversed?-u:u;e.x%2&&(t=Math.abs(d-h)/2*(s.reversed?-1:1),h+=t,p+=t,d+=t),e.plotX=e.clientX=c,e.plotY=p,n+=x,l-=x,h-=f,d+=f,e.tileEdges={x1:n,x2:c,x3:l,y1:h,y2:p,y3:d},e.shapeType="path",e.shapeArgs={d:[["M",c,h],["L",l,p],["L",c,d],["L",n,p],["Z"]]}}this.translateColors()}},circle:{alignDataLabel:C.prototype.alignDataLabel,getSeriesPadding:function(t){return D(t,2,2)},haloPath:function(t){return C.prototype.pointClass.prototype.haloPath.call(this,t+(t&&this.radius))},translate:function(){let t=this.options,e=this.xAxis,i=this.yAxis,s=t.pointPadding||0,o=(t.rowsize||1)/2,a=t.colsize||1,r,n,l,h,p=!1;for(let t of(this.generatePoints(),this.points)){let d=w(Math.round(e.len-e.translate(t.x,0,1,0,0)),-e.len,2*e.len),c=s,u=!1,g=w(Math.round(i.translate(t.y,0,1,0,0)),-i.len,2*i.len);void 0!==t.pointPadding&&(c=t.pointPadding,u=!0,p=!0),(!h||p)&&(l=Math.floor(Math.sqrt((r=Math.abs(w(Math.floor(e.len-e.translate(t.x+a,0,1,0,0)),-e.len,2*e.len)-d))*r+(n=Math.abs(w(Math.floor(i.translate(t.y+o,0,1,0,0)),-i.len,2*i.len)-g))*n)/2),h=Math.min(r,l,n)-c,p&&!u&&(p=!1)),t.x%2&&(g+=n*(i.reversed?-1:1)),t.plotX=t.clientX=d,t.plotY=g,t.radius=h,t.shapeType="circle",t.shapeArgs={x:d,y:g,r:h}}this.translateColors()}},square:{alignDataLabel:S.prototype.alignDataLabel,translate:S.prototype.translate,getSeriesPadding:v,haloPath:S.prototype.pointClass.prototype.haloPath}},{composed:E,noop:z}=h(),{column:H,heatmap:O,scatter:X}=d().seriesTypes,{addEvent:_,extend:F,merge:k,pushUnique:j}=h();function R(){if(this.recomputingForTilemap||"colorAxis"===this.coll)return;let t=this,e=t.series.map(function(e){return e.getSeriesPixelPadding&&e.getSeriesPixelPadding(t)}).reduce(function(t,e){return(t&&t.padding)>(e&&e.padding)?t:e},void 0)||{padding:0,axisLengthFactor:1},i=Math.round(e.padding*e.axisLengthFactor);e.padding&&(t.len-=i,t.recomputingForTilemap=!0,t.setAxisTranslation(),delete t.recomputingForTilemap,t.minPixelPadding+=e.padding,t.len+=i)}class V extends O{static compose(t){j(E,"TilemapSeries")&&_(t,"afterSetAxisTranslation",R)}alignDataLabel(){return this.tileShape.alignDataLabel.apply(this,arguments)}drawPoints(){for(let t of(H.prototype.drawPoints.call(this),this.points))t.graphic&&t.graphic[this.chart.styledMode?"css":"animate"](this.colorAttribs(t))}getSeriesPixelPadding(t){let e=t.isXAxis,i=this.tileShape.getSeriesPadding(this);if(!i)return{padding:0,axisLengthFactor:1};let s=Math.round(t.translate(e?2*i.xPad:i.yPad,0,1,0,1)),o=Math.round(t.translate(e?i.xPad:0,0,1,0,1));return{padding:(t.single?Math.abs(s-o)/2:Math.abs(s-o))||0,axisLengthFactor:e?2:1.1}}setOptions(){let t=super.setOptions.apply(this,arguments);return this.tileShape=I[t.tileShape],t}translate(){return this.tileShape.translate.apply(this,arguments)}}V.defaultOptions=k(O.defaultOptions,{marker:null,states:{hover:{halo:{enabled:!0,size:2,opacity:.5,attributes:{zIndex:3}}}},pointPadding:2,tileShape:"hexagon"}),F(V.prototype,{getSymbol:z,markerAttribs:X.prototype.markerAttribs,pointAttribs:H.prototype.pointAttribs,pointClass:L}),d().registerSeriesType("tilemap",V);let Z=h();V.compose(Z.Axis);let U=h();return n.default})());