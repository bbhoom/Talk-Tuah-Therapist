// Get elements from the DOM
const submitButton = document.getElementById('submitButton');
const textInput = document.getElementById('textInput');
const historyList = document.getElementById('historyList');

// Add event listener to the submit button
submitButton.addEventListener('click', function () {
    const inputText = textInput.value.trim();

    if (inputText) {
        // Add the input text to the history
        const newItem = document.createElement('li');
        newItem.textContent = inputText;
        historyList.appendChild(newItem);

        // Clear the input field
        textInput.value = '';
    } else {
        alert('Please enter some text!');
    }
});
    
