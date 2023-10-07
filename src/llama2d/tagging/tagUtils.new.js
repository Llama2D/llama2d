const assert = (condition, message) => {
    if(!condition) throw new Error(message)
}

const isVisible = (el) => {
    if(el.style && el.style.display === 'none') return false
    if(el.hidden) return false
    if(el.disabled) return false

    const rect = el.getBoundingClientRect()
    if(rect.width === 0 || rect.height === 0) return false

    // make sure the element is at "the top"
    const elCenter = [rect.left + rect.width/2, rect.top + rect.height/2];
    if(elCenter[0] < 0 || elCenter[0] > window.innerWidth || elCenter[1] < 0 || elCenter[1] > window.innerHeight) return false
    const elAtPoint = document.elementFromPoint(...elCenter)
    if(!el.contains(elAtPoint)) return false

    if(el.tagName === 'SCRIPT') return false
    if(el.tagName === 'STYLE') return false

    return true;
}

const getCursor = (el) => el.computedStyleMap().get("cursor")+""
// const hasCursor = (el, cursor) => el.computedStyleMap().get("cursor") === cursor

const typeableTags = ["input","textarea"]
const getClickType = (el,isGt) =>{
    const tagName = el.tagName.toLowerCase()
    const cursor = getCursor(el)

    if(cursor === "pointer" && (isGt || getCursor(el.parentElement) !== "pointer")) {
        return "click"
    }

    if(cursor === "text") {
        if(typeableTags.includes(tagName)) return "type"
        if(el.contentEditable==='true') return "edit"
    }

    return null;
}

window.tagifyWebpageOneEl = (gtCls, gtId, gtBbox) => tagifyWebpage([{
    cls: gtCls,
    tag_id: gtId,
    bbox_rect: gtBbox
}])

const convertHoverToCls = () => 
    [...document.styleSheets].forEach(sheet=>{
        try{
        [...sheet.cssRules].forEach(rule=>{
            if(rule.selectorText) rule.selectorText = rule.selectorText.replace(/:hover/g,".mind2web-hover")
        })
        } catch(err){
            if(!(err+"").includes("Cannot access rules")) throw err;
        }
    })


const convertClsToHover = () => 
    [...document.styleSheets].forEach(sheet=>{
        try{
        [...sheet.cssRules].forEach(rule=>{
            if(rule.selectorText) rule.selectorText = rule.selectorText.replace(/\.mind2web-hover/g,":hover")
        })
        } catch(err){
            if(!(err+"").includes("Cannot access rules")) throw err;
        }
    });

const populateWebpageInputs = (rawHtml) => {
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
        
            if(fragmentIdx<0) throw new Error(`Could not find element with its own selector!! ${selector}`);
        
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

}

window.tagifyWebpage = (gtEls,useGt=true,rawHtml="",value=null) =>{

    const isSelectEl = gtEls.length === 1 && gtEls[0].tag === "select";

    populateWebpageInputs(rawHtml);

    convertHoverToCls();

    let numTagsSoFar = 0;

    let gtCandidates = [];
    let gtOptionId = null;

    let elTags = [];

    const validEls = new Set();
    const hasValidParent = el => validEls.has(el) || (el.parentElement && hasValidParent(el.parentElement));

    for(let el of document.body.querySelectorAll("*")){
        const tagName = el.tagName.toLowerCase()

        const stringifiedClasses = el.classList.toString();

        const gtMatches = gtEls.filter(({cls,tag_id,tag})=>(cls===null || stringifiedClasses===cls) && (tag_id===null || el.id === tag_id) && (tag===null || tagName === tag));
        const isGt = gtMatches.length > 0;

        if(isGt) {
            el.classList.add("mind2web-tagged")
        }

        el.classList.add("mind2web-hover")

        const visible = isVisible(el);
        const clickType = getClickType(el,isGt);

        el.classList.remove("mind2web-hover")

        if(logElements.includes(el)) {
            console.log(`Logging visible=${visible}, clickType=${clickType}, cursor=${getCursor(el)}`)
        }

        const validParent = hasValidParent(el)
        const isValid = visible && clickType !== null;
        if(isValid) validEls.add(el);
        else {
            if(isGt) console.log("Skipping GT!", el,`visible: ${visible}, clickType: ${clickType}`);
            continue;
        }

        const elBbox = el.getBoundingClientRect();
        const elCenter = [elBbox.left + elBbox.width/2, elBbox.top + elBbox.height/2];

        // get closest el in elTags
        const [closestDist,closestEl] = elTags.map(({coords})=>coords).map(([x,y])=>Math.sqrt((x-elCenter[0])*(x-elCenter[0]) + (y-elCenter[1])*(y-elCenter[1]))).reduce((acc,cur,i)=>cur<acc[0]?[cur,i]:acc,[Infinity,-1]);
        const useNewTag = closestDist > 0 || isGt;

        if(isGt){
            const gtTagId = useNewTag ? numTagsSoFar : closestEl;
            console.log("Tagging GT!", el);
            gtCandidates.push({
                el,
                tagId: gtTagId,
                stats:{visible, clickType, tagName, validParent, isValid},
                gtEls: gtMatches
            });
        }

        if(useNewTag){

            const tagStr = `[${numTagsSoFar}/${clickType}/${tagName}] `

            elTags.push({
                word:tagStr,
                coords:elCenter,
            })
            validEls.add(el);

            numTagsSoFar++;
        }

        if(tagName === "select"){
            // place one tag for each option - moving linearly down the page

            const children = [...el.children];
            assert(children.every(child=>child.tagName.toLowerCase()==="option"), "select children are not all options!")

            const optionHeight = 15;

            const optionTags = children.map((child,i)=>{
                const childCenter = [elCenter[0], elCenter[1] + i*optionHeight];
                const ret = {
                    word: `[${numTagsSoFar}/option/${child.innerText}]`,
                    coords: childCenter
                }

                if(child.innerText === value) gtOptionId = numTagsSoFar;

                numTagsSoFar++;
                return ret;
            });

            elTags.push(...optionTags);
        }
    }
        console.log(validEls)

        validEls.forEach(highlightEl);

    convertClsToHover();

    if(!useGt) return [null, elTags];
    if(gtCandidates.length === 0){
        console.log("No GT found!")
        // show stats for all candidates
        console.log(gtCandidates.map(({stats})=>`empty: ${stats.empty}, dirty: ${stats.dirty}, uninteractible: ${stats.uninteractible}`).join("\n"));
        throw new Error(`No GT found!\n${gtCandidates.map(({el})=>el.innerText).join("\n")}`)
    }

    const elementDistancesDeep = gtCandidates.map(({el,gtEls}) => gtEls.map(({bbox_rect})=>bbox_rect).map((gtBbox)=>{
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
    const closestElement = gtCandidates[elementDistances.indexOf(closestDistance)];

    if(closestDistance > 40) {
        throw new Error(`Closest element is ${closestDistance}px away! Bboxes are ${gtCandidates.map(({el})=>el.getBoundingClientRect()).map(({left, top, width, height})=>[left, top, width, height])})}}`);
    }

    console.log("closestElement",closestElement)

    const tagId = isSelectEl ? gtOptionId : closestElement.tagId;

    return [tagId, elTags];
}
logElements=[]; // some elements where you can check your classification performance. useful for debugging.

// add mind2web-tagged style
const style = document.createElement('style');
style.innerHTML = `
.mind2web-tagged {
    background: yellow;
    border: 1px solid black;
}
`;

document.head.appendChild(style);

const highlightEl = (el) => {
    el.classList.add("mind2web-tagged");
}

const clearTags = () => {
    [...document.body.querySelectorAll(".mind2web-tagged")].forEach(el=>el.classList.remove("mind2web-tagged"));
    // remove mind2web-tag
    [...document.body.querySelectorAll(".mind2web-tag")].forEach(el=>el.remove());
}

const showBox = (box) => {
    const [x,y,w,h] = box;
    const myBox = document.createElement("div")
    myBox.style.width = w+"px";
    myBox.style.height = h+"px";
    myBox.style.border = "red 1px solid";
    myBox.style.position = "absolute";
    myBox.style.top = y+"px";
    myBox.style.left = x+"px";

    // make cursor pass through
    myBox.style.pointerEvents = "none";

    myBox.textContent = "";
    myBox.style.zIndex = 2000
    document.body.appendChild(myBox)
}

window.showTag = coords => {
    myBox = document.createElement("div")
    myBox.style.width = "10px";
    myBox.style.height = "10px";
    myBox.style.background = "red";
    myBox.style.position = "absolute";
    myBox.style.top = coords[1]-5+"px";
    myBox.style.left = coords[0]-5+"px";
    myBox.classList.add("mind2web-tag")
    myBox.textContent = "";
    myBox.style.zIndex = 2000
    document.body.appendChild(myBox)
}

window.demo = () => tagifyWebpage([],false)[1].forEach(({coords})=>showTag(coords))
1;


