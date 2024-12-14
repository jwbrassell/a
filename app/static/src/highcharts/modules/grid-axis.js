!/**
 * Highcharts Gantt JS v12.0.2 (2024-12-04)
 * @module highcharts/modules/grid-axis
 * @requires highcharts
 *
 * GridAxis
 *
 * (c) 2016-2024 Lars A. V. Cabrera
 *
 * License: www.highcharts.com/license
 */function(t,i){"object"==typeof exports&&"object"==typeof module?module.exports=i(t._Highcharts,t._Highcharts.Axis):"function"==typeof define&&define.amd?define("highcharts/modules/grid-axis",["highcharts/highcharts"],function(t){return i(t,t.Axis)}):"object"==typeof exports?exports["highcharts/modules/grid-axis"]=i(t._Highcharts,t._Highcharts.Axis):t.Highcharts=i(t.Highcharts,t.Highcharts.Axis)}("undefined"==typeof window?this:window,(t,i)=>(()=>{"use strict";var e,s={532:t=>{t.exports=i},944:i=>{i.exports=t}},r={};function o(t){var i=r[t];if(void 0!==i)return i.exports;var e=r[t]={exports:{}};return s[t](e,e.exports,o),e.exports}o.n=t=>{var i=t&&t.__esModule?()=>t.default:()=>t;return o.d(i,{a:i}),i},o.d=(t,i)=>{for(var e in i)o.o(i,e)&&!o.o(t,e)&&Object.defineProperty(t,e,{enumerable:!0,get:i[e]})},o.o=(t,i)=>Object.prototype.hasOwnProperty.call(t,i);var n={};o.d(n,{default:()=>_});var h=o(944),l=/*#__PURE__*/o.n(h),a=o(532),d=/*#__PURE__*/o.n(a);let{dateFormats:c}=l(),{addEvent:g,defined:f,erase:p,find:u,isArray:m,isNumber:x,merge:k,pick:b,timeUnits:P,wrap:y}=l();function w(t){return l().isObject(t,!0)}function L(t,i){let e={width:0,height:0};if(i.forEach(function(i){let s=t[i],r=0,o=0,n;w(s)&&(r=(n=w(s.label)?s.label:{}).getBBox?n.getBBox().height:0,n.textStr&&!x(n.textPxLength)&&(n.textPxLength=n.getBBox().width),o=x(n.textPxLength)?Math.round(n.textPxLength):0,n.textStr&&(o=Math.round(n.getBBox().width)),e.height=Math.max(r,e.height),e.width=Math.max(o,e.width))}),"treegrid"===this.type&&this.treeGrid&&this.treeGrid.mapOfPosToGridNode){let t=this.treeGrid.mapOfPosToGridNode[-1].height||0;e.width+=this.options.labels.indentation*(t-1)}return e}function B(t){let{grid:i}=this,e=3===this.side;if(e||t.apply(this),!i?.isColumn){let t=i?.columns||[];e&&(t=t.slice().reverse()),t.forEach(t=>{t.getOffset()})}e&&t.apply(this)}function v(t){if(!0===(this.options.grid||{}).enabled){let{axisTitle:i,height:s,horiz:r,left:o,offset:n,opposite:h,options:l,top:a,width:d}=this,c=this.tickSize(),g=i&&i.getBBox().width,f=l.title.x,p=l.title.y,u=b(l.title.margin,r?5:10),m=i?this.chart.renderer.fontMetrics(i).f:0,x=(r?a+s:o)+(r?1:-1)*(h?-1:1)*(c?c[0]/2:0)+(this.side===e.bottom?m:0);t.titlePosition.x=r?o-(g||0)/2-u+f:x+(h?d:0)+n+f,t.titlePosition.y=r?x-(h?s:0)+(h?m:-m)/2+n+p:a-u+p}}function O(){let{chart:t,options:{grid:i={}},userOptions:e}=this;if(i.enabled&&function(t){let i=t.options;i.labels.align=b(i.labels.align,"center"),t.categories||(i.showLastLabel=!1),t.labelRotation=0,i.labels.rotation=0,i.minTickInterval=1}(this),i.columns){let s=this.grid.columns=[],r=this.grid.columnIndex=0;for(;++r<i.columns.length;){let o=k(e,i.columns[r],{isInternal:!0,linkedTo:0,scrollbar:{enabled:!1}},{grid:{columns:void 0}}),n=new(d())(this.chart,o,"yAxis");n.grid.isColumn=!0,n.grid.columnIndex=r,p(t.axes,n),p(t[this.coll]||[],n),s.push(n)}}}function T(){let{axisTitle:t,grid:i,options:s}=this;if(!0===(s.grid||{}).enabled){let r=this.min||0,o=this.max||0,n=this.ticks[this.tickPositions[0]];if(t&&!this.chart.styledMode&&n?.slotWidth&&!this.options.title.style.width&&t.css({width:`${n.slotWidth}px`}),this.maxLabelDimensions=this.getMaxLabelDimensions(this.ticks,this.tickPositions),this.rightWall&&this.rightWall.destroy(),this.grid&&this.grid.isOuterAxis()&&this.axisLine){let t=s.lineWidth;if(t){let i=this.getLinePath(t),n=i[0],h=i[1],l=(this.tickSize("tick")||[1])[0]*(this.side===e.top||this.side===e.left?-1:1);if("M"===n[0]&&"L"===h[0]&&(this.horiz?(n[2]+=l,h[2]+=l):(n[1]+=l,h[1]+=l)),!this.horiz&&this.chart.marginRight){let t=["L",this.left,n[2]||0],i=[n,t],e=["L",this.chart.chartWidth-this.chart.marginRight,this.toPixels(o+this.tickmarkOffset)],l=[["M",h[1]||0,this.toPixels(o+this.tickmarkOffset)],e];this.grid.upperBorder||r%1==0||(this.grid.upperBorder=this.grid.renderBorder(i)),this.grid.upperBorder&&(this.grid.upperBorder.attr({stroke:s.lineColor,"stroke-width":s.lineWidth}),this.grid.upperBorder.animate({d:i})),this.grid.lowerBorder||o%1==0||(this.grid.lowerBorder=this.grid.renderBorder(l)),this.grid.lowerBorder&&(this.grid.lowerBorder.attr({stroke:s.lineColor,"stroke-width":s.lineWidth}),this.grid.lowerBorder.animate({d:l}))}this.grid.axisLineExtra?(this.grid.axisLineExtra.attr({stroke:s.lineColor,"stroke-width":s.lineWidth}),this.grid.axisLineExtra.animate({d:i})):this.grid.axisLineExtra=this.grid.renderBorder(i),this.axisLine[this.showAxis?"show":"hide"]()}}if((i&&i.columns||[]).forEach(t=>t.render()),!this.horiz&&this.chart.hasRendered&&(this.scrollbar||this.linkedParent&&this.linkedParent.scrollbar)&&this.tickPositions.length){let t,i;let e=this.tickmarkOffset,s=this.tickPositions[this.tickPositions.length-1],n=this.tickPositions[0];for(;(t=this.hiddenLabels.pop())&&t.element;)t.show();for(;(i=this.hiddenMarks.pop())&&i.element;)i.show();(t=this.ticks[n].label)&&(r-n>e?this.hiddenLabels.push(t.hide()):t.show()),(t=this.ticks[s].label)&&(s-o>e?this.hiddenLabels.push(t.hide()):t.show());let h=this.ticks[s].mark;h&&s-o<e&&s-o>0&&this.ticks[s].isLast&&this.hiddenMarks.push(h.hide())}}}function M(){let t=this.tickPositions&&this.tickPositions.info,i=this.options,e=i.grid||{},s=this.userOptions.labels||{};e.enabled&&(this.horiz?(this.series.forEach(t=>{t.options.pointRange=0}),t&&i.dateTimeLabelFormats&&i.labels&&!f(s.align)&&(!1===i.dateTimeLabelFormats[t.unitName].range||t.count>1)&&(i.labels.align="left",f(s.x)||(i.labels.x=3))):"treegrid"!==this.type&&this.grid&&this.grid.columns&&(this.minPointOffset=this.tickInterval))}function W(t){let i;let e=this.options,s=t.userOptions,r=e&&w(e.grid)?e.grid:{};!0===r.enabled&&(i=k(!0,{className:"highcharts-grid-axis "+(s.className||""),dateTimeLabelFormats:{hour:{list:["%[HM]","%[H]"]},day:{list:["%[AeB]","%[aeb]","%[E]"]},week:{list:["Week %W","W%W"]},month:{list:["%[B]","%[b]","%o"]}},grid:{borderWidth:1},labels:{padding:2,style:{fontSize:"0.9em"}},margin:0,title:{text:null,reserveSpace:!1,rotation:0,style:{textOverflow:"ellipsis"}},units:[["millisecond",[1,10,100]],["second",[1,10]],["minute",[1,5,15]],["hour",[1,6]],["day",[1]],["week",[1]],["month",[1]],["year",null]]},s),"xAxis"!==this.coll||(f(s.linkedTo)&&!f(s.tickPixelInterval)&&(i.tickPixelInterval=350),!(!f(s.tickPixelInterval)&&f(s.linkedTo))||f(s.tickPositioner)||f(s.tickInterval)||f(s.units)||(i.tickPositioner=function(t,e){let s=this.linkedParent&&this.linkedParent.tickPositions&&this.linkedParent.tickPositions.info;if(s){let r=i.units||[],o,n=1,h="year";for(let t=0;t<r.length;t++){let i=r[t];if(i&&i[0]===s.unitName){o=t;break}}let l=x(o)&&r[o+1];if(l){h=l[0]||"year";let t=l[1];n=t&&t[0]||1}else"year"===s.unitName&&(n=10*s.count);let a=P[h];return this.tickInterval=a*n,this.chart.time.getTimeTicks({unitRange:a,count:n,unitName:h},t,e,this.options.startOfWeek)}})),k(!0,this.options,i),this.horiz&&(e.minPadding=b(s.minPadding,0),e.maxPadding=b(s.maxPadding,0)),x(e.grid.borderWidth)&&(e.tickWidth=e.lineWidth=r.borderWidth))}function S(t){let i=t.userOptions,e=i&&i.grid||{},s=e.columns;e.enabled&&s&&k(!0,this.options,s[0])}function A(){(this.grid.columns||[]).forEach(t=>t.setScale())}function z(t){let{horiz:i,maxLabelDimensions:e,options:{grid:s={}}}=this;if(s.enabled&&e){let r=2*this.options.labels.distance,o=i?s.cellHeight||r+e.height:r+e.width;m(t.tickSize)?t.tickSize[0]=o:t.tickSize=[o,0]}}function E(){this.axes.forEach(t=>{(t.grid&&t.grid.columns||[]).forEach(t=>{t.setAxisSize(),t.setAxisTranslation()})})}function I(t){let{grid:i}=this;(i.columns||[]).forEach(i=>i.destroy(t.keepEvents)),i.columns=void 0}function C(t){let i=t.userOptions||{},e=i.grid||{};e.enabled&&f(e.borderColor)&&(i.tickColor=i.lineColor=e.borderColor),this.grid||(this.grid=new F(this)),this.hiddenLabels=[],this.hiddenMarks=[]}function H(t){let i=this.label,s=this.axis,r=s.reversed,o=s.chart,n=s.options.grid||{},h=s.options.labels,l=h.align,a=e[s.side],d=t.tickmarkOffset,c=s.tickPositions,g=this.pos-d,f=x(c[t.index+1])?c[t.index+1]-d:(s.max||0)+d,p=s.tickSize("tick"),u=p?p[0]:0,m=p?p[1]/2:0;if(!0===n.enabled){let e,n,d,c;if("top"===a?n=(e=s.top+s.offset)-u:"bottom"===a?e=(n=o.chartHeight-s.bottom+s.offset)+u:(e=s.top+s.len-(s.translate(r?f:g)||0),n=s.top+s.len-(s.translate(r?g:f)||0)),"right"===a?c=(d=o.chartWidth-s.right+s.offset)+u:"left"===a?d=(c=s.left+s.offset)-u:(d=Math.round(s.left+(s.translate(r?f:g)||0))-m,c=Math.min(Math.round(s.left+(s.translate(r?g:f)||0))-m,s.left+s.len)),this.slotWidth=c-d,t.pos.x="left"===l?d:"right"===l?c:d+(c-d)/2,t.pos.y=n+(e-n)/2,i){let e=o.renderer.fontMetrics(i),s=i.getBBox().height;if(h.useHTML)t.pos.y+=e.b+-(s/2);else{let i=Math.round(s/e.h);t.pos.y+=(e.b-(e.h-e.f))/2+-((i-1)*e.h/2)}}t.pos.x+=s.horiz&&h.x||0}}function G(t){let{axis:i,value:e}=t;if(i.options.grid&&i.options.grid.enabled){let s;let r=i.tickPositions,o=(i.linkedParent||i).series[0],n=e===r[0],h=e===r[r.length-1],a=o&&u(o.options.data,function(t){return t[i.isXAxis?"x":"y"]===e});a&&o.is("gantt")&&(s=k(a),l().seriesTypes.gantt.prototype.pointClass.setGanttPointAliases(s,i.chart)),t.isFirst=n,t.isLast=h,t.point=s}}function N(){let t=this.options,i=t.grid||{},e=this.categories,s=this.tickPositions,r=s[0],o=s[1],n=s[s.length-1],h=s[s.length-2],l=this.linkedParent&&this.linkedParent.min,a=this.linkedParent&&this.linkedParent.max,d=l||this.min,c=a||this.max,g=this.tickInterval,f=x(d)&&d>=r+g&&d<o,p=x(d)&&r<d&&r+g>d,u=x(c)&&n>c&&n-g<c,m=x(c)&&c<=n-g&&c>h;!0===i.enabled&&!e&&(this.isXAxis||this.isLinked)&&((p||f)&&!t.startOnTick&&(s[0]=d),(u||m)&&!t.endOnTick&&(s[s.length-1]=c))}function j(t){var i;let{options:{grid:e={}}}=this;return!0===e.enabled&&this.categories?this.tickInterval:t.apply(this,(i=arguments,Array.prototype.slice.call(i,1)))}!function(t){t[t.top=0]="top",t[t.right=1]="right",t[t.bottom=2]="bottom",t[t.left=3]="left"}(e||(e={}));class F{constructor(t){this.axis=t}isOuterAxis(){let t=this.axis,i=t.chart,e=t.grid.columnIndex,s=t.linkedParent?.grid.columns||t.grid.columns||[],r=e?t.linkedParent:t,o=-1,n=0;return 3===t.side&&!i.inverted&&s.length?!t.linkedParent:((i[t.coll]||[]).forEach((i,e)=>{i.side!==t.side||i.options.isInternal||(n=e,i!==r||(o=e))}),n===o&&(!x(e)||s.length===e))}renderBorder(t){let i=this.axis,e=i.chart.renderer,s=i.options,r=e.path(t).addClass("highcharts-axis-line").add(i.axisGroup);return e.styledMode||r.attr({stroke:s.lineColor,"stroke-width":s.lineWidth,zIndex:7}),r}}c.E=function(t){return this.dateFormat("%a",t,!0).charAt(0)},c.W=function(t){let i=this.toParts(t),e=(i[7]+6)%7,s=i.slice(0);s[2]=i[2]-e+3;let r=this.toParts(this.makeTime(s[0],0,1));return 4!==r[7]&&(i[1]=0,i[2]=1+(11-r[7])%7),(1+Math.floor((this.makeTime(s[0],s[1],s[2])-this.makeTime(r[0],r[1],r[2]))/6048e5)).toString()};let R=l();({compose:function(t,i,e){return t.keepProps.includes("grid")||(t.keepProps.push("grid"),t.prototype.getMaxLabelDimensions=L,y(t.prototype,"unsquish",j),y(t.prototype,"getOffset",B),g(t,"init",C),g(t,"afterGetTitlePosition",v),g(t,"afterInit",O),g(t,"afterRender",T),g(t,"afterSetAxisTranslation",M),g(t,"afterSetOptions",W),g(t,"afterSetOptions",S),g(t,"afterSetScale",A),g(t,"afterTickSize",z),g(t,"trimTicks",N),g(t,"destroy",I),g(i,"afterSetChartSize",E),g(e,"afterGetLabelPosition",H),g(e,"labelFormat",G)),t}}).compose(R.Axis,R.Chart,R.Tick);let _=l();return n.default})());