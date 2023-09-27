document.body.onload = ()=>{

console.log("hey")

        // listen for updates to the textarea
        // when it updates, extract [input_ids,coords,labels,attention_mask] from the textarea
        const textarea = document.querySelector('textarea');

        textarea.addEventListener('input', function () {
            render();
        });

        const canvas = document.getElementById('rendered-output');
        const ctx = canvas.getContext('2d');

        window.render = ()=>{
            const text = textarea.value;
            // split text into newlines, parse each as JSON
            const lines = text.split('\n').filter(line=>line.trim().length>0);
            const [tokenIds, coords, labels, attentionMask] = lines.map(JSON.parse);

            const lastIdx = tokenIds.findLastIndex(i=>i>0)
            const firstIdxLastChunk = tokenIds.slice(0,lastIdx).findLastIndex(i=>i<=0)+1

            // console.log(lastIdx,firstIdxLastChunk)
            // console.log(labelIds.slice(firstIdxLastChunk,lastIdx+1))
            // console.log(llamaTokenizer.decode([0,...tokenIds.slice(0,firstIdxLastChunk)]))

            const prompt = llamaTokenizer.decode([0,...tokenIds.slice(0,firstIdxLastChunk)])

            const completion = llamaTokenizer.decode([0,...tokenIds.slice(firstIdxLastChunk,lastIdx+1)])

            const coordTokens = coords.map(([x,y],i)=>[x,y,tokenIds[i]]).filter(([x,y,tokenid])=>x>=0);

            /*
            python impl:
                # graph tokens with coords in a matplotlib figure
    # print the tokens without coords

    # every word has a few tokens with the same coord.
    # we should generate the word, turn it into a string, then plot it at the coord

    without_coords = [input_ids[i] for i in range(len(input_ids)) if coords[i][0] == -1 and attention_mask[i] == 1]

    with_coords = [(input_ids[i],coords[i]) for i in range(len(input_ids)) if coords[i][0] != -1 and attention_mask[i] == 1]
    # split with_coords into words - where a word is a list of tokens with the same coord
    words = []
    current_word = []
    current_coord = None
    for token in with_coords:
        if current_coord is None or (token[1] != current_coord).any():
            if len(current_word) > 0:
                words.append(current_word)
            current_word = []
            current_coord = token[1]
        current_word.append(token)
    words.append(current_word)


    # plot with_coords as text on a matplotlib figure

    fig = plt.figure()
    # make fig very big
    fig.set_size_inches(20,20)

    ax = fig.add_subplot(111)
    ax.set_xlim([0,1])
    ax.set_ylim([0,1])
    ax.set_aspect('equal')

    for word in words:
        word_str = "".join(tokenizer.convert_ids_to_tokens([i[0] for i in word]))
        word_coord = word[0][1]
        # very small text
        ax.text(word_coord[0],-word_coord[1],word_str,fontsize=10)
    
    # save the figure
    fig.savefig("tokens_with_coords.png")

            */

            const words = coordTokens.reduce((acc,[x,y,tokenid])=>{
                if(acc.length === 0 || acc[acc.length-1].length === 0 || acc[acc.length-1][0][0] !== x || acc[acc.length-1][0][1] !== y){
                    acc.push([])
                }
                acc[acc.length-1].push([x,y,tokenid])
                return acc
            },[])

            const wordStrings = words.map(word=>llamaTokenizer.decode([0,...word.map(([x,y,tokenid])=>tokenid)]))

            const wordCoords = words.map(word=>word[0].slice(0,2))

            // clear canvas, map onto canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.textAlign = "center";
            ctx.font = '10px monospace';

            const canvasCoords = wordCoords.map(([x,y])=>[x*canvas.width,(1-y)*canvas.height])
            wordCoords.forEach(([x,y],i)=>{
                const wordString = wordStrings[i];
                ctx.fillStyle = wordString.match(/^\[\d+\]/) ? 'red' : 'black';
                ctx.fillText(wordStrings[i],canvasCoords[i][0],canvasCoords[i][1])
            })

            // paste non-coord tokens into the pre
            // the first line is the prompt
            // the second line is the completion
            // find prompt vs. completion using firstIdxLastChunk

            const promptTokens = tokenIds.map((tokenId,i)=>[tokenId,coords[i][0],i<firstIdxLastChunk]).filter(([tokenId,x])=>x<0).filter(([_,__,b])=>b).map(([tokenId,x])=>tokenId)
            const completionTokens = [0,...tokenIds.slice(firstIdxLastChunk,lastIdx+1).filter(i=>i>0)];

            const promptString = llamaTokenizer.decode(promptTokens);
            const completionString = llamaTokenizer.decode(completionTokens);

            const output = document.getElementById('output');
            output.innerText = promptString + '\n' + completionString;

            console.log(llamaTokenizer.decode(tokenIds))
        }

        setTimeout(render, 500);
    }