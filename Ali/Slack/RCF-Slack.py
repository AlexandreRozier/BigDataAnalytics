var url = require('url');
var https = require('https');
var util = require('util');

var POST_OPTIONS = {
    hostname: 'hooks.slack.com',
    path: '/services/TDMT5GBMM/BG2GT6M39/2PaEG28N9X7lczXVlNc7QSZc',
    method: 'POST',
  };

exports.handler = (event, context, callback) => {
    const message = {
        channel: event.Records[0].Sns.Subject || '#aws',
        text: event.Records[0].Sns.Message
    };
    console.log('From SNS:', message);
    var r = https.request(POST_OPTIONS, function(res) {
                        res.setEncoding('utf8');
                        res.on('data', function (data) {
                            context.succeed("Message Sent: " + data);
                     });
    }).on("error", function(e) {context.fail("Failed: " + e);} );
    r.write(util.format("%j", message));
    r.end();
};