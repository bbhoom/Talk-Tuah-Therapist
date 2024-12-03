document.getElementById('submitButton').addEventListener('click', function() {
    const inputText = document.getElementById('textInput').value;
    document.getElementById('output').innerText = `You entered: ${inputText}`;
});