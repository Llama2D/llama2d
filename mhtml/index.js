const { Parser } = require("fast-mhtml");
const p = new Parser({
  rewriteFn: (url)=>{
    // set base url to localhost:8080
  }, // default, urls are rewritten with this function
});


const {readFileSync,writeFileSync} = require('fs');

const mhtmlFileContents = readFileSync('./finance.mhtml'); // read file
const files = p.parse(mhtmlFileContents) // parse file
 .rewrite() // rewrite all links
 .spit(); // return all content

 console.log(result)

 writeFileSync('./finance.json', JSON.stringify(result,null,2)); // write file


 // mkdir -p ./finance
 const {join} = require('path');
  const {mkdirSync} = require('fs');
  mkdirSync('./finance',{recursive:true});

  files.forEach(({filename,content})=>{