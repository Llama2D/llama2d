const assert = (condition, message) => {
    if(!condition) throw new Error(message)
}

const elIsClean = (el) => {
    if(el.style && el.style.display === 'none') return false
    if(el.hidden) return false
    if(el.disabled) return false

    const rect = el.getBoundingClientRect()
    if(rect.width === 0 || rect.height === 0) return false

    if(el.tagName === 'SCRIPT') return false
    if(el.tagName === 'STYLE') return false

    return true;
}

const inputs = ['a', 'button', 'textarea', 'select', 'details', 'label']
const _isInteractible = (el) => inputs.includes(el.tagName.toLowerCase()) ||
    (el.tagName.toLowerCase() === 'input' && el.type !== 'hidden') ||
    el.role === 'button' ||
    el.computedStyleMap().get("cursor") == "pointer" && !(el.parentElement && el.parentElement.computedStyleMap().get("cursor") === "pointer")

const isInteractible = (el) => _isInteractible(el) || el.parentElement && isInteractible(el.parentElement);

const emptyTagWhitelist = ["input","textarea","select","button","a"]
const isEmpty = (el) => {
    const tagName = el.tagName.toLowerCase()
    if(emptyTagWhitelist.includes(tagName)) return false
    if("innerText" in el && el.innerText.trim().length === 0) {
        // look for svg or img in the element
        const svg = el.querySelector("svg")
        const img = el.querySelector("img")

        if(svg || img) return false

        return true
    }

    return false
}

window.tagifyWebpageOneEl = (gtCls, gtId, gtBbox) => tagifyWebpage([{
    cls: gtCls,
    tag_id: gtId,
    bbox_rect: gtBbox
}])

const convertHoverToCls = () => {
    [...document.styleSheets].forEach(sheet=>{
        try{
        [...sheet.cssRules].forEach(rule=>{
            if(rule.selectorText) rule.selectorText = rule.selectorText.replace(/:hover/g,".mind2web-hover")
        })
        } catch(err){
            if(!(err+"").includes("Cannot access rules")) throw err;
        }
    })
}

window.tagifyWebpage = (gtEls,useGt=true,rawHtml="") =>{

    // Populate mHTML input values with raw_html from action JSON
    if(rawHtml.length>0){
        // parse html
        const parser = new DOMParser();
        const htmlDoc = parser.parseFromString(rawHtml, 'text/html');

        [...htmlDoc.querySelectorAll("[input_value], [input_checked]")].forEach(el=>{
            if(el.attributes.bounding_box_rect.value==="-1,-1,-1,-1") return;
            
            // get the position of the input on the page
            const classNames = [...el.classList].map(cls=>"."+cls).join("");
        
            const id = [el.id].filter(e=>e).map(id=>"#"+id)
            console.log(el.id,el.attributes.id)
            const tag = el.tagName.toLowerCase();
        
            const selector = `${tag}${classNames}${id}`;
        
            const fragmentMatches = htmlDoc.querySelectorAll(selector)
            const numMatchesInFragment = fragmentMatches.length;
            const fragmentIdx = [...fragmentMatches].indexOf(el);
        
            if(fragmentIdx<0) throw new Error("Could not find element with its own selector");
        
            const docMatches = document.querySelectorAll(selector);
            if(docMatches.length != fragmentMatches.length) throw new Error(`Mismatched lengths: ${docMatches.length} vs. ${fragmentMatches.length}: ${selector}`);
            const docEl = docMatches[fragmentIdx];
        
            // if has input_value, set docEl.value
            if("input_value" in el.attributes) {
                docEl.value = el.attributes.input_value.value;
            }
            else if("input_checked" in el.attributes) docEl.checked = el.attributes.input_checked.value;
            else {
                throw new Error("didn't find things");
            }
            
        })
    }

    convertHoverToCls();

    let numTagsSoFar = 0;

    let gtCandidates = [];

    let elTags = [];

    const validEls = new Set();
    const hasValidParent = el => validEls.has(el) || (el.parentElement && hasValidParent(el.parentElement));

    for(let el of document.body.querySelectorAll("*")){

        const stringifiedClasses = el.classList.toString();

        const gtMatches = gtEls.filter(({cls,tag_id,bbox_rect})=>(cls===null || stringifiedClasses===cls) && (tag_id===null || el.id === tag_id));
        const isGt = gtMatches.length > 0;

        el.classList.add("mind2web-hover")

        const empty = isEmpty(el);
        const dirty = !elIsClean(el);
        const uninteractible = !isInteractible(el);
        const validParent = hasValidParent(el)

        el.classList.remove("mind2web-hover")

        if(logElements.includes(el)) {
            console.log(`Logging ${el.innerText}, ${empty},${dirty},${uninteractible},${validParent}`)
        }

        const isGood = !(empty || dirty || uninteractible) || validParent;
        if(isGood) validEls.add(el);

        if(!isGood){
            if(isGt) console.log("Skipping!", el,`empty: ${empty}, dirty: ${dirty}, uninteractible: ${uninteractible}, validParent: ${validParent}`);
            continue;
        }

        if(isGt){
            console.log("Tagging GT!", el);
            gtCandidates.push({
                el,
                tagId: numTagsSoFar,
                stats:{empty, dirty, uninteractible, validParent},
                gtEls: gtMatches
            });
        }

        const tagStr = `[${numTagsSoFar}] `

        const elBbox = el.getBoundingClientRect();
        const elCenter = [elBbox.left + elBbox.width/2, elBbox.top + elBbox.height/2];
        elTags.push({
            word:tagStr,
            coords:elCenter,
        })
        validEls.add(el);

        numTagsSoFar++;
    }
        console.log(validEls)

    if(!useGt) return [null, elTags];



    const validGtCandidates = gtCandidates.filter(({el, stats}) => {
        const {empty, dirty, uninteractible, validParent} = stats
        return !empty && !dirty && !uninteractible || validParent
    })

    if(validGtCandidates.length === 0){
        console.log("No GT found!")
        // show stats for all candidates
        console.log(gtCandidates.map(({stats})=>`empty: ${stats.empty}, dirty: ${stats.dirty}, uninteractible: ${stats.uninteractible}`).join("\n"));
        throw new Error(`No GT found!\n${gtCandidates.map(({el})=>el.innerText).join("\n")}`)
    }

    if(validGtCandidates.length > 1){
        console.log("Multiple GTs found!")
    }

    const elementDistancesDeep = validGtCandidates.map(({el,gtEls}) => gtEls.map(({bbox_rect})=>bbox_rect).map((gtBbox)=>{
        const rect = el.getBoundingClientRect()
        const [x,y,w,h] = gtBbox;
        const gtCenter = [x+w/2, y+h/2];
        const elCenter = [rect.left + rect.width/2, rect.top + rect.height/2];

        const dx = gtCenter[0] - elCenter[0];
        const dy = gtCenter[1] - elCenter[1];
        return Math.sqrt(dx*dx + dy*dy)
    }))

    const elementDistances = elementDistancesDeep.map((distances)=>Math.min(...distances));

    const closestDistance = Math.min(...elementDistances);
    const closestElement = validGtCandidates[elementDistances.indexOf(closestDistance)];

    if(closestDistance > 10) {
        throw new Error(`Closest element is ${closestDistance}px away! Bboxes are ${validGtCandidates.map(({el})=>el.getBoundingClientRect()).map(({left, top, width, height})=>[left, top, width, height])})}}`);
    }


    return [closestElement.tagId, elTags];
}
logElements=[]; // some elements where you can check your classification performance. useful for debugging.

// window.showTag = coords => {
//     myBox = document.createElement("div")
//     myBox.style.width = "10px";
//     myBox.style.height = "10px";
//     myBox.style.background = "red";
//     myBox.style.position = "absolute";
//     myBox.style.top = coords[1]-5+"px";
//     myBox.style.left = coords[0]-5+"px";
//     myBox.textContent = "";
//     myBox.style.zIndex = 2000
//     document.body.appendChild(myBox)
// }

