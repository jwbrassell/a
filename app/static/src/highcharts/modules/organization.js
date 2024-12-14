!/**
 * Highcharts JS v12.0.2 (2024-12-04)
 * Organization chart series type
 * @module highcharts/modules/organization
 * @requires highcharts
 * @requires highcharts/modules/sankey
 *
 * (c) 2019-2024 Torstein Honsi
 *
 * License: www.highcharts.com/license
 */function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e(t._Highcharts,t._Highcharts.SeriesRegistry,t._Highcharts.SVGElement):"function"==typeof define&&define.amd?define("highcharts/modules/organization",["highcharts/highcharts"],function(t){return e(t,t.SeriesRegistry,t.SVGElement)}):"object"==typeof exports?exports["highcharts/modules/organization"]=e(t._Highcharts,t._Highcharts.SeriesRegistry,t._Highcharts.SVGElement):t.Highcharts=e(t.Highcharts,t.Highcharts.SeriesRegistry,t.Highcharts.SVGElement)}("undefined"==typeof window?this:window,(t,e,i)=>(()=>{"use strict";var s={28:t=>{t.exports=i},512:t=>{t.exports=e},944:e=>{e.exports=t}},n={};function r(t){var e=n[t];if(void 0!==e)return e.exports;var i=n[t]={exports:{}};return s[t](i,i.exports,r),i.exports}r.n=t=>{var e=t&&t.__esModule?()=>t.default:()=>t;return r.d(e,{a:e}),e},r.d=(t,e)=>{for(var i in e)r.o(e,i)&&!r.o(t,i)&&Object.defineProperty(t,i,{enumerable:!0,get:e[i]})},r.o=(t,e)=>Object.prototype.hasOwnProperty.call(t,e);var o={};r.d(o,{default:()=>D});var a=r(944),h=/*#__PURE__*/r.n(a),l=r(512),d=/*#__PURE__*/r.n(l);let{sankey:{prototype:{pointClass:p}}}=d().seriesTypes,{defined:g,find:u,pick:c}=h(),f=class extends p{constructor(t,e,i){super(t,e,i),this.isNode||(this.dataLabelOnNull=!0,this.formatPrefix="link")}getSum(){return 1}setNodeColumn(){super.setNodeColumn();let t=this,e=t.getFromNode().fromNode;if(!g(t.options.column)&&0!==t.linksTo.length&&e&&"hanging"===e.options.layout){let i=-1,s;t.options.layout=c(t.options.layout,"hanging"),t.hangsFrom=e,u(e.linksFrom,(e,s)=>{let n=e.toNode===t;return n&&(i=s),n});for(let n=0;n<e.linksFrom.length;++n)(s=e.linksFrom[n]).toNode.id===t.id?n=e.linksFrom.length:i+=function t(e){let i=e.linksFrom.length;return e.linksFrom.forEach(e=>{e.id===e.toNode.linksTo[0].id?i+=t(e.toNode):i--}),i}(s.toNode);t.column=(t.column||0)+i}}},y={applyRadius:function(t,e){let i=[];for(let s=0;s<t.length;s++){let n=t[s][1],r=t[s][2];if("number"==typeof n&&"number"==typeof r){if(0===s)i.push(["M",n,r]);else if(s===t.length-1)i.push(["L",n,r]);else if(e){let o=t[s-1],a=t[s+1];if(o&&a){let t=o[1],s=o[2],h=a[1],l=a[2];if("number"==typeof t&&"number"==typeof h&&"number"==typeof s&&"number"==typeof l&&t!==h&&s!==l){let o=t<h?1:-1,a=s<l?1:-1;i.push(["L",n-o*Math.min(Math.abs(n-t),e),r-a*Math.min(Math.abs(r-s),e)],["C",n,r,n,r,n+o*Math.min(Math.abs(n-h),e),r+a*Math.min(Math.abs(r-l),e)])}}}else i.push(["L",n,r])}}return i}};var m=r(28),k=/*#__PURE__*/r.n(m);let{deg2rad:x}=h(),{addEvent:b,merge:A,uniqueKey:L,defined:w,extend:v}=h();function M(t,e){e=A(!0,{enabled:!0,attributes:{dy:-5,startOffset:"50%",textAnchor:"middle"}},e);let i=this.renderer.url,s=this.text||this,n=s.textPath,{attributes:r,enabled:o}=e;if(t=t||n&&n.path,n&&n.undo(),t&&o){let e=b(s,"afterModifyTree",e=>{if(t&&o){let n=t.attr("id");n||t.attr("id",n=L());let o={x:0,y:0};w(r.dx)&&(o.dx=r.dx,delete r.dx),w(r.dy)&&(o.dy=r.dy,delete r.dy),s.attr(o),this.attr({transform:""}),this.box&&(this.box=this.box.destroy());let a=e.nodes.slice(0);e.nodes.length=0,e.nodes[0]={tagName:"textPath",attributes:v(r,{"text-anchor":r.textAnchor,href:`${i}#${n}`}),children:a}}});s.textPath={path:t,undo:e}}else s.attr({dx:0,dy:0}),delete s.textPath;return this.added&&(s.textCache="",this.renderer.buildText(s)),this}function N(t){let e=t.bBox,i=this.element?.querySelector("textPath");if(i){let t=[],{b:s,h:n}=this.renderer.fontMetrics(this.element),r=n-s,o=RegExp('(<tspan>|<tspan(?!\\sclass="highcharts-br")[^>]*>|<\\/tspan>)',"g"),a=i.innerHTML.replace(o,"").split(/<tspan class="highcharts-br"[^>]*>/),h=a.length,l=(t,e)=>{let{x:n,y:o}=e,a=(i.getRotationOfChar(t)-90)*x,h=Math.cos(a),l=Math.sin(a);return[[n-r*h,o-r*l],[n+s*h,o+s*l]]};for(let e=0,s=0;s<h;s++){let n=a[s].length;for(let r=0;r<n;r+=5)try{let n=e+r+s,[o,a]=l(n,i.getStartPositionOfChar(n));0===r?(t.push(a),t.push(o)):(0===s&&t.unshift(a),s===h-1&&t.push(o))}catch(t){break}e+=n-1;try{let n=e+s,r=i.getEndPositionOfChar(n),[o,a]=l(n,r);t.unshift(a),t.unshift(o)}catch(t){break}}t.length&&t.push(t[0].slice()),e.polygon=t}return e}function P(t){let e=t.labelOptions,i=t.point,s=e[i.formatPrefix+"TextPath"]||e.textPath;s&&!e.useHTML&&(this.setTextPath(i.getDataLabelPath?.(this)||i.graphic,s),i.dataLabelPath&&!s.enabled&&(i.dataLabelPath=i.dataLabelPath.destroy()))}let{sankey:T}=d().seriesTypes,{css:O,crisp:S,extend:W,isNumber:F,merge:H,pick:C}=h();({compose:function(t){b(t,"afterGetBBox",N),b(t,"beforeAddingDataLabel",P);let e=t.prototype;e.setTextPath||(e.setTextPath=M)}}).compose(k());class R extends T{alignDataLabel(t,e,i){let s=t.shapeArgs;if(i.useHTML&&s){let t=this.options.borderWidth+2*this.options.dataLabels.padding,i=s.width||0,n=s.height||0;this.chart.inverted&&(i=n,n=s.width||0),n-=t,i-=t;let r=e.text;r&&(O(r.element.parentNode,{width:i+"px",height:n+"px"}),O(r.element,{left:0,top:0,width:"100%",height:"100%",overflow:"hidden"})),e.getBBox=()=>({width:i,height:n,x:0,y:0}),e.width=i,e.height=n}super.alignDataLabel.apply(this,arguments)}createNode(t){let e=super.createNode.call(this,t);return e.getSum=()=>1,e}pointAttribs(t,e){let i=T.prototype.pointAttribs.call(this,t,e),s=t.isNode?t.level:t.fromNode.level,n=this.mapOptionsToLevel[s||0]||{},r=t.options,o=n.states&&n.states[e]||{},a=C(o.borderRadius,r.borderRadius,n.borderRadius,this.options.borderRadius),h=C(o.linkColor,r.linkColor,n.linkColor,this.options.linkColor,o.link&&o.link.color,r.link&&r.link.color,n.link&&n.link.color,this.options.link&&this.options.link.color),l=C(o.linkLineWidth,r.linkLineWidth,n.linkLineWidth,this.options.linkLineWidth,o.link&&o.link.lineWidth,r.link&&r.link.lineWidth,n.link&&n.link.lineWidth,this.options.link&&this.options.link.lineWidth),d=C(o.linkOpacity,r.linkOpacity,n.linkOpacity,this.options.linkOpacity,o.link&&o.link.linkOpacity,r.link&&r.link.linkOpacity,n.link&&n.link.linkOpacity,this.options.link&&this.options.link.linkOpacity);return t.isNode?F(a)&&(i.r=a):(i.stroke=h,i["stroke-width"]=l,i.opacity=d,delete i.fill),i}translateLink(t){let e=this.chart,i=this.options,s=t.fromNode,n=t.toNode,r=C(i.linkLineWidth,i.link.lineWidth,0),o=C(i.link.offset,.5),a=C(t.options.link&&t.options.link.type,i.link.type);if(s.shapeArgs&&n.shapeArgs){let h=i.hangingIndent,l="right"===i.hangingSide,d=n.options.offset,p=/%$/.test(d)&&parseInt(d,10),g=e.inverted,u=S((s.shapeArgs.x||0)+(s.shapeArgs.width||0),r),c=S((s.shapeArgs.y||0)+(s.shapeArgs.height||0)/2,r),f=S(n.shapeArgs.x||0,r),m=S((n.shapeArgs.y||0)+(n.shapeArgs.height||0)/2,r),k;if(g&&(u-=s.shapeArgs.width||0,f+=n.shapeArgs.width||0),k=this.colDistance?S(f+(g?1:-1)*(this.colDistance-this.nodeWidth)/2,r):S((f+u)/2,r),p&&(p>=50||p<=-50)&&(k=f=S(f+(g?-.5:.5)*(n.shapeArgs.width||0),r),m=n.shapeArgs.y||0,p>0&&(m+=n.shapeArgs.height||0)),n.hangsFrom===s&&(e.inverted?(c=l?S((s.shapeArgs.y||0)+h/2,r):S((s.shapeArgs.y||0)+(s.shapeArgs.height||0)-h/2,r),m=l?(n.shapeArgs.y||0)+h/2:(n.shapeArgs.y||0)+(n.shapeArgs.height||0)):c=S((s.shapeArgs.y||0)+h/2,r),k=f=S((n.shapeArgs.x||0)+(n.shapeArgs.width||0)/2,r)),t.plotX=k,t.plotY=(c+m)/2,t.shapeType="path","straight"===a)t.shapeArgs={d:[["M",u,c],["L",f,m]]};else if("curved"===a){let e=Math.abs(f-u)*o*(g?-1:1);t.shapeArgs={d:[["M",u,c],["C",u+e,c,f-e,m,f,m]]}}else t.shapeArgs={d:y.applyRadius([["M",u,c],["L",k,c],["L",k,m],["L",f,m]],C(i.linkRadius,i.link.radius))};t.dlBox={x:(u+f)/2,y:(c+m)/2,height:r,width:0}}}translateNode(t,e){super.translateNode(t,e);let i=this.chart,s=this.options,n=Math.max(Math.round(t.getSum()*this.translationFactor),s.minLinkWidth||0),r="right"===s.hangingSide,o=s.hangingIndent||0,a=s.hangingIndentTranslation,h=s.minNodeLength||10,l=Math.round(this.nodeWidth),d=t.shapeArgs,p=i.inverted?-1:1,g=t.hangsFrom;if(g){if("cumulative"===a)for(d.height-=o,i.inverted&&!r&&(d.y-=p*o);g;)d.y+=(r?1:p)*o,g=g.hangsFrom;else if("shrink"===a)for(;g&&d.height>o+h;)d.height-=o,(!i.inverted||r)&&(d.y+=o),g=g.hangsFrom;else d.height-=o,(!i.inverted||r)&&(d.y+=o)}t.nodeHeight=i.inverted?d.width:d.height,t.shapeArgs&&!t.hangsFrom&&(t.shapeArgs=H(t.shapeArgs,{x:(t.shapeArgs.x||0)+l/2-(t.shapeArgs.width||0)/2,y:(t.shapeArgs.y||0)+n/2-(t.shapeArgs.height||0)/2}))}drawDataLabels(){let t=this.options.dataLabels;if(t.linkTextPath&&t.linkTextPath.enabled)for(let t of this.points)t.options.dataLabels=H(t.options.dataLabels,{useHTML:!1});super.drawDataLabels()}}R.defaultOptions=H(T.defaultOptions,{borderColor:"#666666",borderRadius:3,link:{color:"#666666",lineWidth:1,radius:10,type:"default"},borderWidth:1,dataLabels:{nodeFormatter:function(){let t={width:"100%",height:"100%",display:"flex","flex-direction":"row","align-items":"center","justify-content":"center"},e={"max-height":"100%","border-radius":"50%"},i={width:"100%",padding:0,"text-align":"center","white-space":"normal"};function s(t){return Object.keys(t).reduce(function(e,i){return e+i+":"+t[i]+";"},'style="')+'"'}let{description:n,image:r,title:o}=this.point;r&&(e["max-width"]="30%",i.width="70%"),this.series.chart.renderer.forExport&&(t.display="block",i.position="absolute",i.left=r?"30%":0,i.top=0);let a="<div "+s(t)+">";return r&&(a+='<img src="'+r+'" '+s(e)+">"),a+="<div "+s(i)+">",this.point.name&&(a+="<h4 "+s({margin:0})+">"+this.point.name+"</h4>"),o&&(a+="<p "+s({margin:0})+">"+(o||"")+"</p>"),n&&(a+="<p "+s({opacity:.75,margin:"5px"})+">"+n+"</p>"),a+="</div></div>"},style:{fontWeight:"normal",fontSize:"0.9em"},useHTML:!0,linkTextPath:{attributes:{startOffset:"95%",textAnchor:"end"}}},hangingIndent:20,hangingIndentTranslation:"inherit",hangingSide:"left",minNodeLength:10,nodeWidth:50,tooltip:{nodeFormat:"{point.name}<br>{point.title}<br>{point.description}"}}),W(R.prototype,{pointClass:f}),d().registerSeriesType("organization",R);let D=h();return o.default})());