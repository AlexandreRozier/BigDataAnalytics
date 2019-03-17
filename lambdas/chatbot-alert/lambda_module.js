const axios = require('axios');

exports.handler = function (event, context) {
  const message = event.message

  notifySlack(message)
  
  const chatBoxURL = process.env['CHATBOX_URL']
  if (chatBoxURL) {
    notifyChatBot(chatBoxURL, message)
  }
}

function notifySlack(message) {
  const request = {text: message} 
  const url = process.env['SLACK_URL']
  axios.post(url, request)
}

function notifyChatBot(url, message) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer xyz' 
  }
  const request = {
            status: 'firing',
            description: message,
            priority: 'high'
        }
  
  console.log("Calling ChatBoT: %j", request);
  axios.post(url, request, {headers: headers})
  .then(function (response) {
    console.log('Received response: %j', response);
    console.log(response);
  })
  .catch(function (error) {
    console.log('Failed to call ChatBot with error: %j', error);
    console.log(error);
  });
}
