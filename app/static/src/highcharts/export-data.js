!/**
 * Highcharts JS v12.0.1 (2024-11-28)
 * @module highcharts/modules/export-data
 * @requires highcharts
 * @requires highcharts/modules/exporting
 *
 * Exporting module
 *
 * (c) 2010-2024 Torstein Honsi
 *
 * License: www.highcharts.com/license
 */function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e(require("highcharts"),require("highcharts").AST):"function"==typeof define&&define.amd?define("highcharts/export-data",[["highcharts/highcharts"],["highcharts/highcharts","AST"]],e):"object"==typeof exports?exports["highcharts/export-data"]=e(require("highcharts"),require("highcharts").AST):t.Highcharts=e(t.Highcharts,t.Highcharts.AST)}(this,(t,e)=>(()=>{"use strict";var a={660:t=>{t.exports=e},944:e=>{e.exports=t}},o={};function i(t){var e=o[t];if(void 0!==e)return e.exports;var n=o[t]={exports:{}};return a[t](n,n.exports,i),n.exports}i.n=t=>{var e=t&&t.__esModule?()=>t.default:()=>t;return i.d(e,{a:e}),e},i.d=(t,e)=>{for(var a in e)i.o(e,a)&&!i.o(t,a)&&Object.defineProperty(t,a,{enumerable:!0,get:e[a]})},i.o=(t,e)=>Object.prototype.hasOwnProperty.call(t,e);var n={};i.d(n,{default:()=>W});var r=i(944),s=/*#__PURE__*/i.n(r);let{isSafari:l,win:h,win:{document:c}}=s(),d=h.URL||h.webkitURL||h;function p(t){let e=t.replace(/filename=.*;/,"").match(/data:([^;]*)(;base64)?,([A-Z+\d\/]+)/i);if(e&&e.length>3&&h.atob&&h.ArrayBuffer&&h.Uint8Array&&h.Blob&&d.createObjectURL){let t=h.atob(e[3]),a=new h.ArrayBuffer(t.length),o=new h.Uint8Array(a);for(let e=0;e<o.length;++e)o[e]=t.charCodeAt(e);return d.createObjectURL(new h.Blob([o],{type:e[1]}))}}let u={dataURLtoBlob:p,downloadURL:function(t,e){let a=h.navigator,o=c.createElement("a");if("string"!=typeof t&&!(t instanceof String)&&a.msSaveOrOpenBlob){a.msSaveOrOpenBlob(t,e);return}if(t=""+t,a.userAgent.length>1e3)throw Error("Input too long");let i=/Edge\/\d+/.test(a.userAgent);if((l&&"string"==typeof t&&0===t.indexOf("data:application/pdf")||i||t.length>2e6)&&!(t=p(t)||""))throw Error("Failed to convert to blob");if(void 0!==o.download)o.href=t,o.download=e,c.body.appendChild(o),o.click(),c.body.removeChild(o);else try{if(!h.open(t,"chart"))throw Error("Failed to open window")}catch{h.location.href=t}}};var g=i(660),m=/*#__PURE__*/i.n(g);let f={exporting:{csv:{annotations:{itemDelimiter:"; ",join:!1},columnHeaderFormatter:null,dateFormat:"%Y-%m-%d %H:%M:%S",decimalPoint:null,itemDelimiter:null,lineDelimiter:"\n"},showTable:!1,useMultiLevelHeaders:!0,useRowspanHeaders:!0,showExportInProgress:!0},lang:{downloadCSV:"Download CSV",downloadXLS:"Download XLS",exportData:{annotationHeader:"Annotations",categoryHeader:"Category",categoryDatetimeHeader:"DateTime"},viewData:"View data table",hideData:"Hide data table",exportInProgress:"Exporting..."}},{getOptions:x,setOptions:b}=s(),{downloadURL:y}=u,{doc:w,win:T}=s(),{addEvent:v,defined:D,extend:S,find:L,fireEvent:E,isNumber:A,pick:C}=s();function k(t){let e=!!this.options.exporting?.showExportInProgress,a=T.requestAnimationFrame||setTimeout;a(()=>{e&&this.showLoading(this.options.lang.exportInProgress),a(()=>{try{t.call(this)}finally{e&&this.hideLoading()}})})}function O(){k.call(this,()=>{let t=this.getCSV(!0);y(M(t,"text/csv")||"data:text/csv,\uFEFF"+encodeURIComponent(t),this.getFilename()+".csv")})}function R(){k.call(this,()=>{let t='<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40"><head>\x3c!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>Ark1</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]--\x3e<style>td{border:none;font-family: Calibri, sans-serif;} .number{mso-number-format:"0.00";} .text{ mso-number-format:"@";}</style><meta name=ProgId content=Excel.Sheet><meta charset=UTF-8></head><body>'+this.getTable(!0)+"</body></html>";y(M(t,"application/vnd.ms-excel")||"data:application/vnd.ms-excel;base64,"+T.btoa(unescape(encodeURIComponent(t))),this.getFilename()+".xls")})}function N(t){let e="",a=this.getDataRows(),o=this.options.exporting.csv,i=C(o.decimalPoint,","!==o.itemDelimiter&&t?1.1.toLocaleString()[1]:"."),n=C(o.itemDelimiter,","===i?";":","),r=o.lineDelimiter;return a.forEach((t,o)=>{let s="",l=t.length;for(;l--;)"string"==typeof(s=t[l])&&(s=`"${s}"`),"number"==typeof s&&"."!==i&&(s=s.toString().replace(".",i)),t[l]=s;t.length=a.length?a[0].length:0,e+=t.join(n),o<a.length-1&&(e+=r)}),e}function V(t){let e,a;let o=this.hasParallelCoordinates,i=this.time,n=this.options.exporting&&this.options.exporting.csv||{},r=this.xAxis,s={},l=[],h=[],c=[],d=this.options.lang.exportData,p=d.categoryHeader,u=d.categoryDatetimeHeader,g=function(e,a,o){if(n.columnHeaderFormatter){let t=n.columnHeaderFormatter(e,a,o);if(!1!==t)return t}return e?e.bindAxes?t?{columnTitle:o>1?a:e.name,topLevelColumnTitle:e.name}:e.name+(o>1?" ("+a+")":""):e.options.title&&e.options.title.text||(e.dateTime?u:p):p},m=function(t,e,a){let o={},i={};return e.forEach(function(e){let n=(t.keyToAxis&&t.keyToAxis[e]||e)+"Axis",r=A(a)?t.chart[n][a]:t[n];o[e]=r&&r.categories||[],i[e]=r&&r.dateTime}),{categoryMap:o,dateTimeValueAxisMap:i}},f=function(t,e){let a=t.pointArrayMap||["y"];return t.data.some(t=>void 0!==t.y&&t.name)&&e&&!e.categories&&"name"!==t.exportKey?["x",...a]:a},x=[],b,y,w,T=0,v,S;for(v in this.series.forEach(function(e){let a=e.options.keys,l=e.xAxis,d=a||f(e,l),p=d.length,u=!e.requireSorting&&{},b=r.indexOf(l),y=m(e,d),v,D;if(!1!==e.options.includeInDataExport&&!e.options.isInternal&&!1!==e.visible){for(L(x,function(t){return t[0]===b})||x.push([b,T]),D=0;D<p;)w=g(e,d[D],d.length),c.push(w.columnTitle||w),t&&h.push(w.topLevelColumnTitle||w),D++;v={chart:e.chart,autoIncrement:e.autoIncrement,options:e.options,pointArrayMap:e.pointArrayMap,index:e.index},e.options.data.forEach(function(t,a){let r,h,c;let g={series:v};o&&(y=m(e,d,a)),e.pointClass.prototype.applyOptions.apply(g,[t]);let f=e.data[a]&&e.data[a].name;if(r=(g.x??"")+","+f,D=0,(!l||"name"===e.exportKey||!o&&l&&l.hasNames&&f)&&(r=f),u&&(u[r]&&(r+="|"+a),u[r]=!0),s[r]){let t=`${r},${s[r].pointers[e.index]}`,a=r;s[r].pointers[e.index]&&(s[t]||(s[t]=[],s[t].xValues=[],s[t].pointers=[]),r=t),s[a].pointers[e.index]+=1}else{s[r]=[],s[r].xValues=[];let t=[];for(let a=0;a<e.chart.series.length;a++)t[a]=0;s[r].pointers=t,s[r].pointers[e.index]=1}for(s[r].x=g.x,s[r].name=f,s[r].xValues[b]=g.x;D<p;)h=d[D],c=e.pointClass.prototype.getNestedProperty.apply(g,[h]),s[r][T+D]=C(y.categoryMap[h][c],y.dateTimeValueAxisMap[h]?i.dateFormat(n.dateFormat,c):null,c),D++}),T+=D}}),s)Object.hasOwnProperty.call(s,v)&&l.push(s[v]);for(y=t?[h,c]:[c],T=x.length;T--;)e=x[T][0],a=x[T][1],b=r[e],l.sort(function(t,a){return t.xValues[e]-a.xValues[e]}),S=g(b),y[0].splice(a,0,S),t&&y[1]&&y[1].splice(a,0,S),l.forEach(function(t){let e=t.name;b&&!D(e)&&(b.dateTime?(t.x instanceof Date&&(t.x=t.x.getTime()),e=i.dateFormat(n.dateFormat,t.x)):e=b.categories?C(b.names[t.x],b.categories[t.x],t.x):t.x),t.splice(a,0,e)});return E(this,"exportData",{dataRows:y=y.concat(l)}),y}function H(t){let e=t=>{if(!t.tagName||"#text"===t.tagName)return t.textContent||"";let a=t.attributes,o=`<${t.tagName}`;return a&&Object.keys(a).forEach(t=>{let e=a[t];o+=` ${t}="${e}"`}),o+=">",o+=t.textContent||"",(t.children||[]).forEach(t=>{o+=e(t)}),o+=`</${t.tagName}>`};return e(this.getTableAST(t))}function B(t){let e=0,a=[],o=this.options,i=t?1.1.toLocaleString()[1]:".",n=C(o.exporting.useMultiLevelHeaders,!0),r=this.getDataRows(n),s=n?r.shift():null,l=r.shift(),h=function(t,e){let a=t.length;if(e.length!==a)return!1;for(;a--;)if(t[a]!==e[a])return!1;return!0},c=function(t,e,a,o){let n=C(o,""),r="highcharts-text"+(e?" "+e:"");return"number"==typeof n?(n=n.toString(),","===i&&(n=n.replace(".",i)),r="highcharts-number"):o||(r="highcharts-empty"),{tagName:t,attributes:a=S({class:r},a),textContent:n}};!1!==o.exporting.tableCaption&&a.push({tagName:"caption",attributes:{class:"highcharts-table-caption"},textContent:C(o.exporting.tableCaption,o.title.text?o.title.text:"Chart")});for(let t=0,a=r.length;t<a;++t)r[t].length>e&&(e=r[t].length);a.push(function(t,e,a){let i=[],r=0,s=a||e&&e.length,l,d=0,p;if(n&&t&&e&&!h(t,e)){let a=[];for(;r<s;++r)if((l=t[r])===t[r+1])++d;else if(d)a.push(c("th","highcharts-table-topheading",{scope:"col",colspan:d+1},l)),d=0;else{l===e[r]?o.exporting.useRowspanHeaders?(p=2,delete e[r]):(p=1,e[r]=""):p=1;let t=c("th","highcharts-table-topheading",{scope:"col"},l);p>1&&t.attributes&&(t.attributes.valign="top",t.attributes.rowspan=p),a.push(t)}i.push({tagName:"tr",children:a})}if(e){let t=[];for(r=0,s=e.length;r<s;++r)void 0!==e[r]&&t.push(c("th",null,{scope:"col"},e[r]));i.push({tagName:"tr",children:t})}return{tagName:"thead",children:i}}(s,l,Math.max(e,l.length)));let d=[];r.forEach(function(t){let a=[];for(let o=0;o<e;o++)a.push(c(o?"td":"th",null,o?{}:{scope:"row"},t[o]));d.push({tagName:"tr",children:a})}),a.push({tagName:"tbody",children:d});let p={tree:{tagName:"table",id:`highcharts-data-table-${this.index}`,children:a}};return E(this,"aftergetTableAST",p),p.tree}function F(){this.toggleDataTable(!1)}function I(t){let e=(t=C(t,!this.isDataTableVisible))&&!this.dataTableDiv;if(e&&(this.dataTableDiv=w.createElement("div"),this.dataTableDiv.className="highcharts-data-table",this.renderTo.parentNode.insertBefore(this.dataTableDiv,this.renderTo.nextSibling)),this.dataTableDiv){let a=this.dataTableDiv.style,o=a.display;a.display=t?"block":"none",t?(this.dataTableDiv.innerHTML=m().emptyHTML,new(m())([this.getTableAST()]).addToDOM(this.dataTableDiv),E(this,"afterViewData",{element:this.dataTableDiv,wasHidden:e||o!==a.display})):E(this,"afterHideData")}this.isDataTableVisible=t;let a=this.exportDivElements,o=this.options.exporting,i=o&&o.buttons&&o.buttons.contextButton.menuItems,n=this.options.lang;if(o&&o.menuItemDefinitions&&n&&n.viewData&&n.hideData&&i&&a){let t=a[i.indexOf("viewData")];t&&m().setElementHTML(t,this.isDataTableVisible?n.hideData:n.viewData)}}function U(){this.toggleDataTable(!0)}function M(t,e){let a=T.navigator,o=T.URL||T.webkitURL||T;try{if(a.msSaveOrOpenBlob&&T.MSBlobBuilder){let e=new T.MSBlobBuilder;return e.append(t),e.getBlob("image/svg+xml")}return o.createObjectURL(new T.Blob(["\uFEFF"+t],{type:e}))}catch(t){}}function j(){let t=this,e=t.dataTableDiv,a=(t,e)=>t.children[e].textContent,o=(t,e)=>(o,i)=>{let n,r;return n=a(e?o:i,t),r=a(e?i:o,t),""===n||""===r||isNaN(n)||isNaN(r)?n.toString().localeCompare(r):n-r};if(e&&t.options.exporting&&t.options.exporting.allowTableSorting){let a=e.querySelector("thead tr");a&&a.childNodes.forEach(a=>{let i=a.closest("table");a.addEventListener("click",function(){let n=[...e.querySelectorAll("tr:not(thead tr)")],r=[...a.parentNode.children];n.sort(o(r.indexOf(a),t.ascendingOrderInTable=!t.ascendingOrderInTable)).forEach(t=>{i.appendChild(t)}),r.forEach(t=>{["highcharts-sort-ascending","highcharts-sort-descending"].forEach(e=>{t.classList.contains(e)&&t.classList.remove(e)})}),a.classList.add(t.ascendingOrderInTable?"highcharts-sort-ascending":"highcharts-sort-descending")})})}}function P(){this.options&&this.options.exporting&&this.options.exporting.showTable&&!this.options.chart.forExport&&this.viewData()}function K(){this.dataTableDiv?.remove()}let q=s();q.dataURLtoBlob=q.dataURLtoBlob||u.dataURLtoBlob,q.downloadURL=q.downloadURL||u.downloadURL,({compose:function(t,e){let a=t.prototype;if(!a.getCSV){let o=x().exporting;v(t,"afterViewData",j),v(t,"render",P),v(t,"destroy",K),a.downloadCSV=O,a.downloadXLS=R,a.getCSV=N,a.getDataRows=V,a.getTable=H,a.getTableAST=B,a.hideData=F,a.toggleDataTable=I,a.viewData=U,o&&(S(o.menuItemDefinitions,{downloadCSV:{textKey:"downloadCSV",onclick:function(){this.downloadCSV()}},downloadXLS:{textKey:"downloadXLS",onclick:function(){this.downloadXLS()}},viewData:{textKey:"viewData",onclick:function(){k.call(this,this.toggleDataTable)}}}),o.buttons&&o.buttons.contextButton.menuItems&&o.buttons.contextButton.menuItems.push("separator","downloadCSV","downloadXLS","viewData")),b(f);let{arearange:i,gantt:n,map:r,mapbubble:s,treemap:l,xrange:h}=e.types;i&&(i.prototype.keyToAxis={low:"y",high:"y"}),n&&(n.prototype.exportKey="name",n.prototype.keyToAxis={start:"x",end:"x"}),r&&(r.prototype.exportKey="name"),s&&(s.prototype.exportKey="name"),l&&(l.prototype.exportKey="name"),h&&(h.prototype.keyToAxis={x2:"x"})}}}).compose(q.Chart,q.Series);let W=s();return n.default})());