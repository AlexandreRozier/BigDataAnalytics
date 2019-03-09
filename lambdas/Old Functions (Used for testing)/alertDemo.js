const axios = require('axios');

exports.handler = function (event, context) {
  //const message = event.Records[0].Sns.Message
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
  
  console.log("Will call our friends at ChatBoT: %j", request);
  axios.post(url, request, {headers: headers})
  .then(function (response) {
    console.log('Alles Gut!');
    console.log(response);
  })
  .catch(function (error) {
    console.log('Oh no something went wrong!');
    console.log(error);
  });
}