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
const isInteractible = (el) => inputs.includes(el.tagName.toLowerCase()) ||
    (el.tagName.toLowerCase() === 'input' && el.type !== 'hidden') ||
    el.role === 'button'

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

window.tagifyWebpage = (gtCls, gtId) =>{

    let numTagsSoFar = 0;
    let gtTagId = null;

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
            assert(!isGt, `GT element is marked as unclean or uninteractible. empty=${empty}, dirty=${dirty}, uninteractible=${uninteractible}`)
            continue
        }

        if(isGt){
            console.log("Tagging GT!", el);
            assert(gtTagId === null, "Multiple GTs found!")
            gtTagId = numTagsSoFar;
        }

        const specialTags = ["input", "textarea", "select"];

        const tagLower = el.tagName.toLowerCase();
        const tagStr = `[${numTagsSoFar}] `

        if(!specialTags.includes(tagLower)){
            el.prepend(new Text(tagStr));
            // el.innerText = tagStr + el.innerText
        }
        else if(tagLower === "textarea" || tagLower === "input"){
            if(el.value.length === 0)
                el.placeholder = tagStr + el.placeholder
            else el.value = tagStr + el.value
        }
        else if(tagLower === "select"){
            // leave select blank - we'll give a tag ID to the options
        }

        numTagsSoFar++;
    }

    return gtTagId;
}
logElements=[]; // some elements where you can check your classification performance. useful for debugging.