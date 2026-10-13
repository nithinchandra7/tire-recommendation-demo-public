const {test}=require("node:test");
const assert=require("node:assert/strict");
const {escape,money,comparisonRows}=require("../../dist/tire-demo/helpers.js");
test("warehouse and user text is escaped before HTML rendering",()=>{assert.equal(escape('<script x="a">&\'</script>'),"&lt;script x=&quot;a&quot;&gt;&amp;&#39;&lt;/script&gt;");});
test("comparison contains factual price, stock and freshness",()=>{const rows=comparisonRows([{brand:"Demo",name:"Product",price:125.5,size:"225/55R17",load_index:98,speed_symbol:"V",season:"all-season",available_quantity:4,location_name:"Loop",lead_days:1,age_minutes:12,comfort:7,wet_grip:8}]);assert.equal(rows[1][1],"$125.50");assert.equal(rows[4][1],4);assert.equal(rows[7][1],"12 minutes");assert.equal(money(0),"$0.00");});
