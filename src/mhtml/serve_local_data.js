const express = require('express');
const { Parser } = require("fast-mhtml");
const fs = require('fs');

const filenamify = require('filenamify');

const { join } = require('path');
const mhtmlDir = join(__dirname, '../../data/mind2web-mhtml');
// const mhtmlDir = join(__dirname, 'demos');

const sentinel = 'mind2web_local_serve:'

const app = express();
const fileCache = new Map();
app.get('/:path', (req, res) => {

    const file = req.params.path;

    if (file.endsWith('mhtml')) { // main file
    fileCache.clear(); // empty cache

    let base = null;

    const parser = new Parser({
        rewriteFn: (url) => {
            if(new URL(url,`http://localhost:${port}/`).protocol.startsWith('http')) {
                return url;
            }
            return sentinel+filenamify(url);
        }
    });
    // const fp = promised(fs.readFile, `${mhtmlDir}/${file}`);
    const fp = fs.promises.readFile(`${mhtmlDir}/${file}`);
    fp.then((data) => parser.parse(data).rewrite().spit()).then((spitFiles) => {
        for (const result of spitFiles) {
        fileCache.set(result.filename.replace(/#.*/, ''), result); // remove hash and set in cache
        }
        res.setHeader('Content-Type', spitFiles[0].type);
        res.send(spitFiles[0].content);
        res.end();
    }).catch((err) => {
        res.status(500);
        res.send(`Error: ${err}<br />${err.stack.replace(/\n/, '<br />')}`);
        res.end();
    });
    return;
    }

    // redirect to URL in path
    if(!file.startsWith(sentinel) && (file.includes(".css") || file.includes(".js"))){
        return res.redirect(file);
    }

    const result = fileCache.get(file);
    if (!result) {
    res.status(404);
    res.send(`MISS ${file} FROM${JSON.stringify(fileCache.keys())}`);
    res.end();
    return;
    }
    res.setHeader('Content-Type', result.type);
    res.send(result.content);
    res.end();
});

const port = 5002;
app.listen(port,() => console.log('Listening on port '+port));