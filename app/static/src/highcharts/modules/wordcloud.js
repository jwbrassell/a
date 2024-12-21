!/**
 * Highcharts JS v12.0.2 (2024-12-04)
 * @module highcharts/modules/wordcloud
 * @requires highcharts
 *
 * (c) 2016-2024 Highsoft AS
 * Authors: Jon Arild Nygard
 *
 * License: www.highcharts.com/license
 */function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e(t._Highcharts,t._Highcharts.SeriesRegistry):"function"==typeof define&&define.amd?define("highcharts/modules/wordcloud",["highcharts/highcharts"],function(t){return e(t,t.SeriesRegistry)}):"object"==typeof exports?exports["highcharts/modules/wordcloud"]=e(t._Highcharts,t._Highcharts.SeriesRegistry):t.Highcharts=e(t.Highcharts,t.Highcharts.SeriesRegistry)}("undefined"==typeof window?this:window,(t,e)=>(()=>{"use strict";var i={512:t=>{t.exports=e},944:e=>{e.exports=t}},o={};function n(t){var e=o[t];if(void 0!==e)return e.exports;var r=o[t]={exports:{}};return i[t](r,r.exports,n),r.exports}n.n=t=>{var e=t&&t.__esModule?()=>t.default:()=>t;return n.d(e,{a:e}),e},n.d=(t,e)=>{for(var i in e)n.o(e,i)&&!n.o(t,i)&&Object.defineProperty(t,i,{enumerable:!0,get:e[i]})},n.o=(t,e)=>Object.prototype.hasOwnProperty.call(t,e);var r={};n.d(r,{default:()=>Z});var a=n(944),l=/*#__PURE__*/n.n(a);let s={draw:function(t,e){let{animatableAttribs:i,onComplete:o,css:n,renderer:r}=e,a=t.series&&t.series.chart.hasRendered?void 0:t.series&&t.series.options.animation,l=t.graphic;if(e.attribs={...e.attribs,class:t.getClassName()},t.shouldDraw())l||(l="text"===e.shapeType?r.text():"image"===e.shapeType?r.image(e.imageUrl||"").attr(e.shapeArgs||{}):r[e.shapeType](e.shapeArgs||{}),t.graphic=l,l.add(e.group)),n&&l.css(n),l.attr(e.attribs).animate(i,!e.isNew&&a,o);else if(l){let e=()=>{t.graphic=l=l&&l.destroy(),"function"==typeof o&&o()};Object.keys(i).length?l.animate(i,void 0,()=>e()):e()}}};var h=n(512),d=/*#__PURE__*/n.n(h);let{column:{prototype:{pointClass:p}}}=d().seriesTypes,{extend:u}=l();class g extends p{isValid(){return!0}}u(g.prototype,{weight:1});let{deg2rad:c}=l(),{extend:m,find:f,isNumber:x,isObject:y,merge:b}=l();function w(t,e){return!(e.left>t.right||e.right<t.left||e.top>t.bottom||e.bottom<t.top)}function M(t){let e,i=t.axes||[];return i.length||(i=[],t.concat([t[0]]).reduce((t,e)=>{let o=function(t,e){let i=e[0]-t[0],o=e[1]-t[1];return[[-o,i],[o,-i]]}(t,e)[0];return f(i,t=>t[0]===o[0]&&t[1]===o[1])||i.push(o),e}),t.axes=i),i}function S(t,e){let i=t.map(t=>{let i=t[0],o=t[1];return i*e[0]+o*e[1]});return{min:Math.min.apply(this,i),max:Math.max.apply(this,i)}}function F(t,e){let i=M(t),o=M(e);return!f(i.concat(o),i=>(function(t,e,i){let o=S(e,t),n=S(i,t);return!!(n.min>o.max||n.max<o.min)})(i,t,e))}function P(t,e){let i=4*t,o=Math.ceil((Math.sqrt(i)-1)/2),n=2*o+1,r=Math.pow(n,2),a=!1;return n-=1,t<=1e4&&("boolean"==typeof a&&i>=r-n&&(a={x:o-(r-i),y:-o}),r-=n,"boolean"==typeof a&&i>=r-n&&(a={x:-o,y:-o+(r-i)}),r-=n,"boolean"==typeof a&&(a=i>=r-n?{x:-o+(r-i),y:o}:{x:o,y:o-(r-i-n)}),a.x*=5,a.y*=5),a}function A(t,e){let i=Math.pow(10,x(e)?e:14);return Math.round(t*i)/i}function v(t,e){let i=t[0],o=t[1],n=-(c*e),r=Math.cos(n),a=Math.sin(n);return[A(i*r-o*a),A(i*a+o*r)]}function T(t,e,i){let o=v([t[0]-e[0],t[1]-e[1]],i);return[o[0]+e[0],o[1]+e[1]]}let{noop:H}=l(),{column:z}=d().seriesTypes,{extend:R,isArray:X,isNumber:B,isObject:C,merge:W}=l(),{archimedeanSpiral:_,extendPlayingField:N,getBoundingBoxFromPolygon:O,getPlayingField:D,getPolygon:j,getRandomPosition:Y,getRotation:E,getScale:L,getSpiral:U,intersectionTesting:V,isPolygonsColliding:q,rectangularSpiral:k,rotate2DToOrigin:I,rotate2DToPoint:G,squareSpiral:J,updateFieldBoundaries:K}={archimedeanSpiral:function(t,e){let i=e.field,o=i.width*i.width+i.height*i.height,n=.8*t,r=!1;return t<=1e4&&!(Math.min(Math.abs((r={x:n*Math.cos(n),y:n*Math.sin(n)}).x),Math.abs(r.y))<o)&&(r=!1),r},extendPlayingField:function(t,e){let i,o,n,r,a,l,s,h;return y(t)&&y(e)?(i=e.bottom-e.top,l=(a=(o=e.right-e.left)*(n=t.ratioX)>i*(r=t.ratioY)?o:i)*n,s=a*r,h=b(t,{width:t.width+2*l,height:t.height+2*s})):h=t,h},getBoundingBoxFromPolygon:function(t){return t.reduce(function(t,e){let i=e[0],o=e[1];return t.left=Math.min(i,t.left),t.right=Math.max(i,t.right),t.bottom=Math.max(o,t.bottom),t.top=Math.min(o,t.top),t},{left:Number.MAX_VALUE,right:-Number.MAX_VALUE,bottom:-Number.MAX_VALUE,top:Number.MAX_VALUE})},getPlayingField:function(t,e,i){let o=i.reduce(function(t,e){let i=e.dimensions,o=Math.max(i.width,i.height);return t.maxHeight=Math.max(t.maxHeight,i.height),t.maxWidth=Math.max(t.maxWidth,i.width),t.area+=o*o,t},{maxHeight:0,maxWidth:0,area:0}),n=Math.max(o.maxHeight,o.maxWidth,.85*Math.sqrt(o.area)),r=t>e?t/e:1,a=e>t?e/t:1;return{width:n*r,height:n*a,ratioX:r,ratioY:a}},getPolygon:function(t,e,i,o,n){let r=[t,e],a=t-i/2,l=t+i/2,s=e-o/2,h=e+o/2;return[[a,s],[l,s],[l,h],[a,h]].map(function(t){return T(t,r,-n)})},getRandomPosition:function(t){return Math.round(t*(Math.random()+.5)/2)},getRotation:function(t,e,i,o){let n=!1,r;return x(t)&&x(e)&&x(i)&&x(o)&&t>0&&e>-1&&o>i&&(r=(o-i)/(t-1||1),n=i+e%t*r),n},getScale:function(t,e,i){let o=2*Math.max(Math.abs(i.top),Math.abs(i.bottom)),n=2*Math.max(Math.abs(i.left),Math.abs(i.right));return Math.min(n>0?1/n*t:1,o>0?1/o*e:1)},getSpiral:function(t,e){let i=[];for(let o=1;o<1e4;o++)i.push(t(o,e));return t=>t<=1e4&&i[t-1]},intersectionTesting:function(t,e){let i=e.placed,o=e.field,n=e.rectangle,r=e.polygon,a=e.spiral,l=t.rect=m({},n),s=1,h={x:0,y:0};for(t.polygon=r,t.rotation=e.rotation;!1!==h&&(function(t,e){let i=t.rect,o=t.polygon,n=t.lastCollidedWith,r=function(e){let n=w(i,e.rect);return n&&(t.rotation%90||e.rotation%90)&&(n=F(o,e.polygon)),n},a=!1;return!n||(a=r(n))||delete t.lastCollidedWith,a||(a=!!f(e,function(e){let i=r(e);return i&&(t.lastCollidedWith=e),i})),a}(t,i)||function(t,e){let i={left:-(e.width/2),right:e.width/2,top:-(e.height/2),bottom:e.height/2};return!(i.left<t.left&&i.right>t.right&&i.top<t.top&&i.bottom>t.bottom)}(l,o));)y(h=a(s))&&(l.left=n.left+h.x,l.right=n.right+h.x,l.top=n.top+h.y,l.bottom=n.bottom+h.y,t.polygon=function(t,e,i){return i.map(function(i){return[i[0]+t,i[1]+e]})}(h.x,h.y,r)),s++;return h},isPolygonsColliding:F,isRectanglesIntersecting:w,rectangularSpiral:function(t,e){let i=P(t,e),o=e.field;return i&&(i.x*=o.ratioX,i.y*=o.ratioY),i},rotate2DToOrigin:v,rotate2DToPoint:T,squareSpiral:P,updateFieldBoundaries:function(t,e){return(!x(t.left)||t.left>e.left)&&(t.left=e.left),(!x(t.right)||t.right<e.right)&&(t.right=e.right),(!x(t.top)||t.top>e.top)&&(t.top=e.top),(!x(t.bottom)||t.bottom<e.bottom)&&(t.bottom=e.bottom),t}};class Q extends z{pointAttribs(t,e){let i=l().seriesTypes.column.prototype.pointAttribs.call(this,t,e);return delete i.stroke,delete i["stroke-width"],i}deriveFontSize(t,e,i){let o=B(t)?t:0,n=B(e)?e:1;return Math.floor(Math.max(B(i)?i:1,o*n))}drawPoints(){let t=this.hasRendered,e=this.xAxis,i=this.yAxis,o=this.chart,n=this.group,r=this.options,a=r.animation,l=r.allowExtendPlayingField,h=o.renderer,d=[],p=this.placementStrategy[r.placementStrategy],u=r.rotation,g=this.points.map(function(t){return t.weight}),c=Math.max.apply(null,g),m=this.points.concat().sort((t,e)=>e.weight-t.weight),f=h.text().add(n),x;for(let t of(this.group.attr({scaleX:1,scaleY:1}),m)){let e=1/c*t.weight,i=R({fontSize:this.deriveFontSize(e,r.maxFontSize,r.minFontSize)+"px"},r.style);f.css(i).attr({x:0,y:0,text:t.name});let o=f.getBBox(!0);t.dimensions={height:o.height,width:o.width}}x=D(e.len,i.len,m);let y=U(this.spirals[r.spiral],{field:x});for(let e of m){let i=1/c*e.weight,o=R({fontSize:this.deriveFontSize(i,r.maxFontSize,r.minFontSize)+"px"},r.style),g=p(e,{data:m,field:x,placed:d,rotation:u}),f=R(this.pointAttribs(e,e.selected&&"select"),{align:"center","alignment-baseline":"middle","dominant-baseline":"middle",x:g.x,y:g.y,text:e.name,rotation:B(g.rotation)?g.rotation:void 0}),b=j(g.x,g.y,e.dimensions.width,e.dimensions.height,g.rotation),w=O(b),M=V(e,{rectangle:w,polygon:b,field:x,placed:d,spiral:y,rotation:g.rotation}),S;!M&&l&&(x=N(x,w),M=V(e,{rectangle:w,polygon:b,field:x,placed:d,spiral:y,rotation:g.rotation})),C(M)?(f.x=(f.x||0)+M.x,f.y=(f.y||0)+M.y,w.left+=M.x,w.right+=M.x,w.top+=M.y,w.bottom+=M.y,x=K(x,w),d.push(e),e.isNull=!1,e.isInside=!0):e.isNull=!0,a&&(S={x:f.x,y:f.y},t?(delete f.x,delete f.y):(f.x=0,f.y=0)),s.draw(e,{animatableAttribs:S,attribs:f,css:o,group:n,renderer:h,shapeArgs:void 0,shapeType:"text"})}f=f.destroy();let b=L(e.len,i.len,x);this.group.attr({scaleX:b,scaleY:b})}hasData(){return C(this)&&!0===this.visible&&X(this.points)&&this.points.length>0}getPlotBox(){let t=this.chart,e=t.inverted,i=this[e?"yAxis":"xAxis"],o=this[e?"xAxis":"yAxis"],n=i?i.len:t.plotWidth,r=o?o.len:t.plotHeight;return{translateX:(i?i.left:t.plotLeft)+n/2,translateY:(o?o.top:t.plotTop)+r/2,scaleX:1,scaleY:1}}}Q.defaultOptions=W(z.defaultOptions,{allowExtendPlayingField:!0,animation:{duration:500},borderWidth:0,clip:!1,colorByPoint:!0,cropThreshold:1/0,minFontSize:1,maxFontSize:25,placementStrategy:"center",rotation:{from:0,orientations:2,to:90},showInLegend:!1,spiral:"rectangular",style:{fontFamily:"sans-serif",fontWeight:"900",whiteSpace:"nowrap"},tooltip:{followPointer:!0,pointFormat:'<span style="color:{point.color}">●</span> {series.name}: <b>{point.weight}</b><br/>'}}),R(Q.prototype,{animate:H,animateDrilldown:H,animateDrillupFrom:H,isCartesian:!1,pointClass:g,setClip:H,placementStrategy:{random:function(t,e){let i=e.field,o=e.rotation;return{x:Y(i.width)-i.width/2,y:Y(i.height)-i.height/2,rotation:E(o.orientations,t.index,o.from,o.to)}},center:function(t,e){let i=e.rotation;return{x:0,y:0,rotation:E(i.orientations,t.index,i.from,i.to)}}},pointArrayMap:["weight"],spirals:{archimedean:_,rectangular:k,square:J},utils:{extendPlayingField:N,getRotation:E,isPolygonsColliding:q,rotate2DToOrigin:I,rotate2DToPoint:G}}),d().registerSeriesType("wordcloud",Q);let Z=l();return r.default})());