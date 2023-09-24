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
    el.role === 'button'
const isInteractible = (el) => _isInteractible(el) || el.parentElement && isInteractible(el.parentElement);

const emptyTagWhitelist = ["input","textarea","select","button"]
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

window.tagifyWebpage = (gtCls, gtId, gtBbox) =>{

    let numTagsSoFar = 0;

    let gtCandidates = [];

    let elTags = [];

    for(let el of document.body.querySelectorAll("*")){

        const stringifiedClasses = el.classList.toString();
        const isGt = (gtCls===null || stringifiedClasses===gtCls) && (gtId===null || el.id === gtId);

        const empty = isEmpty(el);
        const dirty = !elIsClean(el);
        const uninteractible = !isInteractible(el);


        if(logElements.includes(el)) {
            console.log(`Logging ${el.innerText}, ${empty},${dirty},${uninteractible}`)
        }

        if(empty || dirty || uninteractible){
            console.log("Skipping!", el);
            continue;
        }

        if(isGt){
            console.log("Tagging GT!", el);
            gtCandidates.push({
                el,
                tagId: numTagsSoFar,
                stats:{empty, dirty, uninteractible}
            });
        }

        const tagStr = `[${numTagsSoFar}] `

        const elBbox = el.getBoundingClientRect();
        const elCenter = [elBbox.left + elBbox.width/2, elBbox.top + elBbox.height/2];
        elTags.push({
            word:tagStr,
            coords:elCenter,
        })

        numTagsSoFar++;
    }

    const validGtCandidates = gtCandidates.filter(({el, stats}) => {
        const {empty, dirty, uninteractible} = stats
        return !empty && !dirty && !uninteractible
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

    const elementDistances = validGtCandidates.map(({el}) => {
        const rect = el.getBoundingClientRect()
        const [x,y,w,h] = gtBbox;
        const gtCenter = [x+w/2, y+h/2];
        const elCenter = [rect.left + rect.width/2, rect.top + rect.height/2];

        const dx = gtCenter[0] - elCenter[0];
        const dy = gtCenter[1] - elCenter[1];
        return Math.sqrt(dx*dx + dy*dy)
    })

    const closestDistance = Math.min(...elementDistances);
    const closestElement = validGtCandidates[elementDistances.indexOf(closestDistance)];

    if(closestDistance > 50) {
        throw new Error(`Closest element is ${closestDistance}px away! Bboxes are ${validGtCandidates.map(({el})=>el.getBoundingClientRect()).map(({left, top, width, height})=>[left, top, width, height])})}}`);
    }

    return [closestElement.tagId, elTags];
}
logElements=[]; // some elements where you can check your classification performance. useful for debugging.