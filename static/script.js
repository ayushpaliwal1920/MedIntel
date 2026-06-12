const sendBtn = document.getElementById("send-btn");
const userInput = document.getElementById("user-input");
const chatArea = document.getElementById("chat-area");

// Escape user/bot text before inserting into the DOM to prevent XSS
function escapeHTML(str){
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function addUserMessage(message){

    const wrapper = document.createElement("div");
    wrapper.className = "message user";

    const text = document.createElement("div");
    text.className = "text";
    text.innerHTML = escapeHTML(message);

    wrapper.appendChild(text);
    chatArea.appendChild(wrapper);
}

function addBotMessage(message){

    const wrapper = document.createElement("div");
    wrapper.className = "message bot";

    const text = document.createElement("div");
    text.className = "text";
    text.innerHTML = escapeHTML(message);

    wrapper.appendChild(text);
    chatArea.appendChild(wrapper);
}

function showTyping(){

    const typing = document.createElement("div");
    typing.className = "typing";
    typing.id = "typing";
    typing.innerHTML = "<span></span><span></span><span></span>";
    chatArea.appendChild(typing);
}

function removeTyping(){

    const typing = document.getElementById("typing");

    if(typing){
        typing.remove();
    }
}

function scrollToBottom(){
    chatArea.scrollTop = chatArea.scrollHeight;
}

function setInputState(disabled){
    userInput.disabled = disabled;
    sendBtn.disabled = disabled;
}

async function sendMessage(){

    const message = userInput.value.trim();

    if(message === ""){
        return;
    }

    document.querySelector(".welcome")?.remove();

    addUserMessage(message);
    userInput.value = "";
    scrollToBottom();

    setInputState(true);
    showTyping();

    try{

        const response = await fetch("/get",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                message:message
            })
        });

        if(!response.ok){
            throw new Error("Request failed");
        }

        const data = await response.json();

        removeTyping();
        addBotMessage(data.answer ?? "Sorry, I couldn't generate a response.");

    }
    catch(error){

        removeTyping();
        addBotMessage("Sorry, something went wrong while processing your request. Please try again.");
    }
    finally{
        setInputState(false);
        userInput.focus();
        scrollToBottom();
    }
}

sendBtn.addEventListener("click", sendMessage);

userInput.addEventListener("keypress", function(event){

    if(event.key === "Enter"){
        sendMessage();
    }
});

function askSuggestion(question){
    userInput.value = question;
    sendMessage();
}

function newChat(){
    location.reload();
}